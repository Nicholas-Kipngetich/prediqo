"""Development-only email or phone authentication with verification codes.

This mode is disabled outside development. Production uses Firebase.
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
from app.services.mail_service import send_verification_code
from app.services.user_service import ensure_seed_roles

TOKEN_PREFIX = "devauth."
TOKEN_TTL_HOURS = 24 * 7


def _dev_mode() -> bool:
    return settings.environment == "development" and settings.auth_mode == "dev"


def _normalise_identifier(email: str | None, phone: str | None) -> str:
    if bool(email) == bool(phone):
        raise ConflictError("Provide exactly one of email or phone.")
    if email:
        return email.strip().lower()
    if phone is None:
        raise ConflictError("A valid phone number is required.")
    digits = "".join(character for character in phone if character.isdigit())
    if len(digits) < 7:
        raise ConflictError("A valid phone number is required.")
    return digits


def _firebase_uid(identifier: str) -> str:
    return f"dev:{identifier}"


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
    session: AsyncSession,
    email: str | None,
    phone: str | None,
    password: str,
    display_name: str | None,
) -> tuple[User, str]:
    if not _dev_mode():
        raise ConflictError("Development authentication is disabled.")
    if len(password) < 6:
        raise ConflictError("Password must be at least 6 characters.")
    identifier = _normalise_identifier(email, phone)
    firebase_uid = _firebase_uid(identifier)

    existing = (
        await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("An account with this identifier already exists.")

    await ensure_seed_roles(session)
    role = (await session.execute(select(Role).where(Role.code == RoleCode.USER))).scalar_one()
    user = User(
        id=uuid.uuid4(),
        firebase_uid=firebase_uid,
        email=email.strip().lower() if email else None,
        phone=_normalise_identifier(None, phone) if phone else None,
        display_name=display_name or (email.split("@")[0] if email else identifier),
        status=UserStatus.PENDING,
    )
    user.roles.append(role)
    session.add(user)
    await session.flush()

    salt = secrets.token_hex(16)
    code = f"{secrets.randbelow(900000) + 100000:06d}"
    session.add(
        DevCredential(
            user_id=user.id,
            salt=salt,
            password_hash=_hash_password(password, salt),
            verification_code_hash=_hash_password(code, salt),
            verification_expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.dev_verification_code_ttl_minutes),
        )
    )
    await session.commit()
    if email:
        send_verification_code(email.strip().lower(), code)
    return user, code


async def verify_code(
    session: AsyncSession, email: str | None, phone: str | None, code: str
) -> tuple[User, str]:
    if not _dev_mode():
        raise ConflictError("Development authentication is disabled.")
    identifier = _normalise_identifier(email, phone)
    firebase_uid = _firebase_uid(identifier)
    user = (
        await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    ).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid verification code.")
    credential = await session.get(DevCredential, user.id)
    if credential is None or credential.verification_code_hash is None:
        raise UnauthorizedError("Invalid verification code.")
    if credential.verified_at is not None:
        return user, create_token(firebase_uid)
    if credential.verification_expires_at is not None:
        expires_at = credential.verification_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise UnauthorizedError("Verification code has expired.")
    if not hmac.compare_digest(
        credential.verification_code_hash, _hash_password(code, credential.salt)
    ):
        raise UnauthorizedError("Invalid verification code.")
    credential.verified_at = datetime.now(UTC)
    user.status = UserStatus.ACTIVE
    await session.commit()
    return user, create_token(firebase_uid)


async def resend_code(session: AsyncSession, email: str | None, phone: str | None) -> str:
    if not _dev_mode():
        raise ConflictError("Development authentication is disabled.")
    identifier = _normalise_identifier(email, phone)
    firebase_uid = _firebase_uid(identifier)
    user = (
        await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    ).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Account not found.")
    credential = await session.get(DevCredential, user.id)
    if credential is None:
        raise UnauthorizedError("Account not found.")
    if credential.verified_at is not None:
        raise ConflictError("Account is already verified.")
    code = f"{secrets.randbelow(900000) + 100000:06d}"
    salt = credential.salt
    credential.verification_code_hash = _hash_password(code, salt)
    credential.verification_expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.dev_verification_code_ttl_minutes
    )
    await session.commit()
    if email:
        send_verification_code(email.strip().lower(), code)
    return code


async def login(
    session: AsyncSession, email: str | None, phone: str | None, password: str
) -> tuple[User, str]:
    if not _dev_mode():
        raise ConflictError("Development authentication is disabled.")
    identifier = _normalise_identifier(email, phone)
    firebase_uid = _firebase_uid(identifier)
    user = (
        await session.execute(select(User).where(User.firebase_uid == firebase_uid))
    ).scalar_one_or_none()
    if user is None or user.status != UserStatus.ACTIVE:
        raise UnauthorizedError("Invalid email or password.")
    credential = await session.get(DevCredential, user.id)
    if credential is None or credential.verified_at is None:
        raise UnauthorizedError("Account is not verified.")
    if not hmac.compare_digest(credential.password_hash, _hash_password(password, credential.salt)):
        raise UnauthorizedError("Invalid email or password.")
    return user, create_token(firebase_uid)
