"""Subscription entitlement synchronisation.

VIP access is derived from an active server-verified subscription, never from a
client-side flag.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.identity import Role, RoleCode, User
from app.models.monetization import (
    Subscription,
    SubscriptionEvent,
    SubscriptionPlan,
    SubscriptionStatus,
)
from app.services.billing_service import VerifiedPurchase, get_purchase_verifier


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite drops timezone info; normalise before comparisons."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


@dataclass
class SubscriptionStatusOut:
    is_vip: bool
    status: str | None
    expires_at: datetime | None
    plan_code: str | None


async def ensure_plans(session: AsyncSession) -> None:
    existing = {row.code for row in (await session.execute(select(SubscriptionPlan))).scalars()}
    for code, interval, price, product_id in [
        ("VIP_MONTHLY", "MONTHLY", 49900, "com.prediqo.vip.monthly"),
        ("VIP_ANNUAL", "ANNUAL", 499000, "com.prediqo.vip.annual"),
    ]:
        if code not in existing:
            session.add(
                SubscriptionPlan(
                    code=code,
                    interval=interval,
                    price_minor=price,
                    currency="KES",
                    google_play_product_id=product_id,
                    entitlements_json=json.dumps(
                        ["predictions:premium:read", "analysis:premium:read"]
                    ),
                    active=True,
                )
            )
    await session.flush()


async def active_subscription(session: AsyncSession, user_id) -> Subscription | None:
    return (
        (
            await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.GRACE]),
                )
            )
        )
        .scalars()
        .first()
    )


async def sync_vip_role(session: AsyncSession, user: User) -> bool:
    """Grant or revoke VIP_USER to match the current subscription state."""
    subscription = await active_subscription(session, user.id)
    expiry = _as_utc(subscription.expires_at) if subscription else None
    vip_active = bool(subscription and (expiry is None or expiry > datetime.now(UTC)))
    vip_role = (
        await session.execute(select(Role).where(Role.code == RoleCode.VIP_USER))
    ).scalar_one_or_none()
    if vip_role is None:
        session.add(Role(code=RoleCode.VIP_USER, description="Active VIP subscriber"))
        await session.flush()
        vip_role = (
            await session.execute(select(Role).where(Role.code == RoleCode.VIP_USER))
        ).scalar_one()
    await session.refresh(user, attribute_names=["roles"])
    has_vip = any(role.code == RoleCode.VIP_USER for role in user.roles)
    if vip_active and not has_vip:
        user.roles.append(vip_role)
    elif not vip_active and has_vip:
        user.roles = [role for role in user.roles if role.code != RoleCode.VIP_USER]
    await session.flush()
    return vip_active


async def verify_subscription(
    session: AsyncSession, user: User, product_id: str, purchase_token: str
) -> SubscriptionStatusOut:
    await ensure_plans(session)
    plan = (
        await session.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.google_play_product_id == product_id,
                SubscriptionPlan.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if plan is None:
        raise ConflictError("Unknown subscription product.")

    verified: VerifiedPurchase = await get_purchase_verifier().verify(
        product_id, purchase_token, subscription=True
    )
    existing = (
        await session.execute(
            select(Subscription).where(Subscription.purchase_token == purchase_token)
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            purchase_token=purchase_token,
            status=SubscriptionStatus.ACTIVE,
            expires_at=verified.expires_at,
            auto_renew=True,
        )
        session.add(existing)
        await session.flush()
    else:
        existing.expires_at = verified.expires_at
        existing.status = SubscriptionStatus.ACTIVE

    event_key = f"subscription-verify:{purchase_token}"
    event_exists = (
        await session.execute(
            select(SubscriptionEvent).where(SubscriptionEvent.idempotency_key == event_key)
        )
    ).scalar_one_or_none()
    if event_exists is None:
        session.add(
            SubscriptionEvent(
                subscription_id=existing.id,
                type="VERIFIED",
                payload_json=json.dumps({"order_id": verified.order_id}),
                idempotency_key=event_key,
                processed_at=datetime.now(UTC),
            )
        )

    vip_active = await sync_vip_role(session, user)
    await session.commit()
    return SubscriptionStatusOut(
        is_vip=vip_active,
        status=existing.status,
        expires_at=_as_utc(existing.expires_at),
        plan_code=plan.code,
    )


async def current_status(session: AsyncSession, user: User) -> SubscriptionStatusOut:
    subscription = await active_subscription(session, user.id)
    vip_active = await sync_vip_role(session, user)
    await session.commit()
    return SubscriptionStatusOut(
        is_vip=vip_active,
        status=subscription.status if subscription else None,
        expires_at=_as_utc(subscription.expires_at) if subscription else None,
        plan_code=None,
    )
