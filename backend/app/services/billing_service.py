"""Google Play purchase verification with a strict dev-only verifier.

Production verification uses the Google Play Developer API and a service account.
The client's claim of a successful purchase is never trusted.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.core.errors import ConflictError


@dataclass(frozen=True)
class VerifiedPurchase:
    product_id: str
    purchase_token: str
    order_id: str
    purchased_at: datetime
    expires_at: datetime | None = None


class PurchaseVerifier:
    async def verify(
        self, product_id: str, purchase_token: str, subscription: bool = False
    ) -> VerifiedPurchase:
        raise NotImplementedError


class DevPurchaseVerifier(PurchaseVerifier):
    """Development-only. Never enabled outside development."""

    async def verify(
        self, product_id: str, purchase_token: str, subscription: bool = False
    ) -> VerifiedPurchase:
        if settings.environment != "development" or settings.auth_mode != "dev":
            raise ConflictError("Dev purchase verification is disabled.")
        digest = hashlib.sha256(purchase_token.encode()).hexdigest()[:24]
        return VerifiedPurchase(
            product_id=product_id,
            purchase_token=purchase_token,
            order_id=f"dev-order-{digest}",
            purchased_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30) if subscription else None,
        )


class GooglePlayVerifier(PurchaseVerifier):
    def _access_token(self) -> str:
        if not settings.google_play_service_account_json:
            raise ConflictError("Google Play service account is not configured.")
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            settings.google_play_service_account_json,
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
        if not credentials.token:
            from google.auth.transport.requests import Request

            credentials.refresh(Request())
        return credentials.token or ""

    async def verify(
        self, product_id: str, purchase_token: str, subscription: bool = False
    ) -> VerifiedPurchase:
        kind = "subscriptions" if subscription else "products"
        url = (
            "https://androidpublisher.googleapis.com/androidpublisher/v3/"
            f"applications/{settings.google_play_package_name}/purchases/{kind}/"
            f"{quote(product_id, safe='')}/tokens/{quote(purchase_token, safe='')}"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url, headers={"Authorization": f"Bearer {self._access_token()}"}
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ConflictError(f"Google Play verification failed: {exc}") from exc

        if not subscription and payload.get("purchaseState") != 0:
            raise ConflictError("Purchase is not in a completed state.")
        if subscription and not payload.get("expiryTimeMillis"):
            raise ConflictError("Subscription response has no expiry time.")

        purchase_time = payload.get("purchaseTimeMillis")
        purchased_at = (
            datetime.fromtimestamp(int(purchase_time) / 1000, tz=UTC)
            if purchase_time
            else datetime.now(UTC)
        )
        expiry = payload.get("expiryTimeMillis")
        return VerifiedPurchase(
            product_id=product_id,
            purchase_token=purchase_token,
            order_id=str(payload.get("orderId") or f"play-{purchase_token[:24]}"),
            purchased_at=purchased_at,
            expires_at=(datetime.fromtimestamp(int(expiry) / 1000, tz=UTC) if expiry else None),
        )


@lru_cache
def get_purchase_verifier() -> PurchaseVerifier:
    if settings.environment == "development" and settings.auth_mode == "dev":
        return DevPurchaseVerifier()
    return GooglePlayVerifier()
