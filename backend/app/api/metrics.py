"""API роуты метрик качества поиска."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_tracker
from app.personalization.metrics import compute_live_metrics, get_metric_history
from app.personalization.tracker import PersonalizationTracker

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/live")
async def live_metrics(
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Живые метрики за последние N часов."""
    return await compute_live_metrics(db, hours)


@router.get("/history/{metric_name}")
async def metric_history(
    metric_name: str,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """История метрики для графика."""
    data = await get_metric_history(db, metric_name, days)
    return {"metric": metric_name, "data": data}


@router.get("/user/{user_id}")
async def user_stats(
    user_id: str,
    tracker: PersonalizationTracker = Depends(get_tracker),
):
    """Статистика персонализации пользователя."""
    return await tracker.get_user_stats(user_id)
