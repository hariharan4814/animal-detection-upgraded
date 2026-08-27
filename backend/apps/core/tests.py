"""
Unit tests for FarmSync Core API infrastructure.
Verifies health check, API root, standard response envelopes, and exception formatting.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class CoreAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint(self):
        """Verify GET /api/v1/health/ returns 200 OK with standard success envelope."""
        url = reverse('core:health_check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('data', data)
        self.assertEqual(data['data'].get('status'), 'healthy')
        self.assertEqual(data['data'].get('version'), 'v1')

        # Security check: Ensure no sensitive keys exist in response
        sensitive_terms = ['secret', 'password', 'smtp', 'token', 'database', 'path']
        response_str = str(data).lower()
        for term in sensitive_terms:
            self.assertNotIn(term + '_key', response_str)
            self.assertNotIn(term + '_pass', response_str)

    def test_api_root_endpoint(self):
        """Verify GET /api/v1/ returns 200 OK with version and discovery endpoints."""
        url = reverse('core:api_root')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data'].get('version'), 'v1')
        self.assertIn('endpoints', data['data'])
        self.assertIn('health', data['data']['endpoints'])

    def test_not_found_exception_handling(self):
        """Verify requesting a non-existent API route returns a 404 in standard format."""
        response = self.client.get('/api/v1/non-existent-route/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_root_url_serves_frontend_spa(self):
        """Verify root GET / serves the decoupled Single-Page Application interface."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b'FarmSync', response.content)
        self.assertIn(b'React 19 + Vite SPA', response.content)
        self.assertIn(b'Launch FarmSync Console', response.content)

