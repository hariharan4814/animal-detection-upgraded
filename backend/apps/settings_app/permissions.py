"""
Permission classes for FarmSync Settings Module.
Enforces role-based authorization so regular users cannot tamper with system-wide configuration.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow safe read-only access to authenticated users,
    while restricting write operations (POST, PUT, PATCH, DELETE) to staff/administrators.
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
    Used for highly sensitive areas such as SMTP credentials.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )
