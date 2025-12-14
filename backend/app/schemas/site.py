from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class VelocityMode(str, Enum):
    NEWS = "news"
    EVERGREEN = "evergreen"


class SiteBase(BaseModel):
    name: str
    url: str
    wp_username: str
    target_language: str = "en"
    velocity_mode: VelocityMode = VelocityMode.NEWS
    category_map: Dict[str, str] = {}
    default_author_id: Optional[str] = None
    watermark_text: Optional[str] = None
    is_active: bool = True


class SiteCreate(SiteBase):
    wp_app_password: str
    bing_cookie: Optional[str] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    wp_username: Optional[str] = None
    wp_app_password: Optional[str] = None
    target_language: Optional[str] = None
    velocity_mode: Optional[VelocityMode] = None
    category_map: Optional[Dict[str, str]] = None
    bing_cookie: Optional[str] = None
    default_author_id: Optional[str] = None
    watermark_text: Optional[str] = None
    is_active: Optional[bool] = None


class SiteResponse(SiteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    sources_count: int = 0
    articles_count: int = 0
    
    class Config:
        from_attributes = True


class SiteListResponse(BaseModel):
    sites: list[SiteResponse]
    total: int
