"""Administration endpoints (foundation for Phase 2 and Phase 9)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.models.identity import Role, User
from app.models.monetization import AuditLog, SubscriptionPlan, TokenPackage
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
