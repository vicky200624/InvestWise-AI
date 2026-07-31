"""
InvestWise AI 3.0 — Celery Application Configuration

Configures the Celery distributed task queue with Redis as the message broker.
All async tasks (LangGraph agent runs, model training, data ingestion) are
dispatched through this application and executed by Celery workers.

Key settings:
- Late acknowledgment: Tasks are ack'd only after completion (prevents data loss on worker crash)
- Low prefetch multiplier: Prevents long-running AI tasks from blocking other workers
- Retry with exponential backoff: Resilient against transient API failures
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'investwise_core.settings')

app = Celery('investwise_core')

# Read config from Django settings, using the CELERY_ namespace so that all
# celery-related configuration keys should have a `CELERY_` prefix in settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed Django apps.
# This will look for a `tasks.py` module in each app listed in INSTALLED_APPS.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery connectivity. Run via: debug_task.delay()"""
    print(f'Request: {self.request!r}')
