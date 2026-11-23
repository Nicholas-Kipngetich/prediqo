"""Administration endpoints (foundation for Phase 2 and Phase 9)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.models.identity import User
from app.models.sports import SyncJob
from app.schemas.sports import SyncResultOut
from app.schemas.user import UserOut, user_to_out
from app.services.sync_service import sync_sports_data

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
        await session.execute(select(func.count()).select_from(User).where(User.status == "ADMIN"))
    ).scalar_one()
    return AdminDashboardOut(total_users=total, active_users=active, admin_users=admins)
