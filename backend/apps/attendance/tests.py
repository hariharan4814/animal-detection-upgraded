from django.test import TestCase
from django.utils import timezone
from datetime import time
from apps.farmers.models import Farmer
from apps.attendance.models import Attendance


class AttendanceModelTests(TestCase):
    def setUp(self):
        self.farmer = Farmer.objects.create(
            name="Jane Smith",
            phone="0987654321",
            field="South Field"
        )

    def test_create_attendance(self):
        att = Attendance.objects.create(
            farmer=self.farmer,
            date=timezone.now().date(),
            check_in=time(8, 30, 0),
            check_out=time(17, 30, 0),
            total_hours=9.0,
            location="12.9716, 77.5946"
        )
        self.assertEqual(att.farmer.name, "Jane Smith")
        self.assertEqual(att.total_hours, 9.0)
        self.assertIn("Jane Smith", str(att))
