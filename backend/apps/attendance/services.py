"""
Service layer for FarmSync Attendance Module.
Encapsulates domain logic for worker check-in, check-out, duration calculation, and reporting.
"""

from typing import Optional
from datetime import datetime, date, time
from django.utils import timezone
from rest_framework import serializers

from apps.farmers.models import Farmer
from apps.attendance.models import Attendance


class AttendanceService:
    """
    Business logic and orchestration for attendance check-in/out and analytical reporting.
    """

    @classmethod
    def check_in(
        cls,
        farmer_id: int,
        device_location: Optional[str] = None,
        check_in_time: Optional[time] = None,
        record_date: Optional[date] = None
    ) -> Attendance:
        """
        Records a worker check-in.
        Legacy rule: Only 1 attendance record per farmer per date.
        """
        try:
            farmer = Farmer.objects.get(pk=farmer_id)
        except Farmer.DoesNotExist:
            raise serializers.ValidationError({"farmer_id": "Farmer not found with the specified ID."})

        target_date = record_date or timezone.localdate()
        target_time = check_in_time or timezone.localtime().time().replace(microsecond=0)

        # Determine location fallback
        location = device_location.strip() if (device_location and device_location.strip()) else farmer.field

        # Verify duplicate check-in rule (Legacy rule: 1 record per farmer per date)
        existing = Attendance.objects.filter(farmer=farmer, date=target_date).first()
        if existing:
            raise serializers.ValidationError({
                "farmer_id": f"An attendance record already exists for {farmer.name} on {target_date}."
            })

        attendance = Attendance.objects.create(
            farmer=farmer,
            date=target_date,
            check_in=target_time,
            check_out=None,
            total_hours=0.0,
            location=location
        )
        return attendance

    @classmethod
    def check_out(
        cls,
        farmer_id: Optional[int] = None,
        attendance_id: Optional[int] = None,
        work_description: str = "",
        device_location: Optional[str] = None,
        check_out_time: Optional[time] = None,
        record_date: Optional[date] = None
    ) -> Attendance:
        """
        Records worker check-out, validates mandatory work description, computes duration,
        persists the completed shift record, and dispatches the daily work report email.
        """
        from apps.attendance.email_service import AttendanceEmailService

        # Validate mandatory work description
        clean_desc = (work_description or '').strip()
        if not clean_desc:
            raise serializers.ValidationError({
                "work_description": "Work description is required before checking out."
            })
        if len(clean_desc) < 5:
            raise serializers.ValidationError({
                "work_description": "Please provide a detailed work summary (minimum 5 characters)."
            })

        target_date = record_date or timezone.localdate()
        target_time = check_out_time or timezone.localtime().time().replace(microsecond=0)

        # Resolve attendance record
        attendance = None
        if attendance_id:
            attendance = Attendance.objects.select_related('farmer').filter(pk=attendance_id).first()
            if not attendance:
                raise serializers.ValidationError({"attendance_id": "Attendance record not found."})
            if attendance.check_out is not None:
                raise serializers.ValidationError({
                    "attendance_id": f"Attendance record #{attendance_id} has already been checked out."
                })
        elif farmer_id:
            try:
                farmer = Farmer.objects.get(pk=farmer_id)
            except Farmer.DoesNotExist:
                raise serializers.ValidationError({"farmer_id": "Farmer not found with the specified ID."})

            attendance = Attendance.objects.select_related('farmer').filter(
                farmer=farmer,
                date=target_date,
                check_out__isnull=True
            ).first()

            if not attendance:
                # Check if farmer already checked out today
                already_completed = Attendance.objects.filter(
                    farmer=farmer,
                    date=target_date,
                    check_out__isnull=False
                ).first()
                if already_completed:
                    raise serializers.ValidationError({
                        "farmer_id": f"{farmer.name} has already checked out for {target_date}."
                    })
                raise serializers.ValidationError({
                    "farmer_id": f"No active check-in found for {farmer.name} on {target_date} to check out."
                })

        if not attendance:
            raise serializers.ValidationError({"farmer_id": "Unable to locate active attendance record."})

        # Calculate duration
        dt_in = datetime.combine(attendance.date, attendance.check_in or time(0, 0))
        dt_out = datetime.combine(attendance.date, target_time)

        diff_seconds = (dt_out - dt_in).total_seconds()
        if diff_seconds < 0:
            raise serializers.ValidationError({
                "check_out_time": "Check-out time cannot be earlier than check-in time."
            })

        hours = round(diff_seconds / 3600.0, 2)

        # 1. Update attendance shift data and save to database FIRST
        attendance.check_out = target_time
        attendance.total_hours = hours
        attendance.work_description = clean_desc
        if device_location and device_location.strip():
            attendance.location = device_location.strip()

        attendance.save()

        # 2. Dispatch automated email report to farmer and administrator
        try:
            email_res = AttendanceEmailService.send_farmer_checkout_report(attendance)
            if email_res.get("sent"):
                attendance.email_sent = True
                attendance.email_sent_at = timezone.now()
                attendance.email_error = None
            else:
                attendance.email_sent = False
                attendance.email_error = email_res.get("error")
            attendance.save(update_fields=['email_sent', 'email_sent_at', 'email_error', 'updated_at'])
        except Exception as mail_err:
            attendance.email_sent = False
            attendance.email_error = str(mail_err)
            attendance.save(update_fields=['email_sent', 'email_error', 'updated_at'])

        return attendance
