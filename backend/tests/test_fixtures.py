"""Phase 3 — sports data integration tests (sample adapter, clearly labelled)."""

import pytest

from tests.conftest import promote_to_admin


@pytest.fixture
async def synced_client(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])
    response = await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)
    assert response.status_code == 200
    return client, auth_headers, response.json()


@pytest.mark.asyncio
async def test_sync_returns_counts_and_no_sample_leak(synced_client):
    _, _, result = synced_client
    assert result["competitions"] == 3
    assert result["teams"] == 8
    assert result["fixtures"] == 28
    assert result["skipped"] == 0


@pytest.mark.asyncio
async def test_fixtures_are_labelled_and_paginated(synced_client):
    client, auth_headers, _ = synced_client
    response = await client.get("/api/v1/fixtures?page=1&page_size=3")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 28
    assert len(data["items"]) == 3
    assert all(item["is_sample_data"] for item in data["items"])
    assert "probabilities" not in data["items"][0]
    assert "corners" not in data["items"][0]


@pytest.mark.asyncio
async def test_fixture_filters(synced_client):
    client, _, _ = synced_client
    scheduled = await client.get("/api/v1/fixtures?status=SCHEDULED")
    finished = await client.get("/api/v1/fixtures?status=FINISHED")

    assert scheduled.status_code == finished.status_code == 200
    assert scheduled.json()["total"] == 7
    assert finished.json()["total"] == 21


@pytest.mark.asyncio
async def test_fixture_detail_and_trending(synced_client):
    client, _, _ = synced_client
    listing = (await client.get("/api/v1/fixtures")).json()
    fixture_id = listing["items"][0]["id"]

    detail = await client.get(f"/api/v1/fixtures/{fixture_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == fixture_id
    assert detail.json()["home_team"]["name"].startswith("Sample")

    trending = await client.get("/api/v1/fixtures/trending")
    assert trending.status_code == 200
    assert trending.json()["total"] >= 1
    assert all(item["status"] == "SCHEDULED" for item in trending.json()["items"])


@pytest.mark.asyncio
async def test_competitions_and_teams(synced_client):
    client, _, _ = synced_client
    competitions = await client.get("/api/v1/competitions")
    teams = await client.get("/api/v1/teams")

    assert competitions.status_code == teams.status_code == 200
    assert len(competitions.json()) == 3
    assert len(teams.json()) == 8
    assert all(item["is_sample_data"] for item in teams.json())


@pytest.mark.asyncio
async def test_search_returns_matching_fixtures(synced_client):
    client, auth_headers, _ = synced_client
    response = await client.get("/api/v1/search?q=Sample&limit=50")

    assert response.status_code == 200
    data = response.json()
    assert len(data["competitions"]) == 3
    assert len(data["teams"]) == 8
    assert len(data["fixtures"]) == 28


@pytest.mark.asyncio
async def test_sync_jobs_are_recorded(synced_client):
    client, auth_headers, _ = synced_client
    jobs = await client.get("/api/v1/admin/sync/jobs", headers=auth_headers)

    assert jobs.status_code == 200
    assert jobs.json()[0]["status"] == "SUCCESS"
    assert jobs.json()[0]["records_processed"] == 39
