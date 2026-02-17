from pydantic import BaseModel


class ArticleCreate(BaseModel):
    title: str | None = None
    description: str | None = None
    body: str | None = None
    tagList: list[str] | None = None


class ArticleCreateRequest(BaseModel):
    article: ArticleCreate


class ArticleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    body: str | None = None
    tagList: list[str] | None = None


class ArticleUpdateRequest(BaseModel):
    article: ArticleUpdate


class CommentCreate(BaseModel):
    body: str | None = None


class CommentCreateRequest(BaseModel):
    comment: CommentCreate
