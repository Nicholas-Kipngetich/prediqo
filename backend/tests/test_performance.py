"""Phase 6 — settlement and performance analytics tests."""

import pytest
from sqlalchemy import select

from app.models.predictions import PredictionSettlement
from app.models.sports import Fixture
from tests.conftest import promote_to_admin


@pytest.fixture
async def settled_client(client, auth_headers):
    profile = (await client.post("/api/v1/auth/verify", headers=auth_headers)).json()
    await promote_to_admin(profile["id"])
    await client.post("/api/v1/admin/sync/trigger", headers=auth_headers)
    await client.post("/api/v1/predictions/generate", headers=auth_headers)

    from app.core.database import get_session_factory

    async with get_session_factory()() as session:
        fixtures = (
            (await session.execute(select(Fixture).where(Fixture.status == "SCHEDULED").limit(4)))
            .scalars()
            .all()
        )
        for index, fixture in enumerate(fixtures):
            fixture.status = "FINISHED"
            fixture.home_score = 2
            fixture.away_score = 1 if index % 2 == 0 else 2
        await session.commit()

    response = await client.post("/api/v1/predictions/settle", headers=auth_headers)
    assert response.status_code == 200
    return client, auth_headers, response.json()


@pytest.mark.asyncio
async def test_settlement_records_are_created(settled_client):
    client, _, result = settled_client
    assert result["settled"] + result["voided"] == 16  # 4 fixtures x 4 markets

    from app.core.database import get_session_factory

    async with get_session_factory()() as session:
        settlements = (await session.execute(select(PredictionSettlement))).scalars().all()
        assert len(settlements) == 16
        assert all(row.source == "fixture_result" for row in settlements)


@pytest.mark.asyncio
async def test_overview_reports_sample_sizes(settled_client):
    client, _, _ = settled_client
    response = await client.get("/api/v1/performance/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["total_predictions"] == 28
    assert data["settled_predictions"] == 16
    assert data["sample_size"] == 16
    assert data["pending"] == 12
    assert data["accuracy"] is not None
    assert 0 <= data["accuracy"] <= 1


@pytest.mark.asyncio
async def test_breakdown_by_market_and_competition(settled_client):
    client, _, _ = settled_client
    response = await client.get("/api/v1/performance/breakdown")

    assert response.status_code == 200
    rows = response.json()
    assert {row["dimension"] for row in rows} == {"market", "competition"}
    assert all(row["total"] >= 1 for row in rows)
    assert all(0 <= row["accuracy"] <= 1 for row in rows)


@pytest.mark.asyncio
async def test_calibration_bins_have_counts(settled_client):
    client, _, _ = settled_client
    response = await client.get("/api/v1/performance/calibration")

    assert response.status_code == 200
    bins = response.json()
    assert sum(item["count"] for item in bins) == 16
    assert all(0 <= item["observed_rate"] <= 1 for item in bins)
