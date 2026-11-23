"""Audit logging for sensitive administrative operations."""

import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monetization import AuditLog


async def log_action(
    session: AsyncSession,
    action: str,
    actor_user_id: UUID | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details_json=json.dumps(details) if details else None,
        )
    )
    await session.flush()
