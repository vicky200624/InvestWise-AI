"""
InvestWise AI 3.0 — ASGI Configuration

Configures the ASGI application with Django Channels for WebSocket support.
HTTP requests are handled by Django's standard ASGI handler, while WebSocket
connections are routed through the Channels authentication middleware to
the investwise.routing module.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'investwise_core.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Import WebSocket URL patterns from investwise app
import investwise.routing

application = ProtocolTypeRouter({
    # Standard HTTP requests → Django's ASGI handler
    'http': get_asgi_application(),

    # WebSocket connections → Django Channels with session auth
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                investwise.routing.websocket_urlpatterns
            )
        )
    ),
})
