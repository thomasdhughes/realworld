from app.models.article import Article
from app.models.comment import Comment
from app.models.user import User


def author_mapper(author: User, current_user_id: int | None = None) -> dict:
    following = False
    if current_user_id and author.followed_by:
        following = any(u.id == current_user_id for u in author.followed_by)
    return {
        "username": author.username,
        "bio": author.bio,
        "image": author.image,
        "following": following,
    }


def article_mapper(article: Article, current_user_id: int | None = None) -> dict:
    return {
        "slug": article.slug,
        "title": article.title,
        "description": article.description,
        "body": article.body,
        "tagList": sorted([tag.name for tag in article.tag_list]),
        "createdAt": article.created_at.isoformat().replace("+00:00", "Z") if article.created_at else None,
        "updatedAt": article.updated_at.isoformat().replace("+00:00", "Z") if article.updated_at else None,
        "favorited": any(u.id == current_user_id for u in article.favorited_by) if current_user_id else False,
        "favoritesCount": len(article.favorited_by),
        "author": author_mapper(article.author, current_user_id),
    }


def article_list_mapper(article: Article, current_user_id: int | None = None) -> dict:
    result = article_mapper(article, current_user_id)
    result.pop("body", None)
    return result


def comment_mapper(comment: Comment, current_user_id: int | None = None) -> dict:
    return {
        "id": comment.id,
        "createdAt": comment.created_at.isoformat().replace("+00:00", "Z") if comment.created_at else None,
        "updatedAt": comment.updated_at.isoformat().replace("+00:00", "Z") if comment.updated_at else None,
        "body": comment.body,
        "author": author_mapper(comment.author, current_user_id),
    }


def profile_mapper(user: User, current_user_id: int | None = None) -> dict:
    following = False
    if current_user_id and user.followed_by:
        following = any(u.id == current_user_id for u in user.followed_by)
    return {
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
        "following": following,
    }
