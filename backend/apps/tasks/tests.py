from django.test import TestCase
from apps.farmers.models import Farmer
from apps.tasks.models import Task


class TaskModelTests(TestCase):
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
