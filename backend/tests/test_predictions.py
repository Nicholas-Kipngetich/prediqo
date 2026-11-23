"""Phase 5 — prediction publication tests."""

import json

import pytest
from sqlalchemy import select

from tests.conftest import promote_to_admin


@pytest.fixture
async def generated_client(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])
    await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)
    response = await client.post("/api/v1/predictions/generate", headers=auth_headers)
    assert response.status_code == 200
    return client, auth_headers, response.json()


@pytest.mark.asyncio
async def test_generation_publishes_four_markets_per_fixture(generated_client):
    _, _, result = generated_client
    assert result["published"] == 28  # 7 scheduled fixtures x 4 markets
    assert result["suppressed"] == 0


@pytest.mark.asyncio
async def test_prediction_feed_has_valid_probabilities(generated_client):
    client, _, _ = generated_client
    response = await client.get("/api/v1/predictions?market=1X2")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 7
    for item in items:
        assert sum(item["probabilities_bp"].values()) == 10000
        assert item["model_version"] == "v1.0.0"
        assert item["status"] == "PENDING"
        assert item["is_sample_data"] is True
        assert item["explanation"]["type"] == "deterministic_v1"


@pytest.mark.asyncio
async def test_prediction_detail_and_immutability(generated_client):
    client, auth_headers, _ = generated_client
    listing = (await client.get("/api/v1/predictions?market=BTTS")).json()
    prediction_id = listing[0]["id"]

    detail = await client.get(f"/api/v1/predictions/{prediction_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == prediction_id

    again = await client.post("/api/v1/predictions/generate", headers=auth_headers)
    assert again.status_code == 200
    assert again.json()["published"] == 0
    assert again.json()["skipped"] == 7  # one skip per already-published fixture


@pytest.mark.asyncio
async def test_snapshot_records_model_and_data_as_of(generated_client):
    from app.core.database import get_session_factory
    from app.models.predictions import Prediction

    _, _, _ = generated_client
    async with get_session_factory()() as session:
        prediction = (await session.execute(select(Prediction))).scalars().first()
        snapshot = json.loads(prediction.snapshot_json)
        assert snapshot["model_version"] == "v1.0.0"
        assert snapshot["is_sample_data"] is True
        assert "expected_home_goals" in snapshot
