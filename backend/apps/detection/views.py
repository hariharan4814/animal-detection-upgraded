"""
REST API Views for FarmSync Detection & Vision Module.
Provides status monitoring, detection toggling, manual image analysis, live MJPEG streaming, and historical logs.
"""

import logging
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.responses import success_response
from apps.core.permissions import IsAdminOrReadOnly
from apps.detection.models import AnimalLog
from apps.detection.services import DetectionService, VideoStreamService
from apps.detection.serializers import (
    AnimalLogSerializer,
    DetectionStatusSerializer,
    DetectionToggleSerializer,
    ImageAnalysisSerializer,
)

logger = logging.getLogger(__name__)


class DetectionStatusView(APIView):
    """
    GET   /api/v1/detection/status/ - Retrieve current YOLO engine health and configuration (Authenticated users).
    PATCH /api/v1/detection/status/ - Toggle detection engine master switch (Staff/Admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        status_data = DetectionService.get_status()
        serializer = DetectionStatusSerializer(status_data)
        return success_response(
            message="Detection status retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, *args, **kwargs):
        serializer = DetectionToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = DetectionService.set_detection_enabled(
            serializer.validated_data['detection_enabled']
        )
        out_serializer = DetectionStatusSerializer(new_status)
        return success_response(
            message="Detection status updated successfully.",
            data=out_serializer.data,
            status_code=status.HTTP_200_OK
        )


class DetectionAnalyzeView(APIView):
    """
    POST /api/v1/detection/analyze/ - Upload an image for immediate YOLO animal detection and threat analysis.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = ImageAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data['image']
        field_name = serializer.validated_data.get('field', 'Main Field')

        try:
            image_bytes = image_file.read()
            analysis_result = DetectionService.analyze_image_bytes(
                image_bytes=image_bytes,
                field_name=field_name
            )
        except ValueError as val_err:
            return success_response(
                message=str(val_err),
                data={"error": str(val_err)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Image analysis error: {e}", exc_info=True)
            return success_response(
                message="An error occurred while processing the image for detection.",
                data={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response(
            message="Image analysis completed successfully.",
            data=analysis_result,
            status_code=status.HTTP_200_OK
        )


class DetectionStreamView(APIView):
    """
    GET /api/v1/detection/stream/ - Multipart MJPEG live video stream endpoint.
    Supports standard Bearer Authorization header, Session, and query parameter token.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed

        # 1. Check if user is already authenticated via header or session
        if not (request.user and request.user.is_authenticated):
            # 2. Check query parameter token for browser <img> streaming
            token = request.query_params.get('token')
            if token:
                try:
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(token)
                    user = jwt_auth.get_user(validated_token)
                    if user and user.is_authenticated:
                        request.user = user
                    else:
                        raise AuthenticationFailed("User not found or inactive.")
                except Exception:
                    raise AuthenticationFailed("Invalid or expired stream token.")
            else:
                raise NotAuthenticated("Authentication credentials were not provided.")

        return StreamingHttpResponse(
            VideoStreamService.generate_frames(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )


class AnimalLogListView(APIView):
    """
    GET /api/v1/detection/logs/ - List historical animal detection event logs with optional filtering.
    Filters: animal_type, field, date, start_date, end_date, min_confidence.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = AnimalLog.objects.all().order_by('-timestamp', '-id')

        # Filter by animal species
        animal_type = request.query_params.get('animal_type')
        if animal_type:
            queryset = queryset.filter(animal_type__iexact=animal_type.strip())

        # Filter by field location
        field_param = request.query_params.get('field')
        if field_param:
            queryset = queryset.filter(field__icontains=field_param.strip())

        # Filter by minimum confidence score
        min_conf = request.query_params.get('min_confidence')
        if min_conf:
            try:
                queryset = queryset.filter(confidence__gte=float(min_conf))
            except (ValueError, TypeError):
                pass

        # Filter by exact date (YYYY-MM-DD)
        date_param = request.query_params.get('date')
        if date_param:
            try:
                queryset = queryset.filter(timestamp__date=date_param)
            except (DjangoValidationError, ValueError):
                pass

        # Filter by date range
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except (DjangoValidationError, ValueError):
                pass

        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except (DjangoValidationError, ValueError):
                pass

        serializer = AnimalLogSerializer(queryset, many=True)
        return success_response(
            message="Animal detection logs retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class AnimalLogDetailView(APIView):
    """
    GET /api/v1/detection/logs/{id}/ - Retrieve detailed record of a single animal detection event.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        log = get_object_or_404(AnimalLog, pk=pk)
        serializer = AnimalLogSerializer(log)
        return success_response(
            message="Animal detection log details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
