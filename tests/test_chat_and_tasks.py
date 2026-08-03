"""
Unit tests for InvestWise AI 3.0 Chat API endpoints and Celery scheduled tasks.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.chat.models import ChatSession, ChatMessage
from tasks.schedulers import retrain_candidate_models

User = get_user_model()


class TestChatAndTasks(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Add X-API-Version header to all requests (required by APIVersioningMiddleware)
        self.client.credentials(HTTP_X_API_VERSION='1.0')
        self.user = User.objects.create_user(
            email='chat@investwise.ai',
            username='chatuser',
            password='SecureChatPassword123!'
        )
        self.client.force_authenticate(user=self.user)

    def test_chat_message_creation_and_fallback(self):
        res = self.client.post('/api/v1/chat/message/', {
            'content': 'How is my portfolio performing?'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', res.data)
        self.assertIn('message', res.data)
        self.assertIn('role', res.data)
        self.assertEqual(res.data['role'], 'ai')

        session_id = res.data['session_id']
        session = ChatSession.objects.get(id=session_id)
        self.assertEqual(session.user, self.user)
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 2)  # User + AI message

    def test_chat_sessions_list(self):
        # Create a session via POST message first
        self.client.post('/api/v1/chat/message/', {'content': 'Hello'}, format='json')
        res = self.client.get('/api/v1/chat/sessions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_voice_chat_endpoint(self):
        res = self.client.post('/api/v1/chat/voice-chat/', {
            'user_text': 'Connect broker account'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('ai_text', res.data)
        self.assertIn('user_text', res.data)
        self.assertEqual(res.data['user_text'], 'Connect broker account')

    def test_celery_task_retrain_candidate_models(self):
        res = retrain_candidate_models()
        self.assertIn('version', res)
        self.assertIn('metrics', res)
        self.assertIn('accuracy', res['metrics'])
        self.assertEqual(res['status'], 'Candidate')

    def test_research_analyze_endpoint(self):
        res = self.client.post('/api/v1/research/analyze/', {
            'symbol': 'RELIANCE.NS',
            'time_horizon': 'LONG'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('action', res.data)
        self.assertIn('score', res.data)
        self.assertIn('narrative', res.data)
        self.assertEqual(res.data['status'], 'COMPLETED')


