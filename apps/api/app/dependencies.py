from fastapi import Depends, HTTPException, Request

from app.utils.auth import verify_token


def _extract_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if header:
        parts = header.split(" ")
        if len(parts) == 2 and parts[0] in ("Token", "Bearer"):
            return parts[1]
    return None


async def get_current_user_required(request: Request) -> int:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return user_id


async def get_current_user_optional(request: Request) -> int | None:
    token = _extract_token(request)
    if not token:
        return None
    user_id = verify_token(token)
    return user_id
