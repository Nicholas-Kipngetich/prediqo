"""Schemas for prediction endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionOut(BaseModel):
    id: UUID
    fixture_id: UUID
    market: str
    model_version: str
    probabilities_bp: dict[str, int]
    selected_outcome: str
    status: str
    published_at: datetime
    data_as_of: datetime
    is_sample_data: bool = False
    explanation: dict[str, object] = Field(default_factory=dict)


class GenerationResultOut(BaseModel):
    published: int
    skipped: int
    suppressed: int
