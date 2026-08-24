"""
Serializers for FarmSync Tasks Module.
Provides input validation, worker foreign key resolution, status validation, and standardized output serialization.
"""

import datetime as dt
from django.utils import timezone
from rest_framework import serializers
from apps.tasks.models import Task
from apps.farmers.models import Farmer


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model CRUD operations.
    Exposes task attributes, worker foreign key linkage, and human-readable worker name.
    """
    assigned_to_name = serializers.CharField(
        source='assigned_to.name',
        read_only=True,
        default=None,
        help_text="Full name of the assigned farm worker"
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'task_name',
            'assigned_to',
            'assigned_to_name',
            'status',
            'date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'assigned_to_name', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """
        Coerce datetime to date if model instance contains datetime from timezone.now default.
        """
        if hasattr(instance, 'date') and isinstance(instance.date, dt.datetime):
            instance.date = instance.date.date()
        return super().to_representation(instance)

    def create(self, validated_data):
        """
        Ensure default date is assigned as a date object when omitted.
        """
        if 'date' not in validated_data or not validated_data['date']:
            validated_data['date'] = timezone.localdate()
        return super().create(validated_data)

    def validate_task_name(self, value: str) -> str:
        """
        Validate that task_name is not blank or composed solely of whitespace characters.
        """
        if not value:
            raise serializers.ValidationError("Task name cannot be blank.")
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Task name cannot be blank or whitespace.")
        return trimmed

    def validate_status(self, value: str) -> str:
        """
        Validate that status is one of the verified lifecycle choices ('Pending', 'Completed').
        """
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status '{value}'. Supported statuses are: {', '.join(valid_statuses)}."
            )
        return value
