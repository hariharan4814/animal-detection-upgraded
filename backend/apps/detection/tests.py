"""
Comprehensive unit and integration tests for FarmSync Detection & Vision Module.
Verifies YOLO engine lifecycle, status APIs, detection toggling, manual image analysis,
threat classification, multi-animal severity resolution, confidence filtering,
cooldown suppression per species+tier, AnimalLog and Alert creation, and historical log retrieval.
All tests are 100% hardware-independent (no webcam, no GPU, no weights download required).
"""

import io
from PIL import Image
import numpy as np
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.settings_app.models import ProjectSettings, AnimalThreatRule
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from apps.detection.services import DetectionService, VideoStreamService, clear_cooldown_cache
from services.threat_classification import (
    classify_animal,
    calculate_highest_threat,
    invalidate_threat_cache,
)
from services.yolo import set_mock_model, reset_model_cache, get_model, is_model_available, ANIMAL_CLASSES


class MockBox:
    """Mock YOLO bounding box."""
    def __init__(self, cls_id: int, conf: float, xyxy=(10, 20, 100, 200)):
        self.cls = [cls_id]
        self.conf = [conf]
        self.xyxy = [xyxy]


class MockResult:
    """Mock YOLO inference result object."""
    def __init__(self, boxes):
        self.boxes = boxes


class MockYOLOModel:
    """Mock Ultralytics YOLO model instance."""
    def __init__(self, detections=None):
        # 0: wolf (HIGH), 1: dog (MEDIUM), 2: bird (LOW), 3: person, 4: lion (HIGH), 5: elephant (HIGH)
        self.names = {0: 'wolf', 1: 'dog', 2: 'bird', 3: 'person', 4: 'lion', 5: 'elephant'}
        self.detections = detections if detections is not None else []

    def __call__(self, image, stream=False, verbose=False):
        boxes = [
            MockBox(cls_id, conf, xyxy)
            for cls_id, conf, xyxy in self.detections
        ]
        return [MockResult(boxes)]


def create_dummy_image_bytes(format="JPEG", width=100, height=100, color=(255, 0, 0)) -> bytes:
    """Helper creating raw image bytes for test payloads."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


class AnimalLogModelTests(TestCase):
    """Preserves baseline unit tests for AnimalLog model."""
    def test_create_animal_log(self):
        log = AnimalLog.objects.create(
            animal_type="wolf",
            confidence=0.88,
            threat_level="HIGH",
            timestamp=timezone.now(),
            field="North Perimeter",
            image_path="detections/detected_wolf_123.jpg"
        )
        self.assertEqual(log.animal_type, "wolf")
        self.assertEqual(log.threat_level, "HIGH")
        self.assertEqual(log.confidence, 0.88)
        self.assertIn("Wolf [HIGH]", str(log))


class DetectionAPITests(TestCase):
    """
    Comprehensive tests for Detection REST API and YOLO computer vision pipeline.
    """
    def setUp(self):
        self.client = APIClient()

        # Regular user
        self.regular_user = User.objects.create_user(
            username="field_worker",
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

        # Initialize ProjectSettings
        self.settings = ProjectSettings.get_settings()
        self.settings.detection_enabled = True
        self.settings.detection_confidence_threshold = 0.50
        self.settings.alert_cooldown_seconds = 60
        self.settings.save()

        # Clear cooldown & threat caches
        clear_cooldown_cache()
        invalidate_threat_cache()
        AnimalThreatRule.seed_default_rules(overwrite_existing=True)

        # Set default mock model
        self.mock_model = MockYOLOModel(detections=[(0, 0.92, (10, 10, 100, 100))])  # wolf at 0.92
        set_mock_model(self.mock_model)

        self.status_url = reverse('detection:detection_status')
        self.analyze_url = reverse('detection:detection_analyze')
        self.logs_url = reverse('detection:animal_log_list')
        self.stream_url = reverse('detection:detection_stream')

    def tearDown(self):
        reset_model_cache()
        clear_cooldown_cache()
        invalidate_threat_cache()

    # ==========================================================================
    # 1. STATUS & TOGGLE API TESTS
    # ==========================================================================
    def test_01_unauthenticated_status_rejected(self):
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_02_authenticated_status_retrieval(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['detection_enabled'])
        self.assertTrue(data['data']['engine_available'])
        self.assertEqual(data['data']['model_name'], "YOLOv8n")
        self.assertEqual(data['data']['confidence_threshold'], 0.50)
        self.assertIn("attach_alert_image_to_email", data['data'])

    def test_03_regular_user_cannot_toggle_detection(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(self.status_url, {"detection_enabled": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.json()['success'])

    def test_04_staff_can_toggle_detection_status(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.status_url, {"detection_enabled": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['data']['detection_enabled'])

        # Verify persisted in database
        self.settings.refresh_from_db()
        self.assertFalse(self.settings.detection_enabled)

    # ==========================================================================
    # 2. MODEL LIFECYCLE & CACHING
    # ==========================================================================
    def test_05_model_loading_and_caching(self):
        model1 = get_model()
        model2 = get_model()
        self.assertIs(model1, model2)
        self.assertTrue(is_model_available())

    def test_06_missing_model_handled_safely(self):
        reset_model_cache()
        set_mock_model(None)
        self.assertFalse(is_model_available())
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        from services.yolo import run_inference
        result = run_inference(img_array)
        self.assertFalse(result['success'])
        self.assertEqual(result['detections'], [])

    # ==========================================================================
    # 3. DETECTION PIPELINE & IMAGE ANALYSIS
    # ==========================================================================
    def test_07_analyze_image_high_threat_animal_creates_log_and_alert(self):
        self.mock_model.detections = [(0, 0.95, (10, 10, 80, 80))]  # wolf at 0.95 (HIGH)
        img_bytes = create_dummy_image_bytes(format="JPEG")

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("test_wolf.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file, "field": "North Orchard"}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['highest_threat_animal'], "wolf")
        self.assertEqual(data['data']['highest_threat_tier'], "HIGH")
        self.assertTrue(data['data']['alert_triggered'])
        self.assertEqual(data['data']['alert_type'], "Email + Buzzer")

        # Verify DB records
        self.assertTrue(AnimalLog.objects.filter(animal_type="wolf", threat_level="HIGH", field="North Orchard").exists())
        log = AnimalLog.objects.get(animal_type="wolf")
        self.assertTrue(Alert.objects.filter(animal_log=log, threat_level="HIGH", alert_type="Email + Buzzer").exists())

    def test_08_analyze_image_medium_threat_creates_email_alert(self):
        self.mock_model.detections = [(1, 0.88, (20, 20, 90, 90))]  # dog at 0.88 (MEDIUM)
        img_bytes = create_dummy_image_bytes(format="PNG")

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("test_dog.png", img_bytes, content_type="image/png")
        response = self.client.post(self.analyze_url, {"image": uploaded_file, "field": "East River"}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['highest_threat_animal'], "dog")
        self.assertEqual(data['data']['highest_threat_tier'], "MEDIUM")
        self.assertEqual(data['data']['alert_type'], "Email")

    def test_09_analyze_image_low_threat_creates_log_only_alert(self):
        self.mock_model.detections = [(2, 0.75, (15, 15, 75, 75))]  # bird at 0.75 (LOW)
        img_bytes = create_dummy_image_bytes(format="JPEG")

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("test_bird.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['highest_threat_animal'], "bird")
        self.assertEqual(data['data']['highest_threat_tier'], "LOW")
        self.assertEqual(data['data']['alert_type'], "Log Only")

    def test_10_multi_animal_threat_severity_resolution(self):
        """Multi-animal frame with bird (LOW) and lion (HIGH) resolves highest threat to lion / HIGH."""
        self.mock_model.detections = [
            (2, 0.95, (10, 10, 50, 50)),  # bird (LOW)
            (4, 0.82, (60, 60, 95, 95))   # lion (HIGH)
        ]
        img_bytes = create_dummy_image_bytes()

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("multi.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['detections_count'], 2)
        self.assertEqual(data['highest_threat_animal'], "lion")
        self.assertEqual(data['highest_threat_tier'], "HIGH")
        self.assertEqual(data['alert_type'], "Email + Buzzer")

    def test_11_cooldown_separated_by_species_and_tier(self):
        """A low-threat detection cooldown does NOT suppress a subsequent high-threat detection."""
        # 1. First detect bird (LOW)
        self.mock_model.detections = [(2, 0.80, (10, 10, 50, 50))]  # bird (LOW)
        img_bytes = create_dummy_image_bytes()

        self.client.force_authenticate(user=self.regular_user)
        file_bird = SimpleUploadedFile("bird.jpg", img_bytes, content_type="image/jpeg")
        res1 = self.client.post(self.analyze_url, {"image": file_bird}, format='multipart')
        self.assertTrue(res1.json()['data']['alert_triggered'])

        # 2. Immediately detect wolf (HIGH) -> Should NOT be suppressed by bird's cooldown!
        self.mock_model.detections = [(0, 0.95, (10, 10, 80, 80))]  # wolf (HIGH)
        file_wolf = SimpleUploadedFile("wolf.jpg", img_bytes, content_type="image/jpeg")
        res2 = self.client.post(self.analyze_url, {"image": file_wolf}, format='multipart')
        self.assertTrue(res2.json()['data']['alert_triggered'])
        self.assertEqual(res2.json()['data']['highest_threat_animal'], "wolf")
        self.assertEqual(res2.json()['data']['highest_threat_tier'], "HIGH")

    # ==========================================================================
    # 4. HISTORICAL LOGS API TESTS
    # ==========================================================================
    def test_12_animal_logs_listing_with_threat_filter(self):
        AnimalLog.objects.create(animal_type="wolf", threat_level="HIGH", confidence=0.91, field="North", image_path="p1.jpg")
        AnimalLog.objects.create(animal_type="deer", threat_level="LOW", confidence=0.74, field="South", image_path="p2.jpg")

        self.client.force_authenticate(user=self.regular_user)

        # Filter threat_level=HIGH
        res_high = self.client.get(f"{self.logs_url}?threat_level=HIGH")
        self.assertEqual(res_high.status_code, status.HTTP_200_OK)
        logs = res_high.json()['data']
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['animal_type'], "wolf")
        self.assertEqual(logs[0]['threat_level'], "HIGH")
