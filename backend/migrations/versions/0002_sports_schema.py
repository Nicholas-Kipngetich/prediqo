"""Create sports domain schema.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sports",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
    )
    op.create_index("ix_sports_code", "sports", ["code"], unique=True)

    op.create_table(
        "data_providers",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_data_providers_code", "data_providers", ["code"], unique=True)

    op.create_table(
        "competitions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport_id", sa.UUID(as_uuid=True), sa.ForeignKey("sports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.UUID(as_uuid=True), sa.ForeignKey("data_providers.id"), nullable=True),
        sa.Column("provider_competition_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("country", sa.String(120), nullable=True),
        sa.Column("tier", sa.Integer(), nullable=True),
        sa.Column("is_sample_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("sport_id", "provider_competition_id", name="uq_competition_provider"),
    )
    op.create_index("ix_competitions_provider_competition_id", "competitions", ["provider_competition_id"])
    op.create_index("ix_competitions_sport_id", "competitions", ["sport_id"])

    op.create_table(
        "seasons",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("competition_id", sa.UUID(as_uuid=True), sa.ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(32), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("competition_id", "label", name="uq_season_label"),
    )
    op.create_index("ix_seasons_competition_id", "seasons", ["competition_id"])

    op.create_table(
        "teams",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("sport_id", sa.UUID(as_uuid=True), sa.ForeignKey("sports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_team_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("short_name", sa.String(32), nullable=True),
        sa.Column("country", sa.String(120), nullable=True),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column("is_sample_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("sport_id", "provider_team_id", name="uq_team_provider"),
    )
    op.create_index("ix_teams_provider_team_id", "teams", ["provider_team_id"])
    op.create_index("ix_teams_sport_id", "teams", ["sport_id"])

    op.create_table(
        "fixtures",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_fixture_id", sa.String(128), nullable=False),
        sa.Column("competition_id", sa.UUID(as_uuid=True), sa.ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("season_id", sa.UUID(as_uuid=True), sa.ForeignKey("seasons.id"), nullable=True),
        sa.Column("home_team_id", sa.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("away_team_id", sa.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("kickoff_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="SCHEDULED"),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("is_sample_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider_fixture_id", name="uq_fixture_provider"),
    )
    op.create_index("ix_fixtures_kickoff_utc", "fixtures", ["kickoff_utc"])
    op.create_index("ix_fixtures_competition_id", "fixtures", ["competition_id"])
    op.create_index("ix_fixtures_home_team_id", "fixtures", ["home_team_id"])
    op.create_index("ix_fixtures_away_team_id", "fixtures", ["away_team_id"])
    op.create_index("ix_fixtures_kickoff_status", "fixtures", ["kickoff_utc", "status"])
    op.create_index("ix_fixtures_competition_kickoff", "fixtures", ["competition_id", "kickoff_utc"])

    op.create_table(
        "match_statistics",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("fixture_id", sa.UUID(as_uuid=True), sa.ForeignKey("fixtures.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.UUID(as_uuid=True), sa.ForeignKey("data_providers.id"), nullable=True),
        sa.Column("stats_json", sa.String(8000), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_sample_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("fixture_id", "provider_id", name="uq_match_stat_provider"),
    )
    op.create_index("ix_match_statistics_fixture_id", "match_statistics", ["fixture_id"])

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_id", sa.UUID(as_uuid=True), sa.ForeignKey("data_providers.id"), nullable=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_text", sa.String(2000), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sync_jobs_job_type", "sync_jobs", ["job_type"])

    op.create_table(
        "user_favorite_competitions",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("competition_id", sa.UUID(as_uuid=True), sa.ForeignKey("competitions.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "user_favorite_teams",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("team_id", sa.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    )

    op.execute(
        sa.text(
            "INSERT INTO sports (id, code, name) VALUES "
            "('a0000000-0000-0000-0000-000000000001', 'football', 'Football')"
        )
    )


def downgrade() -> None:
    op.drop_table("user_favorite_teams")
    op.drop_table("user_favorite_competitions")
    op.drop_table("sync_jobs")
    op.drop_table("match_statistics")
    op.drop_table("fixtures")
    op.drop_table("teams")
    op.drop_table("seasons")
    op.drop_table("competitions")
    op.drop_table("data_providers")
    op.drop_table("sports")
