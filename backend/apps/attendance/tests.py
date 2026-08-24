"""
Comprehensive unit and integration tests for FarmSync Attendance Module.
Verifies listing, detail, check-in, check-out, duration calculation, reporting, permissions, and validation.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from rest_framework.test import APIClient
from rest_framework import status

from apps.farmers.models import Farmer
from apps.attendance.models import Attendance


class AttendanceAPITests(TestCase):
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

        # Standard test farmers
        self.farmer_1 = Farmer.objects.create(
            name="John Doe",
            phone="1234567890",
            field="North Field",
            email="john@example.com"
        )
        self.farmer_2 = Farmer.objects.create(
            name="Jane Smith",
            phone="0987654321",
            field="South Field",
            email="jane@example.com"
        )

        self.list_url = reverse('attendance:attendance_list')
        self.check_in_url = reverse('attendance:check_in')
        self.check_out_url = reverse('attendance:check_out')
        self.report_url = reverse('attendance:attendance_report')

    # ==========================================================================
    # 1. AUTHENTICATION TESTS (1 - 5)
    # ==========================================================================
    def test_01_unauthenticated_list_rejected(self):
        """1. Unauthenticated attendance list is rejected with 401."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_02_unauthenticated_detail_rejected(self):
        """2. Unauthenticated detail is rejected with 401."""
        att = Attendance.objects.create(farmer=self.farmer_1, date=timezone.localdate(), check_in=time(8, 0))
        detail_url = reverse('attendance:attendance_detail', kwargs={'pk': att.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_03_unauthenticated_check_in_rejected(self):
        """3. Unauthenticated check-in is rejected with 401."""
        response = self.client.post(self.check_in_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_04_unauthenticated_check_out_rejected(self):
        """4. Unauthenticated check-out is rejected with 401."""
        response = self.client.post(self.check_out_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_05_unauthenticated_report_rejected(self):
        """5. Unauthenticated report is rejected with 401."""
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================================================
    # 2. READ ACCESS TESTS (6 - 9)
    # ==========================================================================
    def test_06_authenticated_list_succeeds(self):
        """6. Authenticated user can list attendance logs."""
        Attendance.objects.create(farmer=self.farmer_1, date=timezone.localdate(), check_in=time(8, 0))
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['farmer_name'], "John Doe")

    def test_07_empty_attendance_list_succeeds(self):
        """7. Empty attendance list returns 200 OK with empty array."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data'], [])

    def test_08_authenticated_detail_succeeds(self):
        """8. Authenticated user can retrieve attendance record detail."""
        att = Attendance.objects.create(
            farmer=self.farmer_1,
            date=timezone.localdate(),
            check_in=time(8, 30),
            check_out=time(16, 30),
            total_hours=8.0,
            location="North Field"
        )
        detail_url = reverse('attendance:attendance_detail', kwargs={'pk': att.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_hours'], 8.0)
        self.assertEqual(data['data']['farmer_name'], "John Doe")

    def test_09_missing_record_returns_404(self):
        """9. Missing attendance record returns standardized 404."""
        detail_url = reverse('attendance:attendance_detail', kwargs={'pk': 99999})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 3. AUTHORIZATION TESTS (10 - 13)
    # ==========================================================================
    def test_10_regular_user_cannot_check_in(self):
        """10. Regular authenticated user cannot check in (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.check_in_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.json()['success'])

    def test_11_regular_user_cannot_check_out(self):
        """11. Regular authenticated user cannot check out (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.check_out_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_12_staff_can_check_in(self):
        """12. Staff/admin can perform worker check in."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_in_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['success'])
        self.assertTrue(Attendance.objects.filter(farmer=self.farmer_1).exists())

    def test_13_staff_can_check_out(self):
        """13. Staff/admin can perform worker check out."""
        Attendance.objects.create(farmer=self.farmer_1, date=timezone.localdate(), check_in=time(8, 0))
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            self.check_out_url,
            {"farmer_id": self.farmer_1.pk, "check_out_time": "16:30:00"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

    # ==========================================================================
    # 4. CHECK-IN TESTS & VALIDATION (14 - 18)
    # ==========================================================================
    def test_14_valid_farmer_check_in_succeeds(self):
        """14. Valid farmer check in creates attendance record with status 201."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "farmer_id": self.farmer_2.pk,
            "device_location": "12.9716, 77.5946",
            "check_in_time": "08:15:00",
            "date": "2026-08-24"
        }
        response = self.client.post(self.check_in_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()['data']
        self.assertEqual(data['farmer'], self.farmer_2.pk)
        self.assertEqual(data['location'], "12.9716, 77.5946")
        self.assertEqual(data['check_in'], "08:15:00")
        self.assertEqual(data['total_hours'], 0.0)

    def test_15_invalid_farmer_id_rejected(self):
        """15. Invalid farmer ID is rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_in_url, {"farmer_id": 99999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_16_invalid_check_in_payload_rejected(self):
        """16. Missing farmer_id rejected with 400."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_in_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_17_duplicate_check_in_on_same_date_rejected(self):
        """17. Second check in for same farmer on same date is rejected."""
        Attendance.objects.create(farmer=self.farmer_1, date=timezone.localdate(), check_in=time(8, 0))
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_in_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", str(response.json()['errors']['farmer_id']))

    def test_18_location_defaults_to_farmer_field(self):
        """18. If device_location is omitted, location defaults to farmer's assigned field."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_in_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']['location'], "North Field")

    # ==========================================================================
    # 5. CHECK-OUT TESTS & DURATION CALCULATION (19 - 24)
    # ==========================================================================
    def test_19_23_valid_checkout_calculates_total_hours(self):
        """19, 23. Valid check-out calculates total_hours correctly (e.g. 08:00 to 16:30 = 8.5 hrs)."""
        Attendance.objects.create(farmer=self.farmer_1, date=timezone.localdate(), check_in=time(8, 0))
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "farmer_id": self.farmer_1.pk,
            "check_out_time": "16:30:00"
        }
        response = self.client.post(self.check_out_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['total_hours'], 8.5)
        self.assertEqual(data['check_out'], "16:30:00")

    def test_20_checkout_without_active_checkin_fails(self):
        """20. Check-out without an active check-in fails with 400."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_out_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No active check-in", str(response.json()['errors']['farmer_id']))

    def test_21_repeated_checkout_fails(self):
        """21. Repeated check-out after already checked out today fails with 400."""
        Attendance.objects.create(
            farmer=self.farmer_1,
            date=timezone.localdate(),
            check_in=time(8, 0),
            check_out=time(16, 0),
            total_hours=8.0
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.check_out_url, {"farmer_id": self.farmer_1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already checked out", str(response.json()['errors']['farmer_id']))

    def test_22_correct_attendance_record_updated(self):
        """22. Check-out updates only the targeted farmer's open record."""
        today = timezone.localdate()
        att1 = Attendance.objects.create(farmer=self.farmer_1, date=today, check_in=time(8, 0))
        att2 = Attendance.objects.create(farmer=self.farmer_2, date=today, check_in=time(8, 30))

        self.client.force_authenticate(user=self.admin_user)
        self.client.post(self.check_out_url, {"farmer_id": self.farmer_1.pk, "check_out_time": "17:00:00"}, format='json')

        att1.refresh_from_db()
        att2.refresh_from_db()

        self.assertEqual(att1.total_hours, 9.0)
        self.assertIsNone(att2.check_out)
        self.assertEqual(att2.total_hours, 0.0)

    def test_24_checkout_with_explicit_location_updates_location(self):
        """24. Check-out with new GPS coordinates updates location."""
        Attendance.objects.create(farmer=self.farmer_1, date=timezone.localdate(), check_in=time(8, 0), location="North Field")
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "farmer_id": self.farmer_1.pk,
            "check_out_time": "16:00:00",
            "device_location": "12.9800, 77.6000"
        }
        response = self.client.post(self.check_out_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['location'], "12.9800, 77.6000")

    # ==========================================================================
    # 6. ATTENDANCE REPORT & FILTER TESTS (25 - 30)
    # ==========================================================================
    def test_25_26_report_succeeds_and_empty_state_works(self):
        """25, 26. Report succeeds for valid input and handles empty database gracefully."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['total_records'], 0)
        self.assertEqual(data['total_hours_sum'], 0.0)
        self.assertEqual(data['records'], [])

    def test_27_invalid_date_format_rejected_in_report(self):
        """27. Malformed date string rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.report_url}?start_date=invalid-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_28_invalid_date_range_rejected(self):
        """28. start_date > end_date is rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.report_url}?start_date=2026-08-30&end_date=2026-08-01")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Start date cannot be after end date", str(response.json()['errors']['start_date']))

    def test_29_report_filters_by_farmer_id(self):
        """29. Report correctly filters by specific farmer_id."""
        today = timezone.localdate()
        Attendance.objects.create(farmer=self.farmer_1, date=today, check_in=time(8, 0), total_hours=8.0)
        Attendance.objects.create(farmer=self.farmer_2, date=today, check_in=time(8, 0), total_hours=6.5)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.report_url}?farmer_id={self.farmer_1.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['total_records'], 1)
        self.assertEqual(data['total_hours_sum'], 8.0)
        self.assertEqual(data['records'][0]['farmer_name'], "John Doe")

    def test_30_report_filters_by_date_range(self):
        """30. Report correctly filters records within start_date and end_date."""
        d1 = date(2026, 8, 10)
        d2 = date(2026, 8, 15)
        d3 = date(2026, 8, 20)

        Attendance.objects.create(farmer=self.farmer_1, date=d1, check_in=time(8, 0), total_hours=8.0)
        Attendance.objects.create(farmer=self.farmer_1, date=d2, check_in=time(8, 0), total_hours=8.0)
        Attendance.objects.create(farmer=self.farmer_1, date=d3, check_in=time(8, 0), total_hours=8.0)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.report_url}?start_date=2026-08-12&end_date=2026-08-18")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['total_records'], 1)
        self.assertEqual(data['records'][0]['date'], "2026-08-15")

    # ==========================================================================
    # 7. DATA SAFETY & LIST FILTERS (31)
    # ==========================================================================
    def test_31_list_active_filter(self):
        """31. List filter ?is_active=true returns only open attendance records."""
        today = timezone.localdate()
        Attendance.objects.create(farmer=self.farmer_1, date=today, check_in=time(8, 0)) # Open
        Attendance.objects.create(farmer=self.farmer_2, date=today, check_in=time(8, 0), check_out=time(16, 0), total_hours=8.0) # Closed

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_url}?is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)
        self.assertIsNone(response.json()['data'][0]['check_out'])
