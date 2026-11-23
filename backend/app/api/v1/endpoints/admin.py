"""Administration endpoints (foundation for Phase 2 and Phase 9)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.models.identity import User
from app.schemas.user import UserOut, user_to_out

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
