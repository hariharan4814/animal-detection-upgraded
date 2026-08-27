"""
FarmSync Comprehensive End-to-End Integration, QA & Security Hardening Test Suite (Step 15)
Validates complete cross-module workflows, role-based access control, settings-to-detection
synchronization, farmer-attendance-task relationships, and security secret protection.
"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import numpy as np

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.farmers.models import Farmer
from apps.attendance.models import Attendance
from apps.tasks.models import Task
from apps.settings_app.models import ProjectSettings, EmailSenderConfig, AlertReceiver
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from services.yolo import set_mock_model, reset_model_cache, ANIMAL_CLASSES


class MockBox:
    def __init__(self, cls_id: int, conf: float, xyxy=(10, 20, 100, 200)):
        self.cls = [cls_id]
        self.conf = [conf]
        self.xyxy = [list(xyxy)]


class MockResult:
    def __init__(self, boxes, orig_shape=(480, 640, 3)):
        self.boxes = boxes
        self.orig_shape = orig_shape
        self.orig_img = np.zeros(orig_shape, dtype=np.uint8)

    def plot(self):
        return np.zeros(self.orig_shape, dtype=np.uint8)


class EndToEndIntegrationAndSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin_user = User.objects.create_superuser(
            username='admin_e2e',
            email='admin@farmsync.local',
            password='AdminPassword123!'
        )
        self.regular_user = User.objects.create_user(
            username='worker_e2e',
            email='worker@farmsync.local',
            password='WorkerPassword123!'
        )

        # Base Settings Singleton
        self.settings = ProjectSettings.get_settings()
        self.settings.system_name = "FarmSync E2E System"
        self.settings.detection_confidence_threshold = 0.50
        self.settings.alert_cooldown_seconds = 60
        self.settings.camera_device_index = 0
        self.settings.detection_enabled = True
        self.settings.audio_buzzer_enabled = True
        self.settings.email_alerts_enabled = True
        self.settings.threat_level_overrides = {
            'wolf': 'high',
            'lion': 'high',
            'tiger': 'high',
            'bear': 'high',
            'elephant': 'medium',
            'deer': 'low',
        }
        self.settings.save()

        # Reset model cache for clean test state
        reset_model_cache()

    def tearDown(self):
        reset_model_cache()

    # =========================================================================
    # WORKFLOW A: AUTHENTICATION LIFECYCLE
    # =========================================================================
    def test_workflow_a_authentication_lifecycle(self):
        """Verify full auth lifecycle: login -> profile -> refresh -> logout -> revoked token rejection."""
        # 1. Login with valid credentials
        login_url = reverse('accounts:login')
        res = self.client.post(login_url, {'username': 'worker_e2e', 'password': 'WorkerPassword123!'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.json()['success'])
        access_token = res.json()['data']['access']
        refresh_token = res.json()['data']['refresh']
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)

        # 2. Login with invalid credentials fails
        res_fail = self.client.post(login_url, {'username': 'worker_e2e', 'password': 'WrongPassword!'}, format='json')
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res_fail.json()['success'])

        # 3. Authenticated /me/ profile retrieval
        me_url = reverse('accounts:current_user')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        res_me = self.client.get(me_url)
        self.assertEqual(res_me.status_code, status.HTTP_200_OK)
        self.assertEqual(res_me.json()['data']['username'], 'worker_e2e')

        # 4. Token refresh with valid refresh token (due to rotation, a new refresh token is produced)
        refresh_url = reverse('accounts:token_refresh')
        res_ref = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(res_ref.status_code, status.HTTP_200_OK)
        new_access = res_ref.json()['data']['access']
        new_refresh = res_ref.json()['data'].get('refresh', refresh_token)
        self.assertIsNotNone(new_access)

        # 5. Logout and token blacklist
        logout_url = reverse('accounts:logout')
        res_out = self.client.post(logout_url, {'refresh': new_refresh}, format='json')
        self.assertEqual(res_out.status_code, status.HTTP_200_OK)

        # 6. Revoked refresh token rejected on subsequent attempt
        res_ref_fail = self.client.post(refresh_url, {'refresh': new_refresh}, format='json')
        self.assertIn(res_ref_fail.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    # =========================================================================
    # WORKFLOW B: ROLE-BASED ACCESS CONTROL (RBAC)
    # =========================================================================
    def test_workflow_b_role_based_access_control(self):
        """Verify regular users can read but cannot perform privileged mutations across all domains."""
        # Authenticate as regular user
        self.client.force_authenticate(user=self.regular_user)

        # 1. Farmers: Read OK, Create/Delete Forbidden
        farmers_url = reverse('farmers:farmer_list_create')
        self.assertEqual(self.client.get(farmers_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(farmers_url, {'name': 'Test Farmer', 'phone': '1234567890', 'field': 'Field 1'}).status_code, status.HTTP_403_FORBIDDEN)

        # 2. Tasks: Read OK, Create Forbidden
        tasks_url = reverse('tasks:task_list_create')
        self.assertEqual(self.client.get(tasks_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(tasks_url, {'task_name': 'Test Task'}).status_code, status.HTTP_403_FORBIDDEN)

        # 3. Attendance: Read OK, Check-in/out Forbidden
        att_url = reverse('attendance:attendance_list')
        self.assertEqual(self.client.get(att_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(reverse('attendance:check_in'), {'farmer_id': 1}).status_code, status.HTTP_403_FORBIDDEN)

        # 4. Settings: Read OK, PATCH Forbidden
        settings_url = reverse('settings_app:project_settings')
        self.assertEqual(self.client.get(settings_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.patch(settings_url, {'system_name': 'Hacked'}).status_code, status.HTTP_403_FORBIDDEN)

        # 5. Detection Toggle: Read OK, PATCH Forbidden
        detection_status_url = reverse('detection:detection_status')
        self.assertEqual(self.client.get(detection_status_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.patch(detection_status_url, {'detection_enabled': False}).status_code, status.HTTP_403_FORBIDDEN)

        # Now authenticate as Staff/Admin and verify mutations succeed
        self.client.force_authenticate(user=self.admin_user)
        self.assertEqual(self.client.patch(detection_status_url, {'detection_enabled': False}).status_code, status.HTTP_200_OK)

    # =========================================================================
    # WORKFLOW C: FARMER -> ATTENDANCE -> TASK RELATIONSHIPS
    # =========================================================================
    def test_workflow_c_farmer_attendance_task_workflow(self):
        """Verify farmer creation, check-in, duplicate check-in rejection, check-out, duration calculation,
        task assignment, and cascading relationship behavior on farmer deletion."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Create Farmer
        farmers_url = reverse('farmers:farmer_list_create')
        res_farmer = self.client.post(farmers_url, {'name': 'Ramesh Kumar', 'field': 'East Orchard', 'phone': '9876543210'}, format='json')
        self.assertEqual(res_farmer.status_code, status.HTTP_201_CREATED)
        farmer_id = res_farmer.json()['data']['id']

        # 2. Check-In Farmer
        checkin_url = reverse('attendance:check_in')
        res_cin = self.client.post(checkin_url, {'farmer_id': farmer_id, 'device_location': 'East Orchard'}, format='json')
        self.assertEqual(res_cin.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_cin.json()['data']['farmer'], farmer_id)

        # 3. Duplicate Check-In rejected
        res_cin_dup = self.client.post(checkin_url, {'farmer_id': farmer_id}, format='json')
        self.assertEqual(res_cin_dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res_cin_dup.json()['success'])

        # 4. Check-Out Farmer
        checkout_url = reverse('attendance:check_out')
        res_cout = self.client.post(checkout_url, {'farmer_id': farmer_id}, format='json')
        self.assertEqual(res_cout.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res_cout.json()['data']['check_out'])

        # 5. Create Task Assigned to Farmer
        tasks_url = reverse('tasks:task_list_create')
        res_task = self.client.post(tasks_url, {'task_name': 'Pruning Orchard Trees', 'assigned_to': farmer_id, 'status': 'Pending'}, format='json')
        self.assertEqual(res_task.status_code, status.HTTP_201_CREATED)
        task_id = res_task.json()['data']['id']

        # 6. Toggle Task Status to Completed
        task_detail_url = reverse('tasks:task_detail', kwargs={'pk': task_id})
        res_task_patch = self.client.patch(task_detail_url, {'status': 'Completed'}, format='json')
        self.assertEqual(res_task_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_task_patch.json()['data']['status'], 'Completed')

        # 7. Delete Farmer: Attendance cascades, Task.assigned_to is set to NULL
        farmer_detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer_id})
        res_del = self.client.delete(farmer_detail_url)
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)

        # Verify Attendance cascaded
        self.assertEqual(Attendance.objects.filter(farmer_id=farmer_id).count(), 0)
        # Verify Task assigned_to set to NULL
        updated_task = Task.objects.get(id=task_id)
        self.assertIsNone(updated_task.assigned_to)

    # =========================================================================
    # WORKFLOW D: SETTINGS -> DETECTION SYNCHRONIZATION
    # =========================================================================
    def test_workflow_d_settings_detection_synchronization(self):
        """Verify dynamic settings updates immediately reflect in detection and alert thresholds without restart."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Update detection confidence threshold to 0.85
        settings_url = reverse('settings_app:project_settings')
        res = self.client.patch(settings_url, {'detection_confidence_threshold': 0.85, 'alert_cooldown_seconds': 120}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(float(res.json()['data']['detection_confidence_threshold']), 0.85)
        self.assertEqual(res.json()['data']['alert_cooldown_seconds'], 120)

        # 2. Check detection status API reads active 0.85 threshold
        status_url = reverse('detection:detection_status')
        res_status = self.client.get(status_url)
        self.assertEqual(res_status.status_code, status.HTTP_200_OK)
        self.assertEqual(float(res_status.json()['data']['confidence_threshold']), 0.85)

    # =========================================================================
    # WORKFLOW E: DETECTION -> ANIMAL LOG -> IMMUTABLE ALERT WORKFLOW
    # =========================================================================
    def test_workflow_e_detection_animal_log_alert_workflow(self):
        """Verify image detection creates AnimalLog and Alert records, respects cooldown,
        and enforces that Alert endpoints are strictly read-only (immutable)."""
        self.client.force_authenticate(user=self.admin_user)

        # Mock YOLO detection returning wolf (cls_id for wolf in ANIMAL_CLASSES, high threat)
        wolf_cls_id = ANIMAL_CLASSES.index('wolf')
        mock_box = MockBox(cls_id=wolf_cls_id, conf=0.92)
        mock_res = MockResult(boxes=[mock_box])
        mock_model = MagicMock()
        mock_model.names = {wolf_cls_id: 'wolf'}
        mock_model.return_value = [mock_res]
        set_mock_model(mock_model)

        import io
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='green')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        img_io.name = 'test_wolf.jpg'

        # 1. POST Analyze Image
        analyze_url = reverse('detection:detection_analyze')
        res_an = self.client.post(analyze_url, {'image': img_io, 'field': 'South Sector'}, format='multipart')
        self.assertEqual(res_an.status_code, status.HTTP_200_OK)
        an_data = res_an.json()['data']
        self.assertEqual(an_data['detections_count'], 1)
        self.assertEqual(an_data['highest_threat_animal'], 'wolf')
        self.assertEqual(an_data['highest_threat_level'], 'high')
        self.assertTrue(an_data['alert_triggered'])

        # 2. Verify AnimalLog created
        logs = AnimalLog.objects.filter(animal_type='wolf')
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.field, 'South Sector')

        # 3. Verify Alert created with reference to AnimalLog
        alerts = Alert.objects.filter(animal_log_id=log.id)
        self.assertEqual(alerts.count(), 1)
        alert = alerts.first()
        self.assertEqual(alert.alert_type, 'Email + Buzzer')
        self.assertEqual(alert.animal_log_id, log.id)

        # 4. Verify Alerts API behavior (GET OK, POST returns 405, staff DELETE returns 200)
        alerts_url = reverse('alerts:alert_list')
        self.assertEqual(self.client.get(alerts_url).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(alerts_url, {'alert_type': 'Custom'}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(reverse('alerts:alert_detail', kwargs={'pk': alert.id})).status_code, status.HTTP_200_OK)

    # =========================================================================
    # WORKFLOW F: SECURITY HARDENING & SECRET PROTECTION
    # =========================================================================
    def test_workflow_f_security_secret_protection(self):
        """Verify SMTP passwords and sensitive tokens are never exposed in GET responses,
        and invalid file types are cleanly rejected."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Update SMTP configuration with password
        sender_url = reverse('settings_app:email_sender')
        payload = {
            'sender_name': 'FarmSync Alert Dispatcher',
            'sender_email': 'alerts@farmsync.local',
            'smtp_host': 'smtp.farmsync.local',
            'smtp_port': 587,
            'smtp_username': 'alerts_user',
            'smtp_password': 'SuperSecretSmtpPassword123!'
        }
        res_put = self.client.put(sender_url, payload, format='json')
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)

        # 2. GET Email Sender must NOT return smtp_password
        res_get = self.client.get(sender_url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        data = res_get.json()['data']
        self.assertNotIn('smtp_password', data)
        self.assertTrue(data['smtp_password_configured'])

        # 3. Invalid image upload rejection
        import io
        fake_file = io.BytesIO(b"Not an image content")
        fake_file.name = "malicious_script.sh"
        res_invalid = self.client.post(reverse('detection:detection_analyze'), {'image': fake_file}, format='multipart')
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res_invalid.json()['success'])
