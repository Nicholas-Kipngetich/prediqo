"""Ad placement configuration endpoints. Ads are disabled until policy review."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_session
from app.models.identity import User
from app.schemas.ads import ConfigPatch, PlacementOut, PlacementPatch
from app.services.ad_service import (
    client_config,
    list_placements,
    placement_out,
    set_config_value,
    update_placement,
)
from app.services.audit_service import log_action

router = APIRouter(tags=["ads"])


@router.get("/config/client")
async def get_client_config(
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await client_config(session)


@router.get("/admin/ad-placements", response_model=list[PlacementOut])
async def admin_list_placements(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[PlacementOut]:
    rows = await list_placements(session)
    return [PlacementOut(**placement_out(row)) for row in rows]


@router.patch("/admin/ad-placements/{key}", response_model=PlacementOut)
async def admin_update_placement(
    key: str,
    payload: PlacementPatch,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PlacementOut:
    placement = await update_placement(session, key, payload.model_dump(exclude_unset=True))
    await log_action(
        session,
        "AD_PLACEMENT_UPDATED",
        admin.id,
        "ad_placement",
        key,
        payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return PlacementOut(**placement_out(placement))


@router.get("/admin/config")
async def admin_get_config(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await client_config(session)


@router.patch("/admin/config/{key}")
async def admin_set_config(
    key: str,
    payload: ConfigPatch,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await set_config_value(session, key, payload.value)
    await log_action(
        session,
        "SYSTEM_CONFIG_UPDATED",
        admin.id,
        "system_config",
        key,
        {"value": payload.value},
    )
    await session.commit()
    return {key: payload.value}
