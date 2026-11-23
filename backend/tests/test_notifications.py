"""Phase 10 — notification tests."""

import pytest

from tests.conftest import promote_to_admin


@pytest.fixture
async def user_client(client, auth_headers):
    response = await client.post("/api/v1/auth/verify", headers=auth_headers)
    assert response.status_code == 200
    return client, auth_headers


@pytest.mark.asyncio
async def test_preferences_defaults_and_update(user_client):
    client, auth_headers = user_client
    response = await client.get("/api/v1/notifications/preferences", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["upcoming_fixture"] is True

    updated = await client.patch(
        "/api/v1/notifications/preferences",
        json={"upcoming_fixture": False, "quiet_hours_start": 22},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["upcoming_fixture"] is False
    assert updated.json()["quiet_hours_start"] == 22


@pytest.mark.asyncio
async def test_test_notification_is_deduplicated(user_client):
    client, auth_headers = user_client
    first = await client.post("/api/v1/notifications/test", headers=auth_headers)
    second = await client.post("/api/v1/notifications/test", headers=auth_headers)

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == "SENT"

    listing = await client.get("/api/v1/notifications", headers=auth_headers)
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_mark_notification_read(user_client):
    client, auth_headers = user_client
    created = await client.post("/api/v1/notifications/test", headers=auth_headers)
    notification_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/notifications/{notification_id}/read", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["read_at"] is not None


@pytest.mark.asyncio
async def test_device_token_registration_is_idempotent(user_client):
    client, auth_headers = user_client
    payload = {"fcm_token": "dev-fcm-token-1", "platform": "android"}
    first = await client.post(
        "/api/v1/notifications/device-token", json=payload, headers=auth_headers
    )
    second = await client.post(
        "/api/v1/notifications/device-token", json=payload, headers=auth_headers
    )
    assert first.status_code == second.status_code == 200


@pytest.mark.asyncio
async def test_admin_generates_upcoming_notifications(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])
    await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)

    first = await client.post("/api/v1/notifications/admin/generate", headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["created"] >= 1

    second = await client.post("/api/v1/notifications/admin/generate", headers=auth_headers)
    assert second.json()["created"] == 0
