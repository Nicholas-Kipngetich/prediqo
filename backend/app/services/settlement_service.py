"""Prediction settlement with explicit rules for void and rescheduled matches."""

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictions import (
    Prediction,
    PredictionMarket,
    PredictionSettlement,
    PredictionStatus,
)
from app.models.sports import Fixture

VOID_STATUSES = {"POSTPONED", "CANCELLED", "CANC", "ABD", "ABANDONED"}


@dataclass
class SettlementResult:
    settled: int = 0
    voided: int = 0
    skipped: int = 0


def _actual_outcome(market: str, home_score: int, away_score: int, published: dict) -> str:
    if market == "1X2":
        if home_score > away_score:
            return "home"
        if home_score == away_score:
            return "draw"
        return "away"
    if market == "OU25":
        return "over" if home_score + away_score > 2.5 else "under"
    if market == "BTTS":
        return "yes" if home_score > 0 and away_score > 0 else "no"
    if market == "CS":
        score = f"{home_score}-{away_score}"
        return score if score in published else "other"
    return "unknown"


async def settle_predictions(session: AsyncSession) -> SettlementResult:
    result = SettlementResult()
    rows = (
        await session.execute(
            select(Prediction, Fixture, PredictionMarket.code)
            .join(Fixture, Fixture.id == Prediction.fixture_id)
            .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
            .where(Prediction.status == PredictionStatus.PENDING)
        )
    ).all()

    already_settled = {
        row for row in (await session.execute(select(PredictionSettlement.prediction_id))).scalars()
    }

    for prediction, fixture, market_code in rows:
        if prediction.id in already_settled:
            result.skipped += 1
            continue

        if fixture.status in VOID_STATUSES:
            status = PredictionStatus.VOID
            actual = None
            result.voided += 1
        elif (
            fixture.status == "FINISHED"
            and fixture.home_score is not None
            and fixture.away_score is not None
        ):
            try:
                published = json.loads(prediction.probabilities_json)
            except (ValueError, TypeError):
                published = {}
            actual = _actual_outcome(
                market_code,
                int(fixture.home_score),
                int(fixture.away_score),
                published,
            )
            status = (
                PredictionStatus.CORRECT
                if prediction.selected_outcome == actual
                else PredictionStatus.INCORRECT
            )
            result.settled += 1
        else:
            result.skipped += 1
            continue

        session.add(
            PredictionSettlement(
                prediction_id=prediction.id,
                result=status,
                actual_outcome=actual,
                source="fixture_result",
            )
        )
        prediction.status = status

    await session.commit()
    return result
