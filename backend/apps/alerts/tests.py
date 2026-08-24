"""
Comprehensive unit and integration tests for FarmSync Alerts & Notification Module.
Verifies alert listing, detail retrieval, relationship serialization, query filtering,
read-only immutability enforcement, and Step 10 detection-to-alert integration.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from apps.settings_app.models import ProjectSettings
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


class AlertModelTests(TestCase):
    """Preserves baseline unit tests for Alert model."""
    def setUp(self):
        self.log = AnimalLog.objects.create(
            animal_type="tiger",
            confidence=0.95,
            timestamp=timezone.now(),
            field="Main Field",
            image_path="detections/detected_tiger_999.jpg"
        )

    def test_create_alert(self):
        alert = Alert.objects.create(
            animal_log=self.log,
            alert_type="Email + Buzzer",
            status="Triggered"
        )
        self.assertEqual(alert.alert_type, "Email + Buzzer")
        self.assertEqual(alert.status, "Triggered")
        self.assertEqual(alert.animal_log.animal_type, "tiger")
        self.assertIn("Email + Buzzer", str(alert))


class AlertsAPITests(TestCase):
    """
    Integration tests for Alerts REST API endpoints.
    Covers Authentication, Authorization, Detail, Relationships, Filtering, Immutability, and Step 10 Integration.
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

        # Seed detection logs and alerts
        self.log1 = AnimalLog.objects.create(
            animal_type="wolf",
            confidence=0.94,
            timestamp=timezone.now(),
            field="North Perimeter",
            image_path="detections/detected_wolf_1.jpg"
        )
        self.alert1 = Alert.objects.create(
            animal_log=self.log1,
            alert_type="Email + Buzzer",
            status="Triggered"
        )

        self.log2 = AnimalLog.objects.create(
            animal_type="elephant",
            confidence=0.87,
            timestamp=timezone.now() - timedelta(days=1),
            field="South Gate",
            image_path="detections/detected_elephant_2.jpg"
        )
        self.alert2 = Alert.objects.create(
            animal_log=self.log2,
            alert_type="Email",
            status="Sent"
        )

        self.list_url = reverse('alerts:alert_list')

    def tearDown(self):
        reset_model_cache()
        _last_notification_timestamps.clear()

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

    def test_06_alert_detail_retrieval_with_animal_log_context(self):
        """6. Alert detail retrieval returns full detection context."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['id'], self.alert1.id)
        self.assertEqual(data['alert_type'], "Email + Buzzer")
        self.assertEqual(data['status'], "Triggered")
        self.assertEqual(data['animal_type'], "wolf")
        self.assertEqual(data['confidence'], 0.94)
        self.assertEqual(data['field'], "North Perimeter")
        self.assertEqual(data['image_path'], "detections/detected_wolf_1.jpg")

    def test_07_nonexistent_alert_returns_404(self):
        """7. Nonexistent alert ID returns standardized 404."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': 99999})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['success'])

    def test_08_alert_without_animal_log_handled_safely(self):
        """8. Alert with animal_log=None returns null related fields gracefully."""
        orphan_alert = Alert.objects.create(animal_log=None, alert_type="Log Only", status="Triggered")
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': orphan_alert.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertIsNone(data['animal_log'])
        self.assertIsNone(data['animal_type'])

    # ==========================================================================
    # 3. QUERY PARAMETER FILTERING
    # ==========================================================================
    def test_09_filter_by_status(self):
        """9. Filter alerts by status (?status=Triggered)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?status=Triggered")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['status'], "Triggered")

    def test_10_filter_by_alert_type(self):
        """10. Filter alerts by alert_type (?alert_type=Email)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?alert_type=Email")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['alert_type'], "Email")

    def test_11_filter_by_animal_log_id(self):
        """11. Filter alerts by animal_log_id."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?animal_log_id={self.log1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['animal_type'], "wolf")

    def test_12_filter_by_animal_type(self):
        """12. Filter alerts by animal_type (?animal_type=elephant)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?animal_type=elephant")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['animal_type'], "elephant")

    def test_13_filter_by_date(self):
        """13. Filter alerts by exact date (?date=YYYY-MM-DD)."""
        today_str = timezone.localdate().isoformat()
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?date={today_str}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 2)  # Both alerts created today in test DB

    def test_14_filter_by_date_range(self):
        """14. Filter alerts across date range (?start_date=...&end_date=...)."""
        today = timezone.localdate()
        start = (today - timedelta(days=2)).isoformat()
        end = (today + timedelta(days=1)).isoformat()

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?start_date={start}&end_date={end}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_15_invalid_date_returns_400(self):
        """15. Malformed date string returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?date=invalid-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_16_invalid_date_range_returns_400(self):
        """16. Inverted date range (start_date > end_date) returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?start_date=2026-08-25&end_date=2026-08-20")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_17_invalid_status_choice_returns_400(self):
        """17. Unsupported status query choice returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?status=UnknownStatus")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_18_invalid_alert_type_choice_returns_400(self):
        """18. Unsupported alert_type query choice returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?alert_type=SMS")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ==========================================================================
    # 4. READ-ONLY IMMUTABILITY ENFORCEMENT
    # ==========================================================================
    def test_19_post_list_method_not_allowed(self):
        """19. POST /api/v1/alerts/ is rejected with HTTP 405 Method Not Allowed."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.list_url, {"alert_type": "Email"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_20_put_detail_method_not_allowed(self):
        """20. PUT /api/v1/alerts/{id}/ is rejected with HTTP 405 Method Not Allowed."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(detail_url, {"status": "Sent"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_21_patch_detail_method_not_allowed(self):
        """21. PATCH /api/v1/alerts/{id}/ is rejected with HTTP 405 Method Not Allowed."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(detail_url, {"status": "Sent"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_22_delete_detail_method_not_allowed(self):
        """22. DELETE /api/v1/alerts/{id}/ is rejected with HTTP 405 Method Not Allowed."""
        detail_url = reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ==========================================================================
    # 5. STEP 10 INTEGRATION (DETECTION TO ALERTS RETRIEVAL)
    # ==========================================================================
    def test_23_step_10_detection_creates_retrievable_alert(self):
        """23. Alert created by Step 10 DetectionService is immediately accessible via Step 11 Alert APIs."""
        # Configure Step 10 settings & mock
        settings = ProjectSettings.get_settings()
        settings.detection_enabled = True
        settings.threat_level_overrides = {"wolf": "high"}
        settings.save()

        mock_model = MockYOLOModel(detections=[(0, 0.96, (10, 10, 90, 90))])  # wolf
        set_mock_model(mock_model)

        # Execute detection analysis
        import io
        from PIL import Image
        img = Image.new("RGB", (100, 100), (0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        analysis_result = DetectionService.analyze_image_bytes(buf.getvalue(), field_name="West Greenhouse")
        self.assertTrue(analysis_result['alert_triggered'])

        # Now query Step 11 Alert APIs
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?animal_type=wolf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']

        # Find the newly created alert
        wolf_alerts = [a for a in data if a['field'] == "West Greenhouse"]
        self.assertEqual(len(wolf_alerts), 1)
        self.assertEqual(wolf_alerts[0]['alert_type'], "Email + Buzzer")
        self.assertEqual(wolf_alerts[0]['status'], "Triggered")
        self.assertEqual(wolf_alerts[0]['confidence'], 0.96)
