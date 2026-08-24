"""
URL routing configuration for FarmSync Dashboard Module.
"""

from django.urls import path
from apps.dashboard.views import DashboardSummaryView, DashboardRecentActivityView

app_name = 'dashboard'

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='summary'),
    path('recent-activity/', DashboardRecentActivityView.as_view(), name='recent_activity'),
]
