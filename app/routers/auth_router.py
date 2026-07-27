from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import jwt, JWTError

from ..auth import (
    create_user,
    authenticate_user,
    get_user_by_id,
    create_api_key,
    revoke_api_key,
    list_api_keys,
    get_usage_stats,
    update_user_profile,
    change_password,
    hash_password,
)

router = APIRouter()

SECRET_KEY = "ASTROVAKTA_SECRET_KEY"
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
    return _user_response(user, token)


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
        "rate_limit": key_info["rate_limit"],
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
            "rate_limit": k["rate_limit"],
            "request_count": k["request_count"],
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
