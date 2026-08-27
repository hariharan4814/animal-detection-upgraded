"""
Detection Domain Services.
Orchestrates AI inference, snapshot persistence, AnimalLog record creation,
multi-tier threat classification, cooldown evaluation, and Alert triggering.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

from django.conf import settings
from django.utils import timezone

try:
    import cv2
except ImportError:
    cv2 = None

from apps.settings_app.models import ProjectSettings
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from services.yolo import is_model_available, run_inference, ANIMAL_CLASSES
from services.threat_classification import (
    ThreatLevel,
    classify_animal,
    get_threat_score,
    calculate_highest_threat,
)
from services.notifications.service import NotificationService

logger = logging.getLogger(__name__)

# In-memory alert cooldown tracker: {(animal_type, threat_tier): last_alert_epoch_timestamp}
_last_notification_timestamps: Dict[Tuple[str, str], float] = {}


def check_and_update_cooldown(
    animal_type: str,
    threat_tier: str,
    cooldown_window: int
) -> bool:
    """
    Evaluates whether an alert should be triggered based on cooldown window.
    Keys on (animal_type, threat_tier) to ensure low-threat events never suppress high-threat alerts.
    """
    key = (animal_type.strip().lower(), threat_tier.strip().upper())
    now_epoch = time.time()
    last_time = _last_notification_timestamps.get(key, 0.0)

    if (now_epoch - last_time) >= cooldown_window:
        _last_notification_timestamps[key] = now_epoch
        return True
    return False


def clear_cooldown_cache() -> None:
    """Resets in-memory notification timestamps (useful for tests)."""
    _last_notification_timestamps.clear()


class DetectionService:
    """
    Core service coordinating runtime animal detection, image analysis, and notification triggers.
    """

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """
        Retrieves consolidated detection engine runtime metadata and system configuration.
        """
        project_settings = ProjectSettings.get_settings()
        return {
            "detection_enabled": project_settings.detection_enabled,
            "engine_available": is_model_available(),
            "model_name": "YOLOv8n",
            "confidence_threshold": project_settings.detection_confidence_threshold,
            "camera_device_index": project_settings.camera_device_index,
            "alert_cooldown_seconds": project_settings.alert_cooldown_seconds,
            "audio_buzzer_enabled": project_settings.audio_buzzer_enabled,
            "email_alerts_enabled": project_settings.email_alerts_enabled,
            "attach_alert_image_to_email": project_settings.attach_alert_image_to_email,
            "supported_classes_count": len(ANIMAL_CLASSES),
            "supported_classes": ANIMAL_CLASSES
        }

    @classmethod
    def set_detection_enabled(cls, enabled: bool) -> Dict[str, Any]:
        """
        Updates the global detection toggle in ProjectSettings.
        """
        project_settings = ProjectSettings.get_settings()
        project_settings.detection_enabled = enabled
        project_settings.save(update_fields=['detection_enabled', 'updated_at'])
        return cls.get_status()

    @classmethod
    def analyze_image_bytes(
        cls,
        image_bytes: bytes,
        field_name: str = "Main Field",
        dispatch_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Processes an uploaded image through the YOLO detection pipeline.

        :param image_bytes: Raw binary bytes of an image (JPEG, PNG).
        :param field_name: Agricultural sector or camera location string.
        :param dispatch_sync: If True, dispatches notification synchronously (useful for test assertions).
        :return: Structured detection result dictionary including any created log and alert records.
        """
        project_settings = ProjectSettings.get_settings()

        if not project_settings.detection_enabled:
            return {
                "detection_enabled": False,
                "message": "Animal detection engine is currently disabled in system settings.",
                "detections_count": 0,
                "detections": [],
                "highest_threat_animal": None,
                "highest_threat_level": None,
                "animal_log": None,
                "alert_triggered": False
            }

        # Decode image bytes to numpy array
        image_array = None
        if cv2 is not None:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image_array is None:
            from PIL import Image
            import io
            try:
                pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                image_array = np.array(pil_image)
                if cv2 is not None:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            except Exception as decode_err:
                raise ValueError(f"Unable to decode image data: {decode_err}")

        # Execute YOLO inference
        inference_result = run_inference(
            image=image_array,
            confidence_threshold=project_settings.detection_confidence_threshold,
            threat_levels=project_settings.threat_level_overrides,
            annotate=True
        )

        detections = inference_result.get("detections", [])

        # Ensure threat classification on all parsed detections
        for det in detections:
            label = det.get('label') or det.get('animal')
            conf = det.get('confidence', 0.0)
            threat_upper = classify_animal(label, conf, custom_overrides=project_settings.threat_level_overrides)
            det['threat_tier'] = threat_upper
            det['threat_level'] = threat_upper.lower()

        highest_animal, highest_tier, highest_conf = calculate_highest_threat(detections)
        highest_tier = highest_tier or (inference_result.get("highest_threat_level") or "MEDIUM").upper()
        if highest_animal is None:
            highest_animal = inference_result.get("highest_threat_animal")
            highest_conf = inference_result.get("highest_conf", 0.0)

        animal_log_data = None
        alert_triggered = False
        alert_type = None
        created_alert_id = None

        if highest_animal:
            now_dt = timezone.now()
            current_epoch = time.time()

            # Generate and persist snapshot image
            filename = f"detected_{highest_animal}_{int(current_epoch)}.jpg"
            relative_storage_path = f"detections/{filename}"
            
            media_root = getattr(settings, 'MEDIA_ROOT', Path('media'))
            detections_dir = Path(media_root) / 'detections'
            detections_dir.mkdir(parents=True, exist_ok=True)
            full_image_path = detections_dir / filename

            annotated_frame = inference_result.get("annotated_frame", image_array)
            if cv2 is not None:
                cv2.imwrite(str(full_image_path), annotated_frame)
            else:
                from PIL import Image
                im = Image.fromarray(annotated_frame)
                im.save(str(full_image_path))

            # Create persistent AnimalLog record with classified threat_level
            animal_log = AnimalLog.objects.create(
                animal_type=highest_animal,
                confidence=highest_conf,
                threat_level=highest_tier,
                timestamp=now_dt,
                field=field_name or "Main Field",
                image_path=relative_storage_path
            )

            animal_log_data = {
                "id": animal_log.id,
                "animal_type": animal_log.animal_type,
                "confidence": animal_log.confidence,
                "threat_level": animal_log.threat_level,
                "timestamp": animal_log.timestamp.isoformat(),
                "field": animal_log.field,
                "image_path": animal_log.image_path
            }

            # Cooldown evaluation
            cooldown_window = project_settings.alert_cooldown_seconds
            cooldown_passed = check_and_update_cooldown(highest_animal, highest_tier, cooldown_window)

            # Determine alert dispatch policy
            if highest_tier == 'HIGH':
                alert_type = 'Email + Buzzer'
            elif highest_tier == 'MEDIUM':
                alert_type = 'Email'
            else:
                alert_type = 'Log Only'

            email_sent = False
            email_attempted = False
            email_status = "none"

            if cooldown_passed:
                alert = Alert.objects.create(
                    animal_log=animal_log,
                    threat_level=highest_tier,
                    alert_type=alert_type,
                    status='Triggered'
                )
                created_alert_id = alert.id
                alert_triggered = True

                # Dispatch notifications
                dispatch_res = NotificationService.dispatch_threat_alert(
                    alert_id=alert.id,
                    animal_name=highest_animal,
                    threat_level=highest_tier,
                    confidence=highest_conf,
                    detected_at=now_dt,
                    camera_name=field_name or "Main Field",
                    image_relative_path=relative_storage_path
                )
                email_sent = bool(dispatch_res.get("email_sent", False))
                email_attempted = bool(
                    project_settings.email_alerts_enabled and (highest_tier in ['HIGH', 'MEDIUM'])
                )
                if not project_settings.email_alerts_enabled:
                    email_status = "disabled"
                elif email_sent:
                    email_status = "sent"
                elif email_attempted:
                    email_status = "failed"
                else:
                    email_status = "none"
            else:
                email_attempted = False
                email_sent = False
                email_status = "cooldown"

        animal_detected = bool(highest_animal)
        if animal_detected:
            if not project_settings.email_alerts_enabled:
                message = f"Animal Detected: {highest_animal}. Detection has been recorded."
            elif email_sent:
                message = f"Animal Detected: {highest_animal}. Mail has been sent successfully."
            elif email_attempted:
                message = f"Animal Detected: {highest_animal}. Detection was recorded, but the email could not be sent."
            else:
                message = f"Animal Detected: {highest_animal}. Detection recorded."
        else:
            message = "No hazardous animals detected in frame."
            email_status = "none"

        return {
            "success": True,
            "detection_enabled": True,
            "animal_detected": animal_detected,
            "detections_count": len(detections),
            "detections": detections,
            "highest_threat_animal": highest_animal,
            "highest_threat_level": highest_tier.lower() if highest_tier else None,
            "highest_threat_tier": highest_tier,
            "highest_confidence": highest_conf,
            "animal_log": animal_log_data,
            "alert_triggered": alert_triggered,
            "alert_type": alert_type,
            "alert_id": created_alert_id,
            "email_notifications_enabled": project_settings.email_alerts_enabled,
            "email_attempted": email_attempted,
            "email_sent": email_sent,
            "email_status": email_status,
            "message": message,
        }


class VideoStreamService:
    """
    Provides multipart MJPEG frame streaming for real-time camera views.
    Handles device acquisition, error recovery, dynamic settings reflection, and camera toggles.
    """

    @classmethod
    def generate_frames(cls, max_frames: int | None = None):
        """
        Yields multipart HTTP MJPEG frame chunks continuously.
        Safely generates simulated canvas if physical camera hardware is unavailable.
        """
        project_settings = ProjectSettings.get_settings()
        camera_idx = project_settings.camera_device_index

        cap = None
        if cv2 is not None:
            try:
                cap = cv2.VideoCapture(camera_idx)
                if not cap.isOpened():
                    cap.release()
                    cap = None
            except Exception as e:
                logger.warning(f"Unable to open camera hardware index {camera_idx}: {e}")
                cap = None

        frames_yielded = 0

        try:
            while max_frames is None or frames_yielded < max_frames:
                project_settings = ProjectSettings.get_settings()

                if cap is not None and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if project_settings.detection_enabled:
                        inf = run_inference(
                            frame,
                            confidence_threshold=project_settings.detection_confidence_threshold,
                            threat_levels=project_settings.threat_level_overrides or None
                        )
                        frame = inf.get('annotated_frame', frame)

                    if cv2 is not None:
                        ret, buffer = cv2.imencode('.jpg', frame)
                        frame_bytes = buffer.tobytes()
                    else:
                        frame_bytes = b''
                else:
                    synthetic_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    if cv2 is not None:
                        cv2.putText(
                            synthetic_frame,
                            "FarmSync Live Camera Stream Active",
                            (60, 240),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 128),
                            2
                        )
                        ret, buffer = cv2.imencode('.jpg', synthetic_frame)
                        frame_bytes = buffer.tobytes()
                    else:
                        frame_bytes = b''
                    time.sleep(0.04)

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                frames_yielded += 1
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
