"""Development-only email/password authentication helpers.

Passwords are hashed with PBKDF2. Tokens are HMAC-signed and contain only the
firebase_uid used to look up the user. This mode is disabled outside development.
"""

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ConflictError, UnauthorizedError
from app.models.dev_credentials import DevCredential
from app.models.identity import Role, RoleCode, User, UserStatus
from app.services.user_service import ensure_seed_roles

TOKEN_PREFIX = "devauth."
TOKEN_TTL_HOURS = 24 * 7


def _dev_mode() -> bool:
    return settings.environment == "development" and settings.auth_mode == "dev"


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000).hex()


def _sign(payload: str) -> str:
    return hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def create_token(firebase_uid: str) -> str:
    raw = json.dumps(
        {
            "uid": firebase_uid,
            "exp": (datetime.now(UTC) + timedelta(hours=TOKEN_TTL_HOURS)).isoformat(),
        }
    ).encode()
    payload = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return f"{TOKEN_PREFIX}{payload}.{_sign(payload)}"


def parse_token(token: str) -> str:
    if not token.startswith(TOKEN_PREFIX):
        raise UnauthorizedError("Invalid development token.")
    try:
        payload_part, signature = token[len(TOKEN_PREFIX) :].rsplit(".", 1)
        if not hmac.compare_digest(signature, _sign(payload_part)):
            raise UnauthorizedError("Invalid development token.")
        padded = payload_part + "=" * (-len(payload_part) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded))
        expires = datetime.fromisoformat(data["exp"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise UnauthorizedError("Development token has expired.")
        return str(data["uid"])
    except UnauthorizedError:
        raise
    except Exception as exc:
        raise UnauthorizedError("Invalid development token.") from exc


async def register(
    session: AsyncSession, email: str, password: str, display_name: str | None
) -> tuple[User, str]:
    if not _dev_mode():
        raise ConflictError("Development authentication is disabled.")
    if len(password) < 6:
        raise ConflictError("Password must be at least 6 characters.")
    email = email.strip().lower()
    firebase_uid = f"dev:{email}"

    existing = (
        await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("An account with this email already exists.")

    await ensure_seed_roles(session)
    role = (await session.execute(select(Role).where(Role.code == RoleCode.USER))).scalar_one()
    user = User(
        id=uuid.uuid4(),
        firebase_uid=firebase_uid,
        email=email,
        display_name=display_name or email.split("@")[0],
        status=UserStatus.ACTIVE,
    )
    user.roles.append(role)
    session.add(user)
    await session.flush()

    salt = secrets.token_hex(16)
    session.add(
        DevCredential(
            user_id=user.id,
            salt=salt,
            password_hash=_hash_password(password, salt),
        )
    )
    await session.commit()
    return user, create_token(firebase_uid)


async def login(session: AsyncSession, email: str, password: str) -> tuple[User, str]:
    if not _dev_mode():
        raise ConflictError("Development authentication is disabled.")
    email = email.strip().lower()
    firebase_uid = f"dev:{email}"
    user = (
        await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    ).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid email or password.")
    credential = await session.get(DevCredential, user.id)
    if credential is None:
        raise UnauthorizedError("Invalid email or password.")
    if not hmac.compare_digest(credential.password_hash, _hash_password(password, credential.salt)):
        raise UnauthorizedError("Invalid email or password.")
    return user, create_token(firebase_uid)
