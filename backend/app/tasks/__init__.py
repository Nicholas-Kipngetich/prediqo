"""Celery task registration.

Importing this package registers all periodic jobs with the Celery app.
"""

import asyncio

from app.core.celery_app import celery_app
from app.tasks.jobs import (
    run_fixture_sync,
    run_notification_generation,
    run_prediction_generation,
    run_settlement,
)


def _run(coroutine) -> dict:
    return asyncio.run(coroutine)


@celery_app.task(name="prediqo.sync.fixtures")
def sync_fixtures_task() -> dict:
    return _run(run_fixture_sync())


@celery_app.task(name="prediqo.predictions.generate")
def generate_predictions_task() -> dict:
    return _run(run_prediction_generation())


@celery_app.task(name="prediqo.predictions.settle")
def settle_predictions_task() -> dict:
    return _run(run_settlement())


@celery_app.task(name="prediqo.notifications.generate")
def generate_notifications_task() -> dict:
    return _run(run_notification_generation())


__all__ = [
    "sync_fixtures_task",
    "generate_predictions_task",
    "settle_predictions_task",
    "generate_notifications_task",
]
