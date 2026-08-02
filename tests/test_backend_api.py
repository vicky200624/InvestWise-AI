"""
Unit tests for InvestWise AI 3.0 Django REST Framework backend API.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from rest_framework import status

class TestBackendAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Add X-API-Version header to all requests (required by APIVersioningMiddleware)
        self.client.credentials(HTTP_X_API_VERSION='1.0')
        self.user = User.objects.create_user(username='testinvestor', email='test@investwise.ai', password='SecurePassword123!')
        self.client.force_authenticate(user=self.user)

    def test_portfolio_holdings_authenticated(self):
        response = self.client.get('/api/v1/portfolio/holdings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_portfolio_unauthenticated_rejected(self):
        client_unauth = APIClient()
        client_unauth.credentials(HTTP_X_API_VERSION='1.0')
        response = client_unauth.get('/api/v1/portfolio/holdings/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_watchlist_create(self):
        response = self.client.post('/api/v1/watchlist/watchlists/', {'name': 'Tech Stocks'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Tech Stocks')

    def test_auth_register_and_jwt_login(self):
        client_unauth = APIClient()
        client_unauth.credentials(HTTP_X_API_VERSION='1.0')
        reg_res = client_unauth.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@investwise.ai',
            'password': 'NewSecurePassword456!',
            'password_confirm': 'NewSecurePassword456!'
        }, format='json')
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        # Username is set to email since USERNAME_FIELD = 'email'
        self.assertEqual(reg_res.data['username'], 'newuser@investwise.ai')

        login_res = client_unauth.post('/api/v1/auth/login/', {
            'email': 'newuser@investwise.ai',
            'password': 'NewSecurePassword456!'
        }, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_res.data)
        self.assertIn('refresh', login_res.data)

        access_token = login_res.data['access']
        client_unauth.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}', HTTP_X_API_VERSION='1.0')
        profile_res = client_unauth.get('/api/v1/auth/profile/')
        self.assertEqual(profile_res.status_code, status.HTTP_200_OK)
        # Username is set to email since USERNAME_FIELD = 'email'
        self.assertEqual(profile_res.data['username'], 'newuser@investwise.ai')

        refresh_res = client_unauth.post('/api/v1/auth/refresh/', {
            'refresh': login_res.data['refresh']
        }, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_broker_credentials_encryption(self):
        put_res = self.client.put('/api/v1/auth/broker/', {
            'broker_name': 'Zerodha',
            'client_id': 'ZER999',
            'api_key': 'top-secret-api-key-12345',
            'pin': '987654'
        }, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertTrue(put_res.data['is_active'])

        from apps.accounts.models import BrokerCredentials
        cred = BrokerCredentials.objects.get(user=self.user)
        self.assertNotEqual(cred._api_key, 'top-secret-api-key-12345')
        self.assertNotEqual(cred._pin, '987654')
        self.assertEqual(cred.api_key, 'top-secret-api-key-12345')
        self.assertEqual(cred.pin, '987654')


    def test_watchlist_item_auto_watchlist(self):
        item_res = self.client.post('/api/watchlist/items/', {
            'symbol': 'RELIANCE'
        }, format='json')
        self.assertEqual(item_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(item_res.data['symbol'], 'RELIANCE')
        self.assertIsNotNone(item_res.data['watchlist'])

    def test_dashboard_summary_canonical_and_legacy_keys(self):
        dash_res = self.client.get('/api/dashboard/')
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        data = dash_res.data
        self.assertIn('current_value', data)
        self.assertIn('total_portfolio_value', data)
        self.assertIn('overall_score', data)
        self.assertIn('health_score', data)
        self.assertIn('allocation', data)
        self.assertIn('asset_allocation', data)
        self.assertIn('performance', data)
        self.assertIn('performance_30d', data)

    def test_portfolio_sync_broker_endpoint(self):
        # No credentials -> returns 400
        res = self.client.post('/api/portfolio/sync-broker/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['status'], 'error')

        # Add Zerodha creds -> returns 200 success
        from apps.accounts.models import BrokerCredentials
        BrokerCredentials.objects.create(
            user=self.user,
            broker_name='ZERODHA',
            api_key='zero-api-key',
            client_id='Z12345',
            is_active=True
        )
        res_ok = self.client.post('/api/portfolio/sync-broker/')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data['status'], 'success')
        self.assertEqual(res_ok.data['broker'], 'ZERODHA')


if __name__ == "__main__":
    unittest.main()