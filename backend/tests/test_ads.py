"""Ad placement configuration tests."""

import pytest

from tests.conftest import promote_to_admin


@pytest.mark.asyncio
async def test_client_config_exposes_enabled_test_placements(client):
    response = await client.get("/api/v1/config/client")

    assert response.status_code == 200
    data = response.json()
    assert data["ads_enabled"] is True
    assert len(data["placements"]) == 5
    enabled = {item["key"] for item in data["placements"] if item["enabled"]}
    assert enabled == {"app_open", "banner_home"}
    banner = next(item for item in data["placements"] if item["key"] == "banner_home")
    assert banner["unit_id"].startswith("ca-app-pub-")
    assert banner["vip_excluded"] is True


@pytest.mark.asyncio
async def test_admin_can_disable_ads(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])

    patched = await client.patch(
        "/api/v1/admin/ad-placements/banner_home",
        json={"enabled": False, "frequency_cap_per_hour": 3},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False

    config = (await client.get("/api/v1/config/client")).json()
    banner = next(item for item in config["placements"] if item["key"] == "banner_home")
    assert banner["enabled"] is False
    assert banner["unit_id"] == ""

    await client.patch(
        "/api/v1/admin/config/ads_enabled",
        json={"value": False},
        headers=auth_headers,
    )
    config = (await client.get("/api/v1/config/client")).json()
    assert config["ads_enabled"] is False
    assert all(item["enabled"] is False for item in config["placements"])

    audit = await client.get("/api/v1/admin/audit-logs", headers=auth_headers)
    actions = {item["action"] for item in audit.json()}
    assert "AD_PLACEMENT_UPDATED" in actions
    assert "SYSTEM_CONFIG_UPDATED" in actions


@pytest.mark.asyncio
async def test_regular_user_cannot_change_ads(client, auth_headers):
    await client.post("/api/v1/auth/verify", headers=auth_headers)
    response = await client.patch(
        "/api/v1/admin/ad-placements/banner_home",
        json={"enabled": True},
        headers=auth_headers,
    )
    assert response.status_code == 403
