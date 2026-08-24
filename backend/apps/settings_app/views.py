"""
REST API views for FarmSync Settings Module.
Provides secure endpoints for email sender configuration, alert receivers, and project settings.
"""

from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.core.responses import success_response
from apps.settings_app.models import EmailSenderConfig, AlertReceiver, ProjectSettings
from apps.settings_app.permissions import IsAdminOrReadOnly, IsAdminUserOnly
from apps.settings_app.serializers import (
    EmailSenderConfigSerializer,
    AlertReceiverSerializer,
    ProjectSettingsSerializer,
)


class EmailSenderConfigView(APIView):
    """
    GET /api/v1/settings/email-sender/ - Retrieve active SMTP configuration (staff only).
    PUT /api/v1/settings/email-sender/ - Update active SMTP configuration (staff only).
    """
    permission_classes = [IsAdminUserOnly]

    def get(self, request, *args, **kwargs):
        config = EmailSenderConfig.get_active_config()
        serializer = EmailSenderConfigSerializer(config)
        return success_response(
            message="Active email sender configuration retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        config = EmailSenderConfig.get_active_config()
        serializer = EmailSenderConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Email sender configuration updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class AlertReceiverListCreateView(APIView):
    """
    GET  /api/v1/settings/receivers/ - List all alert recipients (authenticated users).
    POST /api/v1/settings/receivers/ - Register a new alert recipient (staff only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        receivers = AlertReceiver.objects.all()
        serializer = AlertReceiverSerializer(receivers, many=True)
        return success_response(
            message="Alert receivers retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = AlertReceiverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Alert receiver created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class AlertReceiverDetailView(APIView):
    """
    GET    /api/v1/settings/receivers/{id}/ - Retrieve single receiver details.
    PUT    /api/v1/settings/receivers/{id}/ - Update receiver (staff only).
    DELETE /api/v1/settings/receivers/{id}/ - Delete receiver (staff only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(AlertReceiver, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        receiver = self.get_object(pk)
        serializer = AlertReceiverSerializer(receiver)
        return success_response(
            message="Alert receiver details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, pk, *args, **kwargs):
        receiver = self.get_object(pk)
        serializer = AlertReceiverSerializer(receiver, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Alert receiver updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request, pk, *args, **kwargs):
        receiver = self.get_object(pk)
        receiver.delete()

        return success_response(
            message="Alert receiver deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )


class ProjectSettingsView(APIView):
    """
    GET   /api/v1/settings/        - Retrieve global system configuration (authenticated users).
    PATCH /api/v1/settings/        - Partially update global system configuration (staff/admin only).
    PUT   /api/v1/settings/        - Update system configuration (staff/admin only).
    GET   /api/v1/settings/project/ - Backward-compatible endpoint for system configuration.
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        settings_obj = ProjectSettings.get_settings()
        serializer = ProjectSettingsSerializer(settings_obj)
        return success_response(
            message="Project settings retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, *args, **kwargs):
        settings_obj = ProjectSettings.get_settings()
        serializer = ProjectSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Project settings partially updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        settings_obj = ProjectSettings.get_settings()
        serializer = ProjectSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Project settings updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
