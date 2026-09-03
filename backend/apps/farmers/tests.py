"""
Comprehensive unit and integration tests for FarmSync Farmers CRUD Module.
Verifies listing, detail, creation, updates (PUT/PATCH), deletion, permissions, validation, and relational cascades.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import time
from rest_framework.test import APIClient
from rest_framework import status

from apps.farmers.models import Farmer
from apps.attendance.models import Attendance
from apps.tasks.models import Task


class FarmersAPITests(TestCase):
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

        self.list_create_url = reverse('farmers:farmer_list_create')

    # ==========================================================================
    # 1. AUTHENTICATION & LISTING TESTS
    # ==========================================================================
    def test_01_unauthenticated_list_rejected(self):
        """1. Unauthenticated list request rejected with HTTP 401."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json()['success'])

    def test_02_authenticated_list_succeeds(self):
        """2. Authenticated user can list farmers."""
        Farmer.objects.create(name="Alice Smith", phone="1234567890", field="North Field", email="alice@example.com")
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], "Alice Smith")

    def test_03_empty_farmer_list_succeeds(self):
        """3. Empty farmer list returns 200 OK with empty array."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], [])

    def test_04_farmer_detail_retrieval(self):
        """4. Farmer detail retrieval succeeds."""
        farmer = Farmer.objects.create(name="Bob Jones", phone="9876543210", field="East Field", email="bob@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], "Bob Jones")
        self.assertEqual(data['data']['phone'], "9876543210")
        self.assertEqual(data['data']['field'], "East Field")

    def test_05_nonexistent_farmer_returns_404(self):
        """5. Nonexistent farmer ID returns standardized 404."""
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': 99999})
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['success'])

    # ==========================================================================
    # 2. CREATION TESTS & AUTHORIZATION
    # ==========================================================================
    def test_06_regular_user_cannot_create_farmer(self):
        """6. Regular authenticated user cannot create farmer (HTTP 403)."""
        self.client.force_authenticate(user=self.regular_user)
        payload = {"name": "Unauthorized Farmer", "phone": "111", "field": "West"}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.json()['success'])

    def test_07_09_staff_can_create_farmer_valid_payload(self):
        """7, 9. Staff/admin can create a farmer with valid payload."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "Charlie Green",
            "phone": "555-1234",
            "field": "Greenhouse A",
            "email": "charlie@farmsync.org"
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], "Charlie Green")
        self.assertEqual(data['data']['field'], "Greenhouse A")
        self.assertTrue(Farmer.objects.filter(name="Charlie Green").exists())

    def test_08_invalid_create_payload_rejected(self):
        """8. Invalid create payload (missing name or blank phone) rejected with 400."""
        self.client.force_authenticate(user=self.admin_user)
        # Missing required field
        invalid_payload = {"phone": "12345", "field": "Barn"}
        response = self.client.post(self.list_create_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

        # Blank string validation
        blank_payload = {"name": "   ", "phone": "123", "field": "Barn"}
        blank_res = self.client.post(self.list_create_url, blank_payload, format='json')
        self.assertEqual(blank_res.status_code, status.HTTP_400_BAD_REQUEST)

    # ==========================================================================
    # 3. FULL & PARTIAL UPDATE TESTS (PUT / PATCH)
    # ==========================================================================
    def test_10_regular_user_cannot_put(self):
        """10. Regular user cannot perform PUT full update (HTTP 403)."""
        farmer = Farmer.objects.create(name="Dave", phone="123", field="Sector 1", email="dave@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.regular_user)
        put_payload = {"name": "Dave Updated", "phone": "123", "field": "Sector 1", "email": "dave@example.com"}
        response = self.client.put(detail_url, put_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_11_staff_can_put_full_update(self):
        """11. Staff/admin can perform PUT full update."""
        farmer = Farmer.objects.create(name="Dave", phone="123", field="Sector 1", email="dave@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.admin_user)
        put_payload = {
            "name": "David Miller",
            "phone": "999-8888",
            "field": "Sector 2",
            "email": "david@farmsync.org"
        }
        response = self.client.put(detail_url, put_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        farmer.refresh_from_db()
        self.assertEqual(farmer.name, "David Miller")
        self.assertEqual(farmer.phone, "999-8888")
        self.assertEqual(farmer.field, "Sector 2")

    def test_12_regular_user_cannot_patch(self):
        """12. Regular user cannot perform PATCH partial update (HTTP 403)."""
        farmer = Farmer.objects.create(name="Eve", phone="456", field="Sector 3", email="eve@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(detail_url, {"field": "Sector 4"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_13_14_staff_can_patch_and_preserves_unspecified_fields(self):
        """13, 14. Staff can PATCH and unspecified fields are preserved."""
        farmer = Farmer.objects.create(
            name="Frank",
            phone="777-1111",
            field="Orchard North",
            email="frank@orchard.local"
        )
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.admin_user)
        patch_payload = {"field": "Orchard South"}
        response = self.client.patch(detail_url, patch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        farmer.refresh_from_db()
        # Changed
        self.assertEqual(farmer.field, "Orchard South")
        # Preserved
        self.assertEqual(farmer.name, "Frank")
        self.assertEqual(farmer.phone, "777-1111")
        self.assertEqual(farmer.email, "frank@orchard.local")

    # ==========================================================================
    # 4. DELETION & RELATIONSHIP TESTS
    # ==========================================================================
    def test_15_regular_user_cannot_delete(self):
        """15. Regular user cannot delete a farmer (HTTP 403)."""
        farmer = Farmer.objects.create(name="Grace", phone="888", field="Poultry", email="grace@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Farmer.objects.filter(pk=farmer.pk).exists())

    def test_16_staff_can_delete_farmer(self):
        """16. Staff/admin can delete a farmer."""
        farmer = Farmer.objects.create(name="Grace", phone="888", field="Poultry", email="grace@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Farmer.objects.filter(pk=farmer.pk).exists())

    def test_17_delete_with_related_attendance_cascades(self):
        """17. Deleting a Farmer cascade-deletes their associated Attendance records (on_delete=CASCADE)."""
        farmer = Farmer.objects.create(name="Henry", phone="333", field="Dairy", email="henry@example.com")
        att = Attendance.objects.create(farmer=farmer, date=timezone.localdate(), check_in=time(8, 0), total_hours=7.5)
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Farmer.objects.filter(pk=farmer.pk).exists())
        self.assertFalse(Attendance.objects.filter(pk=att.pk).exists())

    def test_18_delete_with_related_tasks_sets_null(self):
        """18. Deleting a Farmer sets assigned_to=NULL on their associated Tasks (on_delete=SET_NULL)."""
        farmer = Farmer.objects.create(name="Ivy", phone="444", field="Vineyard", email="ivy@example.com")
        task = Task.objects.create(task_name="Prune vines", assigned_to=farmer, status="Pending", date=timezone.localdate())
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Farmer.objects.filter(pk=farmer.pk).exists())
        task.refresh_from_db()
        self.assertIsNone(task.assigned_to)
        self.assertEqual(task.task_name, "Prune vines")

    # ==========================================================================
    # 5. RESPONSE STANDARDIZATION & WRITE SECURITY
    # ==========================================================================
    def test_19_response_format_standardization(self):
        """19. Standard response envelope is strictly adhered to."""
        farmer = Farmer.objects.create(name="Jack", phone="123", field="Barn", email="jack@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(detail_url)
        data = response.json()

        self.assertIn('success', data)
        self.assertIn('message', data)
        self.assertIn('data', data)
        self.assertTrue(data['success'])

    def test_20_unauthenticated_write_endpoints_rejected(self):
        """20. Zero unauthenticated write access on POST, PUT, PATCH, DELETE."""
        farmer = Farmer.objects.create(name="Karen", phone="000", field="HQ", email="karen@example.com")
        detail_url = reverse('farmers:farmer_detail', kwargs={'pk': farmer.pk})

        # POST
        res_post = self.client.post(self.list_create_url, {"name": "Karen 2", "email": "karen2@example.com"}, format='json')
        self.assertEqual(res_post.status_code, status.HTTP_401_UNAUTHORIZED)

        # PUT
        res_put = self.client.put(detail_url, {"name": "Karen Updated", "email": "karen@example.com"}, format='json')
        self.assertEqual(res_put.status_code, status.HTTP_401_UNAUTHORIZED)

        # PATCH
        res_patch = self.client.patch(detail_url, {"field": "New HQ"}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_401_UNAUTHORIZED)

        # DELETE
        res_del = self.client.delete(detail_url)
        self.assertEqual(res_del.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================================================
    # 6. MANDATORY EMAIL & VALIDATION TESTS
    # ==========================================================================
    def test_21_farmer_create_requires_email(self):
        """21. Farmer creation requires an email address (HTTP 400)."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "No Email Worker",
            "phone": "555-0001",
            "field": "East Field"
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_22_farmer_create_invalid_email_format_rejected(self):
        """22. Farmer creation with invalid email format is rejected."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "Bad Email Worker",
            "phone": "555-0002",
            "field": "East Field",
            "email": "not-a-valid-email"
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_23_farmer_create_duplicate_email_rejected(self):
        """23. Farmer creation with duplicate email is rejected (uniqueness)."""
        Farmer.objects.create(name="Existing Worker", phone="555-1111", field="Field A", email="duplicate@example.com")
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "New Worker",
            "phone": "555-2222",
            "field": "Field B",
            "email": "duplicate@example.com"
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_24_farmer_email_stored_and_returned_correctly(self):
        """24. Farmer email is stored normalized in lowercase and returned in API responses."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "name": "Sanjeev B",
            "phone": "9940099083",
            "field": "Main Field",
            "email": "SanjeevB.Inbox@gmail.com"
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()['data']
        self.assertEqual(data['email'], "sanjeevb.inbox@gmail.com")

        farmer = Farmer.objects.get(name="Sanjeev B")
        self.assertEqual(farmer.email, "sanjeevb.inbox@gmail.com")
