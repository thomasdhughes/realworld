from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from slugify import slugify
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user_required, get_current_user_optional
from app.models.article import Article
from app.models.comment import Comment
from app.models.tag import Tag
from app.models.user import User, article_favorites, article_tags
from app.schemas.article import ArticleCreateRequest, ArticleUpdateRequest, CommentCreateRequest
from app.utils.mappers import article_mapper, article_list_mapper, comment_mapper

router = APIRouter()


def _article_query_options():
    return [
        selectinload(Article.tag_list),
        selectinload(Article.author).selectinload(User.followed_by),
        selectinload(Article.favorited_by),
    ]


@router.get("/api/articles")
async def list_articles(
    tag: str | None = None,
    author: str | None = None,
    favorited: str | None = None,
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    user_id: int | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if author:
        filters.append(Article.author.has(User.username == author))
    if tag:
        filters.append(Article.tag_list.any(Tag.name == tag))
    if favorited:
        filters.append(Article.favorited_by.any(User.username == favorited))

    count_query = select(func.count(Article.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    articles_count = (await db.execute(count_query)).scalar()

    query = (
        select(Article)
        .options(*_article_query_options())
        .order_by(Article.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    articles = result.scalars().unique().all()

    return {
        "articles": [article_list_mapper(a, user_id) for a in articles],
        "articlesCount": articles_count,
    }


@router.get("/api/articles/feed")
async def feed_articles(
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id).options(selectinload(User.following)))
    current_user = result.scalar_one_or_none()
    following_ids = [u.id for u in current_user.following] if current_user else []

    if not following_ids:
        return {"articles": [], "articlesCount": 0}

    count_query = select(func.count(Article.id)).where(Article.author_id.in_(following_ids))
    articles_count = (await db.execute(count_query)).scalar()

    query = (
        select(Article)
        .where(Article.author_id.in_(following_ids))
        .options(*_article_query_options())
        .order_by(Article.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    articles = result.scalars().unique().all()

    return {
        "articles": [article_list_mapper(a, user_id) for a in articles],
        "articlesCount": articles_count,
    }


@router.post("/api/articles")
async def create_article(
    payload: ArticleCreateRequest,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    article_data = payload.article
    title = article_data.title
    description = article_data.description
    body = article_data.body
    tags = article_data.tagList if article_data.tagList else []

    if not title:
        raise HTTPException(status_code=422, detail={"errors": {"title": ["can't be blank"]}})
    if not description:
        raise HTTPException(status_code=422, detail={"errors": {"description": ["can't be blank"]}})
    if not body:
        raise HTTPException(status_code=422, detail={"errors": {"body": ["can't be blank"]}})

    slug = f"{slugify(title)}-{user_id}"

    existing = (await db.execute(select(Article).where(Article.slug == slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=422, detail={"errors": {"title": ["must be unique"]}})

    tag_objects = []
    for tag_name in tags:
        result = await db.execute(select(Tag).where(Tag.name == tag_name))
        tag_obj = result.scalar_one_or_none()
        if not tag_obj:
            tag_obj = Tag(name=tag_name)
            db.add(tag_obj)
        tag_objects.append(tag_obj)

    new_article = Article(
        slug=slug,
        title=title,
        description=description,
        body=body,
        author_id=user_id,
        tag_list=tag_objects,
    )
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)

    result = await db.execute(
        select(Article)
        .where(Article.id == new_article.id)
        .options(*_article_query_options())
    )
    new_article = result.scalar_one()

    return {"article": article_mapper(new_article, user_id)}


@router.get("/api/articles/{slug}")
async def get_article(
    slug: str,
    user_id: int | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .options(*_article_query_options())
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    return {"article": article_mapper(article, user_id)}


@router.put("/api/articles/{slug}")
async def update_article(
    slug: str,
    payload: ArticleUpdateRequest,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .options(*_article_query_options())
    )
    existing_article = result.scalar_one_or_none()

    if not existing_article:
        raise HTTPException(status_code=404, detail={})

    if existing_article.author_id != user_id:
        raise HTTPException(status_code=403, detail={"message": "You are not authorized to update this article"})

    article_data = payload.article
    new_slug = None

    if article_data.title:
        new_slug = f"{slugify(article_data.title)}-{user_id}"
        if new_slug != slug:
            dup = (await db.execute(select(Article).where(Article.slug == new_slug))).scalar_one_or_none()
            if dup:
                raise HTTPException(status_code=422, detail={"errors": {"title": ["must be unique"]}})

    if article_data.title:
        existing_article.title = article_data.title
    if article_data.body:
        existing_article.body = article_data.body
    if article_data.description:
        existing_article.description = article_data.description
    if new_slug:
        existing_article.slug = new_slug
    existing_article.updated_at = datetime.now(timezone.utc)

    if article_data.tagList is not None:
        existing_article.tag_list.clear()
        tag_objects = []
        for tag_name in article_data.tagList:
            r = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag_obj = r.scalar_one_or_none()
            if not tag_obj:
                tag_obj = Tag(name=tag_name)
                db.add(tag_obj)
            tag_objects.append(tag_obj)
        existing_article.tag_list = tag_objects

    await db.commit()
    await db.refresh(existing_article)

    result = await db.execute(
        select(Article)
        .where(Article.id == existing_article.id)
        .options(*_article_query_options())
    )
    existing_article = result.scalar_one()

    return {"article": article_mapper(existing_article, user_id)}


@router.delete("/api/articles/{slug}")
async def delete_article(
    slug: str,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail={})

    if article.author_id != user_id:
        raise HTTPException(status_code=403, detail={"message": "You are not authorized to delete this article"})

    await db.delete(article)
    await db.commit()


@router.post("/api/articles/{slug}/favorite")
async def favorite_article(
    slug: str,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .options(*_article_query_options())
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if user not in article.favorited_by:
        article.favorited_by.append(user)
        await db.commit()
        await db.refresh(article)

    result = await db.execute(
        select(Article)
        .where(Article.id == article.id)
        .options(*_article_query_options())
    )
    article = result.scalar_one()

    return {"article": article_mapper(article, user_id)}


@router.delete("/api/articles/{slug}/favorite")
async def unfavorite_article(
    slug: str,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Article)
        .where(Article.slug == slug)
        .options(*_article_query_options())
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if user in article.favorited_by:
        article.favorited_by.remove(user)
        await db.commit()
        await db.refresh(article)

    result = await db.execute(
        select(Article)
        .where(Article.id == article.id)
        .options(*_article_query_options())
    )
    article = result.scalar_one()

    return {"article": article_mapper(article, user_id)}


@router.get("/api/articles/{slug}/comments")
async def get_comments(
    slug: str,
    user_id: int | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    query = (
        select(Comment)
        .where(Comment.article_id == article.id)
        .options(selectinload(Comment.author).selectinload(User.followed_by))
    )

    result = await db.execute(query)
    comments = result.scalars().unique().all()

    return {"comments": [comment_mapper(c, user_id) for c in comments]}


@router.post("/api/articles/{slug}/comments")
async def add_comment(
    slug: str,
    payload: CommentCreateRequest,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    if not payload.comment.body:
        raise HTTPException(status_code=422, detail={"errors": {"body": ["can't be blank"]}})

    article_result = await db.execute(select(Article).where(Article.slug == slug))
    article = article_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    new_comment = Comment(
        body=payload.comment.body,
        article_id=article.id,
        author_id=user_id,
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    result = await db.execute(
        select(Comment)
        .where(Comment.id == new_comment.id)
        .options(selectinload(Comment.author).selectinload(User.followed_by))
    )
    new_comment = result.scalar_one()

    return {"comment": comment_mapper(new_comment, user_id)}


@router.delete("/api/articles/{slug}/comments/{comment_id}")
async def delete_comment(
    slug: str,
    comment_id: int,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.author_id == user_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail={})

    if comment.author_id != user_id:
        raise HTTPException(status_code=403, detail={"message": "You are not authorized to delete this comment"})

    await db.delete(comment)
    await db.commit()
