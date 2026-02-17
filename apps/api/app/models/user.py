from sqlalchemy import Boolean, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


user_follows = Table(
    "user_follows",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("followed_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

article_favorites = Table(
    "article_favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
)

article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    image = Column(String, nullable=True, default="https://api.realworld.io/images/smiley-cyrus.jpeg")
    bio = Column(String, nullable=True)
    demo = Column(Boolean, default=False)

    articles = relationship("Article", back_populates="author", cascade="all, delete-orphan")
    favorites = relationship("Article", secondary=article_favorites, back_populates="favorited_by", lazy="selectin")
    followed_by = relationship(
        "User",
        secondary=user_follows,
        primaryjoin=id == user_follows.c.followed_id,
        secondaryjoin=id == user_follows.c.follower_id,
        back_populates="following",
        lazy="selectin",
    )
    following = relationship(
        "User",
        secondary=user_follows,
        primaryjoin=id == user_follows.c.follower_id,
        secondaryjoin=id == user_follows.c.followed_id,
        back_populates="followed_by",
        lazy="selectin",
    )
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
