"""Notification creation, deduplication, preferences and FCM delivery."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundError
from app.models.communications import (
    DeviceToken,
    Notification,
    NotificationPreference,
    NotificationType,
)
from app.models.identity import User
from app.models.sports import Fixture


async def ensure_preferences(session: AsyncSession, user_id) -> NotificationPreference:
    prefs = await session.get(NotificationPreference, user_id)
    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        session.add(prefs)
        await session.flush()
    return prefs


async def register_device(
    session: AsyncSession, user_id, fcm_token: str, platform: str = "android"
) -> DeviceToken:
    existing = (
        await session.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == user_id, DeviceToken.fcm_token == fcm_token
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.active = True
        existing.platform = platform
        await session.commit()
        return existing
    token = DeviceToken(user_id=user_id, fcm_token=fcm_token, platform=platform, active=True)
    session.add(token)
    await session.commit()
    return token


async def create_notification(
    session: AsyncSession,
    user_id,
    notification_type: str,
    title: str,
    body: str,
    dedupe_key: str,
    deep_link: str | None = None,
    send: bool = True,
) -> Notification:
    existing = (
        await session.execute(select(Notification).where(Notification.dedupe_key == dedupe_key))
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        deep_link=deep_link,
        dedupe_key=dedupe_key,
        status="PENDING",
    )
    session.add(notification)
    await session.flush()
    if send:
        await deliver_notification(session, notification)
    return notification


async def deliver_notification(session: AsyncSession, notification: Notification) -> None:
    """Send via FCM. In dev mode, delivery is simulated and recorded."""
    dev_mode = settings.environment == "development" and settings.auth_mode == "dev"
    if dev_mode:
        notification.status = "SENT"
        notification.sent_at = datetime.now(UTC)
        await session.flush()
        return

    tokens = (
        (
            await session.execute(
                select(DeviceToken.fcm_token).where(
                    DeviceToken.user_id == notification.user_id, DeviceToken.active.is_(True)
                )
            )
        )
        .scalars()
        .all()
    )
    if not tokens:
        notification.status = "SKIPPED"
        await session.flush()
        return

    def _send() -> None:
        import firebase_admin
        from firebase_admin import messaging

        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=notification.title, body=notification.body),
            data={"type": notification.type, "deep_link": notification.deep_link or ""},
            tokens=list(tokens),
        )
        messaging.send_multicast(message)

    try:
        import asyncio

        await asyncio.to_thread(_send)
        notification.status = "SENT"
        notification.sent_at = datetime.now(UTC)
    except Exception:
        notification.status = "FAILED"
    await session.flush()


async def list_notifications(session: AsyncSession, user_id, limit: int = 50) -> list[Notification]:
    await ensure_preferences(session, user_id)
    return list(
        (
            await session.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
        ).scalars()
    )


async def mark_read(session: AsyncSession, user_id, notification_id) -> Notification:
    notification = await session.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotFoundError("Notification not found.")
    notification.read_at = datetime.now(UTC)
    await session.commit()
    return notification


async def create_upcoming_fixture_notifications(session: AsyncSession) -> int:
    """Create one deduplicated reminder per user per upcoming fixture."""
    now = datetime.now(UTC)
    fixtures = (
        (await session.execute(select(Fixture).where(Fixture.status == "SCHEDULED")))
        .scalars()
        .all()
    )
    fixtures = [
        fixture
        for fixture in fixtures
        if now
        <= (
            fixture.kickoff_utc.replace(tzinfo=UTC)
            if fixture.kickoff_utc.tzinfo is None
            else fixture.kickoff_utc
        )
        <= now + timedelta(hours=24)
    ]
    users = (await session.execute(select(User))).scalars().all()
    for user in users:
        await ensure_preferences(session, user.id)
    prefs = (await session.execute(select(NotificationPreference))).scalars().all()
    count = 0
    for pref in prefs:
        if not pref.upcoming_fixture:
            continue
        for fixture in fixtures:
            key = f"fixture:{fixture.id}:user:{pref.user_id}"
            exists = (
                await session.execute(select(Notification.id).where(Notification.dedupe_key == key))
            ).first()
            await create_notification(
                session,
                pref.user_id,
                NotificationType.UPCOMING_FIXTURE,
                "Match starting soon",
                f"Kickoff at {fixture.kickoff_utc.isoformat()}",
                dedupe_key=key,
                deep_link=f"/matches/{fixture.id}",
                send=False,
            )
            if exists is None:
                count += 1
    await session.commit()
    return count
