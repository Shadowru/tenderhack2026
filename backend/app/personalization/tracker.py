"""Трекинг поведения пользователя и построение профиля для персонализации."""
import json
import logging
from datetime import datetime, timedelta, timezone

import asyncpg
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

# Веса событий для расчёта интереса к категории/товару
EVENT_WEIGHTS = {
    "search": 1.0,
    "click": 3.0,
    "cart": 5.0,
    "purchase": 10.0,
}

# Экспоненциальное затухание: вес = base_weight * decay^(days_ago)
DECAY_FACTOR = 0.95
MAX_HISTORY_DAYS = 90


class PersonalizationTracker:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def track_event(
        self,
        user_id: str,
        event_type: str,
        query: str = "",
        product_id: str = "",
        category: str = "",
        position: int | None = None,
    ):
        """Записать событие пользователя."""
        event = {
            "type": event_type,
            "query": query,
            "product_id": product_id,
            "category": category,
            "position": position,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        key = f"user:{user_id}:events"
        await self.redis.lpush(key, json.dumps(event))
        await self.redis.ltrim(key, 0, 999)  # max 1000 событий
        await self.redis.expire(key, MAX_HISTORY_DAYS * 86400)

        # Инкрементировать счётчики категорий
        if category:
            cat_key = f"user:{user_id}:categories"
            weight = EVENT_WEIGHTS.get(event_type, 1.0)
            await self.redis.zincrby(cat_key, weight, category)
            await self.redis.expire(cat_key, MAX_HISTORY_DAYS * 86400)

        # Инкрементировать счётчики товаров
        if product_id:
            prod_key = f"user:{user_id}:products"
            weight = EVENT_WEIGHTS.get(event_type, 1.0)
            await self.redis.zincrby(prod_key, weight, product_id)
            await self.redis.expire(prod_key, MAX_HISTORY_DAYS * 86400)

    async def load_buyer_history(self, user_id: str):
        """Cold start: load purchase history from buyer_category_weights into Redis.

        Queries the pre-computed buyer_category_weights PG table and populates
        the user's category sorted set in Redis. Skips if profile already exists.
        """
        cat_key = f"user:{user_id}:categories"
        existing = await self.redis.exists(cat_key)
        if existing:
            return  # already loaded, skip cold start

        try:
            conn = await asyncpg.connect(
                user=settings.pg_user, password=settings.pg_password,
                database=settings.pg_database, host=settings.pg_host,
            )
            try:
                rows = await conn.fetch(
                    "SELECT category, weight FROM buyer_category_weights WHERE buyer_inn = $1",
                    user_id,
                )
            finally:
                await conn.close()
        except Exception as e:
            logger.warning("load_buyer_history failed for user %s: %s", user_id, e)
            return

        if not rows:
            return

        # Populate Redis sorted set with category weights from historical contracts.
        # Use a pipeline for efficiency.
        pipe = self.redis.pipeline()
        for row in rows:
            category = row['category']
            # Historical data gets 70% weight — live events are more impactful
            weight = float(row['weight']) * EVENT_WEIGHTS['purchase'] * 0.7
            pipe.zadd(cat_key, {category: weight})
        pipe.expire(cat_key, MAX_HISTORY_DAYS * 86400)
        await pipe.execute()

        logger.debug(
            "Cold-start loaded %d category weights for user %s", len(rows), user_id
        )

    async def get_user_boosts(
        self,
        user_id: str,
        top_n: int = 50,
    ) -> tuple[dict[str, float], dict[str, float]]:
        """
        Получить персональные бусты для ранжирования с учётом затухания.

        Returns:
            product_boosts: {product_id: boost} for top-N products
            category_boosts: {category: boost} for top categories

        Decay is applied: events are read from the event log, and each event's
        weight is multiplied by DECAY_FACTOR^(days_since_event).  The sorted-set
        scores are used as a fast approximation baseline; the decay pass refines
        the top products.
        """
        # --- Product boosts with decay ---
        prod_key = f"user:{user_id}:products"
        top_products_raw = await self.redis.zrevrange(prod_key, 0, top_n - 1, withscores=True)

        product_boosts: dict[str, float] = {}
        if top_products_raw:
            # Refine scores with temporal decay using the event log
            events_key = f"user:{user_id}:events"
            raw_events = await self.redis.lrange(events_key, 0, 999)
            now = datetime.now(timezone.utc)

            # Build decayed scores per product
            decayed: dict[str, float] = {}
            for raw in raw_events:
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                pid = ev.get("product_id", "")
                if not pid:
                    continue
                base_weight = EVENT_WEIGHTS.get(ev.get("type", ""), 1.0)
                try:
                    ts = datetime.fromisoformat(ev["ts"])
                except Exception:
                    ts = now
                days_ago = max(0.0, (now - ts).total_seconds() / 86400.0)
                decay = DECAY_FACTOR ** days_ago
                decayed[pid] = decayed.get(pid, 0.0) + base_weight * decay

            # Use decayed scores when available, fall back to sorted-set score
            combined: dict[str, float] = {}
            for pid_raw, ss_score in top_products_raw:
                pid = pid_raw.decode() if isinstance(pid_raw, bytes) else pid_raw
                combined[pid] = decayed.get(pid, ss_score)

            max_score = max(combined.values(), default=0.0)
            if max_score > 0:
                for pid, score in combined.items():
                    product_boosts[pid] = 1.0 + (score / max_score)

        # --- Category boosts with decay ---
        cat_key = f"user:{user_id}:categories"
        top_cats_raw = await self.redis.zrevrange(cat_key, 0, 19, withscores=True)

        category_boosts: dict[str, float] = {}
        if top_cats_raw:
            max_cat_score = max(score for _, score in top_cats_raw)
            if max_cat_score > 0:
                for cat_raw, score in top_cats_raw:
                    cat = cat_raw.decode() if isinstance(cat_raw, bytes) else cat_raw
                    # Normalize to [1.0, 1.05] — gentle nudge, text relevance dominates
                    category_boosts[cat] = 1.0 + 0.05 * (score / max_cat_score)

        return product_boosts, category_boosts

    async def get_top_categories(self, user_id: str, top_n: int = 10) -> list[tuple[str, float]]:
        """Топ категорий пользователя."""
        cat_key = f"user:{user_id}:categories"
        cats = await self.redis.zrevrange(cat_key, 0, top_n - 1, withscores=True)
        return [
            (c.decode() if isinstance(c, bytes) else c, s)
            for c, s in cats
        ]

    async def get_user_stats(self, user_id: str) -> dict:
        """Статистика пользователя для дашборда."""
        events_key = f"user:{user_id}:events"
        total = await self.redis.llen(events_key)
        top_cats = await self.get_top_categories(user_id, 5)
        return {
            "user_id": user_id,
            "total_events": total,
            "top_categories": [{"name": c, "score": s} for c, s in top_cats],
        }
