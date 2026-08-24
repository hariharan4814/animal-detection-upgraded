"""
Comprehensive unit and integration tests for FarmSync Detection & Vision Module.
Verifies YOLO engine lifecycle, status APIs, detection toggling, manual image analysis,
confidence filtering, class filtering, cooldown suppression, AnimalLog and Alert creation,
and historical log retrieval.
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

from apps.settings_app.models import ProjectSettings
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert
from apps.detection.services import DetectionService, VideoStreamService, _last_notification_timestamps
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
        # 0: wolf (high), 1: elephant (medium), 2: deer (low), 3: person (not in ANIMAL_CLASSES)
        self.names = {0: 'wolf', 1: 'elephant', 2: 'deer', 3: 'person', 4: 'lion'}
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
            timestamp=timezone.now(),
            field="North Perimeter",
            image_path="detections/detected_wolf_123.jpg"
        )
        self.assertEqual(log.animal_type, "wolf")
        self.assertEqual(log.confidence, 0.88)
        self.assertIn("Wolf", str(log))


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
        self.settings.threat_level_overrides = {
            "wolf": "high",
            "lion": "high",
            "elephant": "medium",
            "deer": "low"
        }
        self.settings.save()

        # Clear cooldown cache
        _last_notification_timestamps.clear()

        # Set default mock model
        self.mock_model = MockYOLOModel(detections=[(0, 0.92, (10, 10, 100, 100))])  # wolf at 0.92
        set_mock_model(self.mock_model)

        self.status_url = reverse('detection:detection_status')
        self.analyze_url = reverse('detection:detection_analyze')
        self.logs_url = reverse('detection:animal_log_list')
        self.stream_url = reverse('detection:detection_stream')

    def tearDown(self):
        reset_model_cache()
        _last_notification_timestamps.clear()

    # ==========================================================================
    # 1. STATUS & TOGGLE API TESTS
    # ==========================================================================
    def test_01_unauthenticated_status_rejected(self):
        """1. Unauthenticated status request returns HTTP 401."""
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_02_authenticated_status_retrieval(self):
        """2. Authenticated user can view detection engine status."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['detection_enabled'])
        self.assertTrue(data['data']['engine_available'])
        self.assertEqual(data['data']['model_name'], "YOLOv8n")
        self.assertEqual(data['data']['confidence_threshold'], 0.50)
        self.assertEqual(data['data']['supported_classes_count'], 29)
        self.assertIn("wolf", data['data']['supported_classes'])

    def test_03_regular_user_cannot_toggle_detection(self):
        """3. Regular user cannot perform PATCH update on detection status (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(self.status_url, {"detection_enabled": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.json()['success'])

    def test_04_staff_can_toggle_detection_status(self):
        """4. Staff/admin can toggle detection status via PATCH (HTTP 200)."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.status_url, {"detection_enabled": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['data']['detection_enabled'])

        # Verify persisted in database
        self.settings.refresh_from_db()
        self.assertFalse(self.settings.detection_enabled)

        # Toggle back on
        res_on = self.client.patch(self.status_url, {"detection_enabled": True}, format='json')
        self.assertEqual(res_on.status_code, status.HTTP_200_OK)
        self.assertTrue(res_on.json()['data']['detection_enabled'])

    # ==========================================================================
    # 2. MODEL LIFECYCLE & CACHING
    # ==========================================================================
    def test_05_model_loading_and_caching(self):
        """5. Model instance is cached and reused across calls."""
        model1 = get_model()
        model2 = get_model()
        self.assertIs(model1, model2)
        self.assertTrue(is_model_available())

    def test_06_missing_model_handled_safely(self):
        """6. Missing model is handled gracefully without crashing."""
        reset_model_cache()
        # Mock loader returning None
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
        """7. Analyzing image detecting high-threat animal (wolf) creates AnimalLog and Alert."""
        self.mock_model.detections = [(0, 0.95, (10, 10, 80, 80))]  # wolf at 0.95
        img_bytes = create_dummy_image_bytes(format="JPEG")

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("test_wolf.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file, "field": "North Orchard"}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['highest_threat_animal'], "wolf")
        self.assertEqual(data['data']['highest_threat_level'], "high")
        self.assertTrue(data['data']['alert_triggered'])
        self.assertEqual(data['data']['alert_type'], "Email + Buzzer")

        # Verify DB records
        self.assertTrue(AnimalLog.objects.filter(animal_type="wolf", field="North Orchard").exists())
        log = AnimalLog.objects.get(animal_type="wolf")
        self.assertTrue(Alert.objects.filter(animal_log=log, alert_type="Email + Buzzer").exists())

    def test_08_analyze_image_medium_threat_creates_email_alert(self):
        """8. Analyzing image detecting medium-threat animal (elephant) creates Email alert."""
        self.mock_model.detections = [(1, 0.88, (20, 20, 90, 90))]  # elephant at 0.88
        img_bytes = create_dummy_image_bytes(format="PNG")

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("test_elephant.png", img_bytes, content_type="image/png")
        response = self.client.post(self.analyze_url, {"image": uploaded_file, "field": "East River"}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['highest_threat_animal'], "elephant")
        self.assertEqual(data['data']['highest_threat_level'], "medium")
        self.assertEqual(data['data']['alert_type'], "Email")

    def test_09_analyze_image_low_threat_creates_log_only_alert(self):
        """9. Analyzing image detecting low-threat animal (deer) creates Log Only alert."""
        self.mock_model.detections = [(2, 0.75, (15, 15, 75, 75))]  # deer at 0.75
        img_bytes = create_dummy_image_bytes(format="JPEG")

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("test_deer.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['highest_threat_animal'], "deer")
        self.assertEqual(data['data']['highest_threat_level'], "low")
        self.assertEqual(data['data']['alert_type'], "Log Only")

    def test_10_confidence_threshold_filtering(self):
        """10. Detections below confidence threshold (e.g. 0.40 < 0.50) are filtered out."""
        self.mock_model.detections = [(0, 0.40, (10, 10, 80, 80))]  # wolf at 0.40
        img_bytes = create_dummy_image_bytes()

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("sub_threshold.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['detections_count'], 0)
        self.assertIsNone(data['data']['highest_threat_animal'])
        self.assertFalse(data['data']['alert_triggered'])
        self.assertEqual(AnimalLog.objects.count(), 0)

    def test_11_non_animal_class_filtering(self):
        """11. Non-animal detections (e.g. 'person') are ignored by the animal detection pipeline."""
        self.mock_model.detections = [(3, 0.99, (5, 5, 95, 95))]  # person at 0.99
        img_bytes = create_dummy_image_bytes()

        self.client.force_authenticate(user=self.regular_user)
        uploaded_file = SimpleUploadedFile("person.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": uploaded_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['data']['detections_count'], 0)
        self.assertIsNone(data['data']['highest_threat_animal'])
        self.assertEqual(AnimalLog.objects.count(), 0)

    def test_12_alert_cooldown_suppression(self):
        """12. Repeated detections within cooldown window create AnimalLog but suppress duplicate Alert."""
        self.mock_model.detections = [(0, 0.95, (10, 10, 80, 80))]  # wolf
        img_bytes = create_dummy_image_bytes()

        self.client.force_authenticate(user=self.regular_user)

        # 1st detection -> triggers alert
        file1 = SimpleUploadedFile("wolf1.jpg", img_bytes, content_type="image/jpeg")
        res1 = self.client.post(self.analyze_url, {"image": file1}, format='multipart')
        self.assertTrue(res1.json()['data']['alert_triggered'])
        self.assertEqual(Alert.objects.count(), 1)

        # 2nd immediate detection -> cooldown suppresses alert
        file2 = SimpleUploadedFile("wolf2.jpg", img_bytes, content_type="image/jpeg")
        res2 = self.client.post(self.analyze_url, {"image": file2}, format='multipart')
        self.assertFalse(res2.json()['data']['alert_triggered'])
        # AnimalLog is still created
        self.assertEqual(AnimalLog.objects.count(), 2)
        # But no new Alert was triggered
        self.assertEqual(Alert.objects.count(), 1)

    def test_13_detection_disabled_behavior(self):
        """13. When detection is disabled in settings, analyze endpoint returns early."""
        self.settings.detection_enabled = False
        self.settings.save()

        img_bytes = create_dummy_image_bytes()
        self.client.force_authenticate(user=self.regular_user)
        file_obj = SimpleUploadedFile("disabled.jpg", img_bytes, content_type="image/jpeg")
        response = self.client.post(self.analyze_url, {"image": file_obj}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertFalse(data['data']['detection_enabled'])
        self.assertEqual(data['data']['detections_count'], 0)

    def test_14_invalid_image_upload_rejected(self):
        """14. Non-image file upload is rejected with HTTP 400."""
        self.client.force_authenticate(user=self.regular_user)
        bad_file = SimpleUploadedFile("document.txt", b"Hello text file", content_type="text/plain")
        response = self.client.post(self.analyze_url, {"image": bad_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 4. HISTORICAL LOGS API TESTS
    # ==========================================================================
    def test_15_animal_logs_listing_and_detail(self):
        """15. Listing and detail retrieval for historical AnimalLog records."""
        log1 = AnimalLog.objects.create(animal_type="wolf", confidence=0.91, field="North", image_path="p1.jpg")
        log2 = AnimalLog.objects.create(animal_type="deer", confidence=0.74, field="South", image_path="p2.jpg")

        self.client.force_authenticate(user=self.regular_user)

        # List
        res_list = self.client.get(self.logs_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        logs = res_list.json()['data']
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]['id'], log2.id)  # Reverse ordering

        # Detail
        detail_url = reverse('detection:animal_log_detail', kwargs={'pk': log1.pk})
        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.json()['data']['animal_type'], "wolf")

    def test_16_animal_logs_filtering(self):
        """16. Filtering AnimalLog by species, field, and min_confidence."""
        AnimalLog.objects.create(animal_type="lion", confidence=0.95, field="Perimeter East")
        AnimalLog.objects.create(animal_type="lion", confidence=0.60, field="Perimeter West")
        AnimalLog.objects.create(animal_type="bear", confidence=0.85, field="North Zone")

        self.client.force_authenticate(user=self.regular_user)

        # Filter animal_type
        res_lion = self.client.get(f"{self.logs_url}?animal_type=lion")
        self.assertEqual(len(res_lion.json()['data']), 2)

        # Filter min_confidence
        res_conf = self.client.get(f"{self.logs_url}?min_confidence=0.90")
        self.assertEqual(len(res_conf.json()['data']), 1)
        self.assertEqual(res_conf.json()['data'][0]['animal_type'], "lion")

        # Filter field
        res_field = self.client.get(f"{self.logs_url}?field=North")
        self.assertEqual(len(res_field.json()['data']), 1)
        self.assertEqual(res_field.json()['data'][0]['animal_type'], "bear")

    def test_17_nonexistent_animal_log_returns_404(self):
        """17. Nonexistent AnimalLog ID returns standardized 404."""
        self.client.force_authenticate(user=self.regular_user)
        detail_url = reverse('detection:animal_log_detail', kwargs={'pk': 99999})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 5. LIVE VIDEO STREAMING & CAMERA INTEGRATION TESTS (STEP 13)
    # ==========================================================================
    def test_18_video_stream_unauthenticated_rejected(self):
        """18. Unauthenticated video stream request is rejected with HTTP 401."""
        response = self.client.get(self.stream_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_19_video_stream_endpoint_content_type(self):
        """19. Video stream endpoint returns StreamingHttpResponse with multipart MJPEG content type."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.stream_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'multipart/x-mixed-replace; boundary=frame')
        self.assertTrue(response.streaming)

    def test_20_video_stream_generator_mock_camera(self):
        """20. VideoStreamService acquires camera frames and safely releases resource."""
        from unittest.mock import patch

        class MockCap:
            def __init__(self, index=0):
                self.index = index
                self.read_count = 0
                self.released = False

            def isOpened(self):
                return not self.released

            def read(self):
                if self.read_count >= 2 or self.released:
                    return False, None
                self.read_count += 1
                return True, np.zeros((100, 100, 3), dtype=np.uint8)

            def release(self):
                self.released = True

        mock_cap_instance = MockCap()
        with patch('apps.detection.services.cv2.VideoCapture', return_value=mock_cap_instance):
            frames = list(VideoStreamService.generate_frames(max_frames=2))
            self.assertEqual(len(frames), 2)
            self.assertTrue(frames[0].startswith(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'))
            self.assertTrue(mock_cap_instance.released)

    def test_21_video_stream_uses_project_settings_camera_index(self):
        """21. VideoStreamService passes dynamic ProjectSettings.camera_device_index to cv2.VideoCapture."""
        from unittest.mock import patch
        self.settings.camera_device_index = 4
        self.settings.save()

        recorded_indices = []

        class MockCap:
            def __init__(self, index=0):
                recorded_indices.append(index)
                self.released = False

            def isOpened(self):
                return not self.released

            def read(self):
                return False, None

            def release(self):
                self.released = True

        with patch('apps.detection.services.cv2.VideoCapture', side_effect=MockCap):
            list(VideoStreamService.generate_frames(max_frames=1))
            self.assertEqual(recorded_indices, [4])

    def test_22_video_stream_detection_disabled_skips_inference(self):
        """22. When detection_enabled=False, camera stream skips YOLO inference."""
        from unittest.mock import patch
        self.settings.detection_enabled = False
        self.settings.save()

        class MockCap:
            def __init__(self, index=0):
                self.count = 0
                self.released = False

            def isOpened(self):
                return not self.released

            def read(self):
                if self.count >= 1:
                    return False, None
                self.count += 1
                return True, np.zeros((100, 100, 3), dtype=np.uint8)

            def release(self):
                self.released = True

        with patch('apps.detection.services.cv2.VideoCapture', return_value=MockCap()), \
             patch('apps.detection.services.run_inference') as mock_inf:
            list(VideoStreamService.generate_frames(max_frames=1))
            mock_inf.assert_not_called()

    def test_23_video_stream_detection_enabled_annotates_frame(self):
        """23. When detection_enabled=True, camera stream runs YOLO inference."""
        from unittest.mock import patch
        self.settings.detection_enabled = True
        self.settings.detection_confidence_threshold = 0.60
        self.settings.save()

        class MockCap:
            def __init__(self, index=0):
                self.count = 0
                self.released = False

            def isOpened(self):
                return not self.released

            def read(self):
                if self.count >= 1:
                    return False, None
                self.count += 1
                return True, np.zeros((100, 100, 3), dtype=np.uint8)

            def release(self):
                self.released = True

        dummy_annotated = np.ones((100, 100, 3), dtype=np.uint8)
        with patch('apps.detection.services.cv2.VideoCapture', return_value=MockCap()), \
             patch('apps.detection.services.run_inference', return_value={'annotated_frame': dummy_annotated}) as mock_inf:
            list(VideoStreamService.generate_frames(max_frames=1))
            mock_inf.assert_called_once()

    def test_24_video_stream_camera_open_failure_handled_gracefully(self):
        """24. When camera fails to open, yields synthetic placeholder frames without crashing."""
        from unittest.mock import patch

        class FailCap:
            def isOpened(self):
                return False

            def release(self):
                pass

        with patch('apps.detection.services.cv2.VideoCapture', return_value=FailCap()):
            frames = list(VideoStreamService.generate_frames(max_frames=2))
            self.assertEqual(len(frames), 2)
            self.assertTrue(frames[0].startswith(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'))
