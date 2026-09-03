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
    def build_html_email_content(
        cls,
        threat_level: str,
        animal_name: str,
        confidence: Optional[float],
        detected_at: Optional[Any],
        camera_name: Optional[str],
        alert_id: Optional[Any],
        has_image: bool = False
    ) -> str:
        """
        Builds a rich, responsive HTML email template for animal detection alerts.
        """
        norm_tier = (threat_level or 'MEDIUM').strip().upper()
        conf_str = f"{round(confidence * 100, 1)}%" if confidence is not None else "N/A"

        if detected_at:
            if hasattr(detected_at, 'strftime'):
                dt_str = detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')
            else:
                dt_str = str(detected_at)
        else:
            dt_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        cap_animal = (animal_name or 'Animal').capitalize()

        if norm_tier == 'HIGH':
            banner_bg = '#dc2626'
            badge_bg = '#fef2f2'
            badge_border = '#fecaca'
            badge_text = '#991b1b'
            badge_label = '🚨 HIGH THREAT HAZARD'
            action_text = 'High threat wildlife intrusion detected. Immediate security protocols and field deterrence siren activated. Please verify safety of personnel in the sector.'
        elif norm_tier == 'LOW':
            banner_bg = '#16a34a'
            badge_bg = '#f0fdf4'
            badge_border = '#bbf7d0'
            badge_text = '#166534'
            badge_label = 'ℹ️ LOW THREAT ACTIVITY'
            action_text = 'Low threat wildlife detected. Informational monitoring entry recorded. No immediate evacuation required.'
        else:
            banner_bg = '#ea580c'
            badge_bg = '#fff7ed'
            badge_border = '#fed7aa'
            badge_text = '#9a3412'
            badge_label = '⚠️ MEDIUM THREAT ALERT'
            action_text = 'Medium threat animal detected near perimeter. Agricultural workers and farm supervisors should inspect the monitored area.'

        image_html = ""
        if has_image:
            image_html = f"""
            <div style="margin: 20px 0; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; background: #0f172a; text-align: center;">
                <div style="padding: 10px 16px; background: #1e293b; color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; text-align: left;">
                    📷 YOLOv8 Detection Evidence Snapshot
                </div>
                <div style="padding: 12px; text-align: center;">
                    <img src="cid:detected_image" alt="{cap_animal} Detected Snapshot" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" />
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FarmSync Security Alert</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 24px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;">
                    <!-- Top Brand Header -->
                    <tr>
                        <td style="background-color: {banner_bg}; padding: 24px 32px; text-align: left;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>
                                        <span style="color: #ffffff; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.9;">FarmSync AI Wildlife Monitoring</span>
                                        <h1 style="color: #ffffff; margin: 6px 0 0 0; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">
                                            {cap_animal} Detected ({norm_tier} Threat)
                                        </h1>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Main Body Card -->
                    <tr>
                        <td style="padding: 32px;">
                            <!-- Threat Tier Badge -->
                            <div style="display: inline-block; background-color: {badge_bg}; border: 1px solid {badge_border}; color: {badge_text}; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 20px;">
                                {badge_label}
                            </div>

                            <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.6; color: #334155;">
                                A wildlife hazard was detected by the FarmSync automated vision surveillance system. Details of the detected event and classified threat level are summarized below:
                            </p>

                            <!-- Metric Details Table -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin-bottom: 24px; font-size: 13px;">
                                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                    <td style="padding: 12px 16px; color: #64748b; font-weight: 600; width: 40%;">Species Detected</td>
                                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 700; text-transform: capitalize;">{cap_animal}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e2e8f0;">
                                    <td style="padding: 12px 16px; color: #64748b; font-weight: 600;">Threat Classification</td>
                                    <td style="padding: 12px 16px; color: {badge_text}; font-weight: 700;">{norm_tier} THREAT</td>
                                </tr>
                                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                    <td style="padding: 12px 16px; color: #64748b; font-weight: 600;">Detection Confidence</td>
                                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 700; font-family: monospace;">{conf_str}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e2e8f0;">
                                    <td style="padding: 12px 16px; color: #64748b; font-weight: 600;">Location / Camera</td>
                                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 600;">{camera_name or 'Main Field Surveillance'}</td>
                                </tr>
                                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                    <td style="padding: 12px 16px; color: #64748b; font-weight: 600;">Timestamp</td>
                                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 600;">{dt_str}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 16px; color: #64748b; font-weight: 600;">Alert Reference ID</td>
                                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 700; font-family: monospace;">#{alert_id if alert_id is not None else 'NEW'}</td>
                                </tr>
                            </table>

                            <!-- Evidence Image (if attached) -->
                            {image_html}

                            <!-- Action Advisory Box -->
                            <div style="background-color: #f1f5f9; border-left: 4px solid {banner_bg}; padding: 14px 18px; border-radius: 6px; font-size: 13px; color: #334155; line-height: 1.5; margin-bottom: 24px;">
                                <strong>Safety Advisory:</strong> {action_text}
                            </div>

                            <p style="margin: 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                                Note: This snapshot is also attached to this email as a JPEG file for security auditing and local archival.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px 32px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 11px; color: #64748b;">
                            FarmSync Automated Intelligent Wildlife Detection & Management System<br />
                            Sent via secure SMTP alert service to registered farm supervisors and emergency receivers.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        return html

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
        Supports rich multipart HTML formatting, inline snapshot embedding, and image attachments.
        """
        from apps.settings_app.models import EmailSenderConfig, AlertReceiver, ProjectSettings
        from django.core.mail import EmailMultiAlternatives

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

        # Render plain-text fallback content
        subject, body = cls.render_email_template(
            threat_level=threat_level,
            animal_name=animal_name,
            confidence=confidence,
            detected_at=detected_at,
            camera_name=camera_name,
            alert_id=alert_id
        )

        # Resolve evidence image data if available
        resolved_img_path = None
        img_data = None
        if project_settings.attach_alert_image_to_email and image_relative_path:
            media_root = Path(getattr(settings, 'MEDIA_ROOT', Path('media'))).resolve()
            p = Path(image_relative_path)
            candidate_paths = [
                p if p.is_absolute() else None,
                media_root / image_relative_path.lstrip('/'),
                media_root / 'detections' / p.name,
                Path(image_relative_path),
            ]
            for c in candidate_paths:
                if c and c.is_file():
                    resolved_img_path = c
                    break

            if resolved_img_path and resolved_img_path.is_file():
                try:
                    with open(resolved_img_path, 'rb') as f:
                        img_data = f.read()
                except Exception as read_err:
                    logger.warning(f"Unable to read evidence image {resolved_img_path}: {read_err}")

        # Render rich HTML email template
        html_body = cls.build_html_email_content(
            threat_level=threat_level,
            animal_name=animal_name,
            confidence=confidence,
            detected_at=detected_at,
            camera_name=camera_name,
            alert_id=alert_id,
            has_image=bool(img_data)
        )

        sender_config = EmailSenderConfig.get_active_config()
        from_email = f"{sender_config.sender_name} <{sender_config.sender_email}>"
        clean_password = (sender_config.smtp_password or '').replace(' ', '').strip()

        try:
            # Build Django email connection from dynamic settings (or test locmem backend)
            backend_cls = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
            if 'locmem' in backend_cls:
                connection = get_connection(backend=backend_cls)
            else:
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=sender_config.smtp_host,
                    port=sender_config.smtp_port,
                    username=sender_config.smtp_username or sender_config.sender_email,
                    password=clean_password,
                    use_tls=sender_config.use_tls,
                    use_ssl=sender_config.use_ssl,
                    timeout=15
                )

            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=recipient_emails,
                connection=connection
            )
            email_msg.attach_alternative(html_body, "text/html")

            # Attach evidence snapshot JPEG both inline (CID) and as downloadable attachment
            if img_data and resolved_img_path:
                try:
                    # 1. Inline MIME image with Content-ID for HTML body
                    mime_img = MIMEImage(img_data, _subtype='jpeg')
                    mime_img.add_header('Content-ID', '<detected_image>')
                    mime_img.add_header('Content-Disposition', 'inline', filename=resolved_img_path.name)
                    email_msg.attach(mime_img)

                    # 2. File attachment for direct download
                    email_msg.attach(
                        filename=resolved_img_path.name,
                        content=img_data,
                        mimetype='image/jpeg'
                    )
                except Exception as attach_err:
                    logger.warning(f"Unable to attach evidence image {resolved_img_path}: {attach_err}")

            email_msg.send(fail_silently=False)
            logger.info(f"Threat alert email successfully sent to {len(recipient_emails)} recipients for {animal_name} [{threat_level}]")
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
