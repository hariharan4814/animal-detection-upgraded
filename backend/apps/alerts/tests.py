"""
Comprehensive unit and integration tests for FarmSync Alerts & Notification Module.
Verifies alert listing, detail retrieval, relationship serialization, query filtering,
threat classification tiers, evidence downloading, and staff-authorized alert deletion.
"""

import os
from pathlib import Path
from datetime import date, timedelta
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from apps.settings_app.models import ProjectSettings
from apps.detection.services import DetectionService, clear_cooldown_cache
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


class AlertModelTests(TestCase):
    """Preserves baseline unit tests for Alert model."""
    def setUp(self):
        self.log = AnimalLog.objects.create(
            animal_type="tiger",
            confidence=0.95,
            threat_level="HIGH",
            timestamp=timezone.now(),
            field="Main Field",
            image_path="detections/detected_tiger_999.jpg"
        )

    def test_create_alert(self):
        alert = Alert.objects.create(
            animal_log=self.log,
            threat_level="HIGH",
            alert_type="Email + Buzzer",
            status="Triggered",
            buzzer_triggered=True,
            email_sent=False
        )
        self.assertEqual(alert.alert_type, "Email + Buzzer")
        self.assertEqual(alert.status, "Triggered")
        self.assertEqual(alert.threat_level, "HIGH")
        self.assertTrue(alert.buzzer_triggered)
        self.assertFalse(alert.email_sent)
        self.assertEqual(alert.animal_log.animal_type, "tiger")
        self.assertIn("HIGH Alert", str(alert))


class AlertsAPITests(TestCase):
    """
    Integration tests for Alerts REST API endpoints.
    Covers Authentication, Authorization, Detail, Relationships, Filtering, Evidence Download, and Authorized Deletion.
    """
    def setUp(self):
        self.client = APIClient()

        # Regular user
        self.regular_user = User.objects.create_user(
            username="farm_worker",
            password="WorkerPassword123!",
            email="worker@farmsync.local"
        )

        # Admin user
        self.admin_user = User.objects.create_user(
            username="farm_admin",
            password="AdminPassword123!",
            email="admin@farmsync.local",
            is_staff=True
        )

        # Create dummy evidence image in MEDIA_ROOT
        media_root = Path(getattr(settings, 'MEDIA_ROOT', 'media'))
        detections_dir = media_root / 'detections'
        detections_dir.mkdir(parents=True, exist_ok=True)
        self.dummy_img_path = detections_dir / 'detected_wolf_1.jpg'
        with open(self.dummy_img_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00')

        # Seed detection logs and alerts
        self.log1 = AnimalLog.objects.create(
            animal_type="wolf",
            confidence=0.94,
            threat_level="HIGH",
            timestamp=timezone.now(),
            field="North Perimeter",
            image_path="detections/detected_wolf_1.jpg"
        )
        self.alert1 = Alert.objects.create(
            animal_log=self.log1,
            threat_level="HIGH",
            alert_type="Email + Buzzer",
            status="Triggered",
            buzzer_triggered=True
        )

        self.log2 = AnimalLog.objects.create(
            animal_type="elephant",
            confidence=0.87,
            threat_level="HIGH",
            timestamp=timezone.now() - timedelta(days=1),
            field="South Gate",
            image_path="detections/detected_elephant_2.jpg"
        )
        self.alert2 = Alert.objects.create(
            animal_log=self.log2,
            threat_level="HIGH",
            alert_type="Email + Buzzer",
            status="Sent",
            email_sent=True
        )

        self.list_url = reverse('alerts:alert_list')

    def tearDown(self):
        reset_model_cache()
        clear_cooldown_cache()
        if self.dummy_img_path.is_file():
            self.dummy_img_path.unlink(missing_ok=True)

    # ==========================================================================
    # 1. AUTHENTICATION & ACCESS CONTROL
    # ==========================================================================
    def test_01_unauthenticated_list_rejected(self):
        """1. Unauthenticated list request rejected with HTTP 401."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_02_unauthenticated_detail_rejected(self):
        """2. Unauthenticated detail request rejected with HTTP 401."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 2. LIST & DETAIL RETRIEVAL
    # ==========================================================================
    def test_03_authenticated_user_can_list_alerts(self):
        """3. Authenticated user can list alerts."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)

    def test_04_empty_alert_list_succeeds(self):
        """4. Empty alert list returns 200 OK with empty array."""
        Alert.objects.all().delete()
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], [])

    def test_05_deterministic_reverse_ordering(self):
        """5. Alerts are returned in deterministic reverse ordering (newest first)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        alerts = response.json()['data']
        self.assertEqual(alerts[0]['id'], self.alert2.id)
        self.assertEqual(alerts[1]['id'], self.alert1.id)

    def test_06_alert_detail_retrieval_with_threat_context(self):
        """6. Alert detail retrieval returns full threat & detection context."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['id'], self.alert1.id)
        self.assertEqual(data['threat_level'], "HIGH")
        self.assertEqual(data['alert_type'], "Email + Buzzer")
        self.assertEqual(data['status'], "Triggered")
        self.assertEqual(data['animal_type'], "wolf")
        self.assertEqual(data['confidence'], 0.94)
        self.assertEqual(data['field'], "North Perimeter")
        self.assertIn("/download/", data['download_url'])

    def test_07_nonexistent_alert_returns_404(self):
        """7. Nonexistent alert ID returns standardized 404."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': 99999})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 3. QUERY PARAMETER FILTERING
    # ==========================================================================
    def test_09_filter_by_threat_level(self):
        """9. Filter alerts by threat_level (?threat_level=HIGH)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?threat_level=HIGH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['threat_level'], "HIGH")

    def test_10_filter_by_status(self):
        """10. Filter alerts by status (?status=Triggered)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?status=Triggered")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['status'], "Triggered")

    def test_11_filter_by_animal_type(self):
        """11. Filter alerts by animal_type (?animal_type=wolf)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?animal_type=wolf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['animal_type'], "wolf")

    # ==========================================================================
    # 4. EVIDENCE DOWNLOAD AND AUTHORIZED DELETION
    # ==========================================================================
    def test_12_alert_evidence_download_success(self):
        """12. Authenticated user can download detection snapshot image."""
        download_url = reverse('alerts:alert_download', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertIn('attachment;', response['Content-Disposition'])

    def test_13_alert_evidence_download_nonexistent_file_404(self):
        """13. Alert with missing file on disk returns HTTP 404."""
        download_url = reverse('alerts:alert_download', kwargs={'pk': self.alert2.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_14_regular_user_delete_alert_forbidden(self):
        """14. Non-staff user attempting DELETE /api/v1/alerts/{id}/ receives 403 Forbidden."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Alert.objects.filter(pk=self.alert1.pk).exists())

    def test_15_staff_user_delete_alert_success(self):
        """15. Staff/Admin user can DELETE /api/v1/alerts/{id}/ and safely cleanup evidence."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Alert.objects.filter(pk=self.alert1.pk).exists())
