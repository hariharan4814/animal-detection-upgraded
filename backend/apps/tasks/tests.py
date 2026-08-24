"""
Comprehensive unit and integration tests for FarmSync Tasks REST API Module.
Verifies listing, detail, creation, updates (PUT/PATCH), deletion, permissions, validation,
relational integrity, and filtering.
"""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.farmers.models import Farmer
from apps.tasks.models import Task


class TaskModelTests(TestCase):
    """Preserves baseline unit tests for Task model."""
    def setUp(self):
        self.farmer = Farmer.objects.create(
            name="Bob Worker",
            phone="5551234567",
            field="West Greenhouse"
        )

    def test_create_task(self):
        task = Task.objects.create(
            task_name="Check drip irrigation",
            assigned_to=self.farmer,
            status="Pending"
        )
        self.assertEqual(task.task_name, "Check drip irrigation")
        self.assertEqual(task.status, "Pending")
        self.assertEqual(task.assigned_to.name, "Bob Worker")
        self.assertIn("Check drip irrigation", str(task))

    def test_unassigned_task_str_representation(self):
        task = Task.objects.create(
            task_name="Maintain tractor",
            assigned_to=None,
            status="Pending"
        )
        self.assertIn("Unassigned", str(task))


class TasksAPITests(TestCase):
    """
    Integration tests for Tasks REST API endpoints.
    Covers Authentication, Authorization, Validation, CRUD, Relationships, and Filtering.
    """
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

        # Seed test farmers
        self.farmer1 = Farmer.objects.create(
            name="Alice Smith",
            phone="1234567890",
            field="North Orchard",
            email="alice@farmsync.local"
        )
        self.farmer2 = Farmer.objects.create(
            name="Bob Jones",
            phone="9876543210",
            field="East Vineyard",
            email="bob@farmsync.local"
        )

        self.list_create_url = reverse('tasks:task_list_create')

    # ==========================================================================
    # 1. AUTHENTICATION & ACCESS CONTROL TESTS
    # ==========================================================================
    def test_01_unauthenticated_list_rejected(self):
        """1. Unauthenticated list request rejected with HTTP 401."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_02_unauthenticated_detail_rejected(self):
        """2. Unauthenticated detail request rejected with HTTP 401."""
        task = Task.objects.create(task_name="Clean barn", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_03_unauthenticated_create_rejected(self):
        """3. Unauthenticated task creation rejected with HTTP 401."""
        payload = {"task_name": "Fix fence", "assigned_to": self.farmer1.pk}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_04_unauthenticated_put_rejected(self):
        """4. Unauthenticated PUT update rejected with HTTP 401."""
        task = Task.objects.create(task_name="Prune trees", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        payload = {"task_name": "Prune peach trees", "assigned_to": self.farmer1.pk, "status": "Completed"}
        response = self.client.put(detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_05_unauthenticated_patch_rejected(self):
        """5. Unauthenticated PATCH update rejected with HTTP 401."""
        task = Task.objects.create(task_name="Inspect fence", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        response = self.client.patch(detail_url, {"status": "Completed"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_06_unauthenticated_delete_rejected(self):
        """6. Unauthenticated DELETE request rejected with HTTP 401."""
        task = Task.objects.create(task_name="Harvest tomatoes", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================================================
    # 2. READ ACCESS TESTS (REGULAR AUTHENTICATED USERS)
    # ==========================================================================
    def test_07_authenticated_regular_user_can_list_tasks(self):
        """7. Authenticated regular user can list tasks."""
        Task.objects.create(task_name="Water crops", assigned_to=self.farmer1, status="Pending")
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['task_name'], "Water crops")
        self.assertEqual(data['data'][0]['assigned_to_name'], "Alice Smith")

    def test_08_empty_task_list_returns_empty_array(self):
        """8. Empty task list returns 200 OK with empty array."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], [])

    def test_09_authenticated_regular_user_can_retrieve_detail(self):
        """9. Authenticated regular user can retrieve details of a specific task."""
        task = Task.objects.create(task_name="Fertilize zone B", assigned_to=self.farmer2, status="Pending")
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['task_name'], "Fertilize zone B")
        self.assertEqual(data['data']['assigned_to'], self.farmer2.pk)
        self.assertEqual(data['data']['assigned_to_name'], "Bob Jones")

    def test_10_nonexistent_task_returns_404(self):
        """10. Nonexistent task ID returns standardized 404 envelope."""
        detail_url = reverse('tasks:task_detail', kwargs={'pk': 99999})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 3. WRITE PERMISSIONS & AUTHORIZATION
    # ==========================================================================
    def test_11_regular_user_cannot_create_task(self):
        """11. Regular user cannot create task (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        payload = {"task_name": "Unauthorized task", "assigned_to": self.farmer1.pk}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.json()['success'])

    def test_12_regular_user_cannot_put_task(self):
        """12. Regular user cannot perform PUT update on task (HTTP 403)."""
        task = Task.objects.create(task_name="Original task", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        self.client.force_authenticate(user=self.regular_user)
        payload = {"task_name": "Updated task", "assigned_to": self.farmer1.pk, "status": "Completed"}
        response = self.client.put(detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_13_regular_user_cannot_patch_task(self):
        """13. Regular user cannot perform PATCH update on task (HTTP 403)."""
        task = Task.objects.create(task_name="Original task", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(detail_url, {"status": "Completed"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_14_regular_user_cannot_delete_task(self):
        """14. Regular user cannot delete task (HTTP 403)."""
        task = Task.objects.create(task_name="Task to keep", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_15_staff_can_create_task(self):
        """15. Staff/admin user can create a task."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "task_name": "Repair greenhouse roof",
            "assigned_to": self.farmer1.pk,
            "status": "Pending"
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['task_name'], "Repair greenhouse roof")
        self.assertEqual(data['data']['assigned_to'], self.farmer1.pk)
        self.assertEqual(data['data']['assigned_to_name'], "Alice Smith")
        self.assertEqual(data['data']['status'], "Pending")
        self.assertTrue(Task.objects.filter(task_name="Repair greenhouse roof").exists())

    # ==========================================================================
    # 4. VALIDATION TESTS
    # ==========================================================================
    def test_16_blank_task_name_rejected(self):
        """16. Blank task_name is rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"task_name": "", "assigned_to": self.farmer1.pk}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_17_whitespace_only_task_name_rejected(self):
        """17. Whitespace-only task_name is rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"task_name": "     ", "assigned_to": self.farmer1.pk}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_18_invalid_assigned_farmer_rejected(self):
        """18. Nonexistent farmer foreign key is rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"task_name": "Valid task", "assigned_to": 99999}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_19_unassigned_task_creation_succeeds(self):
        """19. Task creation without assigned_to (unassigned) succeeds."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"task_name": "General maintenance", "assigned_to": None}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIsNone(data['data']['assigned_to'])
        self.assertIsNone(data['data']['assigned_to_name'])

    def test_20_invalid_status_rejected(self):
        """20. Unsupported status choice rejected with HTTP 400."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"task_name": "Check sensors", "assigned_to": self.farmer1.pk, "status": "InProgress"}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_21_valid_verified_statuses_accepted(self):
        """21. Valid verified statuses ('Pending', 'Completed') accepted on create/update."""
        self.client.force_authenticate(user=self.admin_user)
        # Pending
        res_p = self.client.post(self.list_create_url, {"task_name": "Task P", "status": "Pending"}, format='json')
        self.assertEqual(res_p.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_p.json()['data']['status'], "Pending")

        # Completed
        res_c = self.client.post(self.list_create_url, {"task_name": "Task C", "status": "Completed"}, format='json')
        self.assertEqual(res_c.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_c.json()['data']['status'], "Completed")

    def test_22_default_status_is_pending(self):
        """22. Omission of status defaults to 'Pending'."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post(self.list_create_url, {"task_name": "Default status test"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.json()['data']['status'], "Pending")

    # ==========================================================================
    # 5. CRUD & UPDATE BEHAVIOR (PUT / PATCH / DELETE)
    # ==========================================================================
    def test_23_staff_can_put_full_update(self):
        """23. Staff can perform a full PUT update on a task."""
        task = Task.objects.create(task_name="Old Name", assigned_to=self.farmer1, status="Pending")
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})

        self.client.force_authenticate(user=self.admin_user)
        put_payload = {
            "task_name": "New Name",
            "assigned_to": self.farmer2.pk,
            "status": "Completed",
            "date": "2026-05-01"
        }
        response = self.client.put(detail_url, put_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(task.task_name, "New Name")
        self.assertEqual(task.assigned_to, self.farmer2)
        self.assertEqual(task.status, "Completed")
        self.assertEqual(str(task.date), "2026-05-01")

    def test_24_staff_can_patch_and_preserves_unspecified_fields(self):
        """24. Staff can PATCH a task; unspecified fields are preserved."""
        task = Task.objects.create(
            task_name="Check solar panels",
            assigned_to=self.farmer1,
            status="Pending",
            date=date(2026, 4, 15)
        )
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})

        self.client.force_authenticate(user=self.admin_user)
        patch_payload = {"status": "Completed"}
        response = self.client.patch(detail_url, patch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(task.status, "Completed")
        # Preserved fields
        self.assertEqual(task.task_name, "Check solar panels")
        self.assertEqual(task.assigned_to, self.farmer1)
        self.assertEqual(task.date, date(2026, 4, 15))

    def test_25_status_transition_workflow(self):
        """25. Task status workflow transitions (Pending -> Completed -> Pending) via PATCH."""
        task = Task.objects.create(task_name="Test workflow", assigned_to=self.farmer1, status="Pending")
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})

        self.client.force_authenticate(user=self.admin_user)
        # Pending -> Completed
        res1 = self.client.patch(detail_url, {"status": "Completed"}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "Completed")

        # Completed -> Pending (revert)
        res2 = self.client.patch(detail_url, {"status": "Pending"}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "Pending")

    def test_26_staff_can_delete_task(self):
        """26. Staff can delete a task."""
        task = Task.objects.create(task_name="Task to delete", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    # ==========================================================================
    # 6. RELATIONSHIPS & CASCADES
    # ==========================================================================
    def test_27_assigned_farmer_serialization(self):
        """27. Assigned farmer serializes both ID and display name correctly."""
        task = Task.objects.create(task_name="Prune trees", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        data = response.json()['data']
        self.assertEqual(data['assigned_to'], self.farmer1.pk)
        self.assertEqual(data['assigned_to_name'], "Alice Smith")

    def test_28_farmer_deletion_sets_task_assigned_to_null(self):
        """28. Deleting an assigned Farmer preserves the Task and sets assigned_to=NULL (on_delete=SET_NULL)."""
        temp_farmer = Farmer.objects.create(name="Temp Worker", phone="1112223333", field="Shed")
        task = Task.objects.create(task_name="Temporary job", assigned_to=temp_farmer)

        # Delete the farmer
        temp_farmer.delete()

        task.refresh_from_db()
        self.assertIsNone(task.assigned_to)
        self.assertEqual(task.task_name, "Temporary job")

    # ==========================================================================
    # 7. FILTERING & QUERY PARAMETERS
    # ==========================================================================
    def test_29_filter_by_status(self):
        """29. Filter tasks by status (?status=Pending and ?status=Completed)."""
        Task.objects.create(task_name="Task 1", assigned_to=self.farmer1, status="Pending")
        Task.objects.create(task_name="Task 2", assigned_to=self.farmer1, status="Completed")
        Task.objects.create(task_name="Task 3", assigned_to=self.farmer2, status="Pending")

        self.client.force_authenticate(user=self.regular_user)

        # Filter Pending
        res_pending = self.client.get(f"{self.list_create_url}?status=Pending")
        self.assertEqual(res_pending.status_code, status.HTTP_200_OK)
        pending_data = res_pending.json()['data']
        self.assertEqual(len(pending_data), 2)
        self.assertTrue(all(t['status'] == 'Pending' for t in pending_data))

        # Filter Completed
        res_completed = self.client.get(f"{self.list_create_url}?status=Completed")
        self.assertEqual(res_completed.status_code, status.HTTP_200_OK)
        completed_data = res_completed.json()['data']
        self.assertEqual(len(completed_data), 1)
        self.assertEqual(completed_data[0]['task_name'], "Task 2")

    def test_30_filter_by_assigned_to_and_farmer_id(self):
        """30. Filter tasks by assigned farmer ID using either assigned_to or farmer_id."""
        Task.objects.create(task_name="Alice Task 1", assigned_to=self.farmer1)
        Task.objects.create(task_name="Alice Task 2", assigned_to=self.farmer1)
        Task.objects.create(task_name="Bob Task 1", assigned_to=self.farmer2)

        self.client.force_authenticate(user=self.regular_user)

        # ?assigned_to=<id>
        res1 = self.client.get(f"{self.list_create_url}?assigned_to={self.farmer1.pk}")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.json()['data']), 2)

        # ?farmer_id=<id>
        res2 = self.client.get(f"{self.list_create_url}?farmer_id={self.farmer2.pk}")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.json()['data']), 1)
        self.assertEqual(res2.json()['data'][0]['task_name'], "Bob Task 1")

    def test_31_filter_by_exact_date(self):
        """31. Filter tasks by exact assignment date (?date=YYYY-MM-DD)."""
        d1 = date(2026, 4, 10)
        d2 = date(2026, 4, 20)
        Task.objects.create(task_name="Past task", assigned_to=self.farmer1, date=d1)
        Task.objects.create(task_name="Current task", assigned_to=self.farmer1, date=d2)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_create_url}?date=2026-04-10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['task_name'], "Past task")

    def test_32_filter_by_date_range(self):
        """32. Filter tasks across date range (?start_date=...&end_date=...)."""
        Task.objects.create(task_name="Early task", date=date(2026, 4, 1))
        Task.objects.create(task_name="Mid task", date=date(2026, 4, 15))
        Task.objects.create(task_name="Late task", date=date(2026, 4, 30))

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_create_url}?start_date=2026-04-10&end_date=2026-04-20")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['task_name'], "Mid task")

    def test_33_invalid_filter_values_handled_gracefully(self):
        """33. Invalid filter parameters (non-integer ID, malformed date) do not produce 500 errors."""
        Task.objects.create(task_name="Sample task", assigned_to=self.farmer1)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_create_url}?assigned_to=abc&date=not-a-date&start_date=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])

    def test_34_combined_multi_filtering(self):
        """34. Combined filters (status + farmer_id) return exact intersection."""
        Task.objects.create(task_name="Alice Pending", assigned_to=self.farmer1, status="Pending")
        Task.objects.create(task_name="Alice Completed", assigned_to=self.farmer1, status="Completed")
        Task.objects.create(task_name="Bob Pending", assigned_to=self.farmer2, status="Pending")

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.list_create_url}?farmer_id={self.farmer1.pk}&status=Completed")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['task_name'], "Alice Completed")

    # ==========================================================================
    # 8. RESPONSE FORMAT STANDARDIZATION & ORDERING
    # ==========================================================================
    def test_35_response_format_envelope(self):
        """35. Response envelope conforms to {success, message, data} standard."""
        task = Task.objects.create(task_name="Envelope test", assigned_to=self.farmer1)
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        data = response.json()
        self.assertIn('success', data)
        self.assertIn('message', data)
        self.assertIn('data', data)
        self.assertTrue(data['success'])

    def test_36_tasks_ordering_reverse_id(self):
        """36. Tasks returned in reverse ID order (newest first)."""
        t1 = Task.objects.create(task_name="First created")
        t2 = Task.objects.create(task_name="Second created")
        t3 = Task.objects.create(task_name="Third created")

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        tasks = response.json()['data']
        self.assertEqual(tasks[0]['id'], t3.id)
        self.assertEqual(tasks[1]['id'], t2.id)
        self.assertEqual(tasks[2]['id'], t1.id)
