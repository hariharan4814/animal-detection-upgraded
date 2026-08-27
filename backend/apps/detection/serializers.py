"""
Serializers for FarmSync Detection & Vision Module.
Provides serialization for AnimalLog records, detection status, toggle payloads, and image uploads.
"""

from rest_framework import serializers
from apps.detection.models import AnimalLog


class AnimalLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AnimalLog records.
    Exposes historical animal detection event logs and assigned threat classification.
    """
    class Meta:
        model = AnimalLog
        fields = [
            'id',
            'animal_type',
            'confidence',
            'threat_level',
            'timestamp',
            'field',
            'image_path',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DetectionStatusSerializer(serializers.Serializer):
    """
    Read-only status serializer representing YOLO engine health and active detection settings.
    """
    detection_enabled = serializers.BooleanField()
    engine_available = serializers.BooleanField()
    model_name = serializers.CharField()
    confidence_threshold = serializers.FloatField()
    camera_device_index = serializers.IntegerField()
    alert_cooldown_seconds = serializers.IntegerField()
    audio_buzzer_enabled = serializers.BooleanField()
    email_alerts_enabled = serializers.BooleanField()
    attach_alert_image_to_email = serializers.BooleanField(required=False, default=True)
    supported_classes_count = serializers.IntegerField()
    supported_classes = serializers.ListField(child=serializers.CharField())


class DetectionToggleSerializer(serializers.Serializer):
    """
    Payload serializer for updating detection_enabled status via PATCH.
    """
    detection_enabled = serializers.BooleanField(
        required=True,
        help_text="Boolean flag enabling or disabling the AI detection pipeline"
    )


class ImageAnalysisSerializer(serializers.Serializer):
    """
    Payload serializer for manual image upload inference.
    """
    image = serializers.FileField(
        required=True,
        help_text="Image file (JPEG, PNG, WEBP, BMP) to analyze with YOLO object detection"
    )
    field = serializers.CharField(
        required=False,
        default="Main Field",
        max_length=150,
        help_text="Optional agricultural location / zone name"
    )

    def validate_image(self, value):
        """
        Validate image file format and size.
        """
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        name = value.name.lower()
        if not any(name.endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError(
                f"Unsupported image format. Allowed formats: {', '.join(valid_extensions)}"
            )

        # Max 10MB file size limit
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file size exceeds maximum 10MB limit.")

        return value
