"""Authentication tests."""

import pytest


@pytest.mark.asyncio
async def test_verify_token_provisions_user(client, auth_headers):
    response = await client.post("/api/v1/auth/verify", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "dev@prediqo.local"
    assert "USER" in data["roles"]
    assert "predictions:free:read" in data["permissions"]
    assert data["profile"]["timezone"] == "Africa/Nairobi"
    assert data["is_vip"] is False


@pytest.mark.asyncio
async def test_verify_is_idempotent(client, auth_headers):
    first = await client.post("/api/v1/auth/verify", headers=auth_headers)
    second = await client.post("/api/v1/auth/verify", headers=auth_headers)

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_missing_token_is_rejected(client):
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in response.json()["error"]


@pytest.mark.asyncio
async def test_invalid_token_is_rejected(client):
    response = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_request_id_propagated(client):
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer prediqo-dev-token", "X-Request-ID": "test-123"},
    )
    assert response.headers["X-Request-ID"] == "test-123"
