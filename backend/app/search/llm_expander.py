"""LLM-based query expansion for fuzzy/vague searches.

Uses a local Ollama model to reformulate vague user queries into
concrete product names, then searches ES for each reformulation
and merges results.
"""
import asyncio
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты переформулятор поисковых запросов для каталога государственных закупок РФ. "
    "Пользователь пишет нечёткий запрос, ты выдаёшь 3 конкретных коротких названия "
    "товаров на русском языке, которые он мог иметь в виду. "
    "Отвечай СТРОГО по формату: одно название на строке, без нумерации, без пояснений, "
    "без кавычек. Только названия товаров."
)


async def expand_query(query: str, timeout: float = 15.0) -> list[str]:
    """Call Ollama LLM to generate alternative query formulations.

    Returns a list of 1-3 reformulated queries (may be empty on error/timeout).
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.llm_model,
                    "system": SYSTEM_PROMPT,
                    "prompt": query,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 80,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("LLM expand_query failed: %s", e)
        return []

    raw = data.get("response", "")
    if not raw.strip():
        return []

    # Parse response: one query per line, clean up
    lines = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        # Remove numbering like "1.", "- ", "* "
        line = re.sub(r"^[\d]+[.\)]\s*", "", line)
        line = re.sub(r"^[-*]\s*", "", line)
        line = line.strip().strip('"').strip("'")
        if line and len(line) >= 3 and len(line) <= 120:
            lines.append(line)

    return lines[:3]


async def search_with_expansion(
    engine,
    query: str,
    user_boosts: dict | None,
    category_boosts: dict | None,
    size: int = 10,
) -> dict[str, Any]:
    """Run LLM expansion + ES search for each reformulation.

    Returns a dict with expanded queries and merged results.
    """
    # Generate reformulations
    expansions = await expand_query(query)
    if not expansions:
        return {"expansions": [], "items": []}

    # Search ES for each expansion in parallel
    async def _search_one(q: str):
        try:
            result = await engine.search(
                query=q,
                user_boosts=user_boosts,
                category_boosts=category_boosts,
                size=size,
                offset=0,
            )
            return q, result.get("items", [])
        except Exception as e:
            logger.warning("Expansion search failed for %r: %s", q, e)
            return q, []

    tasks = [_search_one(q) for q in expansions]
    results = await asyncio.gather(*tasks)

    # Merge and deduplicate, keeping track of which expansion found each item
    seen_ids = set()
    merged_items = []
    expansion_info = []

    for exp_query, items in results:
        count = 0
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                item["found_by_expansion"] = exp_query
                merged_items.append(item)
                count += 1
        if count > 0:
            expansion_info.append({"query": exp_query, "found": count})

    # Sort by score descending
    merged_items.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "expansions": expansion_info,
        "items": merged_items[:size],
    }
