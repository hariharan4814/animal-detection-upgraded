"""
Serializers for FarmSync Farmers Module.
Provides input validation, field sanitization, and explicit response formatting.
"""

from rest_framework import serializers
from apps.farmers.models import Farmer


class FarmerSerializer(serializers.ModelSerializer):
    """
    Serializer for Farmer CRUD operations.
    Exposes workforce attributes with strict server-side validation.
    """
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Farmer email address is required.',
            'blank': 'Farmer email address cannot be blank.',
            'invalid': 'Enter a valid email address.'
        }
    )

    class Meta:
        model = Farmer
        fields = [
            'id',
            'name',
            'phone',
            'field',
            'email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Farmer name cannot be blank or whitespace.")
        return trimmed

    def validate_phone(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Contact phone number cannot be blank.")
        return trimmed

    def validate_field(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Assigned agricultural field/location cannot be blank.")
        return trimmed

    def validate_email(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Farmer email address is required.")
        trimmed = value.strip().lower()

        # Uniqueness validation
        qs = Farmer.objects.filter(email__iexact=trimmed)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A registered farmer with this email address already exists.")

        return trimmed
