"""
URL routing configuration for FarmSync Settings Module.
"""

from django.urls import path
from apps.settings_app.views import (
    EmailSenderConfigView,
    AlertReceiverListCreateView,
    AlertReceiverDetailView,
    ProjectSettingsView,
)

app_name = 'settings_app'

urlpatterns = [
    path('email-sender/', EmailSenderConfigView.as_view(), name='email_sender'),
    path('receivers/', AlertReceiverListCreateView.as_view(), name='receiver_list_create'),
    path('receivers/<int:pk>/', AlertReceiverDetailView.as_view(), name='receiver_detail'),
    path('project/', ProjectSettingsView.as_view(), name='project_settings'),
]
