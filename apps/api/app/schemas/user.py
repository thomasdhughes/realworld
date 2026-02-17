from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str | None = None
    image: str | None = None
    bio: str | None = None
    demo: bool | None = None


class UserRegisterRequest(BaseModel):
    user: UserRegister


class UserLogin(BaseModel):
    email: str | None = None
    password: str | None = None


class UserLoginRequest(BaseModel):
    user: UserLogin


class UserUpdate(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str | None = None
    image: str | None = None
    bio: str | None = None


class UserUpdateRequest(BaseModel):
    user: UserUpdate


class UserResponse(BaseModel):
    email: str
    username: str
    bio: str | None = None
    image: str | None = None
    token: str
