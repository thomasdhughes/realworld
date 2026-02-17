from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.user import Base, article_favorites, article_tags


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    body = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    author = relationship("User", back_populates="articles", lazy="selectin")
    tag_list = relationship("Tag", secondary=article_tags, back_populates="articles", lazy="selectin")
    favorited_by = relationship("User", secondary=article_favorites, back_populates="favorites", lazy="selectin")
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")
