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
        if value:
            trimmed = value.strip().lower()
            return trimmed
        return value
