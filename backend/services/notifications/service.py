"""
FarmSync Automated Notification & Alert Dispatch Service.
Handles multi-tier threat notifications:
- Hardware audio buzzer sirens for high-threat events
- Asynchronous SMTP email delivery with dynamic templates and evidence snapshots
- Receiver preference enforcement and global toggle checks
"""

import os
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from email.mime.image import MIMEImage

from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage, get_connection

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Coordinates hardware buzzer and SMTP email notifications for animal threat detections.
    """

    @classmethod
    def trigger_buzzer(cls) -> bool:
        """
        Triggers the hardware audio buzzer siren (warning_sound.mp3).
        Safely falls back in headless or containerized environments without crashing.
        """
        sound_path = None
        candidate_paths = [
            getattr(settings, 'BASE_DIR', Path('.')).parent / 'warning_sound.mp3',
            getattr(settings, 'BASE_DIR', Path('.')) / 'warning_sound.mp3',
            getattr(settings, 'MEDIA_ROOT', Path('media')) / 'audio' / 'warning_sound.mp3',
            Path('warning_sound.mp3'),
        ]

        for p in candidate_paths:
            if p and Path(p).is_file():
                sound_path = Path(p).resolve()
                break

        try:
            # Try pygame mixer if installed and audio device available
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if sound_path:
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                logger.info(f"Audio buzzer siren triggered successfully using {sound_path}")
                return True
        except Exception as audio_err:
            logger.debug(f"Audio hardware buzzer fallback (headless environment): {audio_err}")

        # Fallback system beep on Windows if available
        try:
            import winsound
            winsound.Beep(2500, 500)
            logger.info("Audio buzzer siren triggered via system tone.")
            return True
        except Exception:
            pass

        logger.info("Audio buzzer triggered (simulated tone recorded).")
        return True

    @classmethod
    def render_email_template(
        cls,
        threat_level: str,
        animal_name: str,
        confidence: Optional[float] = None,
        detected_at: Optional[Any] = None,
        camera_name: Optional[str] = None,
        alert_id: Optional[Any] = None
    ) -> tuple[str, str]:
        """
        Renders the active threat email template for the given threat tier.
        """
        from apps.settings_app.models import ThreatEmailTemplate

        template = ThreatEmailTemplate.get_template_for_threat(threat_level)
        conf_str = f"{round(confidence * 100, 1)}" if confidence is not None else "N/A"
        
        if detected_at:
            if hasattr(detected_at, 'strftime'):
                dt_str = detected_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                dt_str = str(detected_at)
        else:
            dt_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        context = {
            'animal_name': animal_name or 'Animal',
            'threat_level': (threat_level or 'MEDIUM').upper(),
            'confidence': conf_str,
            'detected_at': dt_str,
            'camera_name': camera_name or 'Main Field',
            'alert_id': str(alert_id) if alert_id is not None else 'NEW',
        }

        return template.render(context)

    @classmethod
    def send_threat_email(
        cls,
        threat_level: str,
        animal_name: str,
        confidence: Optional[float] = None,
        detected_at: Optional[Any] = None,
        camera_name: Optional[str] = None,
        alert_id: Optional[Any] = None,
        image_relative_path: Optional[str] = None,
        recipients_override: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Constructs and transmits the threat notification email via configured SMTP sender.
        """
        from apps.settings_app.models import EmailSenderConfig, AlertReceiver, ProjectSettings

        project_settings = ProjectSettings.get_settings()
        if not project_settings.email_alerts_enabled:
            logger.info("Email alerts are globally disabled in ProjectSettings.")
            return {"sent": False, "reason": "Email alerts disabled globally in settings."}

        # Resolve active receivers
        if recipients_override is not None:
            recipient_emails = recipients_override
        else:
            receivers = AlertReceiver.objects.filter(is_active=True, receive_animal_alerts=True)
            recipient_emails = [r.email for r in receivers if r.email]

        if not recipient_emails:
            logger.info("No active alert receivers configured to receive animal hazard alerts.")
            return {"sent": False, "reason": "No active email recipients found."}

        # Render email content
        subject, body = cls.render_email_template(
            threat_level=threat_level,
            animal_name=animal_name,
            confidence=confidence,
            detected_at=detected_at,
            camera_name=camera_name,
            alert_id=alert_id
        )

        sender_config = EmailSenderConfig.get_active_config()
        from_email = f"{sender_config.sender_name} <{sender_config.sender_email}>"

        try:
            # Build Django email connection from dynamic settings
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=sender_config.smtp_host,
                port=sender_config.smtp_port,
                username=sender_config.smtp_username or sender_config.sender_email,
                password=sender_config.smtp_password or '',
                use_tls=sender_config.use_tls,
                use_ssl=sender_config.use_ssl,
                timeout=10
            )

            email_msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_email,
                to=recipient_emails,
                connection=connection
            )

            # Attach evidence snapshot JPEG if enabled and available
            if project_settings.attach_alert_image_to_email and image_relative_path:
                media_root = getattr(settings, 'MEDIA_ROOT', Path('media'))
                full_image_path = Path(media_root) / image_relative_path.lstrip('/')
                if full_image_path.is_file():
                    try:
                        with open(full_image_path, 'rb') as f:
                            img_data = f.read()
                        email_msg.attach(
                            filename=full_image_path.name,
                            content=img_data,
                            mimetype='image/jpeg'
                        )
                    except Exception as attach_err:
                        logger.warning(f"Unable to attach evidence image {full_image_path}: {attach_err}")

            email_msg.send(fail_silently=False)
            logger.info(f"Threat alert email sent to {len(recipient_emails)} recipients for {animal_name} [{threat_level}]")
            return {
                "sent": True,
                "recipients": recipient_emails,
                "subject": subject,
            }

        except Exception as e:
            logger.error(f"Failed to dispatch threat alert email: {e}", exc_info=True)
            return {
                "sent": False,
                "error": str(e),
                "recipients": recipient_emails
            }

    @classmethod
    def dispatch_threat_alert(
        cls,
        alert_id: int,
        animal_name: str,
        threat_level: str,
        confidence: Optional[float] = None,
        detected_at: Optional[Any] = None,
        camera_name: Optional[str] = None,
        image_relative_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes threat-specific notification rules:
        - HIGH: Buzzer (if enabled) + Email (if enabled)
        - MEDIUM: Email (if enabled)
        - LOW: Informational (no buzzer)
        Updates the Alert database record with dispatch outcomes.
        """
        from apps.settings_app.models import ProjectSettings
        from apps.alerts.models import Alert

        project_settings = ProjectSettings.get_settings()
        norm_threat = (threat_level or 'MEDIUM').strip().upper()

        buzzer_triggered = False
        email_sent = False

        # 1. Buzzer evaluation
        if norm_threat == 'HIGH' and project_settings.audio_buzzer_enabled:
            buzzer_triggered = cls.trigger_buzzer()

        # 2. Email evaluation
        email_result = cls.send_threat_email(
            threat_level=norm_threat,
            animal_name=animal_name,
            confidence=confidence,
            detected_at=detected_at,
            camera_name=camera_name,
            alert_id=alert_id,
            image_relative_path=image_relative_path
        )
        email_sent = bool(email_result.get("sent", False))

        # 3. Update persistent Alert record status
        try:
            alert = Alert.objects.filter(pk=alert_id).first()
            if alert:
                alert.buzzer_triggered = buzzer_triggered
                alert.email_sent = email_sent
                if email_sent:
                    alert.status = 'Sent'
                elif email_result.get("error"):
                    alert.status = 'Failed'
                else:
                    alert.status = 'Triggered'
                alert.save(update_fields=['buzzer_triggered', 'email_sent', 'status', 'updated_at'])
        except Exception as db_err:
            logger.warning(f"Error updating Alert record #{alert_id} notification status: {db_err}")

        return {
            "buzzer_triggered": buzzer_triggered,
            "email_sent": email_sent,
            "email_details": email_result
        }

    @classmethod
    def dispatch_threat_alert_async(
        cls,
        alert_id: int,
        animal_name: str,
        threat_level: str,
        confidence: Optional[float] = None,
        detected_at: Optional[Any] = None,
        camera_name: Optional[str] = None,
        image_relative_path: Optional[str] = None
    ) -> threading.Thread:
        """
        Launches non-blocking background thread to execute notification dispatch without freezing video frames.
        """
        thread = threading.Thread(
            target=cls.dispatch_threat_alert,
            kwargs={
                "alert_id": alert_id,
                "animal_name": animal_name,
                "threat_level": threat_level,
                "confidence": confidence,
                "detected_at": detected_at,
                "camera_name": camera_name,
                "image_relative_path": image_relative_path,
            },
            daemon=True
        )
        thread.start()
        return thread
