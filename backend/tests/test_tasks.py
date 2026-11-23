"""Background automation tests."""

import pytest

from app.core.celery_app import celery_app
from app.tasks import (
    generate_notifications_task,
    generate_predictions_task,
    settle_predictions_task,
    sync_fixtures_task,
)
from app.tasks.jobs import (
    run_fixture_sync,
    run_notification_generation,
    run_prediction_generation,
    run_settlement,
)


@pytest.mark.asyncio
async def test_job_bodies_run_without_request_context():
    sync = await run_fixture_sync()
    assert sync["fixtures"] == 28

    generation = await run_prediction_generation()
    assert generation["published"] == 28

    settlement = await run_settlement()
    assert "settled" in settlement

    notifications = await run_notification_generation()
    assert "created" in notifications


def test_celery_tasks_and_beat_schedule_are_registered():
    for name in (
        "prediqo.sync.fixtures",
        "prediqo.predictions.generate",
        "prediqo.predictions.settle",
        "prediqo.notifications.generate",
    ):
        assert name in celery_app.tasks

    schedule_names = {entry["task"] for entry in celery_app.conf.beat_schedule.values()}
    assert schedule_names == {
        "prediqo.sync.fixtures",
        "prediqo.predictions.generate",
        "prediqo.predictions.settle",
        "prediqo.notifications.generate",
    }


def test_task_wrappers_are_celery_tasks():
    assert all(
        task.name is not None
        for task in (
            sync_fixtures_task,
            generate_predictions_task,
            settle_predictions_task,
            generate_notifications_task,
        )
    )
