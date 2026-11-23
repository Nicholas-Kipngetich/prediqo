"""Role-based access control tests."""

import pytest

from tests.conftest import promote_to_admin


@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_endpoint(client, auth_headers):
    response = await client.get("/api/v1/admin/ping", headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_can_access_admin_endpoint(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])

    response = await client.get("/api/v1/admin/ping", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_admin_can_list_users(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])

    response = await client.get("/api/v1/admin/users", headers=auth_headers)

    assert response.status_code == 200
    assert any(user["id"] == profile["id"] for user in response.json())


@pytest.mark.asyncio
async def test_admin_dashboard_counts_users(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])

    response = await client.get("/api/v1/admin/dashboard", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["total_users"] >= 1


@pytest.mark.asyncio
async def test_permissions_endpoint_lists_user_permissions(client, auth_headers):
    response = await client.get("/api/v1/auth/permissions", headers=auth_headers)

    assert response.status_code == 200
    assert "predictions:free:read" in response.json()
    assert "admin:users:write" not in response.json()
