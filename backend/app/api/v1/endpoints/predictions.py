"""Prediction feed endpoints."""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.core.errors import NotFoundError
from app.models.identity import User
from app.models.predictions import ModelVersion, Prediction, PredictionMarket
from app.schemas.predictions import GenerationResultOut, PredictionOut
from app.services.prediction_service import GenerationResult, generate_predictions
from app.services.settlement_service import SettlementResult, settle_predictions

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _to_out(row, market_code: str, model_version: str) -> PredictionOut:
    try:
        probabilities = json.loads(row.probabilities_json)
    except (ValueError, TypeError):
        probabilities = {}
    try:
        explanation = json.loads(row.explanation_json)
    except (ValueError, TypeError):
        explanation = {}
    return PredictionOut(
        id=row.id,
        fixture_id=row.fixture_id,
        market=market_code,
        model_version=model_version,
        probabilities_bp=probabilities,
        selected_outcome=row.selected_outcome,
        status=row.status,
        published_at=row.published_at,
        data_as_of=row.data_as_of,
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
    query = (
        select(Prediction, PredictionMarket.code, ModelVersion.version)
        .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
        .join(ModelVersion, ModelVersion.id == Prediction.model_version_id)
        .order_by(Prediction.published_at.desc())
        .limit(limit)
    )
    if market:
        query = query.where(PredictionMarket.code == market.upper())
    if status:
        query = query.where(Prediction.status == status.upper())
    rows = (await session.execute(query)).all()
    return [_to_out(row, code, version) for row, code, version in rows]


@router.get("/{prediction_id}", response_model=PredictionOut)
async def get_prediction(
    prediction_id: str,
    session: AsyncSession = Depends(get_session),
) -> PredictionOut:
    from uuid import UUID

    row = (
        await session.execute(
            select(Prediction, PredictionMarket.code, ModelVersion.version)
            .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
            .join(ModelVersion, ModelVersion.id == Prediction.model_version_id)
            .where(Prediction.id == UUID(prediction_id))
        )
    ).first()
    if row is None:
        raise NotFoundError("Prediction not found.")
    prediction, code, version = row
    return _to_out(prediction, code, version)


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
