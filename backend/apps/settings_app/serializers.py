"""
Serializers for FarmSync Settings Module.
Enforces write-only sensitive fields, validation constraints, and safe response formats.
"""

from rest_framework import serializers
from apps.settings_app.models import EmailSenderConfig, AlertReceiver, ProjectSettings


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
        # If smtp_password was omitted or blank in update request, retain existing password
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
        valid_tiers = {'high', 'medium', 'low'}
        for species, tier in value.items():
            if not isinstance(species, str) or not species.strip():
                raise serializers.ValidationError("Species name in threat level overrides must be a non-empty string.")
            if not isinstance(tier, str) or tier.lower() not in valid_tiers:
                raise serializers.ValidationError(
                    f"Invalid threat level '{tier}' for species '{species}'. Must be one of: {', '.join(valid_tiers)}."
                )
        return value
