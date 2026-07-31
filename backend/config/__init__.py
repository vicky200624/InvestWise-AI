"""
InvestWise AI 3.0 Backend Config package.
Exports Celery application for Django integration.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)
