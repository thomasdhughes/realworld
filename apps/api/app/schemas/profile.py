from pydantic import BaseModel


class ProfileResponse(BaseModel):
    username: str
    bio: str | None = None
    image: str | None = None
    following: bool = False
