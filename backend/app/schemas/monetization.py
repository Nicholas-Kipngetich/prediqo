"""Monetization endpoint schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TokenBalanceOut(BaseModel):
    balance: int
    recent_transactions: list[dict] = Field(default_factory=list)


class TokenPackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    tokens: int
    price_minor: int
    currency: str
    google_play_product_id: str


class TokenTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    amount: int
    balance_after: int
    reason: str
    reference_type: str | None = None
    reference_id: str | None = None
    created_at: datetime


class PurchaseVerifyIn(BaseModel):
    product_id: str
    purchase_token: str
    idempotency_key: str | None = None


class PurchaseResultOut(BaseModel):
    credited_tokens: int
    balance: int
    order_id: str
    already_credited: bool = False


class UnlockIn(BaseModel):
    target_type: str
    target_id: str


class UnlockOut(BaseModel):
    unlocked: bool
    entitlement: str
    balance: int


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    interval: str
    price_minor: int
    currency: str


class SubscriptionStatusOut(BaseModel):
    is_vip: bool
    status: str | None = None
    expires_at: datetime | None = None
    plan_code: str | None = None
