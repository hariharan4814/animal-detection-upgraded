"""
REST API Views for FarmSync Alerts & Notification Module.
Provides read-only access to historical alert records with structured query filtering.
"""

from rest_framework.views import APIView
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404

from apps.core.responses import success_response
from apps.alerts.models import Alert
from apps.alerts.serializers import AlertSerializer, AlertFilterSerializer


class AlertListView(APIView):
    """
    GET /api/v1/alerts/ - List historical alert notification records.
    Supports query parameter filters: status, alert_type, animal_log_id, animal_type, date, start_date, end_date.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Validate query parameters
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
    GET /api/v1/alerts/{id}/ - Retrieve detailed record of a specific alert event.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        alert = get_object_or_404(Alert.objects.select_related('animal_log'), pk=pk)
        serializer = AlertSerializer(alert)
        return success_response(
            message="Alert details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
