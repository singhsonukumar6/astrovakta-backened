"""
AI Provider management endpoints.
Developers configure their own AI API keys for /ai/* endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import httpx

from ..auth import (
    create_ai_provider, list_ai_providers, get_ai_provider,
    update_ai_provider, delete_ai_provider,
)
from ..crypto import encrypt_api_key, decrypt_api_key, mask_api_key
from .auth_router import get_current_user

router = APIRouter()

SUPPORTED_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "test_url": "https://api.openai.com/v1/models",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "models": ["claude-sonnet-4-20250514", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"],
        "test_url": "https://api.anthropic.com/v1/messages",
    },
    "groq": {
        "name": "Groq",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama-3.1-8b-instant"],
        "test_url": "https://api.groq.com/openai/v1/models",
    },
    "together": {
        "name": "Together AI",
        "models": [
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ],
        "test_url": "https://api.together.xyz/v1/models",
    },
}


@router.get("/supported")
def supported_providers():
    """List all supported AI providers and their models."""
    return {"providers": SUPPORTED_PROVIDERS}


class AddProviderBody(BaseModel):
    provider: str = Field(..., description="Provider name: openai, anthropic, groq, together")
    api_key: str = Field(..., min_length=10, description="Your API key from the provider")
    model: Optional[str] = Field(None, description="Preferred model (optional, uses default if empty)")


@router.post("")
def add_provider(body: AddProviderBody, user: dict = Depends(get_current_user)):
    if body.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider. Use: {', '.join(SUPPORTED_PROVIDERS.keys())}")

    if body.model:
        valid_models = SUPPORTED_PROVIDERS[body.provider]["models"]
        if body.model not in valid_models:
            raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {valid_models}")

    existing = list_ai_providers(user["id"])
    same_provider = [p for p in existing if p["provider"] == body.provider]
    if len(same_provider) >= 3:
        raise HTTPException(status_code=400, detail=f"Maximum 3 {body.provider} providers allowed")

    encrypted = encrypt_api_key(body.api_key)
    provider = create_ai_provider(user["id"], body.provider, encrypted, body.model)

    return {
        "id": provider["id"],
        "provider": provider["provider"],
        "model": provider["model"],
        "is_active": bool(provider["is_active"]),
        "created_at": provider["created_at"],
    }


@router.get("")
def get_providers(user: dict = Depends(get_current_user)):
    """List user's AI providers (keys masked)."""
    providers = list_ai_providers(user["id"])
    return [
        {
            "id": p["id"],
            "provider": p["provider"],
            "model": p["model"],
            "is_active": bool(p["is_active"]),
            "created_at": p["created_at"],
            "updated_at": p["updated_at"],
        }
        for p in providers
    ]


class UpdateProviderBody(BaseModel):
    model: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/{provider_id}")
def update_provider(provider_id: int, body: UpdateProviderBody, user: dict = Depends(get_current_user)):
    kwargs = {}
    if body.model is not None:
        existing = get_ai_provider(provider_id, user["id"])
        if not existing:
            raise HTTPException(status_code=404, detail="Provider not found")
        prov = existing["provider"]
        if body.model and prov in SUPPORTED_PROVIDERS:
            if body.model not in SUPPORTED_PROVIDERS[prov]["models"]:
                raise HTTPException(status_code=400, detail="Invalid model for this provider")
        kwargs["model"] = body.model
    if body.is_active is not None:
        kwargs["is_active"] = 1 if body.is_active else 0

    ok = update_ai_provider(provider_id, user["id"], **kwargs)
    if not ok:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"detail": "Provider updated"}


@router.delete("/{provider_id}")
def remove_provider(provider_id: int, user: dict = Depends(get_current_user)):
    ok = delete_ai_provider(provider_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"detail": "Provider deleted"}


class TestProviderBody(BaseModel):
    provider: str
    api_key: str


async def _run_provider_test(provider_name: str, api_key: str):
    """Shared logic to test an AI provider connection."""
    if provider_name not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    try:
        if provider_name == "anthropic":
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                    json={"model": "claude-3-haiku-20240307", "max_tokens": 10, "messages": [{"role": "user", "content": "Say OK"}]},
                )
                if resp.status_code == 200:
                    return {"status": "connected", "provider": provider_name}
                return {"status": "failed", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        else:
            url = SUPPORTED_PROVIDERS[provider_name]["test_url"]
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
                if resp.status_code == 200:
                    return {"status": "connected", "provider": provider_name}
                return {"status": "failed", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.post("/test")
async def test_provider(body: TestProviderBody, user: dict = Depends(get_current_user)):
    """Test an AI provider connection without saving."""
    return await _run_provider_test(body.provider, body.api_key)


@router.post("/{provider_id}/test")
async def test_saved_provider(provider_id: int, user: dict = Depends(get_current_user)):
    """Test a saved AI provider by decrypting its stored key."""
    p = get_ai_provider(provider_id, user["id"])
    if not p:
        raise HTTPException(status_code=404, detail="Provider not found")
    api_key = decrypt_api_key(p["encrypted_key"])
    return await _run_provider_test(p["provider"], api_key)
