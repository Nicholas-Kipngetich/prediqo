"""Fixture discovery endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.sports import Competition, Fixture, Team
from app.schemas.sports import CompetitionOut, FixtureOut, Page, TeamOut

router = APIRouter(tags=["fixtures"])


def _fixture_to_out(
    fixture: Fixture, competition: Competition, home: Team, away: Team
) -> FixtureOut:
    return FixtureOut(
        id=fixture.id,
        competition=CompetitionOut.model_validate(competition),
        home_team=TeamOut.model_validate(home),
        away_team=TeamOut.model_validate(away),
        kickoff_utc=fixture.kickoff_utc,
        status=fixture.status,
        venue=fixture.venue,
        home_score=fixture.home_score,
        away_score=fixture.away_score,
        is_sample_data=fixture.is_sample_data,
        last_synced_at=fixture.last_synced_at,
    )


@router.get("/competitions", response_model=list[CompetitionOut])
async def list_competitions(session: AsyncSession = Depends(get_session)) -> list[CompetitionOut]:
    rows = (await session.execute(select(Competition).order_by(Competition.name))).scalars().all()
    return [CompetitionOut.model_validate(row) for row in rows]


@router.get("/teams", response_model=list[TeamOut])
async def list_teams(
    competition_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[TeamOut]:
    query = select(Team)
    if competition_id:
        query = query.join(Fixture, Fixture.home_team_id == Team.id).where(
            Fixture.competition_id == competition_id
        )
    rows = (await session.execute(query.distinct().order_by(Team.name))).scalars().all()
    return [TeamOut.model_validate(row) for row in rows]


@router.get("/fixtures", response_model=Page[FixtureOut])
async def list_fixtures(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: str | None = None,
    competition_id: str | None = None,
    team_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> Page[FixtureOut]:
    query = select(Fixture)
    if date_from:
        query = query.where(Fixture.kickoff_utc >= date_from)
    if date_to:
        query = query.where(Fixture.kickoff_utc <= date_to)
    if status:
        query = query.where(Fixture.status == status.upper())
    if competition_id:
        query = query.where(Fixture.competition_id == UUID(competition_id))
    if team_id:
        parsed_team_id = UUID(team_id)
        query = query.where(
            (Fixture.home_team_id == parsed_team_id) | (Fixture.away_team_id == parsed_team_id)
        )

    total = (await session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (
        (
            await session.execute(
                query.order_by(Fixture.kickoff_utc).offset((page - 1) * page_size).limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    items = []
    for fixture in rows:
        competition = await session.get(Competition, fixture.competition_id)
        home = await session.get(Team, fixture.home_team_id)
        away = await session.get(Team, fixture.away_team_id)
        if competition and home and away:
            items.append(_fixture_to_out(fixture, competition, home, away))
    return Page(items=items, page=page, page_size=page_size, total=total)


@router.get("/fixtures/trending", response_model=Page[FixtureOut])
async def trending_fixtures(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> Page[FixtureOut]:
    """Trending is based only on real fixture data: upcoming kickoffs and tier.

    No fabricated popularity numbers. This is not prediction confidence.
    """
    query = (
        select(Fixture)
        .join(Competition, Competition.id == Fixture.competition_id)
        .where(Fixture.status == "SCHEDULED", Fixture.kickoff_utc >= datetime.now(UTC))
        .order_by(Competition.tier.asc().nullslast(), Fixture.kickoff_utc.asc())
    )
    total = (await session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (
        (await session.execute(query.offset((page - 1) * page_size).limit(page_size)))
        .scalars()
        .all()
    )
    items = []
    for fixture in rows:
        competition = await session.get(Competition, fixture.competition_id)
        home = await session.get(Team, fixture.home_team_id)
        away = await session.get(Team, fixture.away_team_id)
        if competition and home and away:
            items.append(_fixture_to_out(fixture, competition, home, away))
    return Page(items=items, page=page, page_size=page_size, total=total)


@router.get("/fixtures/{fixture_id}", response_model=FixtureOut)
async def get_fixture(
    fixture_id: str,
    session: AsyncSession = Depends(get_session),
) -> FixtureOut:
    fixture = await session.get(Fixture, UUID(fixture_id))
    if fixture is None:
        from app.core.errors import NotFoundError

        raise NotFoundError("Fixture not found.")
    competition = await session.get(Competition, fixture.competition_id)
    home = await session.get(Team, fixture.home_team_id)
    away = await session.get(Team, fixture.away_team_id)
    if not (competition and home and away):
        from app.core.errors import NotFoundError

        raise NotFoundError("Fixture references missing data.")
    return _fixture_to_out(fixture, competition, home, away)
