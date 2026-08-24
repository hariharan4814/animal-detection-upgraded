"""
Unit and integration tests for FarmSync Accounts & JWT Authentication module.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class AuthenticationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = "farmmanager"
        self.password = "SecureFarmPass123!"
        self.email = "manager@farmsync.local"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email,
            first_name="Farm",
            last_name="Manager"
        )
        self.login_url = reverse('accounts:login')
        self.refresh_url = reverse('accounts:token_refresh')
        self.me_url = reverse('accounts:current_user')
        self.logout_url = reverse('accounts:logout')

    def test_login_success(self):
        """Verify valid login returns JWT tokens and safe user profile."""
        response = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('access', data['data'])
        self.assertIn('refresh', data['data'])
        self.assertIn('user', data['data'])
        self.assertEqual(data['data']['user']['username'], self.username)
        self.assertEqual(data['data']['user']['email'], self.email)
        
        # Verify sensitive password/hash fields are NOT present
        self.assertNotIn('password', data['data']['user'])
        self.assertNotIn('password_hash', data['data']['user'])

    def test_login_invalid_password(self):
        """Verify invalid password returns standard 400 error."""
        response = self.client.post(
            self.login_url,
            {"username": self.username, "password": "WrongPassword!"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('message', data)

    def test_login_nonexistent_user(self):
        """Verify non-existent username returns standard 400 error."""
        response = self.client.post(
            self.login_url,
            {"username": "nonexistent_user", "password": "AnyPassword123!"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])

    def test_token_refresh(self):
        """Verify refresh endpoint provides new access token."""
        login_res = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            format='json'
        )
        refresh_token = login_res.json()['data']['refresh']

        refresh_res = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format='json'
        )
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        data = refresh_res.json()
        self.assertTrue(data['success'])
        self.assertIn('access', data['data'])

    def test_current_user_authenticated(self):
        """Verify authenticated GET /api/v1/auth/me/ returns safe user data."""
        login_res = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            format='json'
        )
        access_token = login_res.json()['data']['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['username'], self.username)
        self.assertEqual(data['data']['email'], self.email)
        self.assertNotIn('password', data['data'])

    def test_current_user_unauthenticated(self):
        """Verify unauthenticated GET /api/v1/auth/me/ returns 401 JSON error."""
        self.client.credentials()  # No token
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertFalse(data['success'])

    def test_logout_and_blacklisting(self):
        """Verify logout blacklists the refresh token preventing subsequent refreshes."""
        login_res = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            format='json'
        )
        tokens = login_res.json()['data']
        access_token = tokens['access']
        refresh_token = tokens['refresh']

        # Perform logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_res = self.client.post(
            self.logout_url,
            {"refresh": refresh_token},
            format='json'
        )
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
        self.assertTrue(logout_res.json()['success'])

        # Attempt to refresh with blacklisted token should fail
        self.client.credentials()
        attempt_res = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format='json'
        )
        self.assertIn(attempt_res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])
