"""Development email/password authentication tests."""

import pytest


@pytest.mark.asyncio
async def test_register_login_and_protected_access(client):
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "secret123",
            "confirm_password": "secret123",
            "display_name": "Test User",
        },
    )
    assert registered.status_code == 200
    reg_data = registered.json()
    assert reg_data["verification_required"] is True
    code = reg_data["verification_code"]
    assert code is not None
    assert reg_data["user"]["email"] == "test@example.com"
    assert reg_data["user"]["status"] == "PENDING"

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert duplicate.status_code == 409

    unverified_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert unverified_login.status_code == 401

    verified = await client.post(
        "/api/v1/auth/verify-code",
        json={"email": "test@example.com", "code": code},
    )
    assert verified.status_code == 200
    verify_data = verified.json()
    token = verify_data["access_token"]
    assert token.startswith("devauth.")
    assert verify_data["user"]["status"] == "ACTIVE"

    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert logged_in.status_code == 200
    assert logged_in.json()["user"]["id"] == verify_data["user"]["id"]

    wrong = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpass"},
    )
    assert wrong.status_code == 401

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"

    mismatch = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "mismatch@example.com",
            "password": "secret123",
            "confirm_password": "different",
        },
    )
    assert mismatch.status_code == 409


@pytest.mark.asyncio
async def test_dev_token_still_works(client):
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer prediqo-dev-token"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "dev@prediqo.local"
