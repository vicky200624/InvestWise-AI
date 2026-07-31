"""
Health check and diagnostics endpoint for InvestWise AI 3.0 backend.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            'status': 'healthy',
            'version': '3.0.0',
            'checks': {
                'database': 'unknown',
                'cache': 'unknown'
            }
        }

        # Check PostgreSQL
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'ok'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status['checks']['database'] = 'error'
            health_status['status'] = 'degraded'

        # Check Cache/Redis
        try:
            cache.set('health_check_key', 'ok', timeout=10)
            val = cache.get('health_check_key')
            if val == 'ok':
                health_status['checks']['cache'] = 'ok'
            else:
                health_status['checks']['cache'] = 'error'
                health_status['status'] = 'degraded'
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            health_status['checks']['cache'] = 'degraded'

        response_status = status.HTTP_200_OK if health_status['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(health_status, status=response_status)
