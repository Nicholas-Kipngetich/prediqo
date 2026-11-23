"""Performance analytics computed from settled predictions only."""

import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictions import Prediction, PredictionMarket, PredictionStatus
from app.models.sports import Competition, Fixture


@dataclass
class Overview:
    total_predictions: int
    settled_predictions: int
    correct: int
    incorrect: int
    pending: int
    void: int
    accuracy: float | None
    sample_size: int


@dataclass
class BreakdownRow:
    dimension: str
    key: str
    total: int
    correct: int
    accuracy: float | None


@dataclass
class CalibrationBin:
    bin: int
    count: int
    mean_probability: float
    observed_rate: float


def _probabilities(prediction: Prediction) -> dict[str, int]:
    try:
        return json.loads(prediction.probabilities_json)
    except (ValueError, TypeError):
        return {}


async def _rows(session: AsyncSession) -> Sequence[Row]:
    result = await session.execute(
        select(Prediction, PredictionMarket.code, Competition.name)
        .join(PredictionMarket, PredictionMarket.id == Prediction.market_id)
        .join(Fixture, Fixture.id == Prediction.fixture_id)
        .join(Competition, Competition.id == Fixture.competition_id)
    )
    return result.all()


async def overview(session: AsyncSession) -> Overview:
    rows = await _rows(session)
    statuses = [prediction.status for prediction, _, _ in rows]
    correct = statuses.count(PredictionStatus.CORRECT)
    incorrect = statuses.count(PredictionStatus.INCORRECT)
    settled = correct + incorrect
    decided = settled
    return Overview(
        total_predictions=len(rows),
        settled_predictions=settled,
        correct=correct,
        incorrect=incorrect,
        pending=statuses.count(PredictionStatus.PENDING),
        void=statuses.count(PredictionStatus.VOID),
        accuracy=correct / decided if decided else None,
        sample_size=decided,
    )


async def breakdown(session: AsyncSession) -> list[BreakdownRow]:
    rows = await _rows(session)
    by_market: dict[str, list[bool]] = defaultdict(list)
    by_competition: dict[str, list[bool]] = defaultdict(list)
    for prediction, market_code, competition_name in rows:
        if prediction.status not in {PredictionStatus.CORRECT, PredictionStatus.INCORRECT}:
            continue
        outcome = prediction.status == PredictionStatus.CORRECT
        by_market[market_code].append(outcome)
        by_competition[competition_name].append(outcome)

    result: list[BreakdownRow] = []
    for dimension, groups in (("market", by_market), ("competition", by_competition)):
        for key, outcomes in groups.items():
            correct = sum(outcomes)
            result.append(
                BreakdownRow(
                    dimension=dimension,
                    key=key,
                    total=len(outcomes),
                    correct=correct,
                    accuracy=correct / len(outcomes),
                )
            )
    return result


async def calibration(session: AsyncSession, bins: int = 10) -> list[CalibrationBin]:
    rows = await _rows(session)
    pairs: list[tuple[float, bool]] = []
    for prediction, _, _ in rows:
        if prediction.status not in {PredictionStatus.CORRECT, PredictionStatus.INCORRECT}:
            continue
        probabilities = _probabilities(prediction)
        predicted = probabilities.get(prediction.selected_outcome, 0) / 10000
        pairs.append((predicted, prediction.status == PredictionStatus.CORRECT))

    result: list[CalibrationBin] = []
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [
            (p, correct)
            for p, correct in pairs
            if low <= p < high or (index == bins - 1 and p == 1.0)
        ]
        if not members:
            continue
        result.append(
            CalibrationBin(
                bin=index,
                count=len(members),
                mean_probability=sum(p for p, _ in members) / len(members),
                observed_rate=sum(c for _, c in members) / len(members),
            )
        )
    return result
