"""Test fixtures. Environment must be set before importing the app."""

import os
import tempfile
from uuid import UUID, uuid4

# A temp file (not :memory:) lets each connection see the same schema when
# NullPool is used. Each request opens two sessions (auth + endpoint).
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"prediqo-test-{uuid4().hex}.db").replace(
    "\\", "/"
)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "development"
os.environ["AUTH_MODE"] = "dev"
os.environ["DEV_AUTH_TOKEN"] = "prediqo-dev-token"

import atexit  # noqa: E402

atexit.register(lambda: os.path.exists(TEST_DB_PATH) and os.remove(TEST_DB_PATH))

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.database import Base, get_engine, get_session_factory  # noqa: E402
from app.main import app  # noqa: E402
from app.models.identity import Role, User  # noqa: E402

TOKEN = "prediqo-dev-token"


@pytest.fixture(autouse=True)
async def reset_database() -> AsyncGenerator[None, None]:
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


async def promote_to_admin(user_id) -> None:
    async with get_session_factory()() as session:
        role = (await session.execute(select(Role).where(Role.code == "ADMIN"))).scalar_one()
        user = await session.get(User, UUID(str(user_id)))
        if role not in user.roles:
            user.roles.append(role)
        await session.commit()
