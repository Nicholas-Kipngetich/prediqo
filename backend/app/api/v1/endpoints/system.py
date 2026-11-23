"""System status endpoints (only /health lives at the root; see app.main)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status", tags=["system"])
async def api_status() -> dict[str, str]:
    return {"api": "ok", "version": "v1"}
