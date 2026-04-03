"""Dependency injection для FastAPI."""
from elasticsearch import AsyncElasticsearch
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import async_session
from app.search.engine import SearchEngine
from app.personalization.tracker import PersonalizationTracker

# Singletons — инициализируются в lifespan
_es_client: AsyncElasticsearch | None = None
_redis_client: redis.Redis | None = None
_search_engine: SearchEngine | None = None
_tracker: PersonalizationTracker | None = None


async def init_clients():
    global _es_client, _redis_client, _search_engine, _tracker
    _es_client = AsyncElasticsearch(settings.elasticsearch_url)
    _redis_client = redis.from_url(settings.redis_url, decode_responses=False)
    _search_engine = SearchEngine(_es_client)
    _tracker = PersonalizationTracker(_redis_client)
    await _search_engine.ensure_index()


async def close_clients():
    if _es_client:
        await _es_client.close()
    if _redis_client:
        await _redis_client.close()


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_es_engine() -> SearchEngine:
    return _search_engine


async def get_tracker() -> PersonalizationTracker:
    return _tracker
