"""
Comprehensive unit and integration tests for FarmSync Settings Module.
Verifies Email Sender configuration, Alert Receivers, Project Settings,
Animal Threat Rules, Threat Email Templates, Template Previews, and security boundaries.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.settings_app.models import (
    EmailSenderConfig,
    AlertReceiver,
    ProjectSettings,
    AnimalThreatRule,
    ThreatEmailTemplate,
)
from apps.detection.services import DetectionService, clear_cooldown_cache
from services.threat_classification import (
    classify_animal,
    get_active_threat_rules,
    invalidate_threat_cache,
)
from services.notifications.service import NotificationService
from services.yolo import set_mock_model, reset_model_cache


class SettingsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Regular non-staff user
        self.regular_user = User.objects.create_user(
            username="regular_worker",
            password="WorkerPassword123!",
            email="worker@farmsync.local"
        )

        # Admin / Staff user
        self.admin_user = User.objects.create_user(
            username="farm_admin",
            password="AdminPassword123!",
            email="admin@farmsync.local",
            is_staff=True
        )

        self.settings_root_url = reverse('settings_app:settings_root')
        self.email_sender_url = reverse('settings_app:email_sender')
        self.receivers_url = reverse('settings_app:receiver_list_create')
        self.project_settings_url = reverse('settings_app:project_settings')
        self.threat_rules_url = reverse('settings_app:threat_rule_list_create')
        self.threat_rules_reset_url = reverse('settings_app:threat_rule_reset_defaults')
        self.email_templates_url = reverse('settings_app:email_template_list')
        self.email_templates_preview_url = reverse('settings_app:email_template_preview')
        self.email_templates_reset_url = reverse('settings_app:email_template_reset_defaults')

    def tearDown(self):
        reset_model_cache()
        clear_cooldown_cache()
        invalidate_threat_cache()

    # ==========================================================================
    # 1. EMAIL SENDER CONFIGURATION TESTS
    # ==========================================================================
    def test_01_email_sender_unauthenticated_rejected(self):
        response = self.client.get(self.email_sender_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_email_sender_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.email_sender_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_03_email_sender_admin_can_retrieve(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.email_sender_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('smtp_host', data['data'])
        self.assertIn('smtp_password_configured', data['data'])

    def test_04_email_sender_password_write_only(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "sender_name": "FarmSync Central Alerts",
            "sender_email": "farmalerts@example.com",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_password": "super-secret-app-password-999",
            "use_tls": True
        }
        response = self.client.put(self.email_sender_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertNotIn('smtp_password', data)
        self.assertTrue(data['smtp_password_configured'])

    # ==========================================================================
    # 2. ALERT RECEIVER TESTS
    # ==========================================================================
    def test_05_admin_can_create_receiver(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "Farm Supervisor",
            "email": "supervisor@farmsync.local",
            "is_active": True,
            "receive_animal_alerts": True,
            "receive_attendance_reports": False
        }
        response = self.client.post(self.receivers_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']['email'], "supervisor@farmsync.local")

    # ==========================================================================
    # 3. PROJECT SETTINGS & SNAPSHOT ATTACHMENT TESTS
    # ==========================================================================
    def test_06_project_settings_attach_image_toggle(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            self.settings_root_url,
            {"attach_alert_image_to_email": False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings = ProjectSettings.get_settings()
        self.assertFalse(settings.attach_alert_image_to_email)

    # ==========================================================================
    # 4. ANIMAL THREAT RULES APIS
    # ==========================================================================
    def test_07_threat_rules_listing_and_auto_seed(self):
        """Authenticated users can list threat rules, which auto-seeds default catalog."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.threat_rules_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(len(data) >= 15)
        # Check tiger is HIGH
        tiger_rule = next((r for r in data if r['animal_name'] == 'tiger'), None)
        self.assertIsNotNone(tiger_rule)
        self.assertEqual(tiger_rule['threat_level'], 'HIGH')

    def test_08_threat_rules_filter_by_tier(self):
        """Filter threat rules by threat_level query parameter."""
        AnimalThreatRule.seed_default_rules()
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.threat_rules_url}?threat_level=HIGH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        for r in data:
            self.assertEqual(r['threat_level'], 'HIGH')

    def test_09_staff_can_create_custom_threat_rule(self):
        """Staff user can create a custom threat classification rule."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "animal_name": "hyena",
            "threat_level": "HIGH",
            "is_active": True
        }
        response = self.client.post(self.threat_rules_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']['animal_name'], "hyena")
        self.assertEqual(response.json()['data']['threat_level'], "HIGH")

        # Verify dynamic classification incorporates new rule immediately
        self.assertEqual(classify_animal("hyena"), "HIGH")

    def test_10_regular_user_cannot_create_threat_rule(self):
        """Non-staff user cannot create threat classification rules (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        payload = {"animal_name": "monkey", "threat_level": "LOW"}
        response = self.client.post(self.threat_rules_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_11_staff_can_update_and_delete_threat_rule(self):
        """Staff user can update threat level and delete rule."""
        rule = AnimalThreatRule.objects.create(animal_name="deer", threat_level="LOW", is_active=True)
        detail_url = reverse('settings_app:threat_rule_detail', kwargs={'pk': rule.pk})

        self.client.force_authenticate(user=self.admin_user)
        patch_res = self.client.patch(detail_url, {"threat_level": "MEDIUM"}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.json()['data']['threat_level'], "MEDIUM")

        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertFalse(AnimalThreatRule.objects.filter(pk=rule.pk).exists())

    def test_12_reset_threat_rules_to_defaults(self):
        """Staff user can reset all threat rules back to default factory catalog."""
        AnimalThreatRule.objects.all().delete()
        self.assertEqual(AnimalThreatRule.objects.count(), 0)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.threat_rules_reset_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AnimalThreatRule.objects.count() >= 15)

    # ==========================================================================
    # 5. THREAT EMAIL TEMPLATES APIS
    # ==========================================================================
    def test_13_email_templates_listing_and_auto_seed(self):
        """Authenticated users can list email templates, which auto-seeds defaults."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.email_templates_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 3)  # HIGH, MEDIUM, LOW

    def test_14_staff_can_update_email_template(self):
        """Staff user can update subject and body templates."""
        self.client.force_authenticate(user=self.admin_user)
        detail_url = reverse('settings_app:email_template_detail', kwargs={'threat_level': 'HIGH'})
        payload = {
            "subject_template": "CRITICAL ALERT: {{ animal_name|upper }} DETECTED",
            "body_template": "Threat Level: {{ threat_level }}\nDetected at {{ detected_at }}"
        }
        response = self.client.put(detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("CRITICAL ALERT", response.json()['data']['subject_template'])

    def test_15_invalid_django_template_syntax_rejected(self):
        """Invalid Django template syntax in subject or body returns HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        detail_url = reverse('settings_app:email_template_detail', kwargs={'threat_level': 'HIGH'})
        invalid_payload = {
            "subject_template": "BAD {% if unclosed_tag %} ALERT",
            "body_template": "Hello"
        }
        response = self.client.put(detail_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_16_template_preview_generation(self):
        """Staff user can generate rendered preview without sending email."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "threat_level": "HIGH",
            "sample_animal_name": "elephant",
            "sample_confidence": 92.5,
            "sample_camera_name": "Sector 4"
        }
        response = self.client.post(self.email_templates_preview_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertTrue(data['success'])
        self.assertIn("elephant", data['subject'].lower())
        self.assertIn("Sector 4", data['body'])

    def test_17_reset_email_templates_to_defaults(self):
        """Staff user can reset email templates back to factory default strings."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.email_templates_reset_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ThreatEmailTemplate.objects.count(), 3)
