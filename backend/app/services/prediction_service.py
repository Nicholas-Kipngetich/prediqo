"""Publish predictions from validated statistical models.

Predictions are immutable. Low data quality suppresses publication entirely.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from prediqo_ai.elo import MatchResult, build_elo_state, win_probabilities
from prediqo_ai.ensemble import combine_1x2, publish_market
from prediqo_ai.features import attack_defense, build_features
from prediqo_ai.poisson import MatchInputs, goal_distribution
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictions import (
    ModelVersion,
    ModelVersionStatus,
    Prediction,
    PredictionMarket,
    PredictionStatus,
)
from app.models.sports import Fixture, FixtureStatus


@dataclass
class GenerationResult:
    published: int = 0
    skipped: int = 0
    suppressed: int = 0


async def _ensure_model_seed(session: AsyncSession) -> None:
    """Create the champion model and markets when the DB was built from metadata."""
    champion = (
        await session.execute(
            select(ModelVersion).where(ModelVersion.status == ModelVersionStatus.CHAMPION)
        )
    ).scalar_one_or_none()
    if champion is None:
        session.add(
            ModelVersion(
                name="poisson-elo-ensemble",
                version="v1.0.0",
                feature_version="v1",
                status=ModelVersionStatus.CHAMPION,
                metrics_json=json.dumps({"validation": "pending"}),
            )
        )
    existing_markets = {
        row.code for row in (await session.execute(select(PredictionMarket))).scalars()
    }
    for code, name, group in [
        ("1X2", "Match Result", "result"),
        ("OU25", "Over/Under 2.5 Goals", "goals"),
        ("BTTS", "Both Teams to Score", "goals"),
        ("CS", "Correct Score", "goals"),
    ]:
        if code not in existing_markets:
            session.add(PredictionMarket(code=code, name=name, market_group=group, active=True))
    await session.flush()


async def generate_predictions(session: AsyncSession) -> GenerationResult:
    result = GenerationResult()
    await _ensure_model_seed(session)
    model = (
        await session.execute(
            select(ModelVersion).where(ModelVersion.status == ModelVersionStatus.CHAMPION)
        )
    ).scalar_one_or_none()
    if model is None:
        raise RuntimeError("No champion model version is available.")

    markets = {row.code: row for row in (await session.execute(select(PredictionMarket))).scalars()}
    required = {"1X2", "OU25", "BTTS", "CS"}
    if not required.issubset(markets):
        raise RuntimeError("Required prediction markets are not seeded.")

    finished = (
        (
            await session.execute(
                select(Fixture).where(
                    Fixture.status == FixtureStatus.FINISHED,
                    Fixture.home_score.is_not(None),
                    Fixture.away_score.is_not(None),
                )
            )
        )
        .scalars()
        .all()
    )
    match_results = [
        MatchResult(
            home=str(fixture.home_team_id),
            away=str(fixture.away_team_id),
            home_goals=int(fixture.home_score or 0),
            away_goals=int(fixture.away_score or 0),
            played_at=fixture.kickoff_utc,
        )
        for fixture in finished
    ]
    elo_state = build_elo_state(match_results)
    data_as_of = max((item.played_at for item in match_results), default=datetime.now(UTC))

    upcoming = (
        (
            await session.execute(
                select(Fixture)
                .where(Fixture.status == FixtureStatus.SCHEDULED)
                .order_by(Fixture.kickoff_utc)
            )
        )
        .scalars()
        .all()
    )

    existing = {
        tuple(row)
        for row in (
            await session.execute(
                select(Prediction.fixture_id, Prediction.market_id).where(
                    Prediction.model_version_id == model.id
                )
            )
        ).all()
    }

    for fixture in upcoming:
        home, away = str(fixture.home_team_id), str(fixture.away_team_id)
        features = build_features(match_results, home, away, fixture.kickoff_utc, elo_state)
        if not features.data_quality_ok:
            result.suppressed += 1
            continue
        if any((fixture.id, markets[code].id) in existing for code in required):
            result.skipped += 1
            continue

        home_strength, away_strength = attack_defense(features)
        distribution = goal_distribution(
            MatchInputs(
                home=home_strength,
                away=away_strength,
                league_average_goals=features.league_average_goals,
            )
        )
        elo_values = win_probabilities(elo_state, home, away)
        poisson_values = {
            "home": distribution.home_win,
            "draw": distribution.draw,
            "away": distribution.away_win,
        }
        elo_values_by_key = dict(zip(("home", "draw", "away"), elo_values, strict=True))
        one_x_two = combine_1x2(poisson_values, elo_values_by_key)
        over, under = distribution.over_under(2.5)
        btts, no_btts = distribution.btts
        correct_scores = distribution.correct_scores(top_n=8)
        other = max(0.0, 1.0 - sum(correct_scores.values()))
        correct_scores["other"] = other

        market_probabilities = {
            "1X2": one_x_two,
            "OU25": {"over": over, "under": under},
            "BTTS": {"yes": btts, "no": no_btts},
            "CS": correct_scores,
        }

        explanation = {
            "type": "deterministic_v1",
            "facts": [
                f"elo_home={features.home_elo:.0f}",
                f"elo_away={features.away_elo:.0f}",
                f"home_recent_xg_proxy={features.home_form.recent_goals_for:.2f}",
                f"away_recent_xg_proxy={features.away_form.recent_goals_for:.2f}",
                f"home_matches={features.home_sample_size}",
                f"away_matches={features.away_sample_size}",
                "corners_data_unavailable",
            ],
        }
        snapshot = {
            "model_version": model.version,
            "feature_version": model.feature_version,
            "data_as_of": data_as_of.isoformat(),
            "fixture_id": str(fixture.id),
            "kickoff_utc": fixture.kickoff_utc.isoformat(),
            "expected_home_goals": distribution.home_lambda,
            "expected_away_goals": distribution.away_lambda,
            "is_sample_data": fixture.is_sample_data,
        }

        for code, probabilities in market_probabilities.items():
            published = publish_market(code, probabilities, model.version, features.data_quality_ok)
            session.add(
                Prediction(
                    fixture_id=fixture.id,
                    market_id=markets[code].id,
                    model_version_id=model.id,
                    published_at=datetime.now(UTC),
                    data_as_of=data_as_of,
                    probabilities_json=json.dumps(published.probabilities_bp),
                    selected_outcome=published.selected_outcome,
                    status=PredictionStatus.PENDING,
                    snapshot_json=json.dumps(snapshot),
                    explanation_json=json.dumps(explanation),
                    is_sample_data=fixture.is_sample_data,
                )
            )
            existing.add((fixture.id, markets[code].id))
            result.published += 1

    await session.commit()
    return result
