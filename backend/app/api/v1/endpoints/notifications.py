"""Notification endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_session
from app.models.identity import User
from app.schemas.notifications import (
    DeviceTokenIn,
    NotificationOut,
    PreferencesIn,
    PreferencesOut,
)
from app.services.notification_service import (
    create_notification,
    create_upcoming_fixture_notifications,
    ensure_preferences,
    list_notifications,
    mark_read,
    register_device,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def get_notifications(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[NotificationOut]:
    rows = await list_notifications(session, user.id)
    return [NotificationOut.model_validate(row) for row in rows]


@router.get("/preferences", response_model=PreferencesOut)
async def get_preferences(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PreferencesOut:
    prefs = await ensure_preferences(session, user.id)
    await session.commit()
    return PreferencesOut.model_validate(prefs)


@router.patch("/preferences", response_model=PreferencesOut)
async def update_preferences(
    payload: PreferencesIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PreferencesOut:
    prefs = await ensure_preferences(session, user.id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)
    await session.commit()
    return PreferencesOut.model_validate(prefs)


@router.post("/device-token")
async def register_device_token(
    payload: DeviceTokenIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    token = await register_device(session, user.id, payload.fcm_token, payload.platform)
    return {"status": "registered", "platform": token.platform}


@router.post("/test", response_model=NotificationOut)
async def create_test_notification(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> NotificationOut:
    notification = await create_notification(
        session,
        user.id,
        "TEST",
        "Prediqo test notification",
        "Notifications are working.",
        dedupe_key=f"test:{user.id}",
        deep_link="/home",
    )
    await session.commit()
    return NotificationOut.model_validate(notification)


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def read_notification(
    notification_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> NotificationOut:
    from uuid import UUID

    notification = await mark_read(session, user.id, UUID(notification_id))
    return NotificationOut.model_validate(notification)


@router.post("/admin/generate")
async def generate_notifications(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    created = await create_upcoming_fixture_notifications(session)
    return {"created": created}
