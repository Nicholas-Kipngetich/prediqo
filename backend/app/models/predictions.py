"""Prediction publication tables. Published records are immutable."""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PredictionStatus:
    PENDING = "PENDING"
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    VOID = "VOID"
    POSTPONED = "POSTPONED"
    ABANDONED = "ABANDONED"


class ModelVersionStatus:
    CHALLENGER = "CHALLENGER"
    CHAMPION = "CHAMPION"
    RETIRED = "RETIRED"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(64))
    feature_version: Mapped[str] = mapped_column(String(64), default="v1")
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metrics_json: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default=ModelVersionStatus.CHALLENGER)


class PredictionMarket(Base):
    __tablename__ = "prediction_markets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    market_group: Mapped[str] = mapped_column(String(64), default="other")
    active: Mapped[bool] = mapped_column(default=True)


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "market_id",
            "model_version_id",
            name="uq_prediction_fixture_market_model",
        ),
        Index("ix_predictions_published_at", "published_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fixture_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    market_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prediction_markets.id"), index=True)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_versions.id"), index=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    probabilities_json: Mapped[str] = mapped_column(String(4000))
    selected_outcome: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24), default=PredictionStatus.PENDING)
    snapshot_json: Mapped[str] = mapped_column(String(8000))
    explanation_json: Mapped[str] = mapped_column(String(4000))
    is_sample_data: Mapped[bool] = mapped_column(default=False)


class PredictionSettlement(Base):
    __tablename__ = "prediction_settlements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"), unique=True, index=True
    )
    settled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    result: Mapped[str] = mapped_column(String(24))
    actual_outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="CASCADE"), index=True
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    metrics_json: Mapped[str] = mapped_column(String(4000))
