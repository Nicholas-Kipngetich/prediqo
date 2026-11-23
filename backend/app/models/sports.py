"""Sports domain tables: competitions, seasons, teams, fixtures and statistics."""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FixtureStatus:
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"
    ABANDONED = "ABANDONED"


class SyncStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


competition_favorites = Table(
    "user_favorite_competitions",
    Base.metadata,
    Column(
        "user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "competition_id",
        UUID(as_uuid=True),
        ForeignKey("competitions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

team_favorites = Table(
    "user_favorite_teams",
    Base.metadata,
    Column(
        "user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "team_id", UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))


class DataProvider(Base):
    __tablename__ = "data_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Competition(Base):
    __tablename__ = "competitions"
    __table_args__ = (
        UniqueConstraint("sport_id", "provider_competition_id", name="uq_competition_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sports.id", ondelete="CASCADE"), index=True
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_providers.id"), nullable=True
    )
    provider_competition_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(160))
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    seasons: Mapped[list["Season"]] = relationship(back_populates="competition")


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("competition_id", "label", name="uq_season_label"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(32))
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    competition: Mapped[Competition] = relationship(back_populates="seasons")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("sport_id", "provider_team_id", name="uq_team_provider"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sports.id", ondelete="CASCADE"), index=True
    )
    provider_team_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(160))
    short_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=False)


class Fixture(Base):
    __tablename__ = "fixtures"
    __table_args__ = (
        UniqueConstraint("provider_fixture_id", name="uq_fixture_provider"),
        Index("ix_fixtures_kickoff_status", "kickoff_utc", "status"),
        Index("ix_fixtures_competition_kickoff", "competition_id", "kickoff_utc"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_fixture_id: Mapped[str] = mapped_column(String(128))
    competition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    season_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    home_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    kickoff_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(24), default=FixtureStatus.SCHEDULED)
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    statistics: Mapped[list["MatchStatistic"]] = relationship(
        back_populates="fixture", cascade="all, delete-orphan"
    )


class MatchStatistic(Base):
    __tablename__ = "match_statistics"
    __table_args__ = (UniqueConstraint("fixture_id", "provider_id", name="uq_match_stat_provider"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fixture_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_providers.id"), nullable=True
    )
    stats_json: Mapped[str] = mapped_column(String(8000))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_sample_data: Mapped[bool] = mapped_column(Boolean, default=False)

    fixture: Mapped[Fixture] = relationship(back_populates="statistics")


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_providers.id"), nullable=True
    )
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(24), default=SyncStatus.PENDING)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
