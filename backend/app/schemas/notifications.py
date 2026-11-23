"""Notification schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    body: str
    deep_link: str | None = None
    status: str
    sent_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_insight: bool
    upcoming_fixture: bool
    match_result: bool
    favorite_team: bool
    vip_content: bool
    subscription: bool
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None


class PreferencesIn(BaseModel):
    daily_insight: bool | None = None
    upcoming_fixture: bool | None = None
    match_result: bool | None = None
    favorite_team: bool | None = None
    vip_content: bool | None = None
    subscription: bool | None = None
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None


class DeviceTokenIn(BaseModel):
    fcm_token: str
    platform: str = "android"
