"""Daily analysis access tracking."""

import uuid
from datetime import date, datetime

from sqlalchemy import UUID, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisAccess(Base):
    __tablename__ = "analysis_access"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "fixture_id",
            "accessed_date",
            name="uq_analysis_access_user_fixture_day",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    fixture_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    accessed_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
