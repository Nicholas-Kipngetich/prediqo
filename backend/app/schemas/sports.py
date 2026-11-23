"""Schemas for sports data endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompetitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str | None = None
    tier: int | None = None
    is_sample_data: bool = False


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    short_name: str | None = None
    country: str | None = None
    logo_url: str | None = None
    is_sample_data: bool = False


class FixtureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    competition: CompetitionOut
    home_team: TeamOut
    away_team: TeamOut
    kickoff_utc: datetime
    status: str
    venue: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    is_sample_data: bool = False
    last_synced_at: datetime


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int


class SyncResultOut(BaseModel):
    competitions: int
    teams: int
    fixtures: int
    skipped: int
