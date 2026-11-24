"""Pydantic response schemas for users."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.services.user_service import permission_codes


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timezone: str
    locale: str
    theme: str
    onboarding_completed: bool


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None = None
    display_name: str | None = None
    status: str
    created_at: datetime
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    is_vip: bool = False
    profile: ProfileOut | None = None


class FavoritesOut(BaseModel):
    team_ids: list[str] = Field(default_factory=list)
    competition_ids: list[str] = Field(default_factory=list)


class FavoritesIn(BaseModel):
    ids: list[str] = Field(default_factory=list)


class UserUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)
    theme: str | None = Field(default=None, max_length=16)
    onboarding_completed: bool | None = None


def user_to_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=user.status,
        created_at=user.created_at,
        roles=sorted(user.role_codes),
        permissions=sorted(permission_codes(user)),
        is_vip=user.is_vip,
        profile=ProfileOut.model_validate(user.profile) if user.profile else None,
    )
