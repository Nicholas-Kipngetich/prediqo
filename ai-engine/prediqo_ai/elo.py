"""Football Elo ratings with home advantage and margin-of-victory scaling."""

from dataclasses import dataclass, field
from datetime import datetime

DEFAULT_RATING = 1500.0
HOME_ADVANTAGE = 65.0
K_FACTOR = 24.0


@dataclass(frozen=True)
class MatchResult:
    home: str
    away: str
    home_goals: int
    away_goals: int
    played_at: datetime


@dataclass
class EloState:
    ratings: dict[str, float] = field(default_factory=dict)
    matches: dict[str, int] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.ratings.get(team, DEFAULT_RATING)

    def apply(self, result: MatchResult) -> None:
        home_rating = self.rating(result.home)
        away_rating = self.rating(result.away)
        expected_home = 1.0 / (1.0 + 10 ** (-(home_rating + HOME_ADVANTAGE - away_rating) / 400))
        actual_home = (
            1.0
            if result.home_goals > result.away_goals
            else (0.5 if result.home_goals == result.away_goals else 0.0)
        )
        margin = abs(result.home_goals - result.away_goals)
        multiplier = 1.0 + 0.25 * (margin - 1) if margin > 1 else 1.0
        delta = K_FACTOR * multiplier * (actual_home - expected_home)

        self.ratings[result.home] = home_rating + delta
        self.ratings[result.away] = away_rating - delta
        self.matches[result.home] = self.matches.get(result.home, 0) + 1
        self.matches[result.away] = self.matches.get(result.away, 0) + 1


def build_elo_state(results: list[MatchResult]) -> EloState:
    """Apply results chronologically. Caller must sort by played_at."""
    state = EloState()
    for result in sorted(results, key=lambda item: item.played_at):
        state.apply(result)
    return state


def win_probabilities(
    state: EloState,
    home: str,
    away: str,
    draw_probability: float = 0.26,
) -> tuple[float, float, float]:
    """Convert an Elo difference into 1X2 probabilities with a fixed draw prior."""
    diff = state.rating(home) + HOME_ADVANTAGE - state.rating(away)
    home_conditional = 1.0 / (1.0 + 10 ** (-diff / 400))
    decisive = 1.0 - draw_probability
    return (
        decisive * home_conditional,
        draw_probability,
        decisive * (1.0 - home_conditional),
    )
