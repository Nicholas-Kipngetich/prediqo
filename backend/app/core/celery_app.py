"""Celery application for background jobs (sync, predictions, settlement, notifications)."""

from celery import Celery

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
)
