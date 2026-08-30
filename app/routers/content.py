"""Public content endpoints: page configuration and published blogs."""
from fastapi import APIRouter, HTTPException, Query

from ..content import (
    get_all_config,
    list_blogs,
    get_blog_by_slug,
)

router = APIRouter()


@router.get("/page-config")
def public_page_config():
    return get_all_config()


@router.get("/blogs")
def public_list_blogs(
    search: str = Query(""),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
):
    return list_blogs(include_unpublished=False, search=search, page=page, per_page=per_page)


@router.get("/blogs/{slug}")
def public_get_blog(slug: str):
    blog = get_blog_by_slug(slug, include_unpublished=False)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog
