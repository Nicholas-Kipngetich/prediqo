"""Ad configuration schemas."""

from pydantic import BaseModel, Field


class PlacementOut(BaseModel):
    id: str
    key: str
    name: str
    ad_type: str
    unit_id: str
    enabled: bool
    frequency_cap_per_hour: int
    vip_excluded: bool


class PlacementPatch(BaseModel):
    enabled: bool | None = None
    frequency_cap_per_hour: int | None = Field(default=None, ge=1, le=20)
    unit_id: str | None = None
    vip_excluded: bool | None = None


class ConfigPatch(BaseModel):
    value: object
