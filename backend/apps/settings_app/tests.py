"""
Comprehensive unit and integration tests for FarmSync Settings Module (Step 5 & Step 12).
Verifies Email Sender configuration, Alert Receivers, Project Settings, root /api/v1/settings/ endpoints,
PATCH partial updates, input validation, singleton safety, security boundaries, write-only passwords,
and dynamic integration with Step 10 Detection Engine.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.settings_app.models import EmailSenderConfig, AlertReceiver, ProjectSettings
from apps.detection.services import DetectionService, _last_notification_timestamps
from services.yolo import set_mock_model, reset_model_cache


class MockBox:
    def __init__(self, cls_id: int, conf: float, xyxy=(10, 20, 100, 200)):
        self.cls = [cls_id]
        self.conf = [conf]
        self.xyxy = [xyxy]


class MockResult:
    def __init__(self, boxes):
        self.boxes = boxes


class MockYOLOModel:
    def __init__(self, detections=None):
        self.names = {0: 'wolf', 1: 'elephant', 2: 'deer'}
        self.detections = detections if detections is not None else []

    def __call__(self, image, stream=False, verbose=False):
        boxes = [
            MockBox(cls_id, conf, xyxy)
            for cls_id, conf, xyxy in self.detections
        ]
        return [MockResult(boxes)]


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

    def tearDown(self):
        reset_model_cache()
        _last_notification_timestamps.clear()

    # ==========================================================================
    # 1. EMAIL SENDER CONFIGURATION TESTS
    # ==========================================================================
    def test_01_email_sender_unauthenticated_rejected(self):
        """1. Unauthorized access rejected (HTTP 401)."""
        response = self.client.get(self.email_sender_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_email_sender_regular_user_forbidden(self):
        """2. Regular user cannot modify or view admin-only sender config (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.email_sender_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        put_res = self.client.put(self.email_sender_url, {"sender_email": "hack@example.com"}, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_03_email_sender_admin_can_retrieve(self):
        """3. Authorized administrator can retrieve sender config safely."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.email_sender_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('smtp_host', data['data'])
        self.assertIn('smtp_password_configured', data['data'])

    def test_04_05_06_email_sender_password_write_only(self):
        """4, 5, 6. SMTP password can be submitted, is never returned, and retrieval is safe."""
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

        # Verify password is NOT in response
        self.assertNotIn('smtp_password', data)
        self.assertTrue(data['smtp_password_configured'])
        self.assertEqual(data['sender_email'], "farmalerts@example.com")

        # Verify DB has stored password securely
        config = EmailSenderConfig.get_active_config()
        self.assertEqual(config.smtp_password, "super-secret-app-password-999")

        # Verify subsequent GET never returns password
        get_res = self.client.get(self.email_sender_url)
        self.assertNotIn('smtp_password', get_res.json()['data'])
        self.assertTrue(get_res.json()['data']['smtp_password_configured'])

    def test_07_email_sender_update_preserves_existing_password_when_omitted(self):
        """7. Update does not erase existing password when password field is omitted."""
        config = EmailSenderConfig.get_active_config()
        config.smtp_password = "existing-secret-password"
        config.save()

        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "sender_name": "Updated Sender Name"
        }
        response = self.client.put(self.email_sender_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        config.refresh_from_db()
        self.assertEqual(config.smtp_password, "existing-secret-password")
        self.assertEqual(config.sender_name, "Updated Sender Name")

    # ==========================================================================
    # 2. ALERT RECEIVER TESTS
    # ==========================================================================
    def test_08_admin_can_create_receiver(self):
        """8. Authorized admin can create an alert receiver."""
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
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['email'], "supervisor@farmsync.local")

    def test_09_invalid_email_rejected(self):
        """9. Invalid email format is rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "Bad Email User",
            "email": "not-a-valid-email-address"
        }
        response = self.client.post(self.receivers_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_10_receiver_listing(self):
        """10. Authenticated users can list alert receivers."""
        AlertReceiver.objects.create(name="Lead Farmer", email="lead@farm.local")
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.receivers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(len(data['data']) >= 1)

    def test_11_12_receiver_update_and_enable_disable(self):
        """11, 12. Receiver update and enable/disable toggle works."""
        receiver = AlertReceiver.objects.create(name="Night Guard", email="guard@farm.local", is_active=True)
        detail_url = reverse('settings_app:receiver_detail', kwargs={'pk': receiver.pk})

        self.client.force_authenticate(user=self.admin_user)
        update_res = self.client.put(detail_url, {"is_active": False, "name": "Retired Guard"}, format='json')
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)

        receiver.refresh_from_db()
        self.assertFalse(receiver.is_active)
        self.assertEqual(receiver.name, "Retired Guard")

    def test_13_unauthorized_deletion_rejected(self):
        """13. Regular user cannot delete receivers (HTTP 403)."""
        receiver = AlertReceiver.objects.create(name="Field Officer", email="officer@farm.local")
        detail_url = reverse('settings_app:receiver_detail', kwargs={'pk': receiver.pk})

        self.client.force_authenticate(user=self.regular_user)
        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

        # Admin delete succeeds
        self.client.force_authenticate(user=self.admin_user)
        admin_del_res = self.client.delete(detail_url)
        self.assertEqual(admin_del_res.status_code, status.HTTP_200_OK)
        self.assertFalse(AlertReceiver.objects.filter(pk=receiver.pk).exists())

    # ==========================================================================
    # 3. PROJECT SETTINGS TESTS (LEGACY ALIAS /project/)
    # ==========================================================================
    def test_14_project_settings_safe_retrieval(self):
        """14. Authenticated users can retrieve project settings."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.project_settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertIn('alert_cooldown_seconds', data)
        self.assertIn('detection_confidence_threshold', data)

    def test_15_project_settings_regular_user_cannot_modify(self):
        """15. Regular user cannot modify project settings (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.put(self.project_settings_url, {"alert_cooldown_seconds": 10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_16_project_settings_admin_update(self):
        """16. Administrator can update system settings."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "system_name": "FarmSync Automated Vision",
            "alert_cooldown_seconds": 120,
            "detection_confidence_threshold": 0.65,
            "wage_per_hour": 18.5,
            "threat_level_overrides": {"wolf": "high", "deer": "low"}
        }
        response = self.client.put(self.project_settings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['alert_cooldown_seconds'], 120)
        self.assertEqual(data['detection_confidence_threshold'], 0.65)
        self.assertEqual(data['threat_level_overrides']['wolf'], "high")

    def test_17_invalid_project_configuration_rejected(self):
        """17. Invalid threshold (> 1.0) or negative cooldown rejected with 400."""
        self.client.force_authenticate(user=self.admin_user)
        invalid_payload = {
            "detection_confidence_threshold": 1.50  # Must be <= 1.0
        }
        response = self.client.put(self.project_settings_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 4. STEP 12 ROOT SETTINGS REST API (/api/v1/settings/)
    # ==========================================================================
    def test_20_settings_root_get_unauthenticated_rejected(self):
        """20. Unauthenticated GET /api/v1/settings/ rejected with HTTP 401."""
        response = self.client.get(self.settings_root_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_21_settings_root_get_authenticated_success(self):
        """21. Authenticated regular user can GET /api/v1/settings/."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.settings_root_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('detection_confidence_threshold', data['data'])
        self.assertIn('alert_cooldown_seconds', data['data'])
        self.assertIn('camera_device_index', data['data'])
        self.assertIn('detection_enabled', data['data'])

    def test_22_settings_root_patch_regular_user_forbidden(self):
        """22. Regular user cannot PATCH /api/v1/settings/ (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(self.settings_root_url, {"detection_enabled": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.json()['success'])

    def test_23_settings_root_patch_admin_success_partial_update(self):
        """23. Staff/Admin can PATCH /api/v1/settings/ with partial updates."""
        self.client.force_authenticate(user=self.admin_user)
        patch_payload = {
            "system_name": "FarmSync Vision Pro",
            "alert_cooldown_seconds": 90
        }
        response = self.client.patch(self.settings_root_url, patch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['system_name'], "FarmSync Vision Pro")
        self.assertEqual(data['alert_cooldown_seconds'], 90)

        # Verify DB persistence
        settings = ProjectSettings.get_settings()
        self.assertEqual(settings.system_name, "FarmSync Vision Pro")
        self.assertEqual(settings.alert_cooldown_seconds, 90)

    def test_24_settings_root_patch_preserves_unspecified_fields(self):
        """24. PATCH update preserves all unspecified settings fields."""
        settings = ProjectSettings.get_settings()
        settings.detection_confidence_threshold = 0.72
        settings.camera_device_index = 2
        settings.save()

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.settings_root_url, {"system_name": "New Farm Name"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        settings.refresh_from_db()
        self.assertEqual(settings.system_name, "New Farm Name")
        # Preserved
        self.assertEqual(settings.detection_confidence_threshold, 0.72)
        self.assertEqual(settings.camera_device_index, 2)

    def test_25_invalid_camera_index_rejected(self):
        """25. Negative camera device index rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.settings_root_url, {"camera_device_index": -1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_26_invalid_threat_level_tier_rejected(self):
        """26. Invalid threat tier choice (e.g. 'extreme') rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.settings_root_url, {"threat_level_overrides": {"wolf": "extreme"}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_27_invalid_negative_wage_rejected(self):
        """27. Negative wage_per_hour rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.settings_root_url, {"wage_per_hour": -5.0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_28_settings_root_post_method_not_allowed(self):
        """28. POST /api/v1/settings/ rejected with HTTP 405 Method Not Allowed."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.settings_root_url, {"system_name": "Duplicate Config"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_29_settings_root_delete_method_not_allowed(self):
        """29. DELETE /api/v1/settings/ rejected with HTTP 405 Method Not Allowed."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.settings_root_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_30_singleton_guarantee_no_duplicate_records(self):
        """30. Multiple operations never create duplicate ProjectSettings rows."""
        self.client.force_authenticate(user=self.admin_user)
        self.client.patch(self.settings_root_url, {"alert_cooldown_seconds": 45}, format='json')
        self.client.get(self.settings_root_url)
        self.assertEqual(ProjectSettings.objects.count(), 1)

    # ==========================================================================
    # 5. STEP 10 DETECTION INTEGRATION
    # ==========================================================================
    def test_31_step_10_detection_reflects_settings_changes_dynamically(self):
        """31. Updating settings dynamically changes Step 10 DetectionService behavior immediately."""
        self.client.force_authenticate(user=self.admin_user)

        # Update confidence threshold to 0.85 and disable detection
        patch_res = self.client.patch(
            self.settings_root_url,
            {"detection_confidence_threshold": 0.85, "detection_enabled": False},
            format='json'
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        # Check DetectionService.get_status() reflects this immediately
        det_status = DetectionService.get_status()
        self.assertFalse(det_status['detection_enabled'])
        self.assertEqual(det_status['confidence_threshold'], 0.85)

    # ==========================================================================
    # 6. ACCOUNT SECURITY TESTS
    # ==========================================================================
    def test_18_zero_passwords_or_hashes_in_settings_responses(self):
        """18. Verify no endpoint exposes passwords or hashes."""
        self.client.force_authenticate(user=self.admin_user)
        for url in [self.email_sender_url, self.receivers_url, self.project_settings_url, self.settings_root_url]:
            res = self.client.get(url)
            res_str = str(res.json()).lower()
            self.assertNotIn('pbkdf2', res_str)
            self.assertNotIn('password_hash', res_str)
            self.assertNotIn('smtp_password\'', res_str)

    def test_19_regular_user_cannot_elevate_privileges(self):
        """19. Regular user cannot elevate themselves via settings APIs."""
        self.client.force_authenticate(user=self.regular_user)
        post_res = self.client.post(self.receivers_url, {"name": "Hacker", "email": "hacker@farm.local"})
        self.assertEqual(post_res.status_code, status.HTTP_403_FORBIDDEN)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)
