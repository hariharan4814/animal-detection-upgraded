"""
Serializers for FarmSync Attendance Module.
Provides input validation for check-in/out workflows and structured output contracts.
"""

from rest_framework import serializers
from apps.attendance.models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Standard representation of an Attendance log record.
    """
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id',
            'farmer',
            'farmer_name',
            'date',
            'check_in',
            'check_out',
            'total_hours',
            'location',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'farmer_name', 'total_hours', 'created_at', 'updated_at']


class CheckInSerializer(serializers.Serializer):
    """
    Payload serializer for recording worker check-in.
    """
    farmer_id = serializers.IntegerField(
        required=True,
        help_text="ID of the registered farm worker checking in"
    )
    device_location = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="GPS coordinates or field location string (optional)"
    )
    check_in_time = serializers.TimeField(
        required=False,
        allow_null=True,
        help_text="Explicit check-in time (HH:MM:SS, optional - defaults to current server time)"
    )
    date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Explicit attendance date (YYYY-MM-DD, optional - defaults to today)"
    )


class CheckOutSerializer(serializers.Serializer):
    """
    Payload serializer for recording worker check-out.
    """
    farmer_id = serializers.IntegerField(
        required=True,
        help_text="ID of the registered farm worker checking out"
    )
    device_location = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=255,
        help_text="GPS coordinates or field location string (optional)"
    )
    check_out_time = serializers.TimeField(
        required=False,
        allow_null=True,
        help_text="Explicit check-out time (HH:MM:SS, optional - defaults to current server time)"
    )
    date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Explicit attendance date (YYYY-MM-DD, optional - defaults to today)"
    )


class AttendanceReportFilterSerializer(serializers.Serializer):
    """
    Query parameter serializer for attendance report filtering.
    """
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    farmer_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "start_date": "Start date cannot be after end date."
            })
        return attrs
