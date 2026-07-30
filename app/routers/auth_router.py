from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import jwt, JWTError

from ..auth import (
    create_user,
    authenticate_user,
    get_user_by_id,
    get_user_by_email,
    create_api_key,
    revoke_api_key,
    list_api_keys,
    get_usage_stats,
    update_user_profile,
    change_password,
    hash_password,
    create_verification_token,
    verify_email_token,
    create_password_reset_token,
    reset_password_with_token,
    sync_clerk_user,
    TIER_LIMITS,
    CREDIT_COSTS,
    get_credit_cost,
)

router = APIRouter()

SECRET_KEY = os.getenv("JWT_SECRET", "dev-only-fallback-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72

security = HTTPBearer()


class RegisterBody(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class CreateKeyBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tier: Optional[str] = Field("free", pattern="^(free|starter|pro|enterprise)$")


class UpdateProfileBody(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    plan: Optional[str] = Field(None, pattern="^(free|starter|pro|enterprise)$")


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)


class ClerkSyncBody(BaseModel):
    clerk_id: str
    email: str
    name: str = ""


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _user_response(user: dict, token: str) -> dict:
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "plan": user["plan"],
            "is_admin": bool(user.get("is_admin")),
            "email_verified": bool(user.get("email_verified")),
            "avatar_url": user.get("avatar_url"),
            "created_at": user["created_at"],
        },
    }


@router.post("/register")
def register(body: RegisterBody):
    from ..database import get_db
    existing = get_db().execute("SELECT id FROM users WHERE email = ?", (body.email.lower().strip(),)).fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = create_user(body.email, body.name, body.password)
    token = create_access_token(user["id"])

    verification_token = create_verification_token(user["id"])
    email_sent = False
    try:
        from ..email_service import send_verification_email
        email_sent = send_verification_email(body.email, verification_token, body.name)
        if not email_sent:
            print(f"[AUTH] WARNING: Verification email failed to send to {body.email}")
    except Exception as e:
        print(f"[AUTH] ERROR: Verification email exception for {body.email}: {e}")

    resp = _user_response(user, token)
    resp["email_sent"] = email_sent
    return resp


@router.post("/login")
def login(body: LoginBody):
    user = authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user["id"])
    return _user_response(user, token)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "plan": user["plan"],
        "is_admin": bool(user.get("is_admin")),
        "email_verified": bool(user.get("email_verified")),
        "avatar_url": user.get("avatar_url"),
        "monthly_limit": user.get("monthly_limit", 500),
        "created_at": user["created_at"],
    }


@router.post("/keys")
def create_key(body: CreateKeyBody, user: dict = Depends(get_current_user)):
    keys = list_api_keys(user["id"])
    active = [k for k in keys if k["is_active"]]
    if len(active) >= 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 active API keys allowed")
    key_info = create_api_key(user["id"], body.name, body.tier or user["plan"])
    return {
        "id": key_info["id"],
        "key": key_info["key"],
        "name": key_info["name"],
        "tier": key_info["tier"],
        "monthly_limit": user.get("monthly_limit", 500),
        "created_at": key_info["created_at"],
    }


@router.get("/keys")
def list_keys(user: dict = Depends(get_current_user)):
    keys = list_api_keys(user["id"])
    return [
        {
            "id": k["id"],
            "key": k["key"],
            "name": k["name"],
            "tier": k["tier"],
            "is_active": k["is_active"],
            "last_used_at": k["last_used_at"],
            "created_at": k["created_at"],
            "revoked_at": k["revoked_at"],
        }
        for k in keys
    ]


@router.delete("/keys/{key_id}")
def delete_key(key_id: int, user: dict = Depends(get_current_user)):
    ok = revoke_api_key(key_id, user["id"])
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return {"detail": "API key revoked"}


@router.get("/usage/{key_id}")
def usage(key_id: int, user: dict = Depends(get_current_user)):
    keys = list_api_keys(user["id"])
    owned = any(k["id"] == key_id for k in keys)
    if not owned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    stats = get_usage_stats(key_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return stats


@router.put("/profile")
def update_profile(body: UpdateProfileBody, user: dict = Depends(get_current_user)):
    updated = update_user_profile(user["id"], body.name, body.plan, body.email)
    if not updated:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    return {
        "id": updated["id"],
        "email": updated["email"],
        "name": updated["name"],
        "plan": updated["plan"],
        "created_at": updated["created_at"],
    }


@router.post("/change-password")
def change_password_endpoint(body: ChangePasswordBody, user: dict = Depends(get_current_user)):
    ok = change_password(user["id"], body.current_password, body.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    return {"detail": "Password changed successfully"}


# ──────────────── EMAIL VERIFICATION ────────────────

@router.get("/verify-email")
def verify_email(token: str):
    user = verify_email_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
    return {"detail": "Email verified successfully", "email": user["email"]}


@router.post("/resend-verification")
def resend_verification(body: ForgotPasswordBody):
    user = get_user_by_email(body.email)
    if not user:
        return {"detail": "If that email is registered, a verification link has been sent."}
    if user.get("email_verified"):
        return {"detail": "Email is already verified."}
    verification_token = create_verification_token(user["id"])
    email_sent = False
    try:
        from ..email_service import send_verification_email
        email_sent = send_verification_email(body.email, verification_token, user["name"])
        if not email_sent:
            print(f"[AUTH] WARNING: Resend verification email failed to {body.email}")
    except Exception as e:
        print(f"[AUTH] ERROR: Resend verification email exception for {body.email}: {e}")
    return {"detail": "If that email is registered, a verification link has been sent.", "email_sent": email_sent}


# ──────────────── PASSWORD RESET ────────────────

@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordBody):
    user = get_user_by_email(body.email)
    if not user:
        return {"detail": "If that email is registered, a password reset link has been sent."}
    reset_token = create_password_reset_token(user["id"])
    email_sent = False
    try:
        from ..email_service import send_password_reset_email
        email_sent = send_password_reset_email(body.email, reset_token, user["name"])
        if not email_sent:
            print(f"[AUTH] WARNING: Password reset email failed to {body.email}")
    except Exception as e:
        print(f"[AUTH] ERROR: Password reset email exception for {body.email}: {e}")
    return {"detail": "If that email is registered, a password reset link has been sent.", "email_sent": email_sent}


@router.post("/reset-password")
def reset_password(body: ResetPasswordBody):
    ok = reset_password_with_token(body.token, body.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    return {"detail": "Password reset successfully"}


@router.post("/clerk-sync")
def clerk_sync(body: ClerkSyncBody):
    user = sync_clerk_user(body.clerk_id, body.email, body.name)
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync user")
    token = create_access_token(user["id"])
    return _user_response(user, token)


@router.get("/credits/costs")
def credit_costs():
    """Return the credit cost map so the frontend can display per-endpoint costs."""
    cost_summary = {}
    for path, cost in sorted(CREDIT_COSTS.items()):
        cost_summary[path] = cost
    return {"credit_costs": cost_summary, "note": "Credits are deducted per API call. Different endpoints consume different amounts of credits."}
