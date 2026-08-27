"""
Serializers for FarmSync Settings Module.
Enforces write-only sensitive fields, validation constraints, safe response formats,
threat classification rules, and email template customization.
"""

from rest_framework import serializers
from django.template import Template, TemplateSyntaxError, Context
from django.utils import timezone

from apps.settings_app.models import (
    EmailSenderConfig,
    AlertReceiver,
    ProjectSettings,
    AnimalThreatRule,
    ThreatEmailTemplate,
)


class EmailSenderConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for outgoing SMTP email configuration.
    Security: smtp_password is write-only. The API returns smtp_password_configured: True/False.
    """
    smtp_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text="SMTP app password (write-only, never returned by API)"
    )
    smtp_password_configured = serializers.SerializerMethodField(
        help_text="Indicates whether an SMTP password has been stored"
    )

    class Meta:
        model = EmailSenderConfig
        fields = [
            'id',
            'sender_name',
            'sender_email',
            'smtp_host',
            'smtp_port',
            'smtp_username',
            'smtp_password',
            'smtp_password_configured',
            'use_tls',
            'use_ssl',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'smtp_password_configured']

    def get_smtp_password_configured(self, obj) -> bool:
        return bool(obj.smtp_password and len(obj.smtp_password.strip()) > 0)

    def validate_smtp_port(self, value: int) -> int:
        if value < 1 or value > 65535:
            raise serializers.ValidationError("SMTP port must be a valid port number between 1 and 65535.")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('smtp_password', None)
        if password and password.strip():
            instance.smtp_password = password.strip()

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        instance.save()
        return instance


class AlertReceiverSerializer(serializers.ModelSerializer):
    """
    Serializer for managing alert notification recipients.
    """
    name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')

    class Meta:
        model = AlertReceiver
        fields = [
            'id',
            'name',
            'email',
            'is_active',
            'receive_animal_alerts',
            'receive_attendance_reports',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        query = AlertReceiver.objects.filter(email__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("An alert receiver with this email address already exists.")
        return value

    def validate(self, attrs):
        if not attrs.get('name'):
            email = attrs.get('email', '')
            attrs['name'] = email.split('@')[0].capitalize() if '@' in email else 'Alert Recipient'
        return attrs


class ProjectSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for runtime project configuration parameters and threat thresholds.
    """
    class Meta:
        model = ProjectSettings
        fields = [
            'id',
            'system_name',
            'alert_cooldown_seconds',
            'detection_confidence_threshold',
            'camera_device_index',
            'work_start_time',
            'wage_per_hour',
            'detection_enabled',
            'audio_buzzer_enabled',
            'email_alerts_enabled',
            'attach_alert_image_to_email',
            'threat_level_overrides',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_detection_confidence_threshold(self, value: float) -> float:
        if value < 0.01 or value > 1.00:
            raise serializers.ValidationError("Detection confidence threshold must be between 0.01 and 1.00.")
        return round(value, 2)

    def validate_alert_cooldown_seconds(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("Alert cooldown duration cannot be negative.")
        return value

    def validate_camera_device_index(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("Camera device index cannot be negative.")
        return value

    def validate_wage_per_hour(self, value: float) -> float:
        if value < 0:
            raise serializers.ValidationError("Hourly wage cannot be negative.")
        return round(value, 2)

    def validate_threat_level_overrides(self, value: dict) -> dict:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Threat level overrides must be a dictionary.")
        valid_tiers = {'high', 'medium', 'low', 'HIGH', 'MEDIUM', 'LOW'}
        for species, tier in value.items():
            if not isinstance(species, str) or not species.strip():
                raise serializers.ValidationError("Species name in threat level overrides must be a non-empty string.")
            if not isinstance(tier, str) or tier.lower() not in {'high', 'medium', 'low'}:
                raise serializers.ValidationError(
                    f"Invalid threat level '{tier}' for species '{species}'. Must be one of: HIGH, MEDIUM, LOW."
                )
        return value


class AnimalThreatRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for configurable animal threat classification rules.
    """
    class Meta:
        model = AnimalThreatRule
        fields = [
            'id',
            'animal_name',
            'threat_level',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_animal_name(self, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Animal name cannot be blank.")
        query = AnimalThreatRule.objects.filter(animal_name__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError(f"A threat classification rule for '{value}' already exists.")
        return value

    def validate_threat_level(self, value: str) -> str:
        val_upper = value.strip().upper()
        if val_upper not in {'HIGH', 'MEDIUM', 'LOW'}:
            raise serializers.ValidationError("Threat level must be one of: HIGH, MEDIUM, LOW.")
        return val_upper


class ThreatEmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for managing threat notification email templates with syntax verification.
    """
    class Meta:
        model = ThreatEmailTemplate
        fields = [
            'id',
            'threat_level',
            'subject_template',
            'body_template',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_threat_level(self, value: str) -> str:
        val_upper = value.strip().upper()
        if val_upper not in {'HIGH', 'MEDIUM', 'LOW'}:
            raise serializers.ValidationError("Threat level must be one of: HIGH, MEDIUM, LOW.")
        return val_upper

    def validate_subject_template(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Subject template cannot be empty.")
        try:
            Template(value)
        except TemplateSyntaxError as syn_err:
            raise serializers.ValidationError(f"Invalid Django template syntax in subject: {syn_err}")
        return value.strip()

    def validate_body_template(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Body template cannot be empty.")
        try:
            Template(value)
        except TemplateSyntaxError as syn_err:
            raise serializers.ValidationError(f"Invalid Django template syntax in body: {syn_err}")
        return value.strip()


class EmailTemplatePreviewSerializer(serializers.Serializer):
    """
    Serializer for rendering live email template previews without sending real emails.
    """
    threat_level = serializers.ChoiceField(
        choices=['HIGH', 'MEDIUM', 'LOW'],
        default='HIGH',
        help_text="Threat level to preview"
    )
    subject_template = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional custom subject template string to test"
    )
    body_template = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional custom body template string to test"
    )
    sample_animal_name = serializers.CharField(
        required=False,
        default='elephant',
        help_text="Sample animal species name"
    )
    sample_confidence = serializers.FloatField(
        required=False,
        default=94.7,
        help_text="Sample detection confidence percentage"
    )
    sample_camera_name = serializers.CharField(
        required=False,
        default='Camera 0 (North Perimeter)',
        help_text="Sample camera or field location"
    )
    sample_alert_id = serializers.CharField(
        required=False,
        default='DEMO-001',
        help_text="Sample alert ID"
    )

    def generate_preview(self) -> dict:
        data = self.validated_data
        threat_level = data.get('threat_level', 'HIGH').upper()
        subject_tpl = data.get('subject_template')
        body_tpl = data.get('body_template')

        # If custom template not provided in preview request, fetch currently stored template
        if not subject_tpl or not body_tpl:
            stored = ThreatEmailTemplate.get_template_for_threat(threat_level)
            subject_tpl = subject_tpl or stored.subject_template
            body_tpl = body_tpl or stored.body_template

        now_formatted = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        context_dict = {
            'animal_name': data.get('sample_animal_name', 'elephant'),
            'threat_level': f"{threat_level} THREAT",
            'confidence': f"{data.get('sample_confidence', 94.7)}",
            'detected_at': now_formatted,
            'camera_name': data.get('sample_camera_name', 'Camera 0 (North Perimeter)'),
            'alert_id': data.get('sample_alert_id', 'DEMO-001'),
        }

        try:
            ctx = Context(context_dict)
            subject = Template(subject_tpl).render(ctx).strip()
            body = Template(body_tpl).render(ctx).strip()
            return {
                "success": True,
                "threat_level": threat_level,
                "subject": subject,
                "body": body,
                "context": context_dict
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Template rendering error: {str(e)}",
                "threat_level": threat_level
            }
