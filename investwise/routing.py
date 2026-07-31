"""
InvestWise AI 3.0 — WebSocket URL Routing

Maps WebSocket connection paths to Django Channels consumers.
Used by the ASGI application in investwise_core/asgi.py.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket endpoint for real-time agent progress streaming.
    # Frontend connects to: ws://host/ws/agent/<task_id>/
    # Receives: cluster progress updates, streaming text, final results
    re_path(
        r'ws/agent/(?P<task_id>[0-9a-f-]+)/$',
        consumers.AgentStreamConsumer.as_asgi()
    ),
]
