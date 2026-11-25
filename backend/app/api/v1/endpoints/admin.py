"""Administration endpoints (foundation for Phase 2 and Phase 9)."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.core.errors import NotFoundError
from app.models.identity import Role, User, UserStatus
from app.models.monetization import AuditLog, Subscription, SubscriptionPlan, TokenPackage
from app.models.predictions import ModelVersion, Prediction, PredictionMarket
from app.models.sports import SyncJob
from app.schemas.sports import SyncResultOut
from app.schemas.user import UserOut, user_to_out
from app.services.audit_service import log_action
from app.services.subscription_service import ensure_plans
from app.services.sync_service import sync_sports_data
from app.services.token_purchase_service import ensure_packages

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminDashboardOut(BaseModel):
    total_users: int
    active_users: int
    admin_users: int


@router.get("/ping")
async def admin_ping(user: User = Depends(require_admin)) -> dict[str, str]:
    return {"status": "ok", "user_id": str(user.id)}


@router.get("/users", response_model=list[UserOut])
async def list_users(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[UserOut]:
    users = (await session.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    result = []
    for user in users:
        await session.refresh(user, attribute_names=["profile", "roles"])
        for role in user.roles:
            await session.refresh(role, attribute_names=["permissions"])
        result.append(user_to_out(user))
    return result


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user_to_out(user)


@router.post("/users/{user_id}/suspend", response_model=UserOut)
async def suspend_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    user.status = UserStatus.SUSPENDED
    await session.flush()
    await log_action(
        session,
        "ADMIN_SUSPEND_USER",
        admin.id,
        "user",
        str(user.id),
        {"status": user.status},
    )
    await session.commit()
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user_to_out(user)


@router.post("/users/{user_id}/unsuspend", response_model=UserOut)
async def unsuspend_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    user.status = UserStatus.ACTIVE
    await session.flush()
    await log_action(
        session,
        "ADMIN_UNSUSPEND_USER",
        admin.id,
        "user",
        str(user.id),
        {"status": user.status},
    )
    await session.commit()
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user_to_out(user)


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    await session.delete(user)
    await session.flush()
    await log_action(session, "ADMIN_DELETE_USER", admin.id, "user", str(user.id))
    await session.commit()
    return {"status": "ok"}


class PredictionOverrideIn(BaseModel):
    status: str | None = None
    selected_outcome: str | None = None


@router.patch("/predictions/{prediction_id}")
async def admin_override_prediction(
    prediction_id: UUID,
    payload: PredictionOverrideIn,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    prediction = await session.get(Prediction, prediction_id)
    if prediction is None:
        raise NotFoundError("Prediction not found.")
    changes = {}
    if payload.status is not None:
        prediction.status = payload.status.upper()
        changes["status"] = prediction.status
    if payload.selected_outcome is not None:
        prediction.selected_outcome = payload.selected_outcome
        changes["selected_outcome"] = prediction.selected_outcome
    await session.flush()
    await log_action(
        session,
        "ADMIN_OVERRIDE_PREDICTION",
        admin.id,
        "prediction",
        str(prediction.id),
        changes,
    )
    await session.commit()
    return {
        "id": str(prediction.id),
        "status": prediction.status,
        "selected_outcome": prediction.selected_outcome,
    }


@router.post("/sync/trigger", response_model=SyncResultOut)
async def trigger_sync(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> SyncResultOut:
    result = await sync_sports_data(session)
    await log_action(
        session,
        "ADMIN_SYNC_TRIGGERED",
        admin.id,
        "sync_job",
        details=result.__dict__,
    )
    await session.commit()
    return SyncResultOut(**result.__dict__)


@router.get("/sync/jobs")
async def list_sync_jobs(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    jobs = (
        (await session.execute(select(SyncJob).order_by(SyncJob.started_at.desc()))).scalars().all()
    )
    return [
        {
            "id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "records_processed": job.records_processed,
            "error_text": job.error_text,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }
        for job in jobs
    ]


@router.get("/dashboard", response_model=AdminDashboardOut)
async def dashboard(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminDashboardOut:
    total = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    active = (
        await session.execute(select(func.count()).select_from(User).where(User.status == "ACTIVE"))
    ).scalar_one()
    admins = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .join(User.roles)
            .where(Role.code.in_(["ADMIN", "SUPER_ADMIN"]))
        )
    ).scalar_one()
    return AdminDashboardOut(total_users=total, active_users=active, admin_users=admins)


@router.get("/predictions")
async def admin_predictions(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    rows = (
        await session.execute(
            select(Prediction, PredictionMarket.code, ModelVersion.version)
            .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
            .join(ModelVersion, ModelVersion.id == Prediction.model_version_id)
            .order_by(Prediction.published_at.desc())
            .limit(100)
        )
    ).all()
    return [
        {
            "id": str(prediction.id),
            "fixture_id": str(prediction.fixture_id),
            "market": code,
            "model_version": version,
            "status": prediction.status,
            "selected_outcome": prediction.selected_outcome,
            "is_sample_data": prediction.is_sample_data,
        }
        for prediction, code, version in rows
    ]


@router.get("/token-packages")
async def admin_token_packages(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    await ensure_packages(session)
    await session.commit()
    rows = (await session.execute(select(TokenPackage))).scalars().all()
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "tokens": row.tokens,
            "price_minor": row.price_minor,
            "currency": row.currency,
            "active": row.active,
        }
        for row in rows
    ]


@router.get("/subscription-plans")
async def admin_subscription_plans(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    await ensure_plans(session)
    await session.commit()
    rows = (await session.execute(select(SubscriptionPlan))).scalars().all()
    return [
        {
            "id": str(row.id),
            "code": row.code,
            "interval": row.interval,
            "price_minor": row.price_minor,
            "currency": row.currency,
            "active": row.active,
        }
        for row in rows
    ]


@router.get("/system/health")
async def admin_system_health(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.main import _db_status, _redis_status

    users = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    predictions = (await session.execute(select(func.count()).select_from(Prediction))).scalar_one()
    jobs = (await session.execute(select(func.count()).select_from(SyncJob))).scalar_one()
    return {
        "api": "ok",
        "db": await _db_status(),
        "redis": await _redis_status(),
        "users": users,
        "predictions": predictions,
        "sync_jobs": jobs,
    }


@router.get("/revenue")
async def admin_revenue(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.models.monetization import TokenTransaction, TransactionType

    token_credits = (
        await session.execute(
            select(func.coalesce(func.sum(TokenTransaction.amount), 0)).where(
                TokenTransaction.type == TransactionType.CREDIT
            )
        )
    ).scalar_one()
    token_debits = (
        await session.execute(
            select(func.coalesce(func.sum(TokenTransaction.amount), 0)).where(
                TokenTransaction.type == TransactionType.DEBIT
            )
        )
    ).scalar_one()
    total_users = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    active_subscriptions = (
        await session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.status.in_(["ACTIVE", "GRACE"]))
        )
    ).scalar_one()
    return {
        "token_credits_total": int(token_credits),
        "token_debits_total": int(token_debits),
        "total_users": total_users,
        "active_subscriptions": active_subscriptions,
    }


@router.get("/audit-logs")
async def admin_audit_logs(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    rows = (
        (await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)))
        .scalars()
        .all()
    )
    return [
        {
            "id": str(row.id),
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
