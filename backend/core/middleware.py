"""
Custom middleware for InvestWise AI 3.0 production hardening.
- API versioning
- Security headers
- Request logging
- Rate limiting per IP
"""

import logging
import time
from django.http import JsonResponse
from django.conf import settings
from rest_framework import status

logger = logging.getLogger('investwise.middleware')


class APIVersioningMiddleware:
    """
    Enforces API versioning via X-API-Version header.
    Rejects requests with missing or incorrect version.
    """
    REQUIRED_VERSION = '1.0'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip versioning for admin, static, and health checks
        if request.path.startswith(('/admin/', '/static/', '/api/v1/health/')):
            return self.get_response(request)

        # Check API version header for API requests
        if request.path.startswith('/api/'):
            api_version = request.headers.get('X-API-Version')
            if api_version != self.REQUIRED_VERSION:
                return JsonResponse(
                    {
                        'error': 'INVALID_API_VERSION',
                        'detail': f'X-API-Version header required. Expected: {self.REQUIRED_VERSION}',
                        'code': status.HTTP_426_UPGRADE_REQUIRED
                    },
                    status=status.HTTP_426_UPGRADE_REQUIRED
                )

        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Adds production security headers to all responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # HSTS (only in production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = f'max-age={settings.SECURE_HSTS_SECONDS}; includeSubDomains; preload'

        # Remove server header
        if 'Server' in response:
            del response['Server']

        return response


class RequestLoggingMiddleware:
    """
    Logs all incoming requests with timing and status codes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.path} | "
            f"IP: {self._get_client_ip(request)} | "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )

        response = self.get_response(request)

        # Calculate request duration
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Log response
        logger.info(
            f"Response: {request.method} {request.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.2f}ms"
        )

        # Add timing header
        response['X-Response-Time'] = f"{duration:.2f}ms"

        return response

    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class IPRateLimitMiddleware:
    """
    Simple IP-based rate limiting middleware.
    Blocks IPs that exceed 100 requests per minute.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}  # {ip: [timestamps]}
        self.limit = 100  # requests per minute

    def __call__(self, request):
        # Skip for admin and static files
        if request.path.startswith(('/admin/', '/static/')):
            return self.get_response(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old timestamps
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip]
                if current_time - ts < 60
            ]
        else:
            self.requests[client_ip] = []

        # Check rate limit
        if len(self.requests[client_ip]) >= self.limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse(
                {
                    'error': 'RATE_LIMIT_EXCEEDED',
                    'detail': 'Too many requests. Please try again later.',
                    'code': status.HTTP_429_TOO_MANY_REQUESTS
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Add current request timestamp
        self.requests[client_ip].append(current_time)

        return self.get_response(request)

    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class MaintenanceModeMiddleware:
    """
    Enables maintenance mode when MAINTENANCE_MODE env var is set.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.maintenance_mode = settings.ENV == 'maintenance'

    def __call__(self, request):
        if self.maintenance_mode and not request.path.startswith('/admin/'):
            return JsonResponse(
                {
                    'error': 'MAINTENANCE_MODE',
                    'detail': 'System is under maintenance. Please try again later.',
                    'code': status.HTTP_503_SERVICE_UNAVAILABLE
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return self.get_response(request)