"""Normalise and persist provider data with provenance and validation."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sports import (
    Competition,
    DataProvider,
    Fixture,
    FixtureStatus,
    Sport,
    SyncJob,
    SyncStatus,
    Team,
)
from app.providers.base import ProviderAdapter
from app.providers.factory import get_provider

ALLOWED_STATUSES = {
    FixtureStatus.SCHEDULED,
    FixtureStatus.LIVE,
    FixtureStatus.FINISHED,
    FixtureStatus.POSTPONED,
    FixtureStatus.CANCELLED,
    FixtureStatus.ABANDONED,
    "NS",
    "1H",
    "2H",
    "FT",
    "PST",
    "CANC",
    "ABD",
}


@dataclass
class SyncResult:
    competitions: int = 0
    teams: int = 0
    fixtures: int = 0
    skipped: int = 0


async def _get_or_create_sport(session: AsyncSession) -> Sport:
    sport = (
        await session.execute(select(Sport).where(Sport.code == "football"))
    ).scalar_one_or_none()
    if sport is None:
        sport = Sport(code="football", name="Football")
        session.add(sport)
        await session.flush()
    return sport


async def _get_or_create_provider_row(session: AsyncSession, code: str) -> DataProvider:
    row = (
        await session.execute(select(DataProvider).where(DataProvider.code == code))
    ).scalar_one_or_none()
    if row is None:
        row = DataProvider(code=code, name=code, enabled=True)
        session.add(row)
        await session.flush()
    return row


async def sync_sports_data(
    session: AsyncSession,
    provider: ProviderAdapter | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> SyncResult:
    """Run a full synchronisation for one provider.

    Invalid records are skipped and counted; missing data is never fabricated.
    """
    provider = provider or get_provider()
    is_sample = provider.code == "sample"
    provider_row = await _get_or_create_provider_row(session, provider.code)
    job = SyncJob(
        provider_id=provider_row.id,
        job_type="full",
        status=SyncStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    session.add(job)
    await session.commit()

    result = SyncResult()
    try:
        sport = await _get_or_create_sport(session)

        competition_map: dict[str, Competition] = {
            row.provider_competition_id: row
            for row in (await session.execute(select(Competition))).scalars()
        }
        for competition_data in provider.fetch_competitions():
            if not competition_data.provider_id or not competition_data.name:
                result.skipped += 1
                continue
            existing_competition = competition_map.get(competition_data.provider_id)
            if existing_competition is None:
                existing_competition = Competition(
                    sport_id=sport.id,
                    provider_id=provider_row.id,
                    provider_competition_id=competition_data.provider_id,
                    name=competition_data.name,
                    country=competition_data.country,
                    tier=competition_data.tier,
                    is_sample_data=is_sample,
                )
                session.add(existing_competition)
                await session.flush()
                competition_map[competition_data.provider_id] = existing_competition
            else:
                existing_competition.name = competition_data.name
                existing_competition.country = competition_data.country
                existing_competition.tier = competition_data.tier
            result.competitions += 1

        team_map: dict[str, Team] = {
            row.provider_team_id: row for row in (await session.execute(select(Team))).scalars()
        }
        for competition_provider_id in competition_map:
            for team_data in provider.fetch_teams(competition_provider_id):
                if not team_data.provider_id or not team_data.name:
                    result.skipped += 1
                    continue
                existing_team = team_map.get(team_data.provider_id)
                if existing_team is None:
                    existing_team = Team(
                        sport_id=sport.id,
                        provider_team_id=team_data.provider_id,
                        name=team_data.name,
                        short_name=team_data.short_name,
                        country=team_data.country,
                        logo_url=team_data.logo_url,
                        is_sample_data=is_sample,
                    )
                    session.add(existing_team)
                    await session.flush()
                    team_map[team_data.provider_id] = existing_team
                result.teams += 1

        fixture_map: dict[str, Fixture] = {
            row.provider_fixture_id: row
            for row in (await session.execute(select(Fixture))).scalars()
        }
        for fixture_data in provider.fetch_fixtures(date_from, date_to):
            if (
                not fixture_data.provider_id
                or fixture_data.competition_provider_id not in competition_map
                or fixture_data.home_team_provider_id not in team_map
                or fixture_data.away_team_provider_id not in team_map
                or fixture_data.kickoff_utc.tzinfo is None
                or fixture_data.status not in ALLOWED_STATUSES
            ):
                result.skipped += 1
                continue
            existing_fixture = fixture_map.get(fixture_data.provider_id)
            if existing_fixture is None:
                existing_fixture = Fixture(
                    provider_fixture_id=fixture_data.provider_id,
                    competition_id=competition_map[fixture_data.competition_provider_id].id,
                    home_team_id=team_map[fixture_data.home_team_provider_id].id,
                    away_team_id=team_map[fixture_data.away_team_provider_id].id,
                    kickoff_utc=fixture_data.kickoff_utc,
                    status=fixture_data.status,
                    venue=fixture_data.venue,
                    home_score=fixture_data.home_score,
                    away_score=fixture_data.away_score,
                    is_sample_data=is_sample,
                    last_synced_at=datetime.now(UTC),
                )
                session.add(existing_fixture)
                fixture_map[fixture_data.provider_id] = existing_fixture
            else:
                existing_fixture.kickoff_utc = fixture_data.kickoff_utc
                existing_fixture.status = fixture_data.status
                existing_fixture.venue = fixture_data.venue
                existing_fixture.home_score = fixture_data.home_score
                existing_fixture.away_score = fixture_data.away_score
                existing_fixture.last_synced_at = datetime.now(UTC)
            result.fixtures += 1

        await session.commit()
        job.status = SyncStatus.SUCCESS
        job.records_processed = result.competitions + result.teams + result.fixtures
        job.finished_at = datetime.now(UTC)
        await session.commit()
        return result
    except Exception as exc:
        await session.rollback()
        job.status = SyncStatus.FAILED
        job.error_text = str(exc)[:2000]
        job.finished_at = datetime.now(UTC)
        await session.commit()
        raise
