"""Performance reporting schemas."""

from pydantic import BaseModel


class OverviewOut(BaseModel):
    total_predictions: int
    settled_predictions: int
    correct: int
    incorrect: int
    pending: int
    void: int
    accuracy: float | None
    sample_size: int


class BreakdownOut(BaseModel):
    dimension: str
    key: str
    total: int
    correct: int
    accuracy: float | None


class CalibrationOut(BaseModel):
    bin: int
    count: int
    mean_probability: float
    observed_rate: float
