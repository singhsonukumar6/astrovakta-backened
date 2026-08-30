"""Payments with Dodo Payments integration.

Dodo Payments supports a hosted checkout flow:
1. Create a Checkout Session via Dodo's API (POST /checkouts).
2. Redirect the user to Dodo's hosted checkout URL.
3. Dodo notifies via webhook (Standard Webhooks spec) when the payment succeeds.
"""
import os
import json
import base64
import hmac
import hashlib
import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..content import (
    create_payment,
    get_payment_by_id,
    get_payment_by_dodo_payment,
    update_payment,
    list_payments,
    payments_totals,
)
from .auth_router import get_current_user
from .admin_content import require_admin

router = APIRouter()

DODO_API_KEY = os.getenv("DODO_API_KEY", "")
DODO_WEBHOOK_SECRET = os.getenv("DODO_WEBHOOK_SECRET", "")
DODO_SUCCESS_URL = os.getenv("DODO_SUCCESS_URL", os.getenv("FRONTEND_URL", "http://localhost:5173") + "/dashboard")
DODO_CANCEL_URL = os.getenv("DODO_CANCEL_URL", os.getenv("FRONTEND_URL", "http://localhost:5173") + "/pricing")

# Dodo API hosts: test.dodopayments.com (test keys) / live.dodopayments.com (live keys).
# DODO_API_BASE can override, but the default MUST be a real host (api.dodopayments.com does not exist).
def _dodo_base() -> str:
    override = os.getenv("DODO_API_BASE", "").strip()
    if override:
        return override.rstrip("/")
    if DODO_API_KEY.startswith("dodo_test_"):
        return "https://test.dodopayments.com"
    return "https://live.dodopayments.com"


# Dodo Checkout Sessions are priced per product (product_id), not from a free-form amount.
# Map plan + currency to product IDs configured in the Dodo dashboard. Per-currency IDs
# fall back to the plan-level ID when the currency-specific one isn't set.
_PRODUCT_ENV = {
    "starter": {"usd": "DODO_PRODUCT_STARTER_USD", "inr": "DODO_PRODUCT_STARTER_INR"},
    "pro": {"usd": "DODO_PRODUCT_PRO_USD", "inr": "DODO_PRODUCT_PRO_INR"},
}


def _product_id_for(plan: str, currency: str) -> str:
    currency = (currency or "USD").upper()
    env_key = _PRODUCT_ENV[plan].get(currency.lower(), "")
    pid = os.getenv(env_key) or os.getenv(f"DODO_PRODUCT_{plan.upper()}") or ""
    if not pid:
        detail = f"Dodo product not configured. Set {env_key or f'DODO_PRODUCT_{plan.upper()}'} in .env"
        raise HTTPException(status_code=500, detail=detail)
    return pid


PLAN_PRICES = {
    "starter": {"usd": 2900, "inr": 149900},
    "pro": {"usd": 9900, "inr": 499900},
}


def _amount_for_plan(plan: str, currency: str) -> int:
    prices = PLAN_PRICES.get(plan)
    if not prices:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
    currency = (currency or "USD").upper()
    if currency == "INR":
        return prices["inr"]
    return prices["usd"]


class CreateCheckoutBody(BaseModel):
    plan: str = Field(..., pattern="^(starter|pro)$")
    currency: str = Field("USD", pattern="^(USD|INR)$")


@router.post("/checkout")
def create_checkout(body: CreateCheckoutBody, user: dict = Depends(get_current_user)):
    if not DODO_API_KEY:
        raise HTTPException(status_code=503, detail="Payments not configured. Set DODO_API_KEY.")

    amount = _amount_for_plan(body.plan, body.currency)
    currency = body.currency.upper()

    payment = create_payment({
        "user_id": user["id"],
        "email": user.get("email"),
        "name": user.get("name"),
        "amount": amount,
        "currency": currency,
        "plan": body.plan,
        "provider": "dodo",
        "status": "pending",
        "metadata": {"user_id": user["id"], "plan": body.plan},
    })

    product_id = _product_id_for(body.plan, currency)

    payload = {
        "product_cart": [
            {
                "product_id": product_id,
                "quantity": 1,
            }
        ],
        "customer": {
            "email": user.get("email"),
            "name": user.get("name"),
        },
        "return_url": DODO_SUCCESS_URL,
        "cancel_url": DODO_CANCEL_URL,
        "metadata": {"payment_id": str(payment["id"]), "user_id": str(user["id"]), "plan": body.plan},
    }

    try:
        import httpx
        resp = httpx.post(
            f"{_dodo_base()}/checkouts",
            json=payload,
            headers={
                "Authorization": f"Bearer {DODO_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
        )
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Dodo checkout session failed ({resp.status_code}): {data}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Dodo API error: {e}")

    session_id = data.get("session_id") or data.get("id")
    checkout_url = data.get("checkout_url") or data.get("payment_link")

    if session_id:
        update_payment(payment["id"], {"dodo_payment_id": session_id})

    if not checkout_url:
        raise HTTPException(status_code=502, detail="Dodo returned no checkout URL")

    return {
        "checkout_url": checkout_url,
        "payment_id": payment["id"],
        "dodo_payment_id": session_id,
        "amount": amount,
        "currency": currency,
        "plan": body.plan,
    }


@router.post("/webhook")
async def dodo_webhook(request: Request):
    raw = await request.body()
    if DODO_WEBHOOK_SECRET:
        # Dodo uses the Standard Webhooks specification (Svix):
        # headers: webhook-id, webhook-timestamp, webhook-signature
        # signature = base64(hmac_sha256(secret, "<timestamp>.<raw_body>"))
        sig_header = request.headers.get("Webhook-Signature") or request.headers.get("webhook-signature") or ""
        timestamp = request.headers.get("Webhook-Timestamp") or request.headers.get("webhook-timestamp") or ""
        _id = request.headers.get("Webhook-Id") or request.headers.get("webhook-id") or ""

        sig_parts = [s for s in sig_header.split(" ") if s and not s.startswith("t=")]
        received = ""
        for s in sig_parts:
            if s.startswith("v1,"):
                received = s[len("v1,"):]
                break
        if received:
            signed_content = f"{timestamp}.{raw.decode('utf-8')}".encode()
            computed = base64.b64encode(
                hmac.new(DODO_WEBHOOK_SECRET.encode(), signed_content, hashlib.sha256).digest()
            ).decode()
            if not hmac.compare_digest(received, computed):
                raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        event = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("type") or event.get("event") or ""
    payload = event.get("data") or event.get("payment") or event

    dodo_payment_id = (
        payload.get("id")
        or payload.get("payment_id")
        or event.get("id")
    )

    payment = get_payment_by_dodo_payment(dodo_payment_id) if dodo_payment_id else None
    if not payment:
        metadata = payload.get("metadata") or {}
        pid = metadata.get("payment_id") or payload.get("payment_id")
        if pid:
            try:
                payment = get_payment_by_id(int(pid))
            except (TypeError, ValueError):
                payment = None

    status = str(event_type).lower()
    mapped = None
    if "succeed" in status or status in ("paid", "payment.succeeded", "charge.succeeded", "completed"):
        mapped = "completed"
    elif "fail" in status or status in ("failed", "payment.failed"):
        mapped = "failed"
    elif "cancel" in status:
        mapped = "cancelled"
    elif "refund" in status:
        mapped = "refunded"

    if mapped and not payment:
        # Record from event data even if we couldn't match a local row.
        payment = create_payment({
            "dodo_payment_id": dodo_payment_id,
            "status": mapped,
            "amount": payload.get("amount") or 0,
            "currency": payload.get("currency", "USD"),
            "provider": "dodo",
            "metadata": payload.get("metadata"),
        })

    if mapped and payment:
        update_payment(payment["id"], {"status": mapped, "dodo_payment_id": dodo_payment_id or payment.get("dodo_payment_id")})
        if mapped == "completed" and payment.get("plan") and payment.get("user_id"):
            try:
                from ..auth import admin_update_user_plan
                admin_update_user_plan(payment["user_id"], payment["plan"])
            except Exception:
                pass

    return {"received": True}


# ─── USER'S OWN PAYMENTS ───
@router.get("/my-payments")
def my_payments(
    page: int = 1,
    user: dict = Depends(get_current_user),
):
    return list_payments(user_id=user["id"], page=page)


# ─── ADMIN EARNINGS ───
@router.get("/admin/payments")
def admin_list_payments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str = Query(""),
    admin: dict = Depends(require_admin),
):
    return list_payments(page=page, per_page=per_page, status=status)


@router.get("/admin/payments/totals")
def admin_payments_totals(admin: dict = Depends(require_admin)):
    return payments_totals()
