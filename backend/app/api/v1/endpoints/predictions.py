"""Prediction feed endpoints."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.deps import require_admin
from app.core.database import get_session
from app.core.errors import NotFoundError
from app.models.identity import User
from app.models.predictions import ModelVersion, Prediction, PredictionMarket, PredictionSettlement
from app.models.sports import Competition, Fixture, Team
from app.schemas.predictions import GenerationResultOut, PredictionOut
from app.services.prediction_service import GenerationResult, generate_predictions
from app.services.settlement_service import SettlementResult, settle_predictions

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _to_out(
    row,
    market_code: str,
    model_version: str,
    fixture=None,
    competition=None,
    home_team=None,
    away_team=None,
    settlement=None,
) -> PredictionOut:
    try:
        probabilities = json.loads(row.probabilities_json)
    except (ValueError, TypeError):
        probabilities = {}
    try:
        explanation = json.loads(row.explanation_json)
    except (ValueError, TypeError):
        explanation = {}
    fixture_label = None
    kickoff = None
    competition_name = None
    if fixture is not None:
        kickoff = fixture.kickoff_utc
        if home_team is not None and away_team is not None:
            fixture_label = f"{home_team.name} vs {away_team.name}"
    if competition is not None:
        competition_name = competition.name
    return PredictionOut(
        id=row.id,
        fixture_id=row.fixture_id,
        fixture_label=fixture_label,
        competition_name=competition_name,
        kickoff_utc=kickoff,
        market=market_code,
        model_version=model_version,
        probabilities_bp=probabilities,
        selected_outcome=row.selected_outcome,
        status=row.status,
        published_at=row.published_at,
        data_as_of=row.data_as_of,
        actual_outcome=getattr(settlement, "actual_outcome", None),
        settled_at=getattr(settlement, "settled_at", None),
        is_sample_data=row.is_sample_data,
        explanation=explanation,
    )


@router.get("", response_model=list[PredictionOut])
async def list_predictions(
    market: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[PredictionOut]:
    home_team = aliased(Team)
    away_team = aliased(Team)
    query = (
        select(
            Prediction,
            PredictionMarket.code,
            ModelVersion.version,
            Fixture,
            Competition,
            home_team,
            away_team,
            PredictionSettlement,
        )
        .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
        .join(ModelVersion, ModelVersion.id == Prediction.model_version_id)
        .join(Fixture, Fixture.id == Prediction.fixture_id)
        .join(Competition, Competition.id == Fixture.competition_id)
        .join(home_team, home_team.id == Fixture.home_team_id)
        .join(away_team, away_team.id == Fixture.away_team_id)
        .outerjoin(
            PredictionSettlement,
            PredictionSettlement.prediction_id == Prediction.id,
        )
        .order_by(Prediction.published_at.desc())
        .limit(limit)
    )
    if market:
        query = query.where(PredictionMarket.code == market.upper())
    if status:
        query = query.where(Prediction.status == status.upper())
    rows = (await session.execute(query)).all()
    return [
        _to_out(row, code, version, fixture, competition, home, away, settlement)
        for row, code, version, fixture, competition, home, away, settlement in rows
    ]


@router.get("/history", response_model=list[PredictionOut])
async def prediction_history(
    market: str | None = None,
    status: str | None = None,
    competition_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[PredictionOut]:
    from uuid import UUID

    home_team = aliased(Team)
    away_team = aliased(Team)
    query = (
        select(
            Prediction,
            PredictionMarket.code,
            ModelVersion.version,
            Fixture,
            Competition,
            home_team,
            away_team,
            PredictionSettlement,
        )
        .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
        .join(ModelVersion, ModelVersion.id == Prediction.model_version_id)
        .join(Fixture, Fixture.id == Prediction.fixture_id)
        .join(Competition, Competition.id == Fixture.competition_id)
        .join(home_team, home_team.id == Fixture.home_team_id)
        .join(away_team, away_team.id == Fixture.away_team_id)
        .outerjoin(
            PredictionSettlement,
            PredictionSettlement.prediction_id == Prediction.id,
        )
        .order_by(Prediction.published_at.desc())
        .limit(limit)
    )
    if market:
        query = query.where(PredictionMarket.code == market.upper())
    if status:
        query = query.where(Prediction.status == status.upper())
    if competition_id:
        query = query.where(Fixture.competition_id == UUID(competition_id))
    if date_from:
        query = query.where(Prediction.published_at >= date_from)
    if date_to:
        query = query.where(Prediction.published_at <= date_to)
    rows = (await session.execute(query)).all()
    return [
        _to_out(row, code, version, fixture, competition, home, away, settlement)
        for row, code, version, fixture, competition, home, away, settlement in rows
    ]


@router.get("/{prediction_id}", response_model=PredictionOut)
async def get_prediction(
    prediction_id: str,
    session: AsyncSession = Depends(get_session),
) -> PredictionOut:
    from uuid import UUID

    home_team = aliased(Team)
    away_team = aliased(Team)
    row = (
        await session.execute(
            select(
                Prediction,
                PredictionMarket.code,
                ModelVersion.version,
                Fixture,
                Competition,
                home_team,
                away_team,
                PredictionSettlement,
            )
            .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
            .join(ModelVersion, ModelVersion.id == Prediction.model_version_id)
            .join(Fixture, Fixture.id == Prediction.fixture_id)
            .join(Competition, Competition.id == Fixture.competition_id)
            .join(home_team, home_team.id == Fixture.home_team_id)
            .join(away_team, away_team.id == Fixture.away_team_id)
            .outerjoin(
                PredictionSettlement,
                PredictionSettlement.prediction_id == Prediction.id,
            )
            .where(Prediction.id == UUID(prediction_id))
        )
    ).first()
    if row is None:
        raise NotFoundError("Prediction not found.")
    prediction, code, version, fixture, competition, home, away, settlement = row
    return _to_out(prediction, code, version, fixture, competition, home, away, settlement)


@router.post("/generate", response_model=GenerationResultOut)
async def generate(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> GenerationResultOut:
    result: GenerationResult = await generate_predictions(session)
    return GenerationResultOut(**result.__dict__)


@router.post("/settle")
async def settle(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> SettlementResult:
    return await settle_predictions(session)
