"""Главный модуль FastAPI приложения."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.deps import init_clients, close_clients
from app.models.database import engine, Base
from app.api.search import router as search_router
from app.api.metrics import router as metrics_router
from app.api.cart import router as cart_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_clients()
    logger.info("Ready.")
    yield
    logger.info("Shutting down...")
    await close_clients()


app = FastAPI(
    title="TenderHack Smart Search",
    description="Персонализированный умный поиск продукции для Портала поставщиков",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(metrics_router)
app.include_router(cart_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


_background_tasks = set()


@app.post("/api/admin/load-data")
async def load_data():
    """Запустить полную загрузку данных (СТЕ + контракты)."""
    from app.data.loader import run_full_load
    task = asyncio.create_task(run_full_load())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return {"status": "started", "message": "Data loading started in background"}
