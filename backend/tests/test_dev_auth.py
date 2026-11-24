"""Development email/password authentication tests."""

import pytest


@pytest.mark.asyncio
async def test_register_login_and_protected_access(client):
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "secret123",
            "display_name": "Test User",
        },
    )
    assert registered.status_code == 200
    data = registered.json()
    token = data["access_token"]
    assert token.startswith("devauth.")
    assert data["user"]["email"] == "test@example.com"

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert duplicate.status_code == 409

    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert logged_in.status_code == 200
    assert logged_in.json()["user"]["id"] == data["user"]["id"]

    wrong = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpass"},
    )
    assert wrong.status_code == 401

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_dev_token_still_works(client):
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer prediqo-dev-token"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "dev@prediqo.local"
