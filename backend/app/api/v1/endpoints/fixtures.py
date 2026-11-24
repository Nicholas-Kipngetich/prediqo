"""Fixture discovery endpoints."""

import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import get_current_user
from app.core.database import get_session
from app.core.errors import NotFoundError
from app.models.identity import User
from app.models.predictions import Prediction, PredictionMarket
from app.models.sports import Competition, Fixture, Team
from app.schemas.sports import (
    AnalysisOut,
    CompetitionOut,
    FixtureOut,
    Page,
    SearchOut,
    TeamOut,
)
from app.services.analysis_service import check_analysis_access

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


@router.get("/fixtures/{fixture_id}/analysis", response_model=AnalysisOut)
async def get_fixture_analysis(
    fixture_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisOut:
    fixture = await session.get(Fixture, UUID(fixture_id))
    if fixture is None:
        raise NotFoundError("Fixture not found.")

    entitlement = await check_analysis_access(session, user, fixture.id)
    competition = await session.get(Competition, fixture.competition_id)
    home = await session.get(Team, fixture.home_team_id)
    away = await session.get(Team, fixture.away_team_id)
    if not (competition and home and away):
        raise NotFoundError("Fixture references missing data.")

    rows = (
        await session.execute(
            select(Prediction, PredictionMarket.code, PredictionMarket.name)
            .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
            .where(Prediction.fixture_id == fixture.id)
            .order_by(Prediction.published_at.desc())
        )
    ).all()

    markets: dict[str, dict] = {}
    snapshot: dict = {}
    explanation: dict = {}
    data_as_of = None
    for prediction, code, name in rows:
        if code not in markets:
            markets[code] = {
                "name": name,
                "probabilities_bp": json.loads(prediction.probabilities_json),
                "selected_outcome": prediction.selected_outcome,
                "published_at": prediction.published_at.isoformat(),
            }
            if not snapshot:
                snapshot = json.loads(prediction.snapshot_json)
                explanation = json.loads(prediction.explanation_json)
                data_as_of = prediction.data_as_of

    return AnalysisOut(
        fixture_id=fixture.id,
        competition=CompetitionOut.model_validate(competition),
        home_team=TeamOut.model_validate(home),
        away_team=TeamOut.model_validate(away),
        kickoff_utc=fixture.kickoff_utc,
        status=fixture.status,
        is_sample_data=fixture.is_sample_data,
        entitlement=entitlement,
        data_as_of=data_as_of,
        expected_home_goals=snapshot.get("expected_home_goals"),
        expected_away_goals=snapshot.get("expected_away_goals"),
        markets=markets,
        explanation=explanation,
    )


@router.get("/search", response_model=SearchOut)
async def search(
    q: str = Query(..., min_length=2, max_length=80),
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> SearchOut:
    pattern = f"%{q}%"
    competitions = (
        (
            await session.execute(
                select(Competition).where(Competition.name.ilike(pattern)).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    teams = (
        (
            await session.execute(
                select(Team)
                .where(Team.name.ilike(pattern) | Team.short_name.ilike(pattern))
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    home_team = aliased(Team)
    away_team = aliased(Team)
    fixture_rows = (
        await session.execute(
            select(Fixture, Competition, home_team, away_team)
            .join(Competition, Competition.id == Fixture.competition_id)
            .join(home_team, home_team.id == Fixture.home_team_id)
            .join(away_team, away_team.id == Fixture.away_team_id)
            .where(
                or_(
                    Competition.name.ilike(pattern),
                    home_team.name.ilike(pattern),
                    away_team.name.ilike(pattern),
                )
            )
            .order_by(Fixture.kickoff_utc)
            .limit(limit)
        )
    ).all()
    fixtures = []
    for fixture, competition, home, away in fixture_rows:
        fixtures.append(_fixture_to_out(fixture, competition, home, away))

    return SearchOut(
        competitions=[CompetitionOut.model_validate(row) for row in competitions],
        teams=[TeamOut.model_validate(row) for row in teams],
        fixtures=fixtures,
    )


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
