"""Provider-agnostic data contracts.

All external data is normalised into these structures before it reaches the database.
Missing fields stay None — they are never invented.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class CompetitionData:
    provider_id: str
    name: str
    country: str | None = None
    tier: int | None = None


@dataclass(frozen=True)
class TeamData:
    provider_id: str
    name: str
    short_name: str | None = None
    country: str | None = None
    logo_url: str | None = None


@dataclass(frozen=True)
class FixtureData:
    provider_id: str
    competition_provider_id: str
    home_team_provider_id: str
    away_team_provider_id: str
    kickoff_utc: datetime
    status: str = "SCHEDULED"
    venue: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    statistics: dict[str, object] = field(default_factory=dict)


class ProviderAdapter(Protocol):
    """Interface every sports data provider must implement."""

    code: str

    def fetch_competitions(self) -> Iterable[CompetitionData]: ...

    def fetch_teams(self, competition_provider_id: str) -> Iterable[TeamData]: ...

    def fetch_fixtures(
        self, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> Iterable[FixtureData]: ...
