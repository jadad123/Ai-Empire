from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class SourceType(str, enum.Enum):
    RSS = "rss"
    URL = "url"


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(SourceType), default=SourceType.RSS)
    url = Column(String(1000), nullable=False)
    scrape_config = Column(JSON, default={
        "content_selector": "article",
        "title_selector": "h1",
        "image_selector": "img",
        "anti_ban": {
            "rotate_user_agent": True,
            "random_delay": True,
            "use_scraperapi": False
        }
    })
    poll_interval = Column(Integer, default=10)  # minutes
    max_articles_per_poll = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    last_polled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    site = relationship("Site", back_populates="sources")
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source {self.name} ({self.type})>"
