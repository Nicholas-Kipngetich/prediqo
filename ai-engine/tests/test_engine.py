from datetime import UTC, datetime, timedelta

from prediqo_ai.elo import MatchResult, build_elo_state, win_probabilities
from prediqo_ai.ensemble import combine_1x2, publish_market
from prediqo_ai.evaluation import brier_score, log_loss, probability_vector_is_valid
from prediqo_ai.features import attack_defense, build_features
from prediqo_ai.poisson import MatchInputs, TeamStrength, goal_distribution, to_basis_points


def test_poisson_distribution_normalises_and_derives_markets():
    distribution = goal_distribution(MatchInputs())
    total = sum(sum(row) for row in distribution.matrix)
    assert abs(total - 1.0) < 1e-9
    one_x_two = distribution.home_win + distribution.draw + distribution.away_win
    assert abs(one_x_two - 1.0) < 1e-9
    over, under = distribution.over_under(2.5)
    assert abs(over + under - 1.0) < 1e-9
    btts, no_btts = distribution.btts
    assert abs(btts + no_btts - 1.0) < 1e-9


def test_basis_points_sum_to_ten_thousand():
    result = to_basis_points({"home": 0.4, "draw": 0.3, "away": 0.3})
    assert sum(result.values()) == 10000


def test_elo_updates_and_ordering():
    now = datetime.now(UTC)
    results = [
        MatchResult("A", "B", 2, 0, now - timedelta(days=2)),
        MatchResult("A", "B", 0, 1, now - timedelta(days=1)),
    ]
    state = build_elo_state(results)
    # A won the first match but lost the second by a larger expected margin.
    assert state.rating("A") < 1500
    assert state.rating("B") > 1500
    probabilities = win_probabilities(state, "A", "B")
    assert abs(sum(probabilities) - 1.0) < 1e-9


def test_features_exclude_future_data():
    now = datetime.now(UTC)
    kickoff = now
    results = [
        MatchResult("A", "C", 1, 0, now - timedelta(days=10)),
        MatchResult("A", "C", 2, 1, now - timedelta(days=5)),
        MatchResult("A", "C", 5, 0, now + timedelta(days=1)),
    ]
    state = build_elo_state(results)
    features = build_features(results, "A", "C", kickoff, state)
    assert features.home_sample_size == 2
    assert features.league_average_goals > 0
    home, away = attack_defense(features)
    assert isinstance(home, TeamStrength)
    assert isinstance(away, TeamStrength)


def test_ensemble_and_publication():
    elo = {"home": 0.5, "draw": 0.25, "away": 0.25}
    poisson = {"home": 0.4, "draw": 0.3, "away": 0.3}
    blended = combine_1x2(poisson, elo, weight_poisson=0.6)
    assert probability_vector_is_valid(blended)
    published = publish_market("1X2", blended, "test-v1")
    assert sum(published.probabilities_bp.values()) == 10000
    assert published.model_version == "test-v1"


def test_metrics():
    assert brier_score([0.8, 0.2], [1, 0]) < 0.1
    assert log_loss([0.9, 0.1], [1, 0]) < 0.2
