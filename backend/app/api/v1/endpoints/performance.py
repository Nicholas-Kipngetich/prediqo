"""Performance centre endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.performance import BreakdownOut, CalibrationOut, OverviewOut
from app.services.performance_service import breakdown, calibration, overview

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/overview", response_model=OverviewOut)
async def performance_overview(
    session: AsyncSession = Depends(get_session),
) -> OverviewOut:
    return OverviewOut(**(await overview(session)).__dict__)


@router.get("/breakdown", response_model=list[BreakdownOut])
async def performance_breakdown(
    session: AsyncSession = Depends(get_session),
) -> list[BreakdownOut]:
    return [BreakdownOut(**row.__dict__) for row in await breakdown(session)]


@router.get("/calibration", response_model=list[CalibrationOut])
async def performance_calibration(
    session: AsyncSession = Depends(get_session),
) -> list[CalibrationOut]:
    return [CalibrationOut(**row.__dict__) for row in await calibration(session)]
