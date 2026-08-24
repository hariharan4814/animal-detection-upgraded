from django.test import TestCase
from django.utils import timezone
from apps.detection.models import AnimalLog


class AnimalLogModelTests(TestCase):
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
