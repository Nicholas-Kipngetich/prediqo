"""Token verification with a strict dev-only test mode.

Production always uses Firebase. Dev mode is honoured only when
ENVIRONMENT=development AND AUTH_MODE=dev; it accepts one static token.
"""

import asyncio
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import settings
from app.core.errors import UnauthorizedError


@dataclass(frozen=True)
class AuthContext:
    firebase_uid: str
    email: str | None = None
    display_name: str | None = None


class TokenVerifier:
    async def verify(self, token: str) -> AuthContext:
        raise NotImplementedError


class DevTokenVerifier(TokenVerifier):
    """Never enabled outside development."""

    def __init__(self, token: str) -> None:
        self._token = token

    async def verify(self, token: str) -> AuthContext:
        if token != self._token:
            raise UnauthorizedError("Invalid development token.")
        return AuthContext(
            firebase_uid="dev-firebase-uid",
            email="dev@prediqo.local",
            display_name="Prediqo Developer",
        )


class FirebaseTokenVerifier(TokenVerifier):
    """Verifies Firebase ID tokens using the Admin SDK.

    The SDK is imported lazily so local tests do not need its native dependencies.
    """

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id

    def _verify_sync(self, token: str) -> AuthContext:
        import firebase_admin
        from firebase_admin import auth, credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                credentials.ApplicationDefault(),
                {"projectId": self._project_id},
            )
        decoded = auth.verify_id_token(token)
        uid = decoded.get("uid")
        if not uid:
            raise UnauthorizedError("Token contains no subject.")
        return AuthContext(
            firebase_uid=uid,
            email=decoded.get("email"),
            display_name=decoded.get("name"),
        )

    async def verify(self, token: str) -> AuthContext:
        return await asyncio.to_thread(self._verify_sync, token)


@lru_cache
def get_token_verifier() -> TokenVerifier:
    if settings.environment == "development" and settings.auth_mode == "dev":
        return DevTokenVerifier(settings.dev_auth_token)
    return FirebaseTokenVerifier(settings.firebase_project_id)
