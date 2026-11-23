"""Phase 7 — token ledger and VIP entitlement tests."""

import pytest


@pytest.fixture
async def user_client(client, auth_headers):
    response = await client.post("/api/v1/auth/verify", headers=auth_headers)
    assert response.status_code == 200
    return client, auth_headers


@pytest.mark.asyncio
async def test_packages_are_configurable(user_client):
    client, _ = user_client
    response = await client.get("/api/v1/tokens/packages")

    assert response.status_code == 200
    packages = response.json()
    assert len(packages) == 3
    assert packages[0]["price_minor"] == 9900


@pytest.mark.asyncio
async def test_purchase_credits_tokens_once(user_client):
    client, auth_headers = user_client
    payload = {
        "product_id": "com.prediqo.tokens.starter",
        "purchase_token": "dev-token-purchase-1",
    }
    first = await client.post("/api/v1/tokens/purchases/verify", json=payload, headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["credited_tokens"] == 5
    assert first.json()["balance"] == 5

    duplicate = await client.post(
        "/api/v1/tokens/purchases/verify", json=payload, headers=auth_headers
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["already_credited"] is True
    assert duplicate.json()["balance"] == 5

    balance = await client.get("/api/v1/tokens/balance", headers=auth_headers)
    assert balance.json()["balance"] == 5


@pytest.mark.asyncio
async def test_unlock_debits_and_is_idempotent(user_client):
    client, auth_headers = user_client
    await client.post(
        "/api/v1/tokens/purchases/verify",
        json={
            "product_id": "com.prediqo.tokens.starter",
            "purchase_token": "dev-token-purchase-2",
        },
        headers=auth_headers,
    )
    payload = {"target_type": "prediction", "target_id": "report-1"}
    first = await client.post("/api/v1/tokens/unlock", json=payload, headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["entitlement"] == "token"
    assert first.json()["balance"] == 0

    duplicate = await client.post("/api/v1/tokens/unlock", json=payload, headers=auth_headers)
    assert duplicate.json()["balance"] == 0

    second = await client.post(
        "/api/v1/tokens/unlock",
        json={"target_type": "prediction", "target_id": "report-2"},
        headers=auth_headers,
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_vip_entitlement_skips_token_charge(user_client):
    client, auth_headers = user_client
    subscription = await client.post(
        "/api/v1/subscriptions/verify",
        json={
            "product_id": "com.prediqo.vip.monthly",
            "purchase_token": "dev-vip-purchase-1",
        },
        headers=auth_headers,
    )
    assert subscription.status_code == 200
    assert subscription.json()["is_vip"] is True

    profile = await client.get("/api/v1/users/me", headers=auth_headers)
    assert "VIP_USER" in profile.json()["roles"]

    unlock = await client.post(
        "/api/v1/tokens/unlock",
        json={"target_type": "prediction", "target_id": "report-vip"},
        headers=auth_headers,
    )
    assert unlock.json()["entitlement"] == "vip"
    assert unlock.json()["balance"] == 0

    status = await client.get("/api/v1/subscriptions/status", headers=auth_headers)
    assert status.json()["is_vip"] is True
    assert status.json()["plan_code"] is None or status.json()["plan_code"] == "VIP_MONTHLY"


@pytest.mark.asyncio
async def test_ledger_records_every_movement(user_client):
    client, auth_headers = user_client
    await client.post(
        "/api/v1/tokens/purchases/verify",
        json={
            "product_id": "com.prediqo.tokens.pro",
            "purchase_token": "dev-token-purchase-3",
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/tokens/unlock",
        json={"target_type": "analysis", "target_id": "a-1"},
        headers=auth_headers,
    )
    transactions = await client.get("/api/v1/tokens/transactions", headers=auth_headers)

    assert transactions.status_code == 200
    rows = transactions.json()
    assert [row["type"] for row in rows[:2]] == ["DEBIT", "CREDIT"]
    assert rows[1]["amount"] == 20
    assert rows[0]["balance_after"] == 15
