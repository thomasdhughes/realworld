from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user_required, get_current_user_optional
from app.models.user import User
from app.utils.mappers import profile_mapper

router = APIRouter()


@router.get("/api/profiles/{username}")
async def get_profile(
    username: str,
    user_id: int | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.username == username)
        .options(selectinload(User.followed_by))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail={})

    return {"profile": profile_mapper(profile, user_id)}


@router.post("/api/profiles/{username}/follow")
async def follow_user(
    username: str,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.username == username)
        .options(selectinload(User.followed_by))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail={})

    current_user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = current_user_result.scalar_one()

    if current_user not in profile.followed_by:
        profile.followed_by.append(current_user)
        await db.commit()
        await db.refresh(profile)

    result = await db.execute(
        select(User)
        .where(User.username == username)
        .options(selectinload(User.followed_by))
    )
    profile = result.scalar_one()

    return {"profile": profile_mapper(profile, user_id)}


@router.delete("/api/profiles/{username}/follow")
async def unfollow_user(
    username: str,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(User.username == username)
        .options(selectinload(User.followed_by))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail={})

    current_user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = current_user_result.scalar_one()

    if current_user in profile.followed_by:
        profile.followed_by.remove(current_user)
        await db.commit()
        await db.refresh(profile)

    result = await db.execute(
        select(User)
        .where(User.username == username)
        .options(selectinload(User.followed_by))
    )
    profile = result.scalar_one()

    return {"profile": profile_mapper(profile, user_id)}
