"""Notification, device token and preference tables."""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NotificationType:
    DAILY_INSIGHT = "DAILY_INSIGHT"
    UPCOMING_FIXTURE = "UPCOMING_FIXTURE"
    MATCH_RESULT = "MATCH_RESULT"
    FAVORITE_TEAM = "FAVORITE_TEAM"
    VIP_CONTENT = "VIP_CONTENT"
    SUBSCRIPTION = "SUBSCRIPTION"
    TEST = "TEST"


class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = (UniqueConstraint("user_id", "fcm_token", name="uq_device_token_user_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    fcm_token: Mapped[str] = mapped_column(String(512))
    platform: Mapped[str] = mapped_column(String(16), default="android")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    daily_insight: Mapped[bool] = mapped_column(Boolean, default=True)
    upcoming_fixture: Mapped[bool] = mapped_column(Boolean, default=True)
    match_result: Mapped[bool] = mapped_column(Boolean, default=True)
    favorite_team: Mapped[bool] = mapped_column(Boolean, default=True)
    vip_content: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_hours_start: Mapped[int | None] = mapped_column(nullable=True)
    quiet_hours_end: Mapped[int | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_notification_dedupe_key"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(String(500))
    deep_link: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="PENDING")
    dedupe_key: Mapped[str] = mapped_column(String(256))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
