"""
URL routing configuration for FarmSync Settings Module.
"""

from django.urls import path
from apps.settings_app.views import (
    EmailSenderConfigView,
    AlertReceiverListCreateView,
    AlertReceiverDetailView,
    ProjectSettingsView,
    AnimalThreatRuleListCreateView,
    AnimalThreatRuleDetailView,
    AnimalThreatRuleResetDefaultsView,
    ThreatEmailTemplateListView,
    ThreatEmailTemplateDetailView,
    ThreatEmailTemplatePreviewView,
    ThreatEmailTemplateResetDefaultsView,
)

app_name = 'settings_app'

urlpatterns = [
    path('', ProjectSettingsView.as_view(), name='settings_root'),
    path('project/', ProjectSettingsView.as_view(), name='project_settings'),
    path('email-sender/', EmailSenderConfigView.as_view(), name='email_sender'),
    path('receivers/', AlertReceiverListCreateView.as_view(), name='receiver_list_create'),
    path('receivers/<int:pk>/', AlertReceiverDetailView.as_view(), name='receiver_detail'),
    
    # Animal Threat Classification Rules
    path('threat-rules/', AnimalThreatRuleListCreateView.as_view(), name='threat_rule_list_create'),
    path('threat-rules/<int:pk>/', AnimalThreatRuleDetailView.as_view(), name='threat_rule_detail'),
    path('threat-rules/reset-defaults/', AnimalThreatRuleResetDefaultsView.as_view(), name='threat_rule_reset_defaults'),

    # Threat Notification Email Templates
    path('email-templates/', ThreatEmailTemplateListView.as_view(), name='email_template_list'),
    path('email-templates/preview/', ThreatEmailTemplatePreviewView.as_view(), name='email_template_preview'),
    path('email-templates/reset-defaults/', ThreatEmailTemplateResetDefaultsView.as_view(), name='email_template_reset_defaults'),
    path('email-templates/<str:threat_level>/', ThreatEmailTemplateDetailView.as_view(), name='email_template_detail'),
]
