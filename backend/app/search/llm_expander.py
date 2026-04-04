"""RAG-powered query expansion: LLM + real categories from the index.

Flow:
1. Quick ES aggregation → get real categories matching the query
2. LLM picks best categories and suggests concrete search terms
3. Search ES with category filters for precise results
"""
import asyncio
import logging
import re
from typing import Any

import httpx
from elasticsearch import AsyncElasticsearch

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты помощник поиска товаров в каталоге государственных закупок РФ. "
    "Тебе дан запрос пользователя и список реальных категорий из каталога с количеством товаров. "
    "Выбери 3 самых подходящих категории для запроса пользователя. "
    "Для каждой категории предложи короткий поисковый запрос (1-3 слова), "
    "который найдёт нужные товары внутри этой категории.\n\n"
    "Отвечай СТРОГО по формату, по одной строке:\n"
    "категория | поисковый запрос\n\n"
    "Без нумерации, без пояснений. Только 3 строки."
)


async def _get_candidate_categories(
    es: AsyncElasticsearch, query: str, top_n: int = 15,
) -> list[dict]:
    """Quick ES aggregation to get real categories matching the query.

    Uses subject + category fields WITHOUT fuzziness to avoid noise
    like "Мединский" matching "медицинские".
    """
    body = {
        "size": 0,
        "query": {
            "bool": {
                "should": [
                    # Strict match on subject — most precise
                    {"match": {"subject": {"query": query, "boost": 5}}},
                    # Match on category text
                    {"match": {"category": {"query": query, "boost": 3}}},
                    # Match on name — no fuzziness
                    {"match": {"name": {"query": query, "boost": 2}}},
                ],
                "minimum_should_match": 1,
            }
        },
        "aggs": {
            "categories": {
                "terms": {"field": "category.keyword", "size": top_n}
            }
        },
    }
    result = await es.search(index=settings.es_index, body=body)
    buckets = result.get("aggregations", {}).get("categories", {}).get("buckets", [])
    return [{"name": b["key"], "count": b["doc_count"]} for b in buckets]


async def _llm_pick_categories(
    query: str,
    categories: list[dict],
    timeout: float = 12.0,
) -> list[dict]:
    """Ask LLM to pick best categories and suggest search terms.

    Returns list of {category, search_query}.
    """
    cats_text = "\n".join(
        f"- {c['name']} ({c['count']} товаров)" for c in categories
    )
    prompt = f"Запрос пользователя: {query}\n\nКатегории в каталоге:\n{cats_text}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.llm_model,
                    "system": SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 120},
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("LLM category pick failed: %s", e)
        return []

    raw = data.get("response", "")
    if not raw.strip():
        return []

    # Parse "категория | поисковый запрос"
    results = []
    known_cats = {c["name"] for c in categories}
    for line in raw.strip().split("\n"):
        line = line.strip()
        line = re.sub(r"^[\d]+[.\)]\s*", "", line)
        line = re.sub(r"^[-*]\s*", "", line).strip()
        if "|" not in line:
            continue
        parts = line.split("|", 1)
        cat = parts[0].strip().strip('"').strip("'")
        sq = parts[1].strip().strip('"').strip("'")
        if not cat or not sq:
            continue
        # Match to closest known category
        matched_cat = None
        for kc in known_cats:
            if cat.lower() in kc.lower() or kc.lower() in cat.lower():
                matched_cat = kc
                break
        if not matched_cat:
            # Fuzzy: take first category containing any word from LLM's pick
            cat_words = set(cat.lower().split())
            for kc in known_cats:
                kc_lower = kc.lower()
                if any(w in kc_lower for w in cat_words if len(w) >= 4):
                    matched_cat = kc
                    break
        if matched_cat:
            results.append({"category": matched_cat, "search_query": sq})
            known_cats.discard(matched_cat)

    return results[:3]


async def search_with_expansion(
    engine,
    query: str,
    user_boosts: dict | None,
    category_boosts: dict | None,
    size: int = 10,
) -> dict[str, Any]:
    """RAG expansion: get categories → LLM picks best → search with filters."""

    # Step 1: Get candidate categories from ES
    categories = await _get_candidate_categories(engine.es, query)
    if not categories:
        return {"expansions": [], "items": []}

    # Step 2: LLM picks best categories and search terms
    picks = await _llm_pick_categories(query, categories)
    if not picks:
        # Fallback: use top-3 categories with full query
        picks = [
            {"category": c["name"], "search_query": query}
            for c in categories[:3]
        ]

    # Step 3: Search ES with category filters in parallel
    async def _search_one(pick: dict):
        try:
            result = await engine.search(
                query=pick["search_query"],
                user_boosts=user_boosts,
                category_boosts=category_boosts,
                size=size,
                offset=0,
                category_filter=pick["category"],
            )
            return pick, result.get("items", [])
        except Exception as e:
            logger.warning("Expansion search failed for %r: %s", pick, e)
            return pick, []

    tasks = [_search_one(p) for p in picks]
    results = await asyncio.gather(*tasks)

    # Merge and deduplicate
    seen_ids = set()
    merged_items = []
    expansion_info = []

    for pick, items in results:
        count = 0
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                item["found_by_expansion"] = pick["search_query"]
                item["found_in_category"] = pick["category"]
                merged_items.append(item)
                count += 1
        if count > 0:
            expansion_info.append({
                "query": pick["search_query"],
                "category": pick["category"],
                "found": count,
            })

    merged_items.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "expansions": expansion_info,
        "items": merged_items[:size],
    }
