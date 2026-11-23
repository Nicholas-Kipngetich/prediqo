"""Aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import system

router = APIRouter()
router.include_router(system.router)
