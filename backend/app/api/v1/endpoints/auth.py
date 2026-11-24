"""Authentication verification endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.identity import User
from app.schemas.user import UserOut, user_to_out
from app.services import dev_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class DevAuthIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class DevTokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserOut


@router.post("/register", response_model=DevTokenOut)
async def dev_register(
    payload: DevAuthIn,
    session: AsyncSession = Depends(get_session),
) -> DevTokenOut:
    if "@" not in payload.email:
        from app.core.errors import ConflictError

        raise ConflictError("A valid email address is required.")
    user, token = await dev_auth_service.register(
        session, payload.email, payload.password, payload.display_name
    )
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return DevTokenOut(
        access_token=token,
        user=user_to_out(user),
    )


@router.post("/login", response_model=DevTokenOut)
async def dev_login(
    payload: DevAuthIn,
    session: AsyncSession = Depends(get_session),
) -> DevTokenOut:
    user, token = await dev_auth_service.login(session, payload.email, payload.password)
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return DevTokenOut(
        access_token=token,
        user=user_to_out(user),
    )


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
