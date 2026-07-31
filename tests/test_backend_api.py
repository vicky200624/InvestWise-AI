"""
Unit tests for InvestWise AI 3.0 Django REST Framework backend API.
"""

import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

class TestBackendAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testinvestor', email='test@investwise.ai', password='SecurePassword123!')
        self.client.force_authenticate(user=self.user)

    def test_portfolio_holdings_authenticated(self):
        response = self.client.get('/api/v1/portfolio/holdings/')
        # Should return 200 OK since user is authenticated
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_portfolio_unauthenticated_rejected(self):
        client_unauth = APIClient()
        response = client_unauth.get('/api/v1/portfolio/holdings/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_watchlist_create(self):
        response = self.client.post('/api/v1/watchlist/watchlists/', {'name': 'Tech Stocks'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Tech Stocks')
