"""Token ledger, purchases, subscriptions and audit log.

Token transactions are append-only. Balances change only through ledger entries.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
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


class TransactionType:
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


class PurchaseStatus:
    VERIFIED = "VERIFIED"
    REFUNDED = "REFUNDED"


class SubscriptionStatus:
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    GRACE = "GRACE"


class TokenPackage(Base):
    __tablename__ = "token_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    tokens: Mapped[int] = mapped_column(Integer)
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="KES")
    google_play_product_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TokenAccount(Base):
    __tablename__ = "token_accounts"
    __table_args__ = (CheckConstraint("balance >= 0", name="ck_token_account_balance_nonnegative"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TokenTransaction(Base):
    __tablename__ = "token_transactions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_token_transaction_idempotency"),
        Index("ix_token_transactions_account_created", "account_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("token_accounts.user_id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(24))
    amount: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(120))
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TokenPurchase(Base):
    __tablename__ = "token_purchases"
    __table_args__ = (
        UniqueConstraint("google_play_order_id", name="uq_token_purchase_order"),
        UniqueConstraint("google_play_purchase_token", name="uq_token_purchase_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("token_packages.id"), index=True)
    google_play_order_id: Mapped[str] = mapped_column(String(160))
    google_play_purchase_token: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(24), default=PurchaseStatus.VERIFIED)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    interval: Mapped[str] = mapped_column(String(16))
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="KES")
    google_play_product_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    entitlements_json: Mapped[str] = mapped_column(String(2000), default="[]")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("purchase_token", name="uq_subscription_purchase_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subscription_plans.id"), index=True)
    purchase_token: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(24), default=SubscriptionStatus.ACTIVE)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_subscription_event_idempotency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[str] = mapped_column(String(4000), default="{}")
    idempotency_key: Mapped[str] = mapped_column(String(200))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details_json: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
