"""
URL Routing for FarmSync Detection & Vision Module.
"""

from django.urls import path
from apps.detection.views import (
    DetectionStatusView,
    DetectionAnalyzeView,
    DetectionStreamView,
    AnimalLogListView,
    AnimalLogDetailView,
)

app_name = 'detection'

urlpatterns = [
    path('status/', DetectionStatusView.as_view(), name='detection_status'),
    path('analyze/', DetectionAnalyzeView.as_view(), name='detection_analyze'),
    path('stream/', DetectionStreamView.as_view(), name='detection_stream'),
    path('logs/', AnimalLogListView.as_view(), name='animal_log_list'),
    path('logs/<int:pk>/', AnimalLogDetailView.as_view(), name='animal_log_detail'),
]
