"""Poisson goal model with Dixon-Coles low-score correction."""

import math
from dataclasses import dataclass, field

MAX_GOALS = 10
HOME_ADVANTAGE = 0.15


@dataclass(frozen=True)
class GoalDistribution:
    matrix: list[list[float]]
    home_lambda: float
    away_lambda: float
    rho: float

    @property
    def home_win(self) -> float:
        return sum(
            self.matrix[i][j] for i in range(MAX_GOALS + 1) for j in range(MAX_GOALS + 1) if i > j
        )

    @property
    def draw(self) -> float:
        return sum(self.matrix[i][i] for i in range(MAX_GOALS + 1))

    @property
    def away_win(self) -> float:
        return sum(
            self.matrix[i][j] for i in range(MAX_GOALS + 1) for j in range(MAX_GOALS + 1) if i < j
        )

    def over_under(self, line: float) -> tuple[float, float]:
        over = sum(
            prob
            for i in range(MAX_GOALS + 1)
            for j in range(MAX_GOALS + 1)
            if i + j > line
            for prob in [self.matrix[i][j]]
        )
        return over, 1.0 - over

    @property
    def btts(self) -> tuple[float, float]:
        yes = sum(
            self.matrix[i][j] for i in range(1, MAX_GOALS + 1) for j in range(1, MAX_GOALS + 1)
        )
        return yes, 1.0 - yes

    def correct_scores(self, top_n: int = 8) -> dict[str, float]:
        scores = {
            f"{i}-{j}": self.matrix[i][j]
            for i in range(MAX_GOALS + 1)
            for j in range(MAX_GOALS + 1)
        }
        return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n])


@dataclass
class TeamStrength:
    attack: float = 0.0
    defense: float = 0.0


@dataclass
class MatchInputs:
    home: TeamStrength = field(default_factory=TeamStrength)
    away: TeamStrength = field(default_factory=TeamStrength)
    league_average_goals: float = 1.35
    home_advantage: float = HOME_ADVANTAGE
    rho: float = -0.08


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def estimate_lambdas(inputs: MatchInputs) -> tuple[float, float]:
    home_lambda = inputs.league_average_goals * math.exp(
        inputs.home_advantage + inputs.home.attack - inputs.away.defense
    )
    away_lambda = inputs.league_average_goals * math.exp(inputs.away.attack - inputs.home.defense)
    return min(max(home_lambda, 0.05), 12.0), min(max(away_lambda, 0.05), 12.0)


def goal_distribution(inputs: MatchInputs) -> GoalDistribution:
    """Build a normalised score matrix (sum of all entries == 1)."""
    home_lambda, away_lambda = estimate_lambdas(inputs)
    matrix = [
        [_poisson_pmf(i, home_lambda) * _poisson_pmf(j, away_lambda) for j in range(MAX_GOALS + 1)]
        for i in range(MAX_GOALS + 1)
    ]

    rho = inputs.rho
    matrix[0][0] *= 1 - home_lambda * away_lambda * rho
    matrix[0][1] *= 1 + home_lambda * rho
    matrix[1][0] *= 1 + away_lambda * rho
    matrix[1][1] *= 1 - rho

    total = sum(sum(row) for row in matrix)
    if total <= 0:
        raise ValueError("Invalid goal distribution: non-positive normalisation.")
    matrix = [[value / total for value in row] for row in matrix]
    return GoalDistribution(matrix, home_lambda, away_lambda, rho)


def to_basis_points(probabilities: dict[str, float]) -> dict[str, int]:
    """Largest-remainder rounding so values sum to exactly 10,000."""
    scaled = {key: max(value, 0.0) * 10000 for key, value in probabilities.items()}
    floors = {key: int(math.floor(value)) for key, value in scaled.items()}
    remainder = 10000 - sum(floors.values())
    order = sorted(scaled, key=lambda key: scaled[key] - floors[key], reverse=True)
    for i in range(max(remainder, 0)):
        floors[order[i % len(order)]] += 1
    return floors
