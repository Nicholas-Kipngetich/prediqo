"""As-of feature builder. Only data available before kickoff is used."""

from dataclasses import dataclass
from datetime import datetime

from prediqo_ai.elo import EloState, MatchResult

MIN_MATCHES_PER_TEAM = 5


@dataclass(frozen=True)
class TeamForm:
    matches: int
    goals_for: float
    goals_against: float
    recent_goals_for: float
    recent_goals_against: float
    points_per_match: float

    @property
    def has_sample(self) -> bool:
        return self.matches > 0


@dataclass(frozen=True)
class MatchFeatures:
    home_form: TeamForm
    away_form: TeamForm
    home_elo: float
    away_elo: float
    rest_days_home: int | None
    rest_days_away: int | None
    league_average_goals: float
    home_sample_size: int
    away_sample_size: int

    @property
    def data_quality_ok(self) -> bool:
        return (
            self.home_sample_size >= MIN_MATCHES_PER_TEAM
            and self.away_sample_size >= MIN_MATCHES_PER_TEAM
            and self.home_form.has_sample
            and self.away_form.has_sample
            and self.league_average_goals > 0
        )


def _team_form(results: list[MatchResult], team: str) -> TeamForm:
    played = [
        result
        for result in sorted(results, key=lambda item: item.played_at)
        if result.home == team or result.away == team
    ]
    if not played:
        return TeamForm(0, 0.0, 0.0, 0.0, 0.0, 0.0)

    goals_for = 0
    goals_against = 0
    points = 0.0
    for match in played:
        if match.home == team:
            gf, ga = match.home_goals, match.away_goals
        else:
            gf, ga = match.away_goals, match.home_goals
        goals_for += gf
        goals_against += ga
        if gf > ga:
            points += 3
        elif gf == ga:
            points += 1

    recent = played[-5:]
    recent_gf = sum((m.home_goals if m.home == team else m.away_goals) for m in recent)
    recent_ga = sum((m.away_goals if m.home == team else m.home_goals) for m in recent)
    count = len(played)
    return TeamForm(
        matches=count,
        goals_for=goals_for / count,
        goals_against=goals_against / count,
        recent_goals_for=recent_gf / len(recent),
        recent_goals_against=recent_ga / len(recent),
        points_per_match=points / count,
    )


def build_features(
    results: list[MatchResult],
    home: str,
    away: str,
    kickoff: datetime,
    elo_state: EloState,
) -> MatchFeatures:
    """Build features from results strictly before the kickoff timestamp."""
    prior = [result for result in results if result.played_at < kickoff]
    home_form = _team_form(prior, home)
    away_form = _team_form(prior, away)

    all_goals = [result.home_goals + result.away_goals for result in prior]
    league_average = sum(all_goals) / (2 * len(all_goals)) if all_goals else 0.0

    home_matches = [m for m in prior if home in (m.home, m.away)]
    away_matches = [m for m in prior if away in (m.home, m.away)]
    rest_home = (kickoff - home_matches[-1].played_at).days if home_matches else None
    rest_away = (kickoff - away_matches[-1].played_at).days if away_matches else None

    return MatchFeatures(
        home_form=home_form,
        away_form=away_form,
        home_elo=elo_state.rating(home),
        away_elo=elo_state.rating(away),
        rest_days_home=rest_home,
        rest_days_away=rest_away,
        league_average_goals=league_average,
        home_sample_size=home_form.matches,
        away_sample_size=away_form.matches,
    )


def attack_defense(features: MatchFeatures) -> tuple:
    """Convert form and league average into Poisson strength parameters."""
    from prediqo_ai.poisson import TeamStrength

    baseline = features.league_average_goals or 1.35
    home = TeamStrength(
        attack=features.home_form.recent_goals_for / baseline - 1,
        defense=features.home_form.recent_goals_against / baseline - 1,
    )
    away = TeamStrength(
        attack=features.away_form.recent_goals_for / baseline - 1,
        defense=features.away_form.recent_goals_against / baseline - 1,
    )
    return home, away
