"""Schemas for prediction endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionOut(BaseModel):
    id: UUID
    fixture_id: UUID
    fixture_label: str | None = None
    competition_name: str | None = None
    kickoff_utc: datetime | None = None
    market: str
    model_version: str
    probabilities_bp: dict[str, int]
    selected_outcome: str
    status: str
    published_at: datetime
    data_as_of: datetime
    actual_outcome: str | None = None
    settled_at: datetime | None = None
    is_sample_data: bool = False
    explanation: dict[str, object] = Field(default_factory=dict)


class GenerationResultOut(BaseModel):
    published: int
    skipped: int
    suppressed: int
