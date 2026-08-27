"""
REST API views for FarmSync Settings Module.
Provides secure endpoints for email sender configuration, alert receivers,
project settings, animal threat classification rules, and email template customization.
"""

from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.core.responses import success_response, error_response
from apps.settings_app.models import (
    EmailSenderConfig,
    AlertReceiver,
    ProjectSettings,
    AnimalThreatRule,
    ThreatEmailTemplate,
)
from apps.settings_app.permissions import IsAdminOrReadOnly, IsAdminUserOnly
from apps.settings_app.serializers import (
    EmailSenderConfigSerializer,
    AlertReceiverSerializer,
    ProjectSettingsSerializer,
    AnimalThreatRuleSerializer,
    ThreatEmailTemplateSerializer,
    EmailTemplatePreviewSerializer,
)


class EmailSenderConfigView(APIView):
    """
    GET /api/v1/settings/email-sender/ - Retrieve active SMTP configuration (staff only).
    PUT /api/v1/settings/email-sender/ - Update active SMTP configuration (staff only).
    """
    permission_classes = [IsAdminUserOnly]

    def get(self, request, *args, **kwargs):
        config = EmailSenderConfig.get_active_config()
        serializer = EmailSenderConfigSerializer(config)
        return success_response(
            message="Active email sender configuration retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        config = EmailSenderConfig.get_active_config()
        serializer = EmailSenderConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Email sender configuration updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class AlertReceiverListCreateView(APIView):
    """
    GET  /api/v1/settings/receivers/ - List all alert recipients (authenticated users).
    POST /api/v1/settings/receivers/ - Register a new alert recipient (staff only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        receivers = AlertReceiver.objects.all()
        serializer = AlertReceiverSerializer(receivers, many=True)
        return success_response(
            message="Alert receivers retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = AlertReceiverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Alert receiver created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class AlertReceiverDetailView(APIView):
    """
    GET    /api/v1/settings/receivers/{id}/ - Retrieve single receiver details.
    PUT    /api/v1/settings/receivers/{id}/ - Update receiver (staff only).
    DELETE /api/v1/settings/receivers/{id}/ - Delete receiver (staff only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(AlertReceiver, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        receiver = self.get_object(pk)
        serializer = AlertReceiverSerializer(receiver)
        return success_response(
            message="Alert receiver details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, pk, *args, **kwargs):
        receiver = self.get_object(pk)
        serializer = AlertReceiverSerializer(receiver, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Alert receiver updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def delete(self, request, pk, *args, **kwargs):
        receiver = self.get_object(pk)
        receiver.delete()

        return success_response(
            message="Alert receiver deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )


class ProjectSettingsView(APIView):
    """
    GET   /api/v1/settings/        - Retrieve global system configuration (authenticated users).
    PATCH /api/v1/settings/        - Partially update global system configuration (staff/admin only).
    PUT   /api/v1/settings/        - Update system configuration (staff/admin only).
    GET   /api/v1/settings/project/ - Backward-compatible endpoint for system configuration.
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        settings_obj = ProjectSettings.get_settings()
        serializer = ProjectSettingsSerializer(settings_obj)
        return success_response(
            message="Project settings retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, *args, **kwargs):
        settings_obj = ProjectSettings.get_settings()
        serializer = ProjectSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Project settings partially updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, *args, **kwargs):
        settings_obj = ProjectSettings.get_settings()
        serializer = ProjectSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Project settings updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


# ==============================================================================
# Animal Threat Classification Rules APIs
# ==============================================================================

class AnimalThreatRuleListCreateView(APIView):
    """
    GET  /api/v1/settings/threat-rules/ - List all configured animal threat rules (Authenticated users).
    POST /api/v1/settings/threat-rules/ - Create or override a threat classification rule (Staff/Admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        # Auto-seed default rules if table is empty
        if not AnimalThreatRule.objects.exists():
            AnimalThreatRule.seed_default_rules()

        queryset = AnimalThreatRule.objects.all().order_by('animal_name')
        
        # Optional filter by threat_level query param
        tier = request.query_params.get('threat_level')
        if tier:
            queryset = queryset.filter(threat_level=tier.strip().upper())

        # Optional filter by is_active
        is_active_param = request.query_params.get('is_active')
        if is_active_param is not None:
            if is_active_param.lower() in ('true', '1'):
                queryset = queryset.filter(is_active=True)
            elif is_active_param.lower() in ('false', '0'):
                queryset = queryset.filter(is_active=False)

        serializer = AnimalThreatRuleSerializer(queryset, many=True)
        return success_response(
            message="Animal threat classification rules retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = AnimalThreatRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Animal threat classification rule created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class AnimalThreatRuleDetailView(APIView):
    """
    GET    /api/v1/settings/threat-rules/{id}/ - Retrieve a specific threat rule.
    PUT    /api/v1/settings/threat-rules/{id}/ - Update a threat rule (Staff/Admin only).
    PATCH  /api/v1/settings/threat-rules/{id}/ - Partially update a threat rule (Staff/Admin only).
    DELETE /api/v1/settings/threat-rules/{id}/ - Delete a threat rule (Staff/Admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(AnimalThreatRule, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        rule = self.get_object(pk)
        serializer = AnimalThreatRuleSerializer(rule)
        return success_response(
            message="Animal threat rule retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, pk, *args, **kwargs):
        rule = self.get_object(pk)
        serializer = AnimalThreatRuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Animal threat rule updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, pk, *args, **kwargs):
        return self.put(request, pk, *args, **kwargs)

    def delete(self, request, pk, *args, **kwargs):
        rule = self.get_object(pk)
        rule.delete()

        return success_response(
            message="Animal threat rule deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )


class AnimalThreatRuleResetDefaultsView(APIView):
    """
    POST /api/v1/settings/threat-rules/reset-defaults/ - Reset all rules to factory defaults (Staff/Admin only).
    """
    permission_classes = [IsAdminUserOnly]

    def post(self, request, *args, **kwargs):
        result = AnimalThreatRule.seed_default_rules(overwrite_existing=True)
        rules = AnimalThreatRule.objects.all().order_by('animal_name')
        serializer = AnimalThreatRuleSerializer(rules, many=True)
        return success_response(
            message=f"Threat rules reset to defaults successfully ({result['total']} rules active).",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


# ==============================================================================
# Threat Email Templates APIs
# ==============================================================================

class ThreatEmailTemplateListView(APIView):
    """
    GET  /api/v1/settings/email-templates/ - List all threat email templates (Authenticated users).
    POST /api/v1/settings/email-templates/ - Create a threat email template (Staff/Admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, *args, **kwargs):
        # Auto-seed default templates if table is empty
        if not ThreatEmailTemplate.objects.exists():
            ThreatEmailTemplate.seed_default_templates()

        templates = ThreatEmailTemplate.objects.all().order_by('threat_level')
        serializer = ThreatEmailTemplateSerializer(templates, many=True)
        return success_response(
            message="Threat email templates retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = ThreatEmailTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Threat email template created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


class ThreatEmailTemplateDetailView(APIView):
    """
    GET   /api/v1/settings/email-templates/{threat_level}/ - Retrieve email template by threat level (HIGH, MEDIUM, LOW).
    PUT   /api/v1/settings/email-templates/{threat_level}/ - Update email template by threat level (Staff/Admin only).
    PATCH /api/v1/settings/email-templates/{threat_level}/ - Partially update email template (Staff/Admin only).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, threat_level):
        norm_tier = threat_level.strip().upper()
        template = ThreatEmailTemplate.objects.filter(threat_level=norm_tier).first()
        if not template:
            template = ThreatEmailTemplate.get_template_for_threat(norm_tier)
        return template

    def get(self, request, threat_level, *args, **kwargs):
        template = self.get_object(threat_level)
        serializer = ThreatEmailTemplateSerializer(template)
        return success_response(
            message=f"{threat_level.upper()} threat email template retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def put(self, request, threat_level, *args, **kwargs):
        template = self.get_object(threat_level)
        serializer = ThreatEmailTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message=f"{threat_level.upper()} threat email template updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def patch(self, request, threat_level, *args, **kwargs):
        return self.put(request, threat_level, *args, **kwargs)


class ThreatEmailTemplatePreviewView(APIView):
    """
    POST /api/v1/settings/email-templates/preview/ - Render sample email preview without sending email (Staff/Admin only).
    """
    permission_classes = [IsAdminUserOnly]

    def post(self, request, *args, **kwargs):
        serializer = EmailTemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        preview_data = serializer.generate_preview()

        if not preview_data.get("success", False):
            return error_response(
                message=preview_data.get("error", "Failed to render template preview."),
                errors={"template": preview_data.get("error")},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return success_response(
            message="Template preview generated successfully.",
            data=preview_data,
            status_code=status.HTTP_200_OK
        )


class ThreatEmailTemplateResetDefaultsView(APIView):
    """
    POST /api/v1/settings/email-templates/reset-defaults/ - Reset all email templates to default (Staff/Admin only).
    """
    permission_classes = [IsAdminUserOnly]

    def post(self, request, *args, **kwargs):
        result = ThreatEmailTemplate.seed_default_templates(overwrite_existing=True)
        templates = ThreatEmailTemplate.objects.all().order_by('threat_level')
        serializer = ThreatEmailTemplateSerializer(templates, many=True)
        return success_response(
            message="Threat email templates reset to default successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
