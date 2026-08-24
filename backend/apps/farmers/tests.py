from django.test import TestCase
from apps.farmers.models import Farmer


class FarmerModelTests(TestCase):
    def test_create_farmer(self):
        farmer = Farmer.objects.create(
            name="John Doe",
            phone="1234567890",
            field="North Field",
            email="john@example.com"
        )
        self.assertEqual(farmer.name, "John Doe")
        self.assertEqual(str(farmer), "John Doe (North Field)")
        self.assertTrue(farmer.id is not None)
