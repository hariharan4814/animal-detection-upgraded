"""
REST API Views for FarmSync Alerts & Notification Module.
Provides historical alert listing, threat filtering, evidence downloading, and authorized evidence deletion.
"""

import os
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status, permissions

from apps.core.responses import success_response, error_response
from apps.core.permissions import IsAdminOrReadOnly
from apps.alerts.models import Alert
from apps.detection.models import AnimalLog
from apps.alerts.serializers import AlertSerializer, AlertFilterSerializer


class AlertListView(APIView):
    """
    GET /api/v1/alerts/ - List historical alert notification records.
    Supports query filters: status, alert_type, threat_level, animal_log_id, animal_type, date, start_date, end_date.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        filter_serializer = AlertFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        validated = filter_serializer.validated_data

        queryset = Alert.objects.select_related('animal_log').all().order_by('-created_at', '-id')

        # Filter by status
        status_val = validated.get('status')
        if status_val:
            queryset = queryset.filter(status=status_val)

        # Filter by alert_type
        alert_type_val = validated.get('alert_type')
        if alert_type_val:
            queryset = queryset.filter(alert_type=alert_type_val)

        # Filter by threat_level
        threat_level_val = validated.get('threat_level')
        if threat_level_val:
            queryset = queryset.filter(threat_level=threat_level_val.strip().upper())

        # Filter by animal_log_id
        animal_log_id_val = validated.get('animal_log_id')
        if animal_log_id_val:
            queryset = queryset.filter(animal_log_id=animal_log_id_val)

        # Filter by animal_type
        animal_type_val = validated.get('animal_type')
        if animal_type_val:
            queryset = queryset.filter(animal_log__animal_type__iexact=animal_type_val.strip())

        # Filter by exact creation date
        date_val = validated.get('date')
        if date_val:
            queryset = queryset.filter(created_at__date=date_val)

        # Filter by date range
        start_date = validated.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)

        end_date = validated.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        serializer = AlertSerializer(queryset, many=True)
        return success_response(
            message="Alerts retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class AlertDetailView(APIView):
    """
    GET    /api/v1/alerts/{id}/ - Retrieve detailed record of a specific alert event.
    DELETE /api/v1/alerts/{id}/ - Delete alert record and associated evidence (Staff/Admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk: int, *args, **kwargs):
        alert = get_object_or_404(Alert.objects.select_related('animal_log'), pk=pk)
        serializer = AlertSerializer(alert)
        return success_response(
            message="Alert details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request, pk: int, *args, **kwargs):
        alert = get_object_or_404(Alert.objects.select_related('animal_log'), pk=pk)

        # Safe evidence image cleanup if no other logs or alerts reference the file
        animal_log = alert.animal_log
        if animal_log and animal_log.image_path:
            # Check if any other logs use the same image
            other_logs_count = AnimalLog.objects.filter(image_path=animal_log.image_path).exclude(pk=animal_log.pk).count()
            if other_logs_count == 0:
                media_root = Path(getattr(settings, 'MEDIA_ROOT', 'media')).resolve()
                image_full_path = (media_root / animal_log.image_path.lstrip('/')).resolve()
                # Security: prevent path traversal outside MEDIA_ROOT
                if str(image_full_path).startswith(str(media_root)) and image_full_path.is_file():
                    try:
                        image_full_path.unlink(missing_ok=True)
                    except Exception:
                        pass

        alert.delete()
        return success_response(
            message=f"Alert #{pk} deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )


class AlertDownloadView(APIView):
    """
    GET /api/v1/alerts/{id}/download/ - Securely download the detection snapshot image associated with an alert.
    Enforces authentication and path-traversal prevention.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        alert = get_object_or_404(Alert.objects.select_related('animal_log'), pk=pk)

        if not alert.animal_log or not alert.animal_log.image_path:
            return error_response(
                message="No evidence snapshot image associated with this alert.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        media_root = Path(getattr(settings, 'MEDIA_ROOT', 'media')).resolve()
        image_path = alert.animal_log.image_path.lstrip('/')
        full_image_path = (media_root / image_path).resolve()

        # Path traversal security check
        if not str(full_image_path).startswith(str(media_root)):
            return error_response(
                message="Invalid evidence file path.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if not full_image_path.is_file():
            return error_response(
                message="Evidence image file not found on disk.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Generate clean, informative download filename
        animal = alert.animal_log.animal_type or "animal"
        ts_str = alert.created_at.strftime("%Y%m%d_%H%M%S") if alert.created_at else "evidence"
        download_filename = f"alert_{alert.id}_{animal}_{ts_str}.jpg"

        from django.http import HttpResponse
        with open(full_image_path, 'rb') as f:
            file_data = f.read()

        response = HttpResponse(file_data, content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
        return response
