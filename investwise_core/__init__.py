"""
InvestWise Core — Package Initialization

Imports the Celery app instance so that it is available when Django starts.
This ensures the @shared_task decorator works correctly in all app modules.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
