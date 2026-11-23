"""Development-only sample adapter.

Every record produced here is stored with is_sample_data=true and is labelled in the
API. This data is for UI/API development only — it is NEVER a production prediction
or a real fixture result.
"""

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from app.providers.base import CompetitionData, FixtureData, TeamData


class SampleAdapter:
    code = "sample"

    COMPETITIONS = [
        CompetitionData("sample-pl", "Sample Premier League", "England", 1),
        CompetitionData("sample-kl", "Sample Kenya League", "Kenya", 1),
        CompetitionData("sample-sa", "Sample SA League", "South Africa", 1),
    ]

    TEAMS = {
        "sample-pl": [
            TeamData("sample-t1", "Sample City", "SFC", "England"),
            TeamData("sample-t2", "Sample United", "SUFC", "England"),
            TeamData("sample-t3", "Sample Rovers", "SRFC", "England"),
            TeamData("sample-t4", "Sample Albion", "SAFC", "England"),
        ],
        "sample-kl": [
            TeamData("sample-t5", "Sample Nairobi", "SNFC", "Kenya"),
            TeamData("sample-t6", "Sample Mombasa", "SMFC", "Kenya"),
        ],
        "sample-sa": [
            TeamData("sample-t7", "Sample Johannesburg", "SJFC", "South Africa"),
            TeamData("sample-t8", "Sample Cape Town", "SCTC", "South Africa"),
        ],
    }

    def fetch_competitions(self) -> Iterable[CompetitionData]:
        return self.COMPETITIONS

    def fetch_teams(self, competition_provider_id: str) -> Iterable[TeamData]:
        return self.TEAMS.get(competition_provider_id, [])

    def fetch_fixtures(
        self, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> Iterable[FixtureData]:
        now = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
        offsets = [-1, 0, 0, 0, 1, 1, 2, 3]
        matchups = [
            ("sample-pl", "sample-t1", "sample-t2"),
            ("sample-pl", "sample-t3", "sample-t4"),
            ("sample-kl", "sample-t5", "sample-t6"),
            ("sample-sa", "sample-t7", "sample-t8"),
        ]
        fixtures = []
        for index, offset in enumerate(offsets):
            competition_id, home_id, away_id = matchups[index % len(matchups)]
            kickoff = now + timedelta(days=offset, hours=(index % 3) * 3)
            if date_from and kickoff < date_from:
                continue
            if date_to and kickoff > date_to:
                continue
            finished = offset < 0
            fixtures.append(
                FixtureData(
                    provider_id=f"sample-fixture-{index + 1}",
                    competition_provider_id=competition_id,
                    home_team_provider_id=home_id,
                    away_team_provider_id=away_id,
                    kickoff_utc=kickoff,
                    status="FINISHED" if finished else "SCHEDULED",
                    venue=None,
                    home_score=1 if finished else None,
                    away_score=0 if finished else None,
                    statistics={},  # no fabricated statistics
                )
            )
        return fixtures
