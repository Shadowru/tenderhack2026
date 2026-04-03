from sqlalchemy import Column, Integer, String, Float, DateTime, Text, BigInteger, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.database import Base


class SearchEvent(Base):
    """Лог поисковых запросов и кликов для персонализации и метрик."""
    __tablename__ = "search_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    query = Column(Text, nullable=False)
    product_id = Column(String(128), nullable=True)
    event_type = Column(String(32), nullable=False)  # search, click, cart, purchase
    position = Column(Integer, nullable=True)  # позиция в выдаче при клике
    score = Column(Float, nullable=True)
    session_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_search_events_user_event", "user_id", "event_type"),
    )


class UserProfile(Base):
    """Агрегированный профиль пользователя для персонализации."""
    __tablename__ = "user_profiles"

    user_id = Column(String(64), primary_key=True)
    # JSON с весами категорий, предпочтениями и т.д. — хранится в Redis для быстрого доступа
    total_searches = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SearchMetricSnapshot(Base):
    """Снимки метрик качества поиска."""
    __tablename__ = "search_metric_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metric_name = Column(String(64), nullable=False)  # mrr, ndcg, precision_at_k, ctr, etc.
    metric_value = Column(Float, nullable=False)
    k = Column(Integer, nullable=True)  # для precision@k, ndcg@k
    user_segment = Column(String(64), nullable=True)  # all, new, returning, etc.
    details = Column(Text, nullable=True)  # JSON с деталями
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
