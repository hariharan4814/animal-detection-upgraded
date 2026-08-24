"""
Core infrastructure views for FarmSync REST API.
Provides health monitoring and versioned API root endpoints.
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from apps.core.responses import success_response


class HealthCheckView(APIView):
    """
    Health check endpoint for FarmSync Backend.
    Provides automated uptime monitoring for load balancers and decoupled frontend clients.
    
    Security: Never exposes environment variables, database credentials, or internal paths.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        health_data = {
            "status": "healthy",
            "service": "FarmSync REST API",
            "version": "v1",
        }
        return success_response(
            message="FarmSync backend API is operational",
            data=health_data,
            status_code=status.HTTP_200_OK
        )


class APIRootView(APIView):
    """
    Version 1 API Entry Point.
    Returns metadata about API versioning and operational discovery endpoints.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        root_data = {
            "name": "FarmSync API",
            "version": "v1",
            "status": "operational",
            "documentation": "/docs/api/step_2_api_foundation.md",
            "endpoints": {
                "health": "/api/v1/health/",
            }
        }
        return success_response(
            message="Welcome to FarmSync REST API v1",
            data=root_data,
            status_code=status.HTTP_200_OK
        )
