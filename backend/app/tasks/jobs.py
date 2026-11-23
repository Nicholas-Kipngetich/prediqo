"""Async job bodies used by Celery tasks.

Each job owns its own database session, so it can run outside a request context.
"""

from app.core.database import get_session_factory
from app.services.notification_service import create_upcoming_fixture_notifications
from app.services.prediction_service import generate_predictions
from app.services.settlement_service import settle_predictions
from app.services.sync_service import sync_sports_data


async def run_fixture_sync() -> dict:
    async with get_session_factory()() as session:
        result = await sync_sports_data(session)
        return result.__dict__


async def run_prediction_generation() -> dict:
    async with get_session_factory()() as session:
        result = await generate_predictions(session)
        return result.__dict__


async def run_settlement() -> dict:
    async with get_session_factory()() as session:
        result = await settle_predictions(session)
        return result.__dict__


async def run_notification_generation() -> dict:
    async with get_session_factory()() as session:
        created = await create_upcoming_fixture_notifications(session)
        return {"created": created}
