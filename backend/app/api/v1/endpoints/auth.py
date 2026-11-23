"""Authentication verification endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.identity import User
from app.schemas.user import UserOut, user_to_out

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify", response_model=UserOut)
async def verify_token(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    """Verify a Firebase ID token and return the provisioned user profile."""
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user_to_out(user)


@router.get("/permissions", response_model=list[str])
async def my_permissions(user: User = Depends(get_current_user)) -> list[str]:
    from app.services.user_service import permission_codes

    return sorted(permission_codes(user))
