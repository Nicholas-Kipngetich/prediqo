"""Aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, system, users

router = APIRouter()
router.include_router(system.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(admin.router)
