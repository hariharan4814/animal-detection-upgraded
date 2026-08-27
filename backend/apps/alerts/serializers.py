"""
Serializers for FarmSync Alerts & Notification Module.
Provides serialization for Alert records, threat classification tier,
associated detection context, image download URLs, and query filter validation.
"""

from rest_framework import serializers
from django.urls import reverse
from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    """
    Serializer for Alert records.
    Exposes threat level, notification metadata, associated animal detection context, and download URL.
    """
    animal_type = serializers.CharField(
        source='animal_log.animal_type',
        read_only=True,
        default=None,
        help_text="Species of the detected animal"
    )
    confidence = serializers.FloatField(
        source='animal_log.confidence',
        read_only=True,
        default=None,
        help_text="Model confidence score of the detection"
    )
    field = serializers.CharField(
        source='animal_log.field',
        read_only=True,
        default=None,
        help_text="Agricultural sector or location where detection occurred"
    )
    image_path = serializers.CharField(
        source='animal_log.image_path',
        read_only=True,
        default=None,
        help_text="Storage path to the detection snapshot image"
    )
    detection_timestamp = serializers.DateTimeField(
        source='animal_log.timestamp',
        read_only=True,
        default=None,
        help_text="Exact timestamp of the animal detection event"
    )
    download_url = serializers.SerializerMethodField(
        help_text="Direct endpoint URL to download the evidence snapshot image"
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'animal_log',
            'animal_type',
            'confidence',
            'threat_level',
            'field',
            'image_path',
            'download_url',
            'detection_timestamp',
            'alert_type',
            'status',
            'email_sent',
            'buzzer_triggered',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'animal_log',
            'animal_type',
            'confidence',
            'threat_level',
            'field',
            'image_path',
            'download_url',
            'detection_timestamp',
            'alert_type',
            'status',
            'email_sent',
            'buzzer_triggered',
            'created_at',
            'updated_at',
        ]

    def get_download_url(self, obj) -> str | None:
        if obj.animal_log and obj.animal_log.image_path:
            return f"/api/v1/alerts/{obj.id}/download/"
        return None


class AlertFilterSerializer(serializers.Serializer):
    """
    Validates query parameters for alert listing with strict type and date range validation.
    """
    VALID_STATUSES = ['Triggered', 'Sent', 'Failed']
    VALID_ALERT_TYPES = ['Email + Buzzer', 'Email', 'Log Only']
    VALID_THREAT_LEVELS = ['HIGH', 'MEDIUM', 'LOW', 'high', 'medium', 'low']

    status = serializers.ChoiceField(
        choices=VALID_STATUSES,
        required=False,
        allow_null=True,
        help_text="Filter by alert dispatch status ('Triggered', 'Sent', 'Failed')"
    )
    alert_type = serializers.ChoiceField(
        choices=VALID_ALERT_TYPES,
        required=False,
        allow_null=True,
        help_text="Filter by notification channel ('Email + Buzzer', 'Email', 'Log Only')"
    )
    threat_level = serializers.ChoiceField(
        choices=VALID_THREAT_LEVELS,
        required=False,
        allow_null=True,
        help_text="Filter by threat level ('HIGH', 'MEDIUM', 'LOW')"
    )
    animal_log_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Filter by associated AnimalLog ID"
    )
    animal_type = serializers.CharField(
        required=False,
        allow_null=True,
        max_length=100,
        help_text="Filter by animal species name"
    )
    date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Filter alerts created on an exact date (YYYY-MM-DD)"
    )
    start_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Filter alerts created on or after date (YYYY-MM-DD)"
    )
    end_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Filter alerts created on or before date (YYYY-MM-DD)"
    )

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "start_date": "Start date cannot be after end date."
            })
        return attrs
