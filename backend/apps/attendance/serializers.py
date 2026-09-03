"""
Serializers for FarmSync Attendance Module.
Provides input validation for check-in/out workflows and structured output contracts.
"""

from rest_framework import serializers
from apps.attendance.models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Standard representation of an Attendance log record with work tracking and email audit status.
    """
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)
    farmer_email = serializers.EmailField(source='farmer.email', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id',
            'farmer',
            'farmer_name',
            'farmer_email',
            'date',
            'check_in',
            'check_out',
            'total_hours',
            'location',
            'work_description',
            'email_sent',
            'email_sent_at',
            'email_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'farmer_name',
            'farmer_email',
            'total_hours',
            'email_sent',
            'email_sent_at',
            'email_error',
            'created_at',
            'updated_at'
        ]


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
    Mandates submission of what work was completed today.
    """
    farmer_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the registered farm worker checking out"
    )
    attendance_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Direct ID of the active attendance record being checked out"
    )
    work_description = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
        help_text="What work did you complete today? Mandatory during checkout."
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

    def validate(self, attrs):
        if not attrs.get('farmer_id') and not attrs.get('attendance_id'):
            raise serializers.ValidationError({
                "farmer_id": "Either farmer_id or attendance_id must be provided for checkout."
            })
        raw_desc = attrs.get('work_description')
        if not raw_desc or not str(raw_desc).strip():
            raise serializers.ValidationError({
                "work_description": "Work description is required before checkout."
            })
        trimmed = str(raw_desc).strip()
        if len(trimmed) < 5:
            raise serializers.ValidationError({
                "work_description": "Please provide a detailed work summary (minimum 5 characters)."
            })
        attrs['work_description'] = trimmed
        return attrs


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
