"""Token store and VIP subscription endpoints."""

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.models.identity import User
from app.models.monetization import SubscriptionPlan, TokenPackage
from app.schemas.monetization import (
    PlanOut,
    PurchaseResultOut,
    PurchaseVerifyIn,
    SubscriptionStatusOut,
    TokenBalanceOut,
    TokenPackageOut,
    TokenTransactionOut,
    UnlockIn,
    UnlockOut,
)
from app.services.subscription_service import (
    current_status,
    ensure_plans,
    sync_vip_role,
    verify_subscription,
)
from app.services.token_purchase_service import ensure_packages, verify_token_purchase
from app.services.token_service import (
    debit_tokens,
    get_or_create_account,
    transactions_for,
)

router = APIRouter(tags=["monetization"])


@router.get("/tokens/balance", response_model=TokenBalanceOut)
async def token_balance(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TokenBalanceOut:
    account = await get_or_create_account(session, user.id)
    await session.commit()
    recent = await transactions_for(session, user.id, limit=5)
    return TokenBalanceOut(
        balance=account.balance,
        recent_transactions=[
            {
                "id": str(item.id),
                "type": item.type,
                "amount": item.amount,
                "balance_after": item.balance_after,
                "reason": item.reason,
            }
            for item in recent
        ],
    )


@router.get("/tokens/packages", response_model=list[TokenPackageOut])
async def token_packages(
    session: AsyncSession = Depends(get_session),
) -> list[TokenPackageOut]:
    await ensure_packages(session)
    await session.commit()
    rows = (
        await session.execute(select(TokenPackage).where(TokenPackage.active.is_(True)))
    ).scalars()
    return [TokenPackageOut.model_validate(row) for row in rows]


@router.get("/tokens/transactions", response_model=list[TokenTransactionOut])
async def token_transactions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TokenTransactionOut]:
    rows = await transactions_for(session, user.id, limit=100)
    return [TokenTransactionOut.model_validate(row) for row in rows]


@router.post("/tokens/purchases/verify", response_model=PurchaseResultOut)
async def verify_purchase(
    payload: PurchaseVerifyIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PurchaseResultOut:
    result = await verify_token_purchase(session, user, payload.product_id, payload.purchase_token)
    return PurchaseResultOut(**result.__dict__)


@router.post("/tokens/unlock", response_model=UnlockOut)
async def unlock_report(
    payload: UnlockIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UnlockOut:
    """VIP entitlement wins: a VIP user is never charged tokens."""
    is_vip = await sync_vip_role(session, user)
    if is_vip:
        account = await get_or_create_account(session, user.id)
        await session.commit()
        return UnlockOut(unlocked=True, entitlement="vip", balance=account.balance)

    transaction = await debit_tokens(
        session,
        user.id,
        settings.token_unlock_cost,
        "UNLOCK_FULL_REPORT",
        idempotency_key=f"unlock:{user.id}:{payload.target_type}:{payload.target_id}",
        reference_type=payload.target_type,
        reference_id=payload.target_id,
    )
    await session.commit()
    return UnlockOut(
        unlocked=True,
        entitlement="token",
        balance=transaction.balance_after,
    )


@router.get("/subscriptions/plans", response_model=list[PlanOut])
async def subscription_plans(
    session: AsyncSession = Depends(get_session),
) -> list[PlanOut]:
    await ensure_plans(session)
    await session.commit()
    rows = (
        await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.active.is_(True)))
    ).scalars()
    return [PlanOut.model_validate(row) for row in rows]


@router.get("/subscriptions/status", response_model=SubscriptionStatusOut)
async def subscription_status(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionStatusOut:
    status = await current_status(session, user)
    return SubscriptionStatusOut(**status.__dict__)


@router.post("/subscriptions/verify", response_model=SubscriptionStatusOut)
async def verify_subscription_endpoint(
    payload: PurchaseVerifyIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionStatusOut:
    status = await verify_subscription(session, user, payload.product_id, payload.purchase_token)
    return SubscriptionStatusOut(**status.__dict__)
