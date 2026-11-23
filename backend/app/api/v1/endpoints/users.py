"""Current-user profile endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.identity import User, UserStatus
from app.schemas.user import UserOut, UserUpdateIn, user_to_out

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def read_me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    await session.refresh(user, attribute_names=["profile", "roles"])
    return user_to_out(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdateIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    fields = payload.model_dump(exclude_unset=True)
    profile_fields = {"timezone", "locale", "theme", "onboarding_completed"}
    for key, value in fields.items():
        if value is None:
            continue
        if key in profile_fields and user.profile:
            setattr(user.profile, key, value)
        elif key == "display_name":
            user.display_name = value
    await session.commit()
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user_to_out(user)


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Soft-delete the account. Prediction records are retained pseudonymously."""
    user.status = UserStatus.DELETED
    user.deleted_at = datetime.now(UTC)
    user.email = None
    user.display_name = None
    await session.commit()
    return {"status": "deletion_requested"}
