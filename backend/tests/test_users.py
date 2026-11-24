"""User profile endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    payload = {
        "display_name": "Nick",
        "timezone": "Europe/London",
        "theme": "light",
        "onboarding_completed": True,
    }
    response = await client.patch("/api/v1/users/me", json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Nick"
    assert data["profile"]["timezone"] == "Europe/London"
    assert data["profile"]["theme"] == "light"
    assert data["profile"]["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_validation_error_envelope(client, auth_headers):
    response = await client.patch(
        "/api/v1/users/me", json={"timezone": "x" * 100}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_favorites_endpoints(client, auth_headers):
    from app.core.database import get_session_factory
    from app.services.sync_service import sync_sports_data

    await client.post("/api/v1/auth/verify", headers=auth_headers)
    async with get_session_factory()() as session:
        await sync_sports_data(session)
    fixture = (await client.get("/api/v1/fixtures?page_size=1")).json()["items"][0]
    team_id = fixture["home_team"]["id"]
    competition_id = fixture["competition"]["id"]

    response = await client.put(
        "/api/v1/users/me/favorites/teams",
        json={"ids": [team_id]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert team_id in response.json()["team_ids"]

    response = await client.put(
        "/api/v1/users/me/favorites/competitions",
        json={"ids": [competition_id]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert competition_id in response.json()["competition_ids"]

    listing = await client.get("/api/v1/users/me/favorites", headers=auth_headers)
    assert listing.json()["team_ids"] == [team_id]


@pytest.mark.asyncio
async def test_soft_delete(client, auth_headers):
    await client.post("/api/v1/auth/verify", headers=auth_headers)
    response = await client.delete("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 202
    assert response.json()["status"] == "deletion_requested"

    follow_up = await client.post("/api/v1/auth/verify", headers=auth_headers)
    assert follow_up.status_code == 409
    assert follow_up.json()["error"]["code"] == "CONFLICT"
