"""
Database models for FarmSync dynamic settings, email configuration, alert receivers,
animal threat classification rules, and threat-specific email templates.
"""

from django.db import models
from django.template import Template, Context


class EmailSenderConfig(models.Model):
    """
    SMTP email sender configuration.
    Security: smtp_password is write-only and never exposed via API endpoints or logs.
    """
    sender_name = models.CharField(max_length=150, default='FarmSync Alert System', help_text="Display name for outgoing emails")
    sender_email = models.EmailField(max_length=255, default='alerts@example.com', help_text="Sender email address")
    smtp_host = models.CharField(max_length=255, default='smtp.gmail.com', help_text="SMTP server hostname")
    smtp_port = models.IntegerField(default=587, help_text="SMTP server port (typically 587 for TLS or 465 for SSL)")
    smtp_username = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP login username (usually same as email)")
    smtp_password = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP app password (write-only)")
    use_tls = models.BooleanField(default=True, help_text="Use STARTTLS encryption")
    use_ssl = models.BooleanField(default=False, help_text="Use SSL/TLS encryption")
    is_active = models.BooleanField(default=True, help_text="Whether this sender configuration is actively used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email Sender Configuration'
        verbose_name_plural = 'Email Sender Configurations'

    def __str__(self):
        return f"{self.sender_name} <{self.sender_email}> on {self.smtp_host}:{self.smtp_port} {'(Active)' if self.is_active else ''}"

    @classmethod
    def get_active_config(cls):
        """Returns the current active sender configuration, or creates a default one if none exists."""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create(
                sender_name='FarmSync Alert System',
                sender_email='alerts@example.com',
                smtp_host='smtp.gmail.com',
                smtp_port=587,
                use_tls=True,
                is_active=True
            )
        return config


class AlertReceiver(models.Model):
    """
    Alert notification recipients who receive automated email notifications when hazards are detected.
    """
    name = models.CharField(max_length=150, help_text="Recipient name or role title")
    email = models.EmailField(max_length=255, unique=True, help_text="Recipient email address")
    is_active = models.BooleanField(default=True, help_text="Master toggle to enable or disable alerts for this recipient")
    receive_animal_alerts = models.BooleanField(default=True, help_text="Receive real-time animal hazard alerts")
    receive_attendance_reports = models.BooleanField(default=False, help_text="Receive daily worker attendance summaries")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Alert Receiver'
        verbose_name_plural = 'Alert Receivers'

    def __str__(self):
        status_str = "Active" if self.is_active else "Disabled"
        return f"{self.name} <{self.email}> [{status_str}]"


class ProjectSettings(models.Model):
    """
    Centralized, dynamic project configuration parameters.
    Allows runtime modification of system thresholds, camera indices, and threat classifications.
    """
    system_name = models.CharField(max_length=150, default='FarmSync Intelligent Monitoring', help_text="Application display title")
    alert_cooldown_seconds = models.IntegerField(default=60, help_text="Cooldown duration in seconds between repeated animal alerts")
    detection_confidence_threshold = models.FloatField(default=0.50, help_text="Minimum YOLO confidence score threshold (0.01 to 1.00)")
    camera_device_index = models.IntegerField(default=0, help_text="OpenCV camera device hardware index (e.g. 0 for primary webcam)")
    work_start_time = models.TimeField(default='08:00:00', help_text="Daily farm shift start time for attendance calculations")
    wage_per_hour = models.FloatField(default=15.0, help_text="Standard hourly wage calculation rate")
    detection_enabled = models.BooleanField(default=True, help_text="Master toggle for AI animal detection engine")
    audio_buzzer_enabled = models.BooleanField(default=True, help_text="Toggle host machine audio alarm buzzer on high-threat detections")
    email_alerts_enabled = models.BooleanField(default=True, help_text="Toggle automated email dispatches on medium/high threat detections")
    attach_alert_image_to_email = models.BooleanField(default=True, help_text="Attach detection snapshot JPEG to alert notification emails")
    threat_level_overrides = models.JSONField(default=dict, blank=True, help_text="Species-specific threat level mappings (e.g. {'wolf': 'high', 'deer': 'low'})")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Project Settings'
        verbose_name_plural = 'Project Settings'

    def __str__(self):
        return f"{self.system_name} Configuration (Cooldown: {self.alert_cooldown_seconds}s, Confidence: {self.detection_confidence_threshold})"

    @classmethod
    def get_settings(cls):
        """Returns the singleton project configuration instance, creating one if not present."""
        settings_obj = cls.objects.first()
        if not settings_obj:
            settings_obj = cls.objects.create(
                system_name='FarmSync Intelligent Monitoring',
                alert_cooldown_seconds=60,
                detection_confidence_threshold=0.50,
                camera_device_index=0,
                work_start_time='08:00:00',
                wage_per_hour=15.0,
                detection_enabled=True,
                audio_buzzer_enabled=True,
                email_alerts_enabled=True,
                attach_alert_image_to_email=True,
            )
        return settings_obj


class AnimalThreatRule(models.Model):
    """
    Configurable species-specific threat classification rule.
    Maps animal species name to a persistent threat tier (HIGH, MEDIUM, LOW).
    """
    THREAT_CHOICES = [
        ('HIGH', 'High Threat'),
        ('MEDIUM', 'Medium Threat'),
        ('LOW', 'Low Threat'),
    ]

    animal_name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Normalized lowercase animal species name (e.g. elephant, wolf, deer)"
    )
    threat_level = models.CharField(
        max_length=10,
        choices=THREAT_CHOICES,
        default='MEDIUM',
        help_text="Assigned threat classification tier"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this classification rule is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['animal_name']
        verbose_name = 'Animal Threat Rule'
        verbose_name_plural = 'Animal Threat Rules'

    def __str__(self):
        status_str = "Active" if self.is_active else "Disabled"
        return f"{self.animal_name.capitalize()} -> {self.threat_level} [{status_str}]"

    def save(self, *args, **kwargs):
        self.animal_name = self.animal_name.strip().lower()
        self.threat_level = self.threat_level.strip().upper()
        super().save(*args, **kwargs)
        from services.threat_classification import invalidate_threat_cache
        invalidate_threat_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        from services.threat_classification import invalidate_threat_cache
        invalidate_threat_cache()

    @classmethod
    def seed_default_rules(cls, overwrite_existing: bool = False):
        """
        Seeds default threat classification rules for all known YOLO and domain animal species.
        """
        from services.threat_classification import get_default_threat_rules
        defaults = get_default_threat_rules()
        created_count = 0
        updated_count = 0

        for animal, tier in defaults.items():
            rule, created = cls.objects.get_or_create(
                animal_name=animal,
                defaults={'threat_level': tier, 'is_active': True}
            )
            if created:
                created_count += 1
            elif overwrite_existing and (rule.threat_level != tier or not rule.is_active):
                rule.threat_level = tier
                rule.is_active = True
                rule.save()
                updated_count += 1

        from services.threat_classification import invalidate_threat_cache
        invalidate_threat_cache()
        return {"created": created_count, "updated": updated_count, "total": cls.objects.count()}


class ThreatEmailTemplate(models.Model):
    """
    Configurable email template for threat notifications.
    Supports safe server-side Django template syntax with standard context variables.
    """
    THREAT_CHOICES = [
        ('HIGH', 'HIGH'),
        ('MEDIUM', 'MEDIUM'),
        ('LOW', 'LOW'),
    ]

    DEFAULT_TEMPLATES = {
        'HIGH': {
            'subject': '🚨 [URGENT] HIGH THREAT DETECTED: {{ animal_name|title }}',
            'body': (
                "URGENT SECURITY ALERT\n\n"
                "A high-risk animal has been detected near the monitored farm area.\n\n"
                "Animal: {{ animal_name|title }}\n"
                "Threat Level: HIGH THREAT\n"
                "Confidence: {{ confidence }}%\n"
                "Detected At: {{ detected_at }}\n"
                "Camera/Source: {{ camera_name }}\n"
                "Alert ID: #{{ alert_id }}\n\n"
                "Immediate attention and security protocol activation may be required.\n\n"
                "FarmSync AI Monitoring System"
            )
        },
        'MEDIUM': {
            'subject': '⚠️ [WARNING] MEDIUM THREAT DETECTED: {{ animal_name|title }}',
            'body': (
                "MEDIUM THREAT MONITORING ALERT\n\n"
                "An animal requiring attention has been detected near the monitored farm area.\n\n"
                "Animal: {{ animal_name|title }}\n"
                "Threat Level: MEDIUM THREAT\n"
                "Confidence: {{ confidence }}%\n"
                "Detected At: {{ detected_at }}\n"
                "Camera/Source: {{ camera_name }}\n"
                "Alert ID: #{{ alert_id }}\n\n"
                "Please review the monitoring system when convenient.\n\n"
                "FarmSync AI Monitoring System"
            )
        },
        'LOW': {
            'subject': 'ℹ [INFO] LOW THREAT ACTIVITY DETECTED: {{ animal_name|title }}',
            'body': (
                "LOW THREAT ACTIVITY NOTICE\n\n"
                "Low-risk animal activity was detected by the FarmSync monitoring system.\n\n"
                "Animal: {{ animal_name|title }}\n"
                "Threat Level: LOW THREAT\n"
                "Confidence: {{ confidence }}%\n"
                "Detected At: {{ detected_at }}\n"
                "Camera/Source: {{ camera_name }}\n"
                "Alert ID: #{{ alert_id }}\n\n"
                "This notification is informational.\n\n"
                "FarmSync AI Monitoring System"
            )
        }
    }

    threat_level = models.CharField(
        max_length=10,
        unique=True,
        choices=THREAT_CHOICES,
        help_text="Threat level this template applies to (HIGH, MEDIUM, LOW)"
    )
    subject_template = models.CharField(
        max_length=255,
        help_text="Django template string for email subject line"
    )
    body_template = models.TextField(
        help_text="Django template string for email body content"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is actively used for email dispatches"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['threat_level']
        verbose_name = 'Threat Email Template'
        verbose_name_plural = 'Threat Email Templates'

    def __str__(self):
        status_str = "Active" if self.is_active else "Disabled"
        return f"{self.threat_level} Threat Email Template [{status_str}]"

    def render(self, context_dict: dict) -> tuple[str, str]:
        """
        Safely renders subject and body using Django template engine with supplied context.
        """
        ctx = Context(context_dict or {})
        subject_rendered = Template(self.subject_template).render(ctx).strip()
        body_rendered = Template(self.body_template).render(ctx).strip()
        return subject_rendered, body_rendered

    @classmethod
    def get_template_for_threat(cls, threat_level: str):
        """
        Retrieves the active template for a given threat tier, creating default if not found.
        """
        norm_tier = (threat_level or 'MEDIUM').strip().upper()
        if norm_tier not in cls.DEFAULT_TEMPLATES:
            norm_tier = 'MEDIUM'

        template = cls.objects.filter(threat_level=norm_tier, is_active=True).first()
        if not template:
            default_data = cls.DEFAULT_TEMPLATES.get(norm_tier, cls.DEFAULT_TEMPLATES['MEDIUM'])
            template = cls.objects.create(
                threat_level=norm_tier,
                subject_template=default_data['subject'],
                body_template=default_data['body'],
                is_active=True
            )
        return template

    @classmethod
    def seed_default_templates(cls, overwrite_existing: bool = False):
        """
        Seeds default email templates for HIGH, MEDIUM, and LOW threat tiers.
        """
        created_count = 0
        updated_count = 0

        for tier, data in cls.DEFAULT_TEMPLATES.items():
            template, created = cls.objects.get_or_create(
                threat_level=tier,
                defaults={
                    'subject_template': data['subject'],
                    'body_template': data['body'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
            elif overwrite_existing:
                template.subject_template = data['subject']
                template.body_template = data['body']
                template.is_active = True
                template.save()
                updated_count += 1

        return {"created": created_count, "updated": updated_count, "total": cls.objects.count()}
