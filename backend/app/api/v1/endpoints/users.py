"""Current-user profile endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.identity import User, UserStatus
from app.models.sports import (
    Competition,
    Team,
    competition_favorites,
    team_favorites,
)
from app.schemas.user import FavoritesIn, FavoritesOut, UserOut, UserUpdateIn, user_to_out

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


@router.get("/me/favorites", response_model=FavoritesOut)
async def get_favorites(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FavoritesOut:
    team_ids = (
        (
            await session.execute(
                select(team_favorites.c.team_id).where(team_favorites.c.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    competition_ids = (
        (
            await session.execute(
                select(competition_favorites.c.competition_id).where(
                    competition_favorites.c.user_id == user.id
                )
            )
        )
        .scalars()
        .all()
    )
    return FavoritesOut(
        team_ids=[str(item) for item in team_ids],
        competition_ids=[str(item) for item in competition_ids],
    )


@router.put("/me/favorites/teams", response_model=FavoritesOut)
async def set_favorite_teams(
    payload: FavoritesIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FavoritesOut:
    parsed = []
    for item in payload.ids:
        try:
            parsed.append(UUID(item))
        except ValueError:
            continue
    valid = (
        set((await session.execute(select(Team.id).where(Team.id.in_(parsed)))).scalars().all())
        if parsed
        else set()
    )
    await session.execute(team_favorites.delete().where(team_favorites.c.user_id == user.id))
    for team_id in valid:
        await session.execute(team_favorites.insert().values(user_id=user.id, team_id=team_id))
    await session.commit()
    return await get_favorites(user, session)


@router.put("/me/favorites/competitions", response_model=FavoritesOut)
async def set_favorite_competitions(
    payload: FavoritesIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FavoritesOut:
    parsed = []
    for item in payload.ids:
        try:
            parsed.append(UUID(item))
        except ValueError:
            continue
    valid = (
        set(
            (await session.execute(select(Competition.id).where(Competition.id.in_(parsed))))
            .scalars()
            .all()
        )
        if parsed
        else set()
    )
    await session.execute(
        competition_favorites.delete().where(competition_favorites.c.user_id == user.id)
    )
    for competition_id in valid:
        await session.execute(
            competition_favorites.insert().values(user_id=user.id, competition_id=competition_id)
        )
    await session.commit()
    return await get_favorites(user, session)


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
