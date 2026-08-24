"""
REST API views for FarmSync Dashboard Module.
Read-only authenticated endpoints for aggregated analytics and recent activity feeds.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.core.responses import success_response
from apps.dashboard.services import DashboardService
from apps.dashboard.serializers import DashboardSummarySerializer, DashboardRecentActivitySerializer


class DashboardSummaryView(APIView):
    """
    GET /api/v1/dashboard/summary/
    Retrieves aggregated summary metrics across all farm domains (Farmers, Attendance, Tasks, Detections, Alerts).
    Enforces authentication; read-only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        summary_data = DashboardService.get_summary_metrics()
        serializer = DashboardSummarySerializer(summary_data)
        return success_response(
            message="Dashboard summary retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class DashboardRecentActivityView(APIView):
    """
    GET /api/v1/dashboard/recent-activity/
    Retrieves latest activity feeds across Alerts, Animal Detections, and Tasks.
    Accepts optional query parameter 'limit' (default: 5, max: 20).
    Enforces authentication; read-only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.query_params.get('limit', 5))
        except (TypeError, ValueError):
            limit = 5

        activity_data = DashboardService.get_recent_activity(limit=limit)
        serializer = DashboardRecentActivitySerializer(activity_data)
        return success_response(
            message="Dashboard recent activity retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
