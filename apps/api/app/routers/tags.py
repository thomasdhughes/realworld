from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import Tag
from app.models.user import article_tags

router = APIRouter()


@router.get("/api/tags")
async def get_tags(db: AsyncSession = Depends(get_db)):
    query = (
        select(Tag.name)
        .outerjoin(article_tags, Tag.id == article_tags.c.tag_id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(article_tags.c.article_id).desc())
        .limit(10)
    )
    result = await db.execute(query)
    tags = result.scalars().all()
    return {"tags": list(tags)}
