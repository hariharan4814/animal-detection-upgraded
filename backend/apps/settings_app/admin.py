from django.contrib import admin
from apps.settings_app.models import (
    EmailSenderConfig,
    AlertReceiver,
    ProjectSettings,
    AnimalThreatRule,
    ThreatEmailTemplate,
)


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
    list_display = ('system_name', 'alert_cooldown_seconds', 'detection_confidence_threshold', 'detection_enabled', 'email_alerts_enabled', 'attach_alert_image_to_email')


@admin.register(AnimalThreatRule)
class AnimalThreatRuleAdmin(admin.ModelAdmin):
    list_display = ('animal_name', 'threat_level', 'is_active', 'updated_at')
    list_filter = ('threat_level', 'is_active')
    search_fields = ('animal_name',)


@admin.register(ThreatEmailTemplate)
class ThreatEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('threat_level', 'subject_template', 'is_active', 'updated_at')
    list_filter = ('threat_level', 'is_active')
