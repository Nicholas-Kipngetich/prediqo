"""Phase 9 — administration API tests."""

import pytest

from tests.conftest import promote_to_admin


@pytest.fixture
async def admin_client(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])
    return client, auth_headers


@pytest.mark.asyncio
async def test_admin_cannot_be_reached_by_regular_user(client, auth_headers):
    response = await client.get("/api/v1/admin/predictions", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_lists_predictions(admin_client):
    client, auth_headers = admin_client
    await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)
    await client.post("/api/v1/predictions/generate", headers=auth_headers)

    response = await client.get("/api/v1/admin/predictions", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 28
    assert response.json()[0]["market"] in {"1X2", "OU25", "BTTS", "CS"}


@pytest.mark.asyncio
async def test_admin_lists_monetization_config(admin_client):
    client, auth_headers = admin_client
    packages = await client.get("/api/v1/admin/token-packages", headers=auth_headers)
    plans = await client.get("/api/v1/admin/subscription-plans", headers=auth_headers)

    assert packages.status_code == plans.status_code == 200
    assert len(packages.json()) == 3
    assert {plan["code"] for plan in plans.json()} == {"VIP_MONTHLY", "VIP_ANNUAL"}


@pytest.mark.asyncio
async def test_admin_system_health_and_audit(admin_client):
    client, auth_headers = admin_client
    await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)

    health = await client.get("/api/v1/admin/system/health", headers=auth_headers)
    audit = await client.get("/api/v1/admin/audit-logs", headers=auth_headers)

    assert health.status_code == audit.status_code == 200
    assert health.json()["api"] == "ok"
    assert any(item["action"] == "ADMIN_SYNC_TRIGGERED" for item in audit.json())
