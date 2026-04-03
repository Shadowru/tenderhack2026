"""API роуты поиска."""
import hashlib
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_es_engine, get_tracker, get_db
from app.search.engine import SearchEngine
from app.search.spelling import fix_keyboard_layout, normalize_query, spell_checker
from app.personalization.tracker import PersonalizationTracker
from app.models.schemas import SearchEvent

router = APIRouter(prefix="/api/search", tags=["search"])

# TTLs for search result caching
_TTL_AUTHENTICATED = 60    # seconds — short because personalization changes results
_TTL_ANONYMOUS = 300       # seconds — longer, no personalization to invalidate
_TTL_SUGGEST = 600         # seconds — suggestions change infrequently


def _search_cache_key(query: str, user_id: str, category: str | None, offset: int, size: int) -> str:
    raw = f"{query}|{user_id}|{category or ''}|{offset}|{size}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"cache:search:{digest}"


def _suggest_cache_key(query: str) -> str:
    return f"cache:suggest:{query}"


@router.get("")
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    user_id: str = Query("anonymous"),
    session_id: str = Query(""),
    size: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    engine: SearchEngine = Depends(get_es_engine),
    tracker: PersonalizationTracker = Depends(get_tracker),
    db: AsyncSession = Depends(get_db),
):
    original_query = q
    q = normalize_query(q)

    # Проверка раскладки
    layout_fix = fix_keyboard_layout(q)
    if layout_fix:
        q = layout_fix

    # Проверка опечаток
    correction = spell_checker.correct(q)

    # Персональные бусты
    user_boosts = None
    category_boosts = None
    is_anonymous = user_id == "anonymous"
    if not is_anonymous:
        # Cold start: populate Redis from historical contracts if profile is empty
        await tracker.load_buyer_history(user_id)
        user_boosts, category_boosts = await tracker.get_user_boosts(user_id)
        # Normalize empty dicts to None so engine skips the boost blocks
        if not user_boosts:
            user_boosts = None
        if not category_boosts:
            category_boosts = None

    # Cache lookup — skip caching entirely when a spelling correction is present,
    # because corrected queries produce variable results depending on the correction.
    redis = tracker.redis
    cache_key = _search_cache_key(q, user_id, category, offset, size)
    should_cache = correction is None

    result = None
    if should_cache:
        cached = await redis.get(cache_key)
        if cached is not None:
            result = json.loads(cached)

    if result is None:
        result = await engine.search(
            query=q,
            user_boosts=user_boosts,
            category_boosts=category_boosts,
            size=size,
            offset=offset,
            category_filter=category,
        )

        if should_cache:
            ttl = _TTL_ANONYMOUS if is_anonymous else _TTL_AUTHENTICATED
            await redis.set(cache_key, json.dumps(result), ex=ttl)

    # Трекинг
    if not is_anonymous:
        await tracker.track_event(
            user_id,
            "search",
            query=q,
        )

    # Лог в БД
    db.add(SearchEvent(user_id=user_id, query=q, event_type="search", session_id=session_id))
    await db.commit()

    result["correction"] = correction
    result["layout_fixed"] = layout_fix is not None
    result["original_query"] = original_query
    return result


@router.get("/suggest")
async def suggest(
    q: str = Query(..., min_length=1, max_length=200),
    user_id: str = Query("anonymous"),
    engine: SearchEngine = Depends(get_es_engine),
    tracker: PersonalizationTracker = Depends(get_tracker),
):
    q = normalize_query(q)
    layout_fix = fix_keyboard_layout(q)
    if layout_fix:
        q = layout_fix

    redis = tracker.redis
    # Cache key includes user_id for personalized suggestions
    cache_key = _suggest_cache_key(q) + f":{user_id}"

    cached = await redis.get(cache_key)
    if cached is not None:
        suggestions = json.loads(cached)
        return {"suggestions": suggestions}

    # Get category boosts for personalization
    category_boosts = None
    if user_id != "anonymous":
        await tracker.load_buyer_history(user_id)
        _, category_boosts = await tracker.get_user_boosts(user_id)
        if not category_boosts:
            category_boosts = None

    suggestions = await engine.suggest(q, category_boosts=category_boosts)
    ttl = _TTL_SUGGEST if user_id == "anonymous" else _TTL_AUTHENTICATED
    await redis.set(cache_key, json.dumps(suggestions), ex=ttl)
    return {"suggestions": suggestions}


@router.get("/expand")
async def expand_search(
    q: str = Query(..., min_length=1, max_length=500),
    user_id: str = Query("anonymous"),
    size: int = Query(10, ge=1, le=30),
    engine: SearchEngine = Depends(get_es_engine),
    tracker: PersonalizationTracker = Depends(get_tracker),
):
    """AI-powered query expansion: LLM reformulates vague queries, searches each."""
    from app.search.llm_expander import search_with_expansion
    from app.search.spelling import fix_keyboard_layout, normalize_query

    q = normalize_query(q)
    layout_fix = fix_keyboard_layout(q)
    if layout_fix:
        q = layout_fix

    user_boosts = None
    category_boosts = None
    if user_id != "anonymous":
        await tracker.load_buyer_history(user_id)
        user_boosts, category_boosts = await tracker.get_user_boosts(user_id)
        if not user_boosts:
            user_boosts = None
        if not category_boosts:
            category_boosts = None

    result = await search_with_expansion(
        engine=engine,
        query=q,
        user_boosts=user_boosts,
        category_boosts=category_boosts,
        size=size,
    )
    return result


@router.post("/event")
async def track_event(
    user_id: str,
    event_type: str,
    product_id: str = "",
    category: str = "",
    query: str = "",
    position: int | None = None,
    session_id: str = "",
    tracker: PersonalizationTracker = Depends(get_tracker),
    db: AsyncSession = Depends(get_db),
):
    """Записать событие: click, cart, purchase.

    For click events, category should be provided so that category-level
    personalization weights are updated alongside product weights.
    """
    await tracker.track_event(
        user_id=user_id,
        event_type=event_type,
        query=query,
        product_id=product_id,
        category=category,
        position=position,
    )
    db.add(SearchEvent(
        user_id=user_id,
        query=query,
        product_id=product_id,
        event_type=event_type,
        position=position,
        session_id=session_id,
    ))
    await db.commit()
    return {"ok": True}
