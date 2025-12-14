from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://empire:empire123@localhost:5432/empire_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    
    # Encryption
    encryption_key: str = ""
    
    # OpenRouter (Single API for all AI operations)
    openrouter_api_key: str = "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"
    
    # Image APIs (Optional - for stock photos)
    pexels_api_key: Optional[str] = None
    unsplash_access_key: Optional[str] = None
    
    # App
    debug: bool = True
    secret_key: str = "change-me-in-production"
    allowed_origins: str = "http://localhost:3000"
    
    # Similarity threshold for deduplication
    similarity_threshold: float = 0.80
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
