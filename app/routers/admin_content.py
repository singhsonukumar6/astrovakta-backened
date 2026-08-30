"""Admin content management: page configuration and blog CRUD."""
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..content import (
    get_all_config,
    update_config,
    list_blogs,
    get_blog_by_id,
    create_blog,
    update_blog,
    delete_blog,
    slug_exists,
    DEFAULT_CONFIG,
    get_config,
)
from .auth_router import get_current_user

router = APIRouter()


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ─── PAGE CONFIGURATION ───
@router.get("/config")
def admin_get_config(admin: dict = Depends(require_admin)):
    return get_all_config()


@router.put("/config")
def admin_update_config(payload: dict, admin: dict = Depends(require_admin)):
    return update_config(payload)


class ConfigBody(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: object = None


@router.post("/config")
def admin_set_config(body: ConfigBody, admin: dict = Depends(require_admin)):
    update_config({body.key: body.value})
    return get_all_config()


@router.post("/config/reset")
def admin_reset_config(admin: dict = Depends(require_admin)):
    from ..content import set_config
    for key, value in DEFAULT_CONFIG.items():
        set_config(key, value)
    return get_all_config()


# ─── BLOGS ───
@router.get("/blogs")
def admin_list_blogs(
    search: str = Query(""),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin),
):
    return list_blogs(include_unpublished=True, search=search, page=page, per_page=per_page)


def _slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "post"


def _make_unique_slug(title: str, exclude_id: int = None) -> str:
    base = _slugify(title)
    slug = base
    n = 2
    while slug_exists(slug, exclude_id):
        slug = f"{base}-{n}"
        n += 1
    return slug


class BlogCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    slug: str = Field("", max_length=300)
    excerpt: str = ""
    body: str = ""
    cover_image: str = ""
    author: str = ""
    tag: str = ""
    read_time: str = ""
    is_published: bool = True


@router.post("/blogs")
def admin_create_blog(body: BlogCreateBody, admin: dict = Depends(require_admin)):
    slug = body.slug.strip() or _make_unique_slug(body.title)
    if slug_exists(slug):
        slug = _make_unique_slug(body.title)
    data = {
        "slug": slug,
        "title": body.title,
        "excerpt": body.excerpt,
        "body": body.body,
        "cover_image": body.cover_image,
        "author": body.author or admin.get("name"),
        "author_id": admin.get("id"),
        "tag": body.tag,
        "read_time": body.read_time,
        "is_published": body.is_published,
    }
    return create_blog(data)


class BlogUpdateBody(BaseModel):
    title: str = Field(None, min_length=1, max_length=300)
    slug: str = Field(None, max_length=300)
    excerpt: str = None
    body: str = None
    cover_image: str = None
    author: str = None
    tag: str = None
    read_time: str = None
    is_published: bool = None


@router.put("/blogs/{blog_id}")
def admin_update_blog_ep(blog_id: int, body: BlogUpdateBody, admin: dict = Depends(require_admin)):
    if not get_blog_by_id(blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")
    data = {k: v for k, v in body.dict().items() if v is not None}
    if "slug" in data and data["slug"]:
        data["slug"] = data["slug"].strip()
        if slug_exists(data["slug"], blog_id):
            data["slug"] = _make_unique_slug(data["slug"], blog_id)
    return update_blog(blog_id, data)


@router.delete("/blogs/{blog_id}")
def admin_delete_blog_ep(blog_id: int, admin: dict = Depends(require_admin)):
    if not delete_blog(blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")
    return {"detail": "Blog deleted"}


@router.post("/blogs/{blog_id}/publish")
def admin_publish_blog(blog_id: int, admin: dict = Depends(require_admin)):
    if not get_blog_by_id(blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")
    return update_blog(blog_id, {"is_published": True})


@router.post("/blogs/{blog_id}/unpublish")
def admin_unpublish_blog(blog_id: int, admin: dict = Depends(require_admin)):
    if not get_blog_by_id(blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")
    return update_blog(blog_id, {"is_published": False})
