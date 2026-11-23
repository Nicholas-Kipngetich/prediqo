"""Daily free analysis quota tests."""

import pytest

from tests.conftest import promote_to_admin


@pytest.fixture
async def analysis_client(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])
    await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)
    await client.post("/api/v1/predictions/generate", headers=auth_headers)
    fixtures = (await client.get("/api/v1/fixtures?status=SCHEDULED&page_size=10")).json()
    return client, auth_headers, [item["id"] for item in fixtures["items"]]


@pytest.mark.asyncio
async def test_free_quota_allows_one_fixture_per_day(analysis_client):
    client, auth_headers, fixture_ids = analysis_client
    assert len(fixture_ids) >= 3

    first = await client.get(f"/api/v1/fixtures/{fixture_ids[0]}/analysis", headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["entitlement"] == "free"
    assert "1X2" in first.json()["markets"]

    repeat = await client.get(f"/api/v1/fixtures/{fixture_ids[0]}/analysis", headers=auth_headers)
    assert repeat.status_code == 200
    assert repeat.json()["entitlement"] == "free"

    second = await client.get(f"/api/v1/fixtures/{fixture_ids[1]}/analysis", headers=auth_headers)
    assert second.status_code == 403
    assert second.json()["error"]["code"] == "ENTITLEMENT_REQUIRED"
    assert second.json()["error"]["details"]["used_today"] == 1


@pytest.mark.asyncio
async def test_vip_bypasses_daily_quota(analysis_client):
    client, auth_headers, fixture_ids = analysis_client
    await client.get(f"/api/v1/fixtures/{fixture_ids[0]}/analysis", headers=auth_headers)

    vip = await client.post(
        "/api/v1/subscriptions/verify",
        json={
            "product_id": "com.prediqo.vip.monthly",
            "purchase_token": "quota-vip-token",
        },
        headers=auth_headers,
    )
    assert vip.status_code == 200

    response = await client.get(f"/api/v1/fixtures/{fixture_ids[1]}/analysis", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["entitlement"] == "vip"


@pytest.mark.asyncio
async def test_token_unlock_bypasses_daily_quota(analysis_client):
    client, auth_headers, fixture_ids = analysis_client
    await client.get(f"/api/v1/fixtures/{fixture_ids[0]}/analysis", headers=auth_headers)

    purchase = await client.post(
        "/api/v1/tokens/purchases/verify",
        json={
            "product_id": "com.prediqo.tokens.starter",
            "purchase_token": "quota-token-purchase",
        },
        headers=auth_headers,
    )
    assert purchase.status_code == 200

    unlock = await client.post(
        "/api/v1/tokens/unlock",
        json={"target_type": "analysis", "target_id": fixture_ids[1]},
        headers=auth_headers,
    )
    assert unlock.status_code == 200
    assert unlock.json()["entitlement"] == "token"

    response = await client.get(f"/api/v1/fixtures/{fixture_ids[1]}/analysis", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["entitlement"] == "token"
