"""
URL routing configuration for FarmSync Accounts & Authentication module.
"""

from django.urls import path
from apps.accounts.views import (
    LoginView,
    CustomTokenRefreshView,
    CurrentUserView,
    LogoutView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
