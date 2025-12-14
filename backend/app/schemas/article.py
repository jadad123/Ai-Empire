from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class ArticleStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class ImageSource(str, Enum):
    ORIGINAL = "original"
    STOCK = "stock"
    BING = "bing"
    FLUX = "flux"
    NONE = "none"


class ArticleResponse(BaseModel):
    id: UUID
    source_id: UUID
    site_id: UUID
    original_url: str
    original_title: str
    processed_title: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    category_name: Optional[str] = None
    image_url: Optional[str] = None
    image_source: ImageSource
    wp_post_id: Optional[int] = None
    wp_post_url: Optional[str] = None
    status: ArticleStatus
    error_message: Optional[str] = None
    created_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ArticleDetailResponse(ArticleResponse):
    original_content: str
    processed_content: Optional[str] = None
    meta_description: Optional[str] = None
    vector_id: Optional[str] = None
    similarity_score: Optional[str] = None
    retry_count: int
    processed_at: Optional[datetime] = None


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    page: int
    per_page: int


class ArticleFilter(BaseModel):
    site_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    status: Optional[ArticleStatus] = None
    page: int = 1
    per_page: int = 20
