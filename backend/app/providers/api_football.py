"""API-Football (api-sports.io) adapter.

Activated only when FOOTBALL_DATA_PROVIDER=api-football and an API key is configured.
The adapter intentionally raises if the key is missing — it never falls back to sample
data silently. Commercial licensing must be confirmed before production use.
"""

from collections.abc import Iterable
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.core.errors import ConflictError
from app.providers.base import CompetitionData, FixtureData, TeamData


class ApiFootballAdapter:
    code = "api-football"

    def __init__(self) -> None:
        if not settings.football_data_api_key:
            raise ConflictError("Football data API key is not configured.")
        self._client = httpx.Client(
            base_url=settings.football_data_base_url,
            headers={"x-apisports-key": settings.football_data_api_key},
            timeout=10.0,
        )

    def _get(
        self, path: str, params: dict[str, str | int | float | bool | None] | None = None
    ) -> list[dict]:
        try:
            response = self._client.get(path, params=params or {})
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConflictError(f"Sports data provider unavailable: {exc}") from exc
        result = payload.get("response")
        if not isinstance(result, list):
            return []
        return result

    def fetch_competitions(self) -> Iterable[CompetitionData]:
        # League id 3 = English Premier League in API-Football; broad coverage
        # requires a paid plan and is configured by the administrator.
        for item in self._get("/leagues", {"id": 3}):
            league = item.get("league") or {}
            country = item.get("country") or {}
            if not league.get("id") or not league.get("name"):
                continue
            yield CompetitionData(
                provider_id=str(league["id"]),
                name=str(league["name"]),
                country=str(country.get("name")) if country.get("name") else None,
            )

    def fetch_teams(self, competition_provider_id: str) -> Iterable[TeamData]:
        for item in self._get(
            "/teams", {"league": competition_provider_id, "season": datetime.now(UTC).year}
        ):
            team = item.get("team") or {}
            if not team.get("id") or not team.get("name"):
                continue
            yield TeamData(
                provider_id=str(team["id"]),
                name=str(team["name"]),
                short_name=team.get("code"),
                country=team.get("country"),
                logo_url=team.get("logo"),
            )

    def fetch_fixtures(
        self, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> Iterable[FixtureData]:
        params: dict[str, str | int | float | bool | None] = {}
        if date_from and date_to:
            params["from"] = date_from.date().isoformat()
            params["to"] = date_to.date().isoformat()
        elif date_from:
            params["from"] = date_from.date().isoformat()
        for item in self._get("/fixtures", params):
            fixture = item.get("fixture") or {}
            league = item.get("league") or {}
            teams = item.get("teams") or {}
            home, away = teams.get("home") or {}, teams.get("away") or {}
            kickoff = fixture.get("date")
            if not (
                fixture.get("id")
                and league.get("id")
                and home.get("id")
                and away.get("id")
                and kickoff
            ):
                continue
            try:
                parsed = datetime.fromisoformat(str(kickoff).replace("Z", "+00:00"))
            except ValueError:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            yield FixtureData(
                provider_id=str(fixture["id"]),
                competition_provider_id=str(league["id"]),
                home_team_provider_id=str(home["id"]),
                away_team_provider_id=str(away["id"]),
                kickoff_utc=parsed,
                status=str((fixture.get("status") or {}).get("short") or "SCHEDULED"),
                venue=fixture.get("venue", {}).get("name"),
                home_score=(item.get("goals") or {}).get("home"),
                away_score=(item.get("goals") or {}).get("away"),
                statistics={},  # statistics are synced separately when validated
            )
