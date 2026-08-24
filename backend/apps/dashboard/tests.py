"""
Comprehensive unit and integration tests for FarmSync Dashboard Module.
Verifies summary aggregation, recent activity feeds, zero-data behavior, read-only enforcement, and authentication.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import time, timedelta
from rest_framework.test import APIClient
from rest_framework import status

from apps.farmers.models import Farmer
from apps.attendance.models import Attendance
from apps.tasks.models import Task
from apps.detection.models import AnimalLog
from apps.alerts.models import Alert


class DashboardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="dashboard_viewer",
            password="SecurePass123!",
            email="viewer@farmsync.local"
        )
        self.summary_url = reverse('dashboard:summary')
        self.recent_url = reverse('dashboard:recent_activity')

    # 1. Unauthenticated access rejected
    def test_01_unauthenticated_access_rejected(self):
        """1. Verify unauthenticated requests to dashboard endpoints return 401."""
        res_summary = self.client.get(self.summary_url)
        self.assertEqual(res_summary.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(res_summary.json()['success'])

        res_recent = self.client.get(self.recent_url)
        self.assertEqual(res_recent.status_code, status.HTTP_401_UNAUTHORIZED)

    # 2 & 3. Authenticated retrieval & standard response envelope
    def test_02_03_authenticated_summary_standard_envelope(self):
        """2, 3. Verify authenticated user receives standard response envelope with HTTP 200."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('data', data)
        self.assertIn('farmers', data['data'])
        self.assertIn('attendance', data['data'])
        self.assertIn('tasks', data['data'])
        self.assertIn('detections', data['data'])
        self.assertIn('alerts', data['data'])

    # 4. Empty database zero-data behavior
    def test_04_zero_data_state_behavior(self):
        """4. Verify empty database produces clean zero-state metrics without errors."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']
        self.assertEqual(data['farmers']['total_farmers'], 0)
        self.assertEqual(data['attendance']['today_attendance'], 0)
        self.assertEqual(data['attendance']['total_records'], 0)
        self.assertEqual(data['tasks']['total_tasks'], 0)
        self.assertEqual(data['tasks']['completed_tasks'], 0)
        self.assertEqual(data['tasks']['pending_tasks'], 0)
        self.assertEqual(data['detections']['detections_today'], 0)
        self.assertEqual(data['detections']['total_detections'], 0)
        self.assertEqual(data['alerts']['alerts_today'], 0)
        self.assertEqual(data['alerts']['total_alerts'], 0)

        # Recent activity zero state
        recent_res = self.client.get(self.recent_url)
        self.assertEqual(recent_res.status_code, status.HTTP_200_OK)
        recent_data = recent_res.json()['data']
        self.assertEqual(recent_data['recent_alerts'], [])
        self.assertEqual(recent_data['recent_detections'], [])
        self.assertEqual(recent_data['recent_tasks'], [])

    # 5, 6, 7, 8, 9, 12, 13. Accurate metric calculation and timezone handling
    def test_05_to_09_metric_calculations_with_data(self):
        """5-9. Verify accurate metrics for farmers, attendance, tasks, detections, and alerts."""
        # Setup test data
        f1 = Farmer.objects.create(name="Farmer One", phone="111", field="North")
        f2 = Farmer.objects.create(name="Farmer Two", phone="222", field="South")

        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        # Attendance: 1 today, 1 yesterday
        Attendance.objects.create(farmer=f1, date=today, check_in=time(8, 0), total_hours=8.0)
        Attendance.objects.create(farmer=f2, date=yesterday, check_in=time(8, 0), total_hours=8.0)

        # Tasks: 2 completed, 1 pending
        Task.objects.create(task_name="Prune trees", assigned_to=f1, status="Completed", date=today)
        Task.objects.create(task_name="Clean filters", assigned_to=f2, status="Completed", date=today)
        Task.objects.create(task_name="Repair fence", assigned_to=f1, status="Pending", date=today)

        # Detections: 1 today, 1 yesterday
        log1 = AnimalLog.objects.create(
            animal_type="wolf",
            confidence=0.92,
            timestamp=timezone.now(),
            field="North",
            image_path="detections/wolf.jpg"
        )
        log2 = AnimalLog.objects.create(
            animal_type="deer",
            confidence=0.85,
            timestamp=timezone.now() - timedelta(days=2),
            field="South",
            image_path="detections/deer.jpg"
        )

        # Alerts: 1 for log1 (today), 1 for log2 (2 days ago)
        Alert.objects.create(animal_log=log1, alert_type="Email + Buzzer", status="Triggered")
        Alert.objects.create(animal_log=log2, alert_type="Log Only", status="Logged")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']

        # Farmer count
        self.assertEqual(data['farmers']['total_farmers'], 2)

        # Attendance counts
        self.assertEqual(data['attendance']['today_attendance'], 1)
        self.assertEqual(data['attendance']['total_records'], 2)

        # Task counts
        self.assertEqual(data['tasks']['total_tasks'], 3)
        self.assertEqual(data['tasks']['completed_tasks'], 2)
        self.assertEqual(data['tasks']['pending_tasks'], 1)

        # Detection counts
        self.assertEqual(data['detections']['detections_today'], 1)
        self.assertEqual(data['detections']['total_detections'], 2)

        # Alert counts
        self.assertEqual(data['alerts']['alerts_today'], 1)
        self.assertEqual(data['alerts']['total_alerts'], 2)
        self.assertEqual(data['alerts']['triggered_alerts'], 1)

    # 10. No sensitive data exposed
    def test_10_zero_sensitive_data_in_dashboard(self):
        """10. Verify no passwords, tokens, or SMTP secrets are returned in dashboard responses."""
        self.client.force_authenticate(user=self.user)
        for url in [self.summary_url, self.recent_url]:
            res = self.client.get(url)
            res_str = str(res.json()).lower()
            self.assertNotIn('password', res_str)
            self.assertNotIn('secret', res_str)
            self.assertNotIn('token', res_str)
            self.assertNotIn('smtp', res_str)

    # 11. Read-only enforcement (no mutations)
    def test_11_dashboard_is_strictly_read_only(self):
        """11. Verify dashboard queries do not modify DB records."""
        f = Farmer.objects.create(name="Immutable Farmer", phone="999", field="East")
        initial_count = Farmer.objects.count()

        self.client.force_authenticate(user=self.user)
        self.client.get(self.summary_url)
        self.client.get(self.recent_url)

        self.assertEqual(Farmer.objects.count(), initial_count)

    # 14. Invalid HTTP methods rejected
    def test_14_invalid_http_methods_rejected(self):
        """14. Verify mutating methods (POST, PUT, DELETE) are rejected with 405 Method Not Allowed."""
        self.client.force_authenticate(user=self.user)
        post_res = self.client.post(self.summary_url, {"dummy": "data"}, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_res = self.client.put(self.summary_url, {"dummy": "data"}, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        del_res = self.client.delete(self.summary_url)
        self.assertEqual(del_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # 15. Recent activity feed verification
    def test_15_recent_activity_feed(self):
        """15. Verify recent activity endpoint returns populated records with correct limits."""
        farmer = Farmer.objects.create(name="Activity Worker", phone="777", field="Greenhouse")
        log = AnimalLog.objects.create(animal_type="tiger", confidence=0.99, field="Greenhouse", image_path="tiger.jpg")
        Alert.objects.create(animal_log=log, alert_type="Email + Buzzer", status="Triggered")
        Task.objects.create(task_name="Feed animals", assigned_to=farmer, status="Pending", date=timezone.localdate())

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.recent_url}?limit=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()['data']
        self.assertEqual(len(data['recent_alerts']), 1)
        self.assertEqual(data['recent_alerts'][0]['animal_type'], "tiger")
        self.assertEqual(len(data['recent_detections']), 1)
        self.assertEqual(data['recent_detections'][0]['animal_type'], "tiger")
        self.assertEqual(len(data['recent_tasks']), 1)
        self.assertEqual(data['recent_tasks'][0]['task_name'], "Feed animals")
        self.assertEqual(data['recent_tasks'][0]['assigned_to_name'], "Activity Worker")
