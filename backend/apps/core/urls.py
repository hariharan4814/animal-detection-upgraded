"""
URL routing configuration for FarmSync Core module.
"""

from django.urls import path
from apps.core.views import HealthCheckView, APIRootView

app_name = 'core'

urlpatterns = [
    path('', APIRootView.as_view(), name='api_root'),
    path('health/', HealthCheckView.as_view(), name='health_check'),
]
