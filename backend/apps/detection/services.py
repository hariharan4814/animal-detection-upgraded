"""
Detection Domain Services.
Orchestrates AI inference, snapshot persistence, AnimalLog record creation, and Alert triggering.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime

from django.conf import settings
from django.utils import timezone

try:
    import cv2
except ImportError:
    cv2 = None

from apps.settings_app.models import ProjectSettings
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from services.yolo import get_model, is_model_available, run_inference, ANIMAL_CLASSES

logger = logging.getLogger(__name__)

# In-memory alert cooldown tracker for fast runtime checks: {animal_type: last_alert_timestamp}
_last_notification_timestamps: Dict[str, float] = {}


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
        field_name: str = "Main Field"
    ) -> Dict[str, Any]:
        """
        Processes an uploaded image through the YOLO detection pipeline.

        :param image_bytes: Raw binary bytes of an image (JPEG, PNG).
        :param field_name: Agricultural sector or camera location string.
        :return: Structured detection result dictionary including any created log records.
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
                # Convert RGB to BGR for standard cv2 drawing compatibility if available
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

        highest_animal = inference_result.get("highest_threat_animal")
        highest_level = inference_result.get("highest_threat_level")
        highest_conf = inference_result.get("highest_conf", 0.0)
        detections = inference_result.get("detections", [])

        animal_log_data = None
        alert_triggered = False
        alert_type = None

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

            # Create persistent AnimalLog record
            animal_log = AnimalLog.objects.create(
                animal_type=highest_animal,
                confidence=highest_conf,
                timestamp=now_dt,
                field=field_name or "Main Field",
                image_path=relative_storage_path
            )

            animal_log_data = {
                "id": animal_log.id,
                "animal_type": animal_log.animal_type,
                "confidence": animal_log.confidence,
                "timestamp": animal_log.timestamp.isoformat(),
                "field": animal_log.field,
                "image_path": animal_log.image_path
            }

            # Cooldown evaluation and Alert creation
            last_alert_time = _last_notification_timestamps.get(highest_animal, 0.0)
            cooldown_window = project_settings.alert_cooldown_seconds

            if (current_epoch - last_alert_time) >= cooldown_window:
                if highest_level == 'high':
                    alert_type = 'Email + Buzzer'
                elif highest_level == 'medium':
                    alert_type = 'Email'
                else:
                    alert_type = 'Log Only'

                Alert.objects.create(
                    animal_log=animal_log,
                    alert_type=alert_type,
                    status='Triggered'
                )
                _last_notification_timestamps[highest_animal] = current_epoch
                alert_triggered = True

        return {
            "detection_enabled": True,
            "detections_count": len(detections),
            "detections": detections,
            "highest_threat_animal": highest_animal,
            "highest_threat_level": highest_level,
            "highest_confidence": highest_conf,
            "animal_log": animal_log_data,
            "alert_triggered": alert_triggered,
            "alert_type": alert_type
        }


class VideoStreamService:
    """
    Provides multipart MJPEG frame streaming for real-time camera views.
    Handles device acquisition, error recovery, dynamic settings reflection, and camera toggles.
    """

    @classmethod
    def generate_frames(cls, max_frames: int | None = None):
        """
        Yields multipart HTTP MJPEG frame chunks.
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
        default_limit = 100 if max_frames is None else max_frames

        try:
            while frames_yielded < default_limit:
                # Dynamic settings lookup on every frame
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
                    # Generate synthetic placeholder frame for headless / non-hardware environments
                    synthetic_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    if cv2 is not None:
                        cv2.putText(
                            synthetic_frame,
                            "FarmSync Camera Stream Active",
                            (80, 240),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 128),
                            2
                        )
                        ret, buffer = cv2.imencode('.jpg', synthetic_frame)
                        frame_bytes = buffer.tobytes()
                    else:
                        frame_bytes = b''

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                frames_yielded += 1
                time.sleep(0.05)
        finally:
            if cap is not None:
                cap.release()
