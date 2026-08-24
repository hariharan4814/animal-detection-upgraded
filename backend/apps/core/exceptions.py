"""
Global exception handling configuration for FarmSync Django REST API.

Standardizes all DRF exceptions into the unified JSON error envelope:
{
    "success": false,
    "message": "Error description",
    "errors": {
        "field_name": ["Validation error message"]
    }
}
"""

import logging
from typing import Any, Dict
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response:
    """
    Custom exception handler for Django REST Framework.
    Intercepts standard DRF and Django exceptions and formats them
    consistently according to FarmSync API contracts.
    """
    # Call DRF's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    if response is not None:
        custom_errors: Dict[str, Any] = {}
        message = "An error occurred while processing your request."

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = str(response.data['detail'])
                # Capture any supplementary error fields if present
                for key, val in response.data.items():
                    if key != 'detail':
                        custom_errors[key] = val if isinstance(val, list) else [str(val)]
            else:
                message = "Validation failed for one or more fields."
                for key, val in response.data.items():
                    custom_errors[key] = val if isinstance(val, list) else [str(val)]
        elif isinstance(response.data, list):
            message = "Validation error."
            custom_errors["non_field_errors"] = response.data
        else:
            message = str(response.data)

        # Mutate response data to conform to unified contract
        response.data = {
            "success": False,
            "message": message,
            "errors": custom_errors
        }
        return response

    # Handle unhandled server exceptions (HTTP 500)
    view_name = context.get('view', 'UnknownView')
    logger.error(f"Unhandled server exception in {view_name}: {exc}", exc_info=True)

    return Response(
        {
            "success": False,
            "message": "An unexpected server error occurred.",
            "errors": {
                "server": ["Internal server error. Please contact the administrator."]
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
