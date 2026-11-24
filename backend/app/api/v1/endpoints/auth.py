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


class IdentifierIn(BaseModel):
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    confirm_password: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class VerifyCodeIn(BaseModel):
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)
    code: str = Field(min_length=4, max_length=12)


class ResendCodeIn(BaseModel):
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=32)


class DevTokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserOut


class RegistrationOut(BaseModel):
    user: UserOut
    verification_required: bool = True
    verification_code: str | None = None
    message: str


@router.post("/register", response_model=RegistrationOut)
async def dev_register(
    payload: IdentifierIn,
    session: AsyncSession = Depends(get_session),
) -> RegistrationOut:
    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        from app.core.errors import ConflictError

        raise ConflictError("Passwords do not match.")
    user, code = await dev_auth_service.register(
        session,
        payload.email,
        payload.phone,
        payload.password,
        payload.display_name,
    )
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return RegistrationOut(
        user=user_to_out(user),
        verification_code=code if dev_auth_service._dev_mode() else None,
        message="Account created. Enter the verification code to continue.",
    )


@router.post("/verify-code", response_model=DevTokenOut)
async def dev_verify_code(
    payload: VerifyCodeIn,
    session: AsyncSession = Depends(get_session),
) -> DevTokenOut:
    user, token = await dev_auth_service.verify_code(
        session, payload.email, payload.phone, payload.code
    )
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return DevTokenOut(access_token=token, user=user_to_out(user))


@router.post("/resend-code")
async def dev_resend_code(
    payload: ResendCodeIn,
    session: AsyncSession = Depends(get_session),
) -> dict:
    code = await dev_auth_service.resend_code(session, payload.email, payload.phone)
    return {
        "message": "Verification code sent.",
        "verification_code": code if dev_auth_service._dev_mode() else None,
    }


@router.post("/login", response_model=DevTokenOut)
async def dev_login(
    payload: IdentifierIn,
    session: AsyncSession = Depends(get_session),
) -> DevTokenOut:
    user, token = await dev_auth_service.login(
        session, payload.email, payload.phone, payload.password
    )
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return DevTokenOut(access_token=token, user=user_to_out(user))


@router.post("/verify", response_model=UserOut)
async def verify_token(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    """Verify a Firebase or development token and return the profile."""
    await session.refresh(user, attribute_names=["profile", "roles"])
    for role in user.roles:
        await session.refresh(role, attribute_names=["permissions"])
    return user_to_out(user)


@router.get("/permissions", response_model=list[str])
async def my_permissions(user: User = Depends(get_current_user)) -> list[str]:
    from app.services.user_service import permission_codes

    return sorted(permission_codes(user))
