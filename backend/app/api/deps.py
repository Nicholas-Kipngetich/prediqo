"""Shared FastAPI dependencies for authentication and authorisation."""

from collections.abc import Callable

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_token_verifier
from app.core.database import get_session
from app.core.errors import ForbiddenError, UnauthorizedError
from app.models.identity import RoleCode, User
from app.services.user_service import permission_codes, upsert_user


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("A Bearer token is required.")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise UnauthorizedError("A Bearer token is required.")
    context = await get_token_verifier().verify(token)
    return await upsert_user(session, context)


def require_roles(*allowed: str) -> Callable[..., object]:
    allowed_set = set(allowed)

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if not allowed_set.intersection(user.role_codes):
            raise ForbiddenError("Your role does not grant access to this resource.")
        return user

    return dependency


def require_permission(code: str) -> Callable[..., object]:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if code not in permission_codes(user):
            raise ForbiddenError("Your account lacks the required permission.")
        return user

    return dependency


def require_admin(
    user: User = Depends(require_roles(RoleCode.ADMIN, RoleCode.SUPER_ADMIN)),
) -> User:
    return user
