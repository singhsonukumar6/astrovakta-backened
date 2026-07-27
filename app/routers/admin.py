"""
Admin panel endpoints.
All endpoints require is_admin=1.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import (
    is_admin, get_all_users, admin_update_user_plan, admin_revoke_all_keys,
    set_user_admin, admin_get_stats, admin_get_all_keys, admin_revoke_key,
    admin_update_key_tier, admin_get_usage_daily, admin_get_usage_endpoints,
    get_all_jobs, admin_reset_password, admin_create_key_for_user,
    admin_get_user_keys, admin_get_user_usage, admin_get_all_usage_daily,
    admin_get_all_usage_by_user, create_api_key,
)
from .auth_router import get_current_user

router = APIRouter()


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ─── USERS ───
@router.get("/users")
def admin_list_users(
    page: int = Query(1, ge=1),
    search: str = Query(""),
    plan: str = Query(""),
    admin: dict = Depends(require_admin),
):
    return get_all_users(page=page, search=search, plan_filter=plan)


@router.get("/users/{user_id}")
def admin_get_user(user_id: int, admin: dict = Depends(require_admin)):
    from ..auth import get_user_by_id
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = dict(user)
    user_data.pop("password_hash", None)
    keys = admin_get_user_keys(user_id)
    usage = admin_get_user_usage(user_id)
    return {**user_data, "keys": keys, "usage": usage}


class PlanBody(BaseModel):
    plan: str = Field(..., pattern="^(free|starter|pro|enterprise)$")


@router.put("/users/{user_id}/plan")
def admin_change_plan(user_id: int, body: PlanBody, admin: dict = Depends(require_admin)):
    user = admin_update_user_plan(user_id, body.plan)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": f"Plan changed to {body.plan}", "user": {k: v for k, v in user.items() if k != "password_hash"}}


class AdminBody(BaseModel):
    is_admin: bool


@router.put("/users/{user_id}/admin")
def admin_toggle_admin(user_id: int, body: AdminBody, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot change your own admin status")
    ok = set_user_admin(user_id, body.is_admin)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": f"Admin status set to {body.is_admin}"}


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: int, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    count = admin_revoke_all_keys(user_id)
    return {"detail": f"Revoked {count} keys for user {user_id}"}


class ResetPasswordBody(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


@router.put("/users/{user_id}/reset-password")
def admin_reset_user_password(user_id: int, body: ResetPasswordBody, admin: dict = Depends(require_admin)):
    ok = admin_reset_password(user_id, body.new_password)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Password reset successfully"}


class CreateKeyForUserBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tier: str = Field("free", pattern="^(free|starter|pro|enterprise)$")


@router.post("/users/{user_id}/keys")
def admin_create_key_for_user_endpoint(user_id: int, body: CreateKeyForUserBody, admin: dict = Depends(require_admin)):
    key = admin_create_key_for_user(user_id, body.name, body.tier)
    if not key:
        raise HTTPException(status_code=404, detail="User not found")
    return key


@router.get("/users/{user_id}/usage")
def admin_user_usage(user_id: int, admin: dict = Depends(require_admin)):
    usage = admin_get_user_usage(user_id)
    if not usage:
        raise HTTPException(status_code=404, detail="User not found")
    return usage


# ─── KEYS ───
@router.get("/keys")
def admin_list_keys(
    page: int = Query(1, ge=1),
    admin: dict = Depends(require_admin),
):
    return admin_get_all_keys(page=page)


@router.put("/keys/{key_id}/revoke")
def admin_revoke_api_key(key_id: int, admin: dict = Depends(require_admin)):
    ok = admin_revoke_key(key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"detail": "Key revoked"}


class KeyTierBody(BaseModel):
    tier: str = Field(..., pattern="^(free|starter|pro|enterprise)$")


@router.put("/keys/{key_id}/tier")
def admin_change_key_tier(key_id: int, body: KeyTierBody, admin: dict = Depends(require_admin)):
    ok = admin_update_key_tier(key_id, body.tier)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"detail": f"Key tier changed to {body.tier}"}


# ─── STATS ───
@router.get("/stats")
def admin_stats(admin: dict = Depends(require_admin)):
    return admin_get_stats()


# ─── USAGE ───
@router.get("/usage/daily")
def admin_usage_daily(days: int = Query(30), admin: dict = Depends(require_admin)):
    return admin_get_all_usage_daily(days)


@router.get("/usage/endpoints")
def admin_usage_endpoints(limit: int = Query(20), admin: dict = Depends(require_admin)):
    return admin_get_usage_endpoints(limit)


@router.get("/usage/by-user")
def admin_usage_by_user(limit: int = Query(50), admin: dict = Depends(require_admin)):
    return admin_get_all_usage_by_user(limit)


# ─── JOBS ───
@router.get("/jobs")
def admin_list_jobs(
    page: int = Query(1, ge=1),
    status: str = Query(""),
    admin: dict = Depends(require_admin),
):
    return get_all_jobs(page=page, status=status if status else None)
