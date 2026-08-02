"""
Health check endpoint for InvestWise AI 3.0.
Provides system status, database connectivity, and cache health.
"""
import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('investwise.health')


def health_check(request):
    """
    Comprehensive health check endpoint.
    Returns system status, database, cache, and external service health.
    """
    health_status = {
        'status': 'healthy',
        'version': '3.0.0',
        'checks': {}
    }

    # Check database connectivity
    try:
        connection.ensure_connection()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'engine': connection.vendor
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'

    # Check Redis cache
    try:
        cache.set('health_check', 'ok', timeout=5)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'backend': settings.CACHES['default']['BACKEND']
            }
        else:
            raise Exception("Cache read/write failed")
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'

    # Check Celery (optional)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = {
                'status': 'healthy',
                'workers': len(stats)
            }
        else:
            health_status['checks']['celery'] = {
                'status': 'warning',
                'message': 'No active workers found'
            }
    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
        health_status['checks']['celery'] = {
            'status': 'unavailable',
            'error': str(e)
        }

    # Determine HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503

    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Kubernetes readiness probe.
    Checks if the application is ready to serve traffic.
    """
    try:
        # Check database
        connection.ensure_connection()
        
        # Check cache
        cache.set('readiness_check', 'ok', timeout=5)
        if cache.get('readiness_check') != 'ok':
            raise Exception("Cache not ready")
        
        return JsonResponse({'status': 'ready'}, status=200)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({'status': 'not ready', 'error': str(e)}, status=503)


def liveness_check(request):
    """
    Kubernetes liveness probe.
    Simple check to verify the application is running.
    """
    return JsonResponse({'status': 'alive'}, status=200)