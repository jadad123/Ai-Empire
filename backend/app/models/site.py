from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class VelocityMode(str, enum.Enum):
    NEWS = "news"           # 10 minute polling
    EVERGREEN = "evergreen" # 24 hour polling


class Site(Base):
    __tablename__ = "sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    wp_username = Column(String(255), nullable=False)
    wp_app_password = Column(Text, nullable=False)  # Encrypted
    category_map = Column(JSON, default={})  # {id: name} mapping
    bing_cookie = Column(Text, nullable=True)  # Encrypted
    velocity_mode = Column(Enum(VelocityMode), default=VelocityMode.NEWS)
    target_language = Column(String(10), default="en")
    default_author_id = Column(String(50), nullable=True)
    watermark_text = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sources = relationship("Source", back_populates="site", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="site", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Site {self.name}>"
