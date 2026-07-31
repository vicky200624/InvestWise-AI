"""
Celery Configuration and Beat Schedule for InvestWise AI 3.0.
Configures Redis broker/backend and registers periodic jobs:
- Daily: Download Stock Prices, Download News
- Weekly: Feature Regeneration, Financial Statements
- Monthly: Macroeconomic Data Update
- Quarterly: SEC EDGAR 10-K/10-Q Reports, Retrain Candidate Models
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.development")

app = Celery("investwise_ai")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["backend.tasks", "apps.research"])

# Celery Beat Periodic Tasks Schedule
app.conf.beat_schedule = {
    # DAILY JOBS
    "daily-price-update": {
        "task": "backend.tasks.schedulers.daily_price_update",
        "schedule": crontab(hour=1, minute=0),  # 1:00 AM daily
        "args": (),
    },
    "daily-news-update": {
        "task": "backend.tasks.schedulers.daily_news_update",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM daily
        "args": (),
    },
    # WEEKLY JOBS
    "weekly-feature-regeneration": {
        "task": "backend.tasks.schedulers.weekly_feature_regeneration",
        "schedule": crontab(day_of_week="sunday", hour=3, minute=0),  # Sunday 3:00 AM
        "args": (),
    },
    "weekly-financial-statements": {
        "task": "backend.tasks.schedulers.weekly_financial_statements",
        "schedule": crontab(day_of_week="saturday", hour=4, minute=0),  # Saturday 4:00 AM
        "args": (),
    },
    # MONTHLY JOBS
    "monthly-macro-update": {
        "task": "backend.tasks.schedulers.monthly_macro_update",
        "schedule": crontab(day_of_month=1, hour=5, minute=0),  # 1st of month 5:00 AM
        "args": (),
    },
    # QUARTERLY JOBS
    "quarterly-edgar-filings": {
        "task": "backend.tasks.schedulers.quarterly_edgar_filings",
        "schedule": crontab(month_of_year="1,4,7,10", day_of_month=15, hour=6, minute=0),
        "args": (),
    },
    "retrain-candidate-models": {
        "task": "backend.tasks.schedulers.retrain_candidate_models",
        "schedule": crontab(day_of_week="sunday", hour=7, minute=0),  # Every Sunday 7:00 AM
        "args": (),
    },
}

app.conf.timezone = "UTC"
