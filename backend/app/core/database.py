"""SQLAlchemy async engine, session factory and declarative base.

The engine is created lazily so importing the application (and running unit tests)
never requires a live PostgreSQL driver or connection.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


@lru_cache
def get_engine():
    url = settings.async_database_url
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    return create_async_engine(url, pool_pre_ping=True, echo=False)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
