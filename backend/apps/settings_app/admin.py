from django.contrib import admin
from apps.settings_app.models import EmailSenderConfig, AlertReceiver, ProjectSettings


@admin.register(EmailSenderConfig)
class EmailSenderConfigAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'sender_email', 'smtp_host', 'smtp_port', 'use_tls', 'is_active')
    list_filter = ('is_active', 'use_tls')


@admin.register(AlertReceiver)
class AlertReceiverAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active', 'receive_animal_alerts', 'receive_attendance_reports')
    list_filter = ('is_active', 'receive_animal_alerts', 'receive_attendance_reports')
    search_fields = ('name', 'email')


@admin.register(ProjectSettings)
class ProjectSettingsAdmin(admin.ModelAdmin):
    list_display = ('system_name', 'alert_cooldown_seconds', 'detection_confidence_threshold', 'detection_enabled', 'email_alerts_enabled')
