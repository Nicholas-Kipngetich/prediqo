"""Daily analysis quota enforcement with VIP and token entitlement bypass."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import EntitlementError
from app.models.access import AnalysisAccess
from app.models.identity import User
from app.models.monetization import TokenTransaction, TransactionType
from app.services.subscription_service import sync_vip_role


async def check_analysis_access(session: AsyncSession, user: User, fixture_id) -> str:
    """Return the entitlement used ('vip', 'token', 'free') or raise."""
    if await sync_vip_role(session, user):
        return "vip"

    unlocked = (
        await session.execute(
            select(TokenTransaction.id).where(
                TokenTransaction.account_id == user.id,
                TokenTransaction.type == TransactionType.DEBIT,
                TokenTransaction.reason == "UNLOCK_FULL_REPORT",
                TokenTransaction.reference_type == "analysis",
                TokenTransaction.reference_id == str(fixture_id),
            )
        )
    ).first()
    if unlocked is not None:
        return "token"

    today = datetime.now(UTC).date()
    already = (
        await session.execute(
            select(AnalysisAccess.id).where(
                AnalysisAccess.user_id == user.id,
                AnalysisAccess.fixture_id == fixture_id,
                AnalysisAccess.accessed_date == today,
            )
        )
    ).first()
    if already is not None:
        return "free"

    used = (
        await session.execute(
            select(func.count())
            .select_from(AnalysisAccess)
            .where(
                AnalysisAccess.user_id == user.id,
                AnalysisAccess.accessed_date == today,
            )
        )
    ).scalar_one()
    if used >= settings.free_daily_analysis:
        raise EntitlementError(
            "Daily free analysis limit reached. Upgrade to VIP or unlock with tokens.",
            details={
                "free_daily_analysis": settings.free_daily_analysis,
                "used_today": used,
            },
        )

    session.add(
        AnalysisAccess(
            user_id=user.id,
            fixture_id=fixture_id,
            accessed_date=today,
        )
    )
    await session.commit()
    return "free"
