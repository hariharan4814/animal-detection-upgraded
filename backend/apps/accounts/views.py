"""
Authentication views for FarmSync REST API.
Handles login, token refresh, authenticated user profile (/me), and logout.
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from apps.core.responses import success_response
from apps.accounts.serializers import LoginSerializer, UserSerializer, LogoutSerializer


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Authenticates user credentials and issues JWT access and refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.validated_data

        user_data = UserSerializer(result['user']).data
        response_payload = {
            "access": result['access'],
            "refresh": result['refresh'],
            "user": user_data
        }

        return success_response(
            message="Login successful",
            data=response_payload,
            status_code=status.HTTP_200_OK
        )


class CustomTokenRefreshView(APIView):
    """
    POST /api/v1/auth/refresh/
    Accepts a valid refresh token and issues a new access token.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return success_response(
            message="Token refreshed successfully",
            data=serializer.validated_data,
            status_code=status.HTTP_200_OK
        )


class CurrentUserView(APIView):
    """
    GET /api/v1/auth/me/
    Retrieves safe profile information for the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_data = UserSerializer(request.user).data
        return success_response(
            message="Current user profile retrieved successfully",
            data=user_data,
            status_code=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the provided refresh token, invalidating future refresh attempts.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Logout successful. Refresh token has been revoked.",
            data={},
            status_code=status.HTTP_200_OK
        )
