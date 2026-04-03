"""Метрики качества поиска.

Набор метрик и обоснование выбора:

1. MRR (Mean Reciprocal Rank)
   - Показывает, насколько высоко в выдаче находится первый релевантный результат
   - Критично для поиска, где пользователь обычно кликает на первый подходящий результат
   - Чем ближе к 1.0 — тем лучше

2. nDCG@k (Normalized Discounted Cumulative Gain)
   - Учитывает позицию ВСЕХ релевантных результатов, а не только первого
   - Штрафует за релевантные результаты на низких позициях
   - Стандартная метрика для ранжирования в поиске

3. Precision@k
   - Доля релевантных результатов в топ-k
   - Простая и интерпретируемая: "из 10 результатов сколько реально полезных?"
   - Используем k=5, k=10, k=20

4. CTR (Click-Through Rate)
   - Реальная метрика вовлечённости: какой % результатов кликают
   - Позволяет отследить деградацию поиска в реальном времени

5. Zero-Result Rate
   - % запросов, не вернувших результатов
   - Высокий показатель = проблемы с покрытием словаря/синонимов

6. Mean Position of Click
   - Средняя позиция, на которую кликает пользователь
   - Если пользователи кликают далеко от топа — ранжирование плохое

7. Personalization Lift
   - Сравнение CTR/MRR с персонализацией vs без
   - Ключевая метрика для оценки эффекта персонализации

8. Session Success Rate
   - % поисковых сессий, закончившихся кликом/покупкой
   - Общий индикатор здоровья поиска
"""
import math
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import SearchEvent, SearchMetricSnapshot

logger = logging.getLogger(__name__)


def calc_mrr(ranked_results: list[dict], relevant_ids: set[str]) -> float:
    """Mean Reciprocal Rank."""
    for i, item in enumerate(ranked_results, 1):
        if item["id"] in relevant_ids:
            return 1.0 / i
    return 0.0


def calc_ndcg(ranked_results: list[dict], relevant_ids: set[str], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain @ k."""
    dcg = 0.0
    for i, item in enumerate(ranked_results[:k], 1):
        rel = 1.0 if item["id"] in relevant_ids else 0.0
        dcg += rel / math.log2(i + 1)

    # Ideal DCG
    ideal_rels = sorted([1.0 if item["id"] in relevant_ids else 0.0 for item in ranked_results[:k]], reverse=True)
    idcg = sum(rel / math.log2(i + 1) for i, rel in enumerate(ideal_rels, 1))

    return dcg / idcg if idcg > 0 else 0.0


def calc_precision_at_k(ranked_results: list[dict], relevant_ids: set[str], k: int = 10) -> float:
    """Precision @ k."""
    if not ranked_results[:k]:
        return 0.0
    relevant_in_top_k = sum(1 for item in ranked_results[:k] if item["id"] in relevant_ids)
    return relevant_in_top_k / min(k, len(ranked_results))


async def _compute_mrr_from_events(db: AsyncSession, since: datetime) -> float:
    """Estimate MRR from search_events by treating clicked products as relevant.

    For each (user_id, query) pair we find the click position and compute
    reciprocal rank.  Multiple clicks per query → take the highest-rank click.
    """
    # Fetch all clicks with position in the window
    click_rows = await db.execute(
        select(
            SearchEvent.user_id,
            SearchEvent.query,
            SearchEvent.position,
        ).where(
            SearchEvent.event_type == "click",
            SearchEvent.position.is_not(None),
            SearchEvent.created_at >= since,
        )
    )
    clicks = click_rows.all()

    if not clicks:
        return 0.0

    # Group by (user_id, query): take best (lowest) position per group
    best_pos: dict[tuple, int] = {}
    for user_id, query, position in clicks:
        key = (user_id, query or "")
        if key not in best_pos or position < best_pos[key]:
            best_pos[key] = position

    # MRR: position is 1-based in our tracking
    reciprocal_ranks = []
    for pos in best_pos.values():
        if pos and pos > 0:
            reciprocal_ranks.append(1.0 / pos)
        else:
            reciprocal_ranks.append(0.0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


async def _compute_precision_at_k_from_events(
    db: AsyncSession, since: datetime, k: int = 10
) -> float:
    """Estimate Precision@k from search_events.

    For each search query session (user_id, query) we treat all clicked
    product_ids as relevant.  We then assume the user was shown results in
    positions 1..max_position and check how many clicks fell in positions 1..k.

    This is an approximation: we do not have the full ranked list, only the
    positions that were clicked.
    """
    # Clicks with position <= k (relevant items shown in top-k)
    clicks_in_topk = await db.scalar(
        select(func.count()).where(
            SearchEvent.event_type == "click",
            SearchEvent.position.is_not(None),
            SearchEvent.position <= k,
            SearchEvent.created_at >= since,
        )
    ) or 0

    # Total number of distinct search sessions
    total_searches = await db.scalar(
        select(func.count()).where(
            SearchEvent.event_type == "search",
            SearchEvent.created_at >= since,
        )
    ) or 0

    if total_searches == 0:
        return 0.0

    # Each search session shows k results; precision = relevant_in_topk / (k * sessions)
    # We cap denominator at total_searches * k to avoid division by zero
    return clicks_in_topk / (total_searches * k)


async def compute_live_metrics(db: AsyncSession, hours: int = 24) -> dict:
    """Посчитать живые метрики за последние N часов."""
    since = datetime.utcnow() - timedelta(hours=hours)

    # Всего поисков
    total_searches = await db.scalar(
        select(func.count()).where(
            SearchEvent.event_type == "search",
            SearchEvent.created_at >= since,
        )
    ) or 0

    # Всего кликов
    total_clicks = await db.scalar(
        select(func.count()).where(
            SearchEvent.event_type == "click",
            SearchEvent.created_at >= since,
        )
    ) or 0

    # CTR
    ctr = total_clicks / total_searches if total_searches > 0 else 0.0

    # Средняя позиция клика
    avg_click_pos = await db.scalar(
        select(func.avg(SearchEvent.position)).where(
            SearchEvent.event_type == "click",
            SearchEvent.position.is_not(None),
            SearchEvent.created_at >= since,
        )
    )

    # Уникальные пользователи
    unique_users = await db.scalar(
        select(func.count(func.distinct(SearchEvent.user_id))).where(
            SearchEvent.created_at >= since,
        )
    ) or 0

    # Покупки
    total_purchases = await db.scalar(
        select(func.count()).where(
            SearchEvent.event_type == "purchase",
            SearchEvent.created_at >= since,
        )
    ) or 0

    # Session success rate (сессии с хотя бы одним кликом)
    users_with_clicks = await db.scalar(
        select(func.count(func.distinct(SearchEvent.user_id))).where(
            SearchEvent.event_type == "click",
            SearchEvent.created_at >= since,
        )
    ) or 0
    users_who_searched = await db.scalar(
        select(func.count(func.distinct(SearchEvent.user_id))).where(
            SearchEvent.event_type == "search",
            SearchEvent.created_at >= since,
        )
    ) or 0
    session_success = users_with_clicks / users_who_searched if users_who_searched > 0 else 0.0

    # MRR — computed from click positions in the event log
    mrr = await _compute_mrr_from_events(db, since)

    # Precision@k for k=5, k=10, k=20
    precision_at_5 = await _compute_precision_at_k_from_events(db, since, k=5)
    precision_at_10 = await _compute_precision_at_k_from_events(db, since, k=10)
    precision_at_20 = await _compute_precision_at_k_from_events(db, since, k=20)

    return {
        "period_hours": hours,
        "total_searches": total_searches,
        "total_clicks": total_clicks,
        "total_purchases": total_purchases,
        "unique_users": unique_users,
        "ctr": round(ctr, 4),
        "avg_click_position": round(float(avg_click_pos), 2) if avg_click_pos else None,
        "session_success_rate": round(session_success, 4),
        "mrr": round(mrr, 4),
        "precision_at_5": round(precision_at_5, 4),
        "precision_at_10": round(precision_at_10, 4),
        "precision_at_20": round(precision_at_20, 4),
    }


async def save_metric_snapshot(db: AsyncSession, name: str, value: float, k: int | None = None, segment: str = "all"):
    """Сохранить снимок метрики."""
    snapshot = SearchMetricSnapshot(
        metric_name=name,
        metric_value=value,
        k=k,
        user_segment=segment,
    )
    db.add(snapshot)
    await db.commit()


async def save_live_metric_snapshots(db: AsyncSession, hours: int = 24):
    """Вычислить живые метрики и сохранить снимки для всех ключевых показателей."""
    metrics = await compute_live_metrics(db, hours=hours)

    snapshot_map = {
        "ctr": (metrics["ctr"], None),
        "session_success_rate": (metrics["session_success_rate"], None),
        "mrr": (metrics["mrr"], None),
        "precision_at_k": (metrics["precision_at_5"], 5),
        "precision_at_10": (metrics["precision_at_10"], 10),
        "precision_at_20": (metrics["precision_at_20"], 20),
    }
    for name, (value, k) in snapshot_map.items():
        await save_metric_snapshot(db, name, value, k=k)

    logger.info(
        "Metric snapshots saved — MRR=%.4f  P@10=%.4f  CTR=%.4f",
        metrics["mrr"],
        metrics["precision_at_10"],
        metrics["ctr"],
    )
    return metrics


async def get_metric_history(db: AsyncSession, metric_name: str, days: int = 7) -> list[dict]:
    """Получить историю метрики для графика."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(SearchMetricSnapshot)
        .where(
            SearchMetricSnapshot.metric_name == metric_name,
            SearchMetricSnapshot.created_at >= since,
        )
        .order_by(SearchMetricSnapshot.created_at)
    )
    rows = result.scalars().all()
    return [
        {
            "value": r.metric_value,
            "k": r.k,
            "segment": r.user_segment,
            "timestamp": r.created_at.isoformat(),
        }
        for r in rows
    ]
