"""Prediqo FastAPI application entry point."""

import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import app.models as _models  # noqa: F401
from app import __version__
from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, validation_error_handler

app = FastAPI(
    title="Prediqo API",
    description="AI-powered football analytics and prediction platform.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


async def _db_status() -> str:
    try:
        from app.core.database import get_session_factory

        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"


async def _redis_status() -> str:
    try:
        import redis.asyncio as redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
        )
        await client.ping()
        await client.aclose()
        return "ok"
    except Exception:
        return "unavailable"


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness endpoint. Dependency status is reported but never fails the request."""
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.environment,
        "db": await _db_status(),
        "redis": await _redis_status(),
    }
