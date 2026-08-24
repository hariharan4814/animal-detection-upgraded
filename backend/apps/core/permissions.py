"""
Core reusable permission classes for FarmSync REST API.
Enforces role-based authorization: authenticated users have read access, while write/mutate actions require staff/superuser privileges.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission allowing safe read-only access (GET, HEAD, OPTIONS) to authenticated users,
    while restricting write operations (POST, PUT, PATCH, DELETE) strictly to staff/administrators.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user.is_staff or request.user.is_superuser)


class IsAdminUserOnly(permissions.BasePermission):
    """
    Restricts both read and write access strictly to staff or superusers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )
