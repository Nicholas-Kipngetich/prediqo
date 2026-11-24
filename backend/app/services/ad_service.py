"""Ad placement configuration.

Ads can be enabled from the admin dashboard; there is no policy-review gate in this
build. Test ad unit IDs are used until real IDs are configured.
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.ads import AdPlacement, SystemConfig

TEST_PLACEMENTS = [
    ("app_open", "App open", "APP_OPEN", "ca-app-pub-3940256099942544/9235187345", True),
    ("banner_home", "Home banner", "BANNER", "ca-app-pub-3940256099942544/6300978111", True),
    ("native_feed", "Native feed", "NATIVE", "ca-app-pub-3940256099942544/3130260592", True),
    (
        "interstitial_navigation",
        "Navigation interstitial",
        "INTERSTITIAL",
        "ca-app-pub-3940256099942544/1033173712",
        True,
    ),
    (
        "rewarded_unlock",
        "Rewarded unlock",
        "REWARDED",
        "ca-app-pub-3940256099942544/6498350057",
        True,
    ),
]
CLIENT_CONFIG_KEYS = {
    "ads_enabled",
    "ads_policy_reviewed",
    "admob_app_id_android",
}


async def ensure_seed(session: AsyncSession) -> None:
    existing = {row.key for row in (await session.execute(select(AdPlacement))).scalars()}
    for key, name, ad_type, unit_id, enabled in TEST_PLACEMENTS:
        if key not in existing:
            session.add(
                AdPlacement(
                    key=key,
                    name=name,
                    ad_type=ad_type,
                    unit_id=unit_id,
                    enabled=enabled,
                    frequency_cap_per_hour=2,
                    vip_excluded=True,
                )
            )
    configs = {row.key for row in (await session.execute(select(SystemConfig))).scalars()}
    defaults = {
        "ads_enabled": True,
        "ads_policy_reviewed": True,
        "admob_app_id_android": "ca-app-pub-3940256099942544~3347511713",
    }
    for key, value in defaults.items():
        if key not in configs:
            session.add(SystemConfig(key=key, value_json=json.dumps(value)))
    await session.flush()


async def get_config_value(session: AsyncSession, key: str, default=None):
    row = await session.get(SystemConfig, key)
    if row is None:
        return default
    try:
        return json.loads(row.value_json)
    except (ValueError, TypeError):
        return default


async def set_config_value(session: AsyncSession, key: str, value) -> None:
    row = await session.get(SystemConfig, key)
    if row is None:
        row = SystemConfig(key=key, value_json=json.dumps(value))
        session.add(row)
    else:
        row.value_json = json.dumps(value)
    await session.flush()


async def list_placements(session: AsyncSession) -> list[AdPlacement]:
    await ensure_seed(session)
    await session.commit()
    return list((await session.execute(select(AdPlacement))).scalars())


async def update_placement(session: AsyncSession, key: str, changes: dict) -> AdPlacement:
    await ensure_seed(session)
    placement = (
        await session.execute(select(AdPlacement).where(AdPlacement.key == key))
    ).scalar_one_or_none()
    if placement is None:
        raise NotFoundError("Ad placement not found.")
    for field in ("enabled", "frequency_cap_per_hour", "unit_id", "vip_excluded"):
        if field in changes and changes[field] is not None:
            setattr(placement, field, changes[field])
    await session.commit()
    return placement


def placement_out(placement: AdPlacement) -> dict:
    return {
        "id": str(placement.id),
        "key": placement.key,
        "name": placement.name,
        "ad_type": placement.ad_type,
        "unit_id": placement.unit_id,
        "enabled": placement.enabled,
        "frequency_cap_per_hour": placement.frequency_cap_per_hour,
        "vip_excluded": placement.vip_excluded,
    }


async def client_config(session: AsyncSession) -> dict:
    """Public, safe config consumed by the mobile app."""
    await ensure_seed(session)
    await session.commit()
    config = {}
    for key in CLIENT_CONFIG_KEYS:
        config[key] = await get_config_value(session, key)
    global_enabled = bool(config.get("ads_enabled"))
    placements = (await session.execute(select(AdPlacement))).scalars().all()
    config["placements"] = [
        {
            "key": item.key,
            "ad_type": item.ad_type,
            "unit_id": item.unit_id if (item.enabled and global_enabled) else "",
            "enabled": bool(item.enabled and global_enabled),
            "frequency_cap_per_hour": item.frequency_cap_per_hour,
            "vip_excluded": item.vip_excluded,
        }
        for item in placements
    ]
    return config
