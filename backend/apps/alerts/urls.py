"""
URL Routing for FarmSync Alerts & Notification Module.
"""

from django.urls import path
from apps.alerts.views import AlertListView, AlertDetailView, AlertDownloadView

app_name = 'alerts'

urlpatterns = [
    path('', AlertListView.as_view(), name='alert_list'),
    path('<int:pk>/', AlertDetailView.as_view(), name='alert_detail'),
    path('<int:pk>/download/', AlertDownloadView.as_view(), name='alert_download'),
]
