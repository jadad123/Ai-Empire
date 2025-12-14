from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class SourceType(str, Enum):
    RSS = "rss"
    URL = "url"


class ScrapeConfig(BaseModel):
    content_selector: str = "article"
    title_selector: str = "h1"
    image_selector: str = "img"
    anti_ban: Dict[str, Any] = {
        "rotate_user_agent": True,
        "random_delay": True,
        "use_scraperapi": False
    }


class SourceBase(BaseModel):
    site_id: UUID
    name: str
    type: SourceType = SourceType.RSS
    url: str
    poll_interval: int = 10
    max_articles_per_poll: int = 5
    is_active: bool = True


class SourceCreate(SourceBase):
    scrape_config: Optional[ScrapeConfig] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[SourceType] = None
    poll_interval: Optional[int] = None
    max_articles_per_poll: Optional[int] = None
    scrape_config: Optional[ScrapeConfig] = None
    is_active: Optional[bool] = None


class SourceResponse(SourceBase):
    id: UUID
    scrape_config: Dict[str, Any]
    last_polled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    articles_count: int = 0
    
    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int
