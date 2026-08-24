"""
Standardized API response helper functions for FarmSync.

Enforces unified response envelope contracts:
- Success: {"success": True, "message": "...", "data": {...}}
- Error:   {"success": False, "message": "...", "errors": {...}}
"""

from rest_framework.response import Response
from rest_framework import status
from typing import Any, Optional, Dict


def standard_response(
    success: bool = True,
    message: str = "Success",
    data: Optional[Any] = None,
    errors: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """
    Constructs a uniform JSON response envelope conforming to API contracts.
    
    :param success: Boolean indicating operation outcome.
    :param message: Human-readable summary message.
    :param data: Data payload (dictionary, list, or primitive) for successful requests.
    :param errors: Error details or validation dictionary for failed requests.
    :param status_code: HTTP status code.
    :return: rest_framework.response.Response object.
    """
    payload = {
        "success": success,
        "message": message,
    }
    if success:
        payload["data"] = data if data is not None else {}
    else:
        payload["errors"] = errors if errors is not None else {}
        
    return Response(payload, status=status_code)


def success_response(
    message: str = "Operation completed successfully.",
    data: Optional[Any] = None,
    status_code: int = status.HTTP_200_OK
) -> Response:
    """Convenience helper for successful responses."""
    return standard_response(
        success=True,
        message=message,
        data=data,
        status_code=status_code
    )


def error_response(
    message: str = "An error occurred while processing the request.",
    errors: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> Response:
    """Convenience helper for error responses."""
    return standard_response(
        success=False,
        message=message,
        errors=errors,
        status_code=status_code
    )
