"""Celery application for background jobs (sync, predictions, settlement, notifications)."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "prediqo",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "sync-fixtures-every-6-hours": {
            "task": "prediqo.sync.fixtures",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "generate-predictions-hourly": {
            "task": "prediqo.predictions.generate",
            "schedule": crontab(minute=15),
        },
        "settle-predictions-every-30-minutes": {
            "task": "prediqo.predictions.settle",
            "schedule": crontab(minute="*/30"),
        },
        "generate-notifications-every-15-minutes": {
            "task": "prediqo.notifications.generate",
            "schedule": crontab(minute="*/15"),
        },
    },
)
