"""
REST API views for FarmSync Attendance Module.
Provides list, detail, check-in, check-out, and report generation endpoints.
"""

from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.core.responses import success_response
from apps.core.permissions import IsAdminOrReadOnly
from apps.attendance.models import Attendance
from apps.attendance.services import AttendanceService
from apps.attendance.serializers import (
    AttendanceSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    AttendanceReportFilterSerializer,
)


class AttendanceListView(APIView):
    """
    GET /api/v1/attendance/ - Lists attendance logs in reverse chronological order.
    Supports optional query filters: farmer_id, date, start_date, end_date, is_active.
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        queryset = Attendance.objects.select_related('farmer').all().order_by('-date', '-check_in', '-id')

        # Optional filters
        farmer_id = request.query_params.get('farmer_id')
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)

        date_val = request.query_params.get('date')
        if date_val:
            queryset = queryset.filter(date=date_val)

        start_date = request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        end_date = request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ('true', '1'):
                queryset = queryset.filter(check_out__isnull=True)
            elif is_active.lower() in ('false', '0'):
                queryset = queryset.filter(check_out__isnull=False)

        serializer = AttendanceSerializer(queryset, many=True)
        return success_response(
            message="Attendance records retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class AttendanceDetailView(APIView):
    """
    GET /api/v1/attendance/{id}/ - Retrieve details of a specific attendance record.
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk: int, *args, **kwargs):
        attendance = get_object_or_404(Attendance.objects.select_related('farmer'), pk=pk)
        serializer = AttendanceSerializer(attendance)
        return success_response(
            message="Attendance record details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class CheckInView(APIView):
    """
    POST /api/v1/attendance/check-in/ - Records a worker check-in (staff/admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def post(self, request, *args, **kwargs):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attendance = AttendanceService.check_in(
            farmer_id=serializer.validated_data['farmer_id'],
            device_location=serializer.validated_data.get('device_location'),
            check_in_time=serializer.validated_data.get('check_in_time'),
            record_date=serializer.validated_data.get('date')
        )

        out_serializer = AttendanceSerializer(attendance)
        return success_response(
            message="Worker check-in recorded successfully.",
            data=out_serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class CheckOutView(APIView):
    """
    POST /api/v1/attendance/check-out/ - Records a worker check-out and computes hours (staff/admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def post(self, request, *args, **kwargs):
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attendance = AttendanceService.check_out(
            farmer_id=serializer.validated_data['farmer_id'],
            device_location=serializer.validated_data.get('device_location'),
            check_out_time=serializer.validated_data.get('check_out_time'),
            record_date=serializer.validated_data.get('date')
        )

        out_serializer = AttendanceSerializer(attendance)
        return success_response(
            message="Worker check-out recorded successfully.",
            data=out_serializer.data,
            status_code=status.HTTP_200_OK
        )


class AttendanceReportView(APIView):
    """
    GET /api/v1/attendance/report/ - Generates structured attendance reports across date ranges.
    Supports query parameters: start_date, end_date, farmer_id.
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        filter_serializer = AttendanceReportFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        validated = filter_serializer.validated_data

        queryset = Attendance.objects.select_related('farmer').all().order_by('-date', '-check_in', '-id')

        start_date = validated.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        end_date = validated.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        farmer_id = validated.get('farmer_id')
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)

        records_serializer = AttendanceSerializer(queryset, many=True)
        total_hours_sum = round(sum(att.total_hours or 0.0 for att in queryset), 2)

        report_data = {
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "farmer_id": farmer_id,
            "total_records": queryset.count(),
            "total_hours_sum": total_hours_sum,
            "records": records_serializer.data
        }

        return success_response(
            message="Attendance report generated successfully.",
            data=report_data,
            status_code=status.HTTP_200_OK
        )
