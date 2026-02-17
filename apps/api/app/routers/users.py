from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_required
from app.models.user import User
from app.schemas.user import (
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.utils.auth import generate_token
from app.utils.security import hash_password, verify_password

router = APIRouter()


@router.post("/api/users")
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    user = payload.user
    email = user.email.strip() if user.email else ""
    username = user.username.strip() if user.username else ""
    password = user.password.strip() if user.password else ""

    if not email:
        raise HTTPException(status_code=422, detail={"errors": {"email": ["can't be blank"]}})
    if not username:
        raise HTTPException(status_code=422, detail={"errors": {"username": ["can't be blank"]}})
    if not password:
        raise HTTPException(status_code=422, detail={"errors": {"password": ["can't be blank"]}})

    existing_email = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    existing_username = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()

    if existing_email or existing_username:
        errors = {}
        if existing_email:
            errors["email"] = ["has already been taken"]
        if existing_username:
            errors["username"] = ["has already been taken"]
        raise HTTPException(status_code=422, detail={"errors": errors})

    hashed = hash_password(password)
    new_user = User(
        email=email,
        username=username,
        password=hashed,
        image=user.image if user.image else "https://api.realworld.io/images/smiley-cyrus.jpeg",
        bio=user.bio,
        demo=user.demo if user.demo else False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "bio": new_user.bio,
            "image": new_user.image,
            "token": generate_token(new_user.id),
        }
    }


@router.post("/api/users/login")
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    user = payload.user
    email = user.email.strip() if user.email else ""
    password = user.password.strip() if user.password else ""

    if not email:
        raise HTTPException(status_code=422, detail={"errors": {"email": ["can't be blank"]}})
    if not password:
        raise HTTPException(status_code=422, detail={"errors": {"password": ["can't be blank"]}})

    result = await db.execute(select(User).where(User.email == email))
    found_user = result.scalar_one_or_none()

    if found_user and verify_password(password, found_user.password):
        return {
            "user": {
                "email": found_user.email,
                "username": found_user.username,
                "bio": found_user.bio,
                "image": found_user.image,
                "token": generate_token(found_user.id),
            }
        }

    raise HTTPException(
        status_code=403,
        detail={"errors": {"email or password": ["is invalid"]}},
    )


@router.get("/api/user")
async def get_current_user(
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "bio": user.bio,
            "image": user.image,
            "token": generate_token(user.id),
        }
    }


@router.put("/api/user")
async def update_user(
    payload: UserUpdateRequest,
    user_id: int = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.user
    if update_data.email:
        user.email = update_data.email
    if update_data.username:
        user.username = update_data.username
    if update_data.password:
        user.password = hash_password(update_data.password)
    if update_data.image:
        user.image = update_data.image
    if update_data.bio:
        user.bio = update_data.bio

    await db.commit()
    await db.refresh(user)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "bio": user.bio,
            "image": user.image,
            "token": generate_token(user.id),
        }
    }
