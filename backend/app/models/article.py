from sqlalchemy import Column, String, Text, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class ArticleStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class ImageSource(str, enum.Enum):
    ORIGINAL = "original"
    STOCK = "stock"
    BING = "bing"
    FLUX = "flux"
    NONE = "none"


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    
    # Original content
    original_url = Column(String(1000), nullable=False)
    original_title = Column(Text, nullable=False)
    original_content = Column(Text, nullable=False)
    original_image_url = Column(String(1000), nullable=True)
    
    # Processed content
    processed_title = Column(Text, nullable=True)
    processed_content = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Languages
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), nullable=True)
    
    # Categorization
    category_id = Column(Integer, nullable=True)
    category_name = Column(String(255), nullable=True)
    
    # Vector DB
    vector_id = Column(String(255), nullable=True)
    similarity_score = Column(String(50), nullable=True)
    
    # Image
    image_url = Column(String(1000), nullable=True)
    image_source = Column(Enum(ImageSource), default=ImageSource.NONE)
    
    # WordPress
    wp_post_id = Column(Integer, nullable=True)
    wp_post_url = Column(String(1000), nullable=True)
    
    # Status
    status = Column(Enum(ArticleStatus), default=ArticleStatus.PENDING)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    source = relationship("Source", back_populates="articles")
    site = relationship("Site", back_populates="articles")
    
    def __repr__(self):
        return f"<Article {self.original_title[:50]}... ({self.status})>"
