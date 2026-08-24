from django.test import TestCase
from django.utils import timezone
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert


class AlertModelTests(TestCase):
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
