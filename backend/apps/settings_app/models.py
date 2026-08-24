"""
Database models for FarmSync dynamic settings, email configuration, alert receivers, and project parameters.
"""

from django.db import models


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
                email_alerts_enabled=True
            )
        return settings_obj
