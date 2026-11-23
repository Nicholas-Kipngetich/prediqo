"""Aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    fixtures,
    monetization,
    performance,
    predictions,
    system,
    users,
)

router = APIRouter()
router.include_router(system.router)
router.include_router(fixtures.router)
router.include_router(predictions.router)
router.include_router(performance.router)
router.include_router(monetization.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(admin.router)
