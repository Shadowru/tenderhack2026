from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    elasticsearch_url: str = "http://elasticsearch:9200"
    postgres_url: str = "postgresql+asyncpg://tenderhack:tenderhack@postgres:5432/tenderhack"
    redis_url: str = "redis://redis:6379/0"
    ollama_url: str = "http://ollama:11434"
    llm_model: str = "qwen2.5:7b"
    embed_model: str = "nomic-embed-text"
    es_index: str = "products"
    es_index_history: str = "search_history"
    pg_user: str = "tenderhack"
    pg_password: str = "tenderhack"
    pg_host: str = "postgres"
    pg_database: str = "tenderhack"


settings = Settings()
