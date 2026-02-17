from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_DAYS


def generate_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "user": {"id": user_id},
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user", {}).get("id")
        return int(user_id) if user_id is not None else None
    except JWTError:
        return None
