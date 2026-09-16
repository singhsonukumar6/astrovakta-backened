"""Site builder: owner-facing management endpoints for tenant websites.

All routes require the site owner's JWT (get_current_user). A tenant resolves
their site via /sites/my/* — sites are looked up by id and verified against the
owner's user id, so tenants can never touch each other's data.
"""
import os
import re
from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from .admin_content import require_admin
from ..email_service import send_booking_emails, send_invoice_email
from ..tenants import (
    get_site_by_slug,
    validate_slug, normalize_domain, slug_exists, domain_exists, TEMPLATES, WEEKDAYS,
    RESERVED_SLUGS, list_sites, get_site_by_id, create_site, update_site, set_site_status, delete_site,
    list_pages, upsert_page,
    list_services, get_service, create_service, update_service, delete_service,
    list_availability, set_availability,
    list_bookings, get_booking, create_booking, update_booking,
    list_leads,
    list_clients, get_client, create_client, update_client, delete_client, convert_lead_to_client,
    list_invoices, get_invoice, create_invoice, update_invoice, delete_invoice,
    list_products, get_product, create_product, update_product, delete_product,
    list_social_posts, create_social_post, update_social_post, delete_social_post,
    list_master_categories, create_master_category, update_master_category, delete_master_category,
    list_master_products, get_master_product, create_master_product, update_master_product, delete_master_product,
    import_master_product,
    site_credit_balance, adjust_site_credits, site_credit_history, site_analytics, record_site_event,
    list_store_connections, get_store_connection, create_store_connection, delete_store_connection,
    record_integration_product, get_integration_product_map, get_order, create_order,
    create_oauth_state, get_oauth_state, delete_oauth_state, delete_oauth_state_for_site,
    list_orders, get_order, create_order, update_order, ORDER_STATUSES,
    site_stats, adjust_product_stock,
)
from .auth_router import get_current_user

router = APIRouter()

_DATA_URL_RE = re.compile(r"^data:image/(png|jpe?g|webp|svg\+xml);base64,[A-Za-z0-9+/=\s]+$")
_MAX_MEDIA_BYTES = 500 * 1024  # 500 KB decoded — data URLs live in a TEXT column


def _validate_media_data_url(value: str, label: str) -> str:
    if not _DATA_URL_RE.match(value or ""):
        raise HTTPException(status_code=400, detail=f"{label} must be a PNG, JPEG, WebP or SVG image")
    try:
        b64 = value.split(",", 1)[1]
        padding = b64.count("=")
        size = (len(b64) * 3) // 4 - padding
    except Exception:
        size = _MAX_MEDIA_BYTES + 1
    if size > _MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail=f"{label} is too large — please use an image under 500 KB")
    return value


def _require_owned_site(site_id: int, user: dict) -> dict:
    site = get_site_by_id(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if site["user_id"] != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="You do not own this site")
    return site


# ─────────────── bodies ───────────────

class CreateSiteBody(BaseModel):
    slug: str = Field(..., min_length=3, max_length=32)
    name: str = Field(None, min_length=1, max_length=80)
    tagline: str = Field(None, max_length=140)
    template: str = Field("aurora")

class UpdateSiteBody(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    tagline: Optional[str] = Field(None, max_length=140)
    template: Optional[str] = None
    theme: Optional[dict] = None

class SetDomainBody(BaseModel):
    domain: str = Field(..., min_length=4, max_length=255)

class PageBody(BaseModel):
    title: Optional[str] = Field(None, max_length=120)
    content: Optional[dict] = None
    is_published: bool = True

class ServiceBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    duration_minutes: int = Field(30, ge=5, le=480)
    price: int = Field(0, ge=0)
    currency: str = Field("INR", max_length=3)
    is_active: bool = True
    sort_order: int = 0

class AvailabilityRule(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")

class AvailabilityBody(BaseModel):
    rules: List[AvailabilityRule]

class BookingBody(BaseModel):
    service_id: Optional[int] = None
    client_name: str = Field(..., min_length=1, max_length=120)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    amount: int = Field(0, ge=0)
    currency: str = Field("INR", max_length=3)

class UpdateBookingBody(BaseModel):
    status: Optional[str] = Field(None, pattern="^(confirmed|completed|cancelled|no_show)$")
    notes: Optional[str] = Field(None, max_length=1000)

class ProductBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=140)
    description: Optional[str] = Field(None, max_length=1000)
    price: int = Field(0, ge=0)
    currency: str = Field("INR", max_length=3)
    image: Optional[str] = None
    stock: int = Field(-1, ge=-1)
    is_active: bool = True
    sort_order: int = 0
    category: Optional[str] = Field(None, max_length=80)

class UpdateProductBody(ProductBody):
    name: Optional[str] = Field(None, min_length=1, max_length=140)

class OrderItemBody(BaseModel):
    product_id: int
    name: str = Field(..., min_length=1, max_length=140)
    price: int = Field(0, ge=0)
    qty: int = Field(1, ge=1, le=99)

class CreateOrderBody(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=120)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)
    items: List[OrderItemBody]
    notes: Optional[str] = Field(None, max_length=1000)

class UpdateOrderBody(BaseModel):
    status: Optional[str] = Field(None, pattern="^(new|confirmed|fulfilled|cancelled)$")
    notes: Optional[str] = Field(None, max_length=1000)


# ─────────────── availability checks (public, used by the wizard) ───────────────

@router.get("/check-slug")
def check_slug(slug: str):
    slug = (slug or "").strip().lower()
    err = validate_slug(slug)
    if err:
        return {"available": False, "reason": err, "suggestion": _slug_suggestion(slug)}
    if slug_exists(slug):
        return {"available": False, "reason": "That web address is already taken", "suggestion": _slug_suggestion(slug)}
    return {"available": True, "reason": None, "suggestion": None}


def _slug_suggestion(slug: str):
    base = (slug or "mysite").strip().lower()
    for candidate in (f"{base}-astrology", f"{base}-jyotish", f"astro-{base}"):
        if not validate_slug(candidate) and not slug_exists(candidate):
            return candidate
    import random
    while True:
        candidate = f"{base}{random.randint(10, 999)}"
        if not validate_slug(candidate) and not slug_exists(candidate):
            return candidate


@router.get("/check-domain")
def check_domain(domain: str):
    d = normalize_domain(domain)
    if not d or "." not in d:
        return {"valid": False, "available": False, "reason": "Enter a valid domain like yourname.com"}
    available = not domain_exists(d)
    return {"valid": True, "available": available,
            "reason": None if available else "That domain is already connected to another site"}


# ─────────────── sites ───────────────

_TEMPLATE_META = {
    "aurora": {"name": "Aurora", "desc": "Indigo & amber — clean, light and modern", "tier": "free"},
    "classic": {"name": "Classic", "desc": "Traditional warm browns on a deep night theme", "tier": "free"},
    "minimal": {"name": "Minimal", "desc": "Fresh teal — calm and clutter-free", "tier": "free"},
    "devotional": {"name": "Devotional", "desc": "Saffron & marigold — temple-inspired", "tier": "free"},
    "celestial": {"name": "Celestial", "desc": "Indigo night sky with stars & elegant serif headings", "tier": "premium"},
    "royal": {"name": "Royal Heritage", "desc": "Deep maroon & gold — regal, luxurious", "tier": "premium"},
    "tantra": {"name": "Tantra", "desc": "Crimson & ember — bold, mystical energy", "tier": "premium"},
    "modern-light": {"name": "Modern Studio", "desc": "Blue & violet on white — sleek agency look", "tier": "premium"},
}


@router.get("/templates")
def list_templates():
    from ..tenants import TEMPLATE_THEMES
    return {"templates": [
        {"id": t, **_TEMPLATE_META.get(t, {"name": t.capitalize(), "desc": "", "tier": "free"}),
         "preview": {"theme": TEMPLATE_THEMES.get(t, {})}}
        for t in TEMPLATES
    ]}


@router.get("/my")
def my_sites(user: dict = Depends(get_current_user)):
    return {"sites": list_sites(user["id"])}


@router.post("/my")
def create_my_site(body: CreateSiteBody, user: dict = Depends(get_current_user)):
    slug = body.slug.strip().lower()
    err = validate_slug(slug)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if slug_exists(slug):
        raise HTTPException(status_code=409, detail="That web address is already taken")
    site = create_site(user["id"], {
        "slug": slug,
        "name": body.name,
        "tagline": body.tagline,
        "template": body.template,
    })
    from ..tenants import grant_starter_credits
    grant_starter_credits(site["id"])
    return site


@router.get("/my/{site_id}")
def my_site_detail(site_id: int, user: dict = Depends(get_current_user)):
    site = _require_owned_site(site_id, user)
    site["pages"] = list_pages(site_id)
    site["services"] = list_services(site_id)
    site["availability"] = list_availability(site_id)
    return site


@router.put("/my/{site_id}")
def update_my_site(site_id: int, body: UpdateSiteBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if body.template is not None and body.template not in TEMPLATES:
        raise HTTPException(status_code=400, detail="Invalid template")
    return update_site(site_id, body.model_dump(exclude_none=True))


@router.post("/my/{site_id}/publish")
def publish_my_site(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return set_site_status(site_id, "published")


@router.post("/my/{site_id}/unpublish")
def unpublish_my_site(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return set_site_status(site_id, "draft")


@router.delete("/my/{site_id}")
def delete_my_site(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not delete_site(site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    return {"deleted": True}


# ─────────────── domain ───────────────

# Second-level public suffixes: "yourname.co.in" has three labels but is
# still an apex domain, not a subdomain.
_SECOND_LEVEL_SUFFIXES = {
    "co.in", "net.in", "org.in", "firm.in", "gen.in", "ind.in", "ac.in",
    "edu.in", "res.in", "gov.in", "mil.in", "co.uk", "org.uk", "ac.uk",
    "gov.uk", "com.au", "net.au", "org.au", "co.nz", "co.za", "com.br",
    "com.mx", "co.jp", "or.jp", "ne.jp",
}


def _is_subdomain(domain: str) -> bool:
    """True for astro.yourname.com (served by a single CNAME), False for
    apex domains like yourname.com / yourname.co.in."""
    parts = [p for p in (domain or "").split(".") if p]
    if len(parts) < 3:
        return False
    if len(parts) == 3 and ".".join(parts[-2:]) in _SECOND_LEVEL_SUFFIXES:
        return False
    return True


@router.post("/my/{site_id}/domain")
def set_my_site_domain(site_id: int, body: SetDomainBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    domain = normalize_domain(body.domain)
    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Enter a valid domain like yourname.com or astro.yourname.com")
    if domain_exists(domain, exclude_id=site_id):
        raise HTTPException(status_code=409, detail="That domain is already connected to another site")
    site = update_site(site_id, {"custom_domain": domain, "domain_status": "pending"})
    # The main frontend is hosted on Vercel: the custom domain points at
    # Vercel's edge (A 76.76.21.21 for the apex, CNAME cname.vercel-dns.com
    # for subdomains), which serves this tenant's site for that hostname.
    # Activation is confirmed by the verify endpoint once records resolve.
    if _is_subdomain(domain):
        records = [{
            "type": "CNAME", "host": domain, "value": "cname.vercel-dns.com",
            "label": f"CNAME for {domain}",
        }]
        note = (
            f"Add a CNAME record for {domain} pointing to cname.vercel-dns.com "
            f"at your DNS provider (some providers show the host as just "
            f"'{domain.split('.')[0]}'), then tap Verify."
        )
    else:
        records = [
            {"type": "A", "host": "@", "value": "76.76.21.21",
             "label": f"A record for {domain} (apex)"},
            {"type": "CNAME", "host": "www", "value": "cname.vercel-dns.com",
             "label": f"CNAME for www.{domain}"},
        ]
        note = (
            f"Add an A record @ → 76.76.21.21 and a CNAME www → cname.vercel-dns.com "
            f"at your DNS provider, then tap Verify."
        )
    return {**site, "dns_instructions": {"records": records, "note": note}}


@router.post("/my/{site_id}/domain/verify")
def verify_my_site_domain(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    site = get_site_by_id(site_id)
    if not site.get("custom_domain"):
        raise HTTPException(status_code=400, detail="Add a domain first")
    import socket
    domain = site["custom_domain"]
    # The domain itself resolves for subdomain CNAMEs and apex A records;
    # www covers apex setups that only point the www host. Try in that order.
    resolved = None
    for host in dict.fromkeys([domain, f"www.{domain}"]):
        try:
            resolved = socket.gethostbyname(host)
            break
        except Exception:
            continue
    if not resolved:
        return {**site, "domain_status": "pending", "verified": False,
                "message": f"DNS not propagated yet — {domain} does not resolve. Wait a few minutes and try again."}
    updated = update_site(site_id, {"domain_status": "active"})
    return {**updated, "domain_status": "active", "verified": True,
            "message": f"Domain {domain} connected! SSL will be issued automatically within minutes."}


@router.delete("/my/{site_id}/domain")
def remove_my_site_domain(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    site = update_site(site_id, {"custom_domain": None, "domain_status": "none"})
    return site


# ─────────────── media (logo & hero photo) ───────────────

class MediaBody(BaseModel):
    logo_url: Optional[str] = None
    hero_image: Optional[str] = None


@router.put("/my/{site_id}/media")
def update_my_site_media(site_id: int, body: MediaBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    data = {}
    if body.logo_url is not None:
        data["logo_url"] = _validate_media_data_url(body.logo_url, "Logo") if body.logo_url else None
    if body.hero_image is not None:
        data["hero_image"] = _validate_media_data_url(body.hero_image, "Hero photo") if body.hero_image else None
    if not data:
        raise HTTPException(status_code=400, detail="Nothing to update")
    return update_site(site_id, data)


# ─────────────── settings (alerts, contact & social links) ───────────────

_SOCIAL_FIELDS = {
    "instagram": "instagram",
    "youtube": "youtube",
    "facebook": "facebook",
    "twitter": "twitter",
    "linkedin": "linkedin",
    "telegram": "telegram",
    "websiteUrl": "websiteUrl",
    "email": "email",
    "phone": "phone",
    "city": "city",
}


class SettingsBody(BaseModel):
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    booking_alerts: Optional[bool] = None
    reminder_hours: Optional[int] = Field(None, ge=1, le=72)
    instagram: Optional[str] = Field(None, max_length=255)
    youtube: Optional[str] = Field(None, max_length=255)
    facebook: Optional[str] = Field(None, max_length=255)
    twitter: Optional[str] = Field(None, max_length=255)
    linkedin: Optional[str] = Field(None, max_length=255)
    telegram: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=30)
    city: Optional[str] = Field(None, max_length=120)
    show_store: Optional[bool] = None
    show_testimonials: Optional[bool] = None
    show_gallery: Optional[bool] = None
    payments_mode: Optional[str] = Field(None, pattern="^(later|upi|razorpay)$")
    upi_id: Optional[str] = Field(None, max_length=120)
    razorpay_key_id: Optional[str] = Field(None, max_length=120)
    social_auto_daily: Optional[bool] = None
    store_banners: Optional[list] = None
    store_sections: Optional[list] = None


@router.put("/my/{site_id}/settings")
def update_my_site_settings(site_id: int, body: SettingsBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    site = get_site_by_id(site_id)
    settings = dict(site.get("settings") or {})
    if body.whatsapp_number is not None:
        cleaned = re.sub(r"[^\d+]", "", body.whatsapp_number)
        if cleaned and not 8 <= len(cleaned.lstrip("+")) <= 15:
            raise HTTPException(status_code=400, detail="Enter a valid WhatsApp number with country code")
        settings["whatsappNumber"] = cleaned
    if body.booking_alerts is not None:
        settings["bookingAlerts"] = body.booking_alerts
    if body.reminder_hours is not None:
        settings["reminderHours"] = body.reminder_hours

    # social links & contact block — stored verbatim (full URL or handle)
    if body.instagram is not None:
        settings["instagram"] = body.instagram.strip()
    if body.youtube is not None:
        settings["youtube"] = body.youtube.strip()
    if body.facebook is not None:
        settings["facebook"] = body.facebook.strip()
    if body.twitter is not None:
        settings["twitter"] = body.twitter.strip()
    if body.linkedin is not None:
        settings["linkedin"] = body.linkedin.strip()
    if body.telegram is not None:
        settings["telegram"] = body.telegram.strip()
    if body.website_url is not None:
        settings["websiteUrl"] = body.website_url.strip()
    if body.contact_email is not None:
        settings["email"] = body.contact_email.strip()
    if body.contact_phone is not None:
        settings["phone"] = body.contact_phone.strip()
    if body.city is not None:
        settings["city"] = body.city.strip()
    if body.show_store is not None:
        settings["showStore"] = body.show_store
    if body.show_testimonials is not None:
        settings["showTestimonials"] = body.show_testimonials
    if body.show_gallery is not None:
        settings["showGallery"] = body.show_gallery
    # payments — how clients pay for bookings (pay later / UPI / Razorpay)
    if body.payments_mode is not None:
        settings["paymentsMode"] = body.payments_mode
    if body.upi_id is not None:
        cleaned_upi = body.upi_id.strip()
        if cleaned_upi and ("@" not in cleaned_upi):
            raise HTTPException(status_code=400, detail="Enter a valid UPI ID (e.g. name@bank)")
        settings["upiId"] = cleaned_upi
    if body.razorpay_key_id is not None:
        settings["razorpayKeyId"] = body.razorpay_key_id.strip()
    if body.social_auto_daily is not None:
        settings["socialAutoDaily"] = body.social_auto_daily
    # storefront merchandising: carousel banners + curated sections
    if body.store_banners is not None:
        import json as _jsonb
        cleaned = []
        for b in body.store_banners[:6]:
            if not isinstance(b, dict) or not b.get("image"):
                continue
            cleaned.append({
                "image": str(b["image"])[:500000],
                "title": str(b.get("title", ""))[:120],
                "subtitle": str(b.get("subtitle", ""))[:200],
                "link": str(b.get("link", "#/shop"))[:200],
            })
        settings["storeBanners"] = cleaned
    if body.store_sections is not None:
        import json as _jsons
        cleaned = []
        for sec in body.store_sections[:8]:
            if not isinstance(sec, dict) or not sec.get("title"):
                continue
            kind = sec.get("kind") if sec.get("kind") in ("bestselling", "top", "trending", "manual") else "manual"
            cleaned.append({
                "title": str(sec["title"])[:80],
                "kind": kind,
                "product_ids": [int(x) for x in (sec.get("product_ids") or [])[:12] if str(x).isdigit()][:12],
            })
        settings["storeSections"] = cleaned
    return update_site(site_id, {"settings": settings})


# ─────────────── leads (from free tools) ───────────────

@router.get("/my/{site_id}/leads")
def my_site_leads(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"leads": list_leads(site_id)}


@router.post("/my/{site_id}/leads/{lead_id}/convert")
def convert_lead(site_id: int, lead_id: int, user: dict = Depends(get_current_user)):
    """Turn a captured lead into a client (deduped by email)."""
    _require_owned_site(site_id, user)
    client = convert_lead_to_client(site_id, lead_id)
    if not client:
        raise HTTPException(status_code=404, detail="Lead not found")
    return client


# ─────────────── clients (converted leads + manual) ───────────────

class ClientBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        extra = "forbid"


@router.get("/my/{site_id}/clients")
def my_clients(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"clients": list_clients(site_id)}


@router.post("/my/{site_id}/clients")
def create_my_client(site_id: int, body: ClientBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return create_client(site_id, body.model_dump())


@router.put("/my/{site_id}/clients/{client_id}")
def update_my_client(site_id: int, client_id: int, body: ClientBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_client(site_id, client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return update_client(site_id, client_id, body.model_dump(exclude_none=True))


@router.delete("/my/{site_id}/clients/{client_id}")
def delete_my_client(site_id: int, client_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not delete_client(site_id, client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"deleted": True}


# ─────────────── invoices ───────────────

class InvoiceItemBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    qty: int = Field(1, ge=1, le=999)
    price: int = Field(0, ge=0)

    class Config:
        extra = "forbid"


class InvoiceBody(BaseModel):
    client_id: int
    items: List[InvoiceItemBody] = Field(..., min_length=1, max_length=30)
    tax_rate: float = Field(0, ge=0, le=50)
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        extra = "forbid"


class InvoiceStatusBody(BaseModel):
    status: str = Field(..., pattern="^(draft|sent|paid)$")


@router.get("/my/{site_id}/invoices")
def my_invoices(site_id: int, client_id: int = None, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"invoices": list_invoices(site_id, client_id=client_id)}


@router.post("/my/{site_id}/invoices")
def create_my_invoice(site_id: int, body: InvoiceBody, background_tasks: BackgroundTasks,
                      user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_client(site_id, body.client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return create_invoice(site_id, body.model_dump())


@router.put("/my/{site_id}/invoices/{invoice_id}")
def update_my_invoice(site_id: int, invoice_id: int, body: InvoiceBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_invoice(site_id, invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return update_invoice(site_id, invoice_id, body.model_dump(exclude_none=True))


@router.post("/my/{site_id}/invoices/{invoice_id}/send")
def send_my_invoice(site_id: int, invoice_id: int, background_tasks: BackgroundTasks,
                    user: dict = Depends(get_current_user)):
    """Email the invoice to the client (white-label) and mark it sent."""
    _require_owned_site(site_id, user)
    invoice = get_invoice(site_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not invoice.get("client_email"):
        raise HTTPException(status_code=400, detail="This client has no email address — add one, or share via WhatsApp")
    site = get_site_by_id(site_id)
    client = get_client(site_id, invoice["client_id"])
    invoice = update_invoice(site_id, invoice_id, {"status": "sent"})
    background_tasks.add_task(send_invoice_email, site, invoice, client)
    return {"sent": True, "invoice": invoice}


@router.post("/my/{site_id}/invoices/{invoice_id}/status")
def set_my_invoice_status(site_id: int, invoice_id: int, body: InvoiceStatusBody,
                          user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_invoice(site_id, invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return update_invoice(site_id, invoice_id, {"status": body.status})


@router.delete("/my/{site_id}/invoices/{invoice_id}")
def delete_my_invoice(site_id: int, invoice_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not delete_invoice(site_id, invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"deleted": True}


# ─────────────── pages ───────────────

@router.put("/my/{site_id}/pages/{page_key}")
def upsert_my_page(site_id: int, page_key: str, body: PageBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not page_key or len(page_key) > 40:
        raise HTTPException(status_code=400, detail="Invalid page key")
    return upsert_page(site_id, page_key, body.model_dump())


# ─────────────── AI content generation (site owner's own AI provider) ───────────────

class AiGenerateBody(BaseModel):
    field: str = Field(..., pattern="^(heroTitle|heroSubtitle|aboutTitle|aboutText|pageTitle|pageText|serviceDescription|tagline)$")
    tone: str = Field("warm", pattern="^(warm|professional|spiritual|friendly)$")
    keywords: Optional[str] = Field(None, max_length=300)
    # free-form "what should the AI focus on" from the Write-with-AI dialog
    instructions: Optional[str] = Field(None, max_length=500)
    # serviceDescription: which service; pageTitle/pageText: which page key
    context_key: Optional[str] = Field(None, max_length=40)


@router.post("/my/{site_id}/ai-generate")
def my_site_ai_generate(site_id: int, body: AiGenerateBody, user: dict = Depends(get_current_user)):
    """Generate website copy with the site owner's configured AI provider
    (AI Providers tab). Falls back to template copy when no provider is set,
    so the button always returns something usable."""
    site = _require_owned_site(site_id, user)
    name = site.get("name") or "our astrologer"
    tagline = site.get("tagline") or ""
    services = list_services(site_id) or []
    svc_names = ", ".join(s["name"] for s in services[:6]) or "kundli reading, match making, career guidance"

    TONE = {"warm": "warm and inviting", "professional": "polished and professional",
            "spiritual": "devotional and rooted in Vedic tradition", "friendly": "friendly and easygoing"}
    tone = TONE.get(body.tone, "warm and inviting")
    kw = f" Weave in these themes if natural: {body.keywords}." if body.keywords else ""

    fallbacks = {
        "heroTitle": f"{name} — Vedic Astrology Guidance",
        "heroSubtitle": f"{tagline or 'Authentic kundli readings'} by {name}. Personalised guidance for career, "
                        "relationships and life's big decisions — book a consultation today.",
        "aboutTitle": f"About {name}",
        "aboutText": f"{name} is a dedicated Vedic astrologer offering kundli readings, match making and "
                     "remedial guidance. With a practical, compassionate approach, every reading is prepared "
                     "personally for you. Services include {svc_names}.",
        "pageTitle": f"{body.context_key or 'About'.capitalize()}",
        "pageText": f"Welcome. {name} offers {svc_names} with personal attention to every chart. "
                    "Reach out to book a consultation or ask a question — you'll hear back the same day.",
        "serviceDescription": f"A personal session with {name} — detailed analysis of your chart with clear, "
                               "actionable guidance. Book online in under a minute.",
        "tagline": "Authentic Vedic astrology, personalised for you",
    }
    fallback = fallbacks.get(body.field)

    prompt_extra = {
        "heroTitle": "ONE punchy headline, max 8 words, no quotes.",
        "heroSubtitle": "ONE sub-headline of 1-2 sentences (max 180 chars).",
        "aboutTitle": "ONE section title, max 6 words.",
        "aboutText": "2-3 short paragraphs (max 900 chars total), plain text, no markdown.",
        "pageTitle": "ONE page title, max 6 words.",
        "pageText": "2-3 short paragraphs (max 1200 chars total), plain text, no markdown.",
        "serviceDescription": "ONE sentence of 15-35 words describing the service.",
        "tagline": "ONE short tagline, max 10 words.",
    }.get(body.field, "ONE short value.")

    prompt = (
        f"You write website copy for a professional Vedic astrology practice.\n"
        f"Astrologer / business: {name}. Tagline: {tagline or 'none yet'}. Services: {svc_names}.\n"
        f"Write in a {tone} tone.{kw}"
        + (f"\nThe astrologer specifically asks: {body.instructions} — honour this above everything else.\n"
           if body.instructions else "\n")
        + f"Produce ONLY the requested copy — no greeting, no explanation, no quotes, no markdown.\n"
        f"Requested: {prompt_extra}"
    )

    # Reuse the platform's AI plumbing: the owner's active provider from the
    # AI Providers tab, decrypted server-side exactly like horoscope generation.
    text = None
    try:
        from ..auth import get_active_ai_provider
        from ..crypto import decrypt_api_key
        from ..i18n.ai_translate import _call_ai
        cfg = get_active_ai_provider(user["id"])
        if cfg:
            api_key = decrypt_api_key(cfg["api_key_encrypted"])
            text = _call_ai(prompt, api_key, cfg["provider"], cfg.get("model"))
    except Exception:
        text = None

    if not text or not text.strip():
        text = fallback or "Welcome to our practice."
    text = text.strip().strip('"').strip()

    return {"field": body.field, "text": text, "ai": bool(text != fallback and fallback is not None)}


# ─────────────── services ───────────────

@router.get("/my/{site_id}/services")
def my_services(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"services": list_services(site_id)}


@router.post("/my/{site_id}/services")
def create_my_service(site_id: int, body: ServiceBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return create_service(site_id, body.model_dump())


@router.put("/my/{site_id}/services/{service_id}")
def update_my_service(site_id: int, service_id: int, body: ServiceBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_service(site_id, service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return update_service(site_id, service_id, body.model_dump())


@router.delete("/my/{site_id}/services/{service_id}")
def delete_my_service(site_id: int, service_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not delete_service(site_id, service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"deleted": True}


# ─────────────── availability ───────────────

@router.get("/my/{site_id}/availability")
def my_availability(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"availability": list_availability(site_id), "weekdays": WEEKDAYS}


@router.put("/my/{site_id}/availability")
def set_my_availability(site_id: int, body: AvailabilityBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    rules = [r.model_dump() for r in body.rules]
    for r in rules:
        if r["end_time"] <= r["start_time"]:
            raise HTTPException(status_code=400, detail=f"End time must be after start time for {WEEKDAYS[r['weekday']]}")
    return {"availability": set_availability(site_id, rules), "weekdays": WEEKDAYS}


# ─────────────── bookings (owner view + manual create) ───────────────

@router.get("/my/{site_id}/bookings")
def my_bookings(site_id: int, date_from: str = None, date_to: str = None, status: str = "", user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"bookings": list_bookings(site_id, date_from=date_from, date_to=date_to, status=status)}


@router.post("/my/{site_id}/bookings")
def create_my_booking(site_id: int, body: BookingBody, background_tasks: BackgroundTasks,
                      user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if body.end_time <= body.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    booking = create_booking(site_id, body.model_dump())
    # The astrologer booked on a client's behalf — send the client the same
    # white-label confirmation (no owner alert needed; they made the booking).
    if booking.get("client_email"):
        site = get_site_by_id(site_id)
        service = get_service(site_id, booking.get("service_id")) if booking.get("service_id") else None
        background_tasks.add_task(send_booking_emails, site, booking, service, False)
    return booking


@router.put("/my/{site_id}/bookings/{booking_id}")
def update_my_booking(site_id: int, booking_id: int, body: UpdateBookingBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_booking(site_id, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return update_booking(site_id, booking_id, body.model_dump(exclude_none=True))


# ─────────────── stats (owner dashboard overview) ───────────────

@router.get("/my/{site_id}/stats")
def my_site_stats(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return site_stats(site_id)


# ─────────────── social media automation ───────────────

class SocialPostBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    platforms: Optional[str] = Field("", max_length=120)
    scheduled_at: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
    status: Optional[str] = Field("draft", pattern="^(draft|scheduled|posted|cancelled)$")


class GeneratePostBody(BaseModel):
    kind: str = Field("daily", pattern="^(daily|festival|promo|custom)$")
    topic: Optional[str] = Field(None, max_length=200)


_TIPS = [
    "A calm mind attracts favourable planets — start your day with 5 minutes of silence.",
    "Light a diya at sunrise and let gratitude set the tone of your day.",
    "Offer water to the Sun (Surya Arghya) for confidence and clarity.",
    "Keep your north-east corner clean and clutter-free for positive energy.",
    "Chanting even one mantra daily with devotion is more powerful than a hundred done absent-mindedly.",
    "Thursdays are auspicious for worshiping Lord Vishnu and donating yellow food.",
    "Wearing gemstones without consulting your chart can do more harm than good — always check first.",
    "Charity done quietly multiplies good karma — donate what you can, when you can.",
]


def _compose_social_post(site: dict, kind: str, topic: Optional[str] = None) -> str:
    """Compose a ready-to-post update from the live astrology engines."""
    from datetime import date as _date, datetime as _datetime
    from .festival import HINDU_FESTIVALS
    from ..utils import compute_panchang

    name = site.get("name") or "Your astrologer"
    site_url = f"https://{site.get('slug')}.astrovakta.com" if site.get("slug") else ""
    today = _date.today()

    if kind == "daily":
        p = compute_panchang(today.isoformat(), "12:00", "Asia/Kolkata", 28.6139, 77.2090)
        tithi = p.get("tithi") or p.get("Tithi") or ""
        nak = p.get("nakshatra") or p.get("Nakshatra") or ""
        tip = _TIPS[today.timetuple().tm_yday % len(_TIPS)]
        lines = [
            f"🕉️ {today.strftime('%A, %d %B %Y')} — Today's Panchang",
            f"Tithi: {tithi} | Nakshatra: {nak}" if (tithi or nak) else "Auspicious day for new beginnings.",
            "",
            f"✨ Astro tip of the day: {tip}",
            "",
            f"For a personal reading, book a consultation with {name}." + (f" 👉 {site_url}" if site_url else ""),
            "#astrology #vedicastrology #panchang #dailyhoroscope #jyotish",
        ]
        return "\n".join(lines)

    if kind == "festival":
        year = today.year
        upcoming = []
        for fest, fest_date in (HINDU_FESTIVALS.get(year, {})).items():
            try:
                d = _datetime.strptime(fest_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if d >= today:
                upcoming.append((d, fest))
        upcoming.sort()
        if upcoming:
            d, fest = upcoming[0]
            days_to = (d - today).days
            when = f"tomorrow!" if days_to == 0 else f"on {d.strftime('%d %B')} ({days_to} days to go)"
            lines = [
                f"🪔 {fest} falls {when}",
                "",
                f"Wishing you and your family divine blessings on this auspicious occasion. "
                f"Celebrate with devotion — and if you want to know what this festival means for your chart, "
                f"book a consultation with {name}." + (f" 👉 {site_url}" if site_url else ""),
                "#festival #hindufestival #astrology #vedicastrology",
            ]
            return "\n".join(lines)
        return _compose_social_post(site, "daily")

    if kind == "promo":
        from .tenants import list_services
        svcs = list_services(site.get("id")) or []
        svc_lines = "\n".join(f"• {s['name']} — ₹{s.get('price', 0)}" for s in svcs[:4])
        lines = [
            "🔮 Consultations now open!",
            "",
            svc_lines or "• Kundli reading • Match making • Career & business guidance",
            "",
            f"Book online in under a minute." + (f" 👉 {site_url}" if site_url else ""),
            "#astrologyconsultation #kundli #vedicastrology #booknow",
        ]
        return "\n".join(lines)

    # custom
    clean_topic = (topic or "").strip() or "Astrology wisdom for everyday life"
    lines = [
        f"✨ {clean_topic}",
        "",
        f"— {name}" + (f" | {site_url}" if site_url else ""),
        "#astrology #vedicastrology #jyotish",
    ]
    return "\n".join(lines)


@router.get("/my/{site_id}/social")
def my_social_posts(site_id: int, ensure: int = 0, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if ensure:
        site = get_site_by_id(site_id)
        settings = site.get("settings") or {}
        if settings.get("socialAutoDaily"):
            today = date.today().isoformat()
            posts = list_social_posts(site_id)
            if not any((p.get("created_at") or "")[:10] == today and p.get("kind") == "daily" for p in posts):
                content = _compose_social_post(site, "daily")
                create_social_post(site_id, {"content": content, "kind": "daily", "status": "scheduled",
                                             "scheduled_at": f"{today}T09:00", "platforms": "whatsapp,facebook"})
    return {"posts": list_social_posts(site_id)}


@router.post("/my/{site_id}/social/generate")
def generate_social_post(site_id: int, body: GeneratePostBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    site = get_site_by_id(site_id)
    content = _compose_social_post(site, body.kind, body.topic)
    return {"content": content}


@router.post("/my/{site_id}/social")
def add_social_post(site_id: int, body: SocialPostBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    status = body.status
    if body.scheduled_at and status == "draft":
        status = "scheduled"
    post = create_social_post(site_id, {"content": body.content, "platforms": body.platforms,
                                        "scheduled_at": body.scheduled_at, "status": status, "kind": "custom"})
    return post


@router.put("/my/{site_id}/social/{post_id}")
def edit_social_post(site_id: int, post_id: int, body: SocialPostBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    post = update_social_post(site_id, post_id, body.model_dump(exclude_none=True))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/my/{site_id}/social/{post_id}")
def remove_social_post(site_id: int, post_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    delete_social_post(site_id, post_id)
    return {"ok": True}


class SocialMediaBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    format: str = Field("image", pattern="^(image|video)$")


@router.post("/my/{site_id}/social/media")
def social_post_media(site_id: int, body: SocialMediaBody, user: dict = Depends(get_current_user)):
    """Phase-1 media pipeline: branded image card (Pillow) or short slideshow
    video (ffmpeg) rendered from the post text in the site's theme colors."""
    _require_owned_site(site_id, user)
    from ..tenants import charge_site_credits
    if not charge_site_credits(site_id, "media_render"):
        raise HTTPException(status_code=402, detail="Out of credits — recharge to render more media")
    site = get_site_by_id(site_id)
    from ..social_media import render_image, render_video
    lines = [ln.strip() for ln in body.content.split("\n") if ln.strip()]
    headline = lines[0].lstrip("🕉️🪔✨🔮📅📣 ") if lines else site.get("name") or "AstroVakta"
    body_lines = lines[1:] or [""]
    footer = f"{site.get('slug')}.astrovakta.com" if site.get("slug") else ""
    try:
        if body.format == "video":
            return {"dataUrl": render_video(site, headline, body_lines, footer)}
        return {"dataUrl": render_image(site, headline, body_lines, footer)}
    except Exception:
        # don't leak renderer internals (paths, ffmpeg output) to the client
        raise HTTPException(status_code=500, detail="Could not render media — try shorter text")


# ─────────────── products (store) ───────────────

@router.get("/my/{site_id}/products")
def my_products(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"products": list_products(site_id)}


@router.post("/my/{site_id}/products")
def create_my_product(site_id: int, body: ProductBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    data = body.model_dump()
    if data.get("image"):
        data["image"] = _validate_media_data_url(data["image"], "Product photo")
    return create_product(site_id, data)


@router.put("/my/{site_id}/products/{product_id}")
def update_my_product(site_id: int, product_id: int, body: UpdateProductBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_product(site_id, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    data = body.model_dump(exclude_none=True)
    if data.get("image"):
        data["image"] = _validate_media_data_url(data["image"], "Product photo")
    return update_product(site_id, product_id, data)


@router.delete("/my/{site_id}/products/{product_id}")
def delete_my_product(site_id: int, product_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not delete_product(site_id, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"deleted": True}


# ─────────────── orders (store) ───────────────

@router.get("/my/{site_id}/orders")
def my_orders(site_id: int, status: str = "", user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if status and status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid order status")
    return {"orders": list_orders(site_id, status=status)}


@router.put("/my/{site_id}/orders/{order_id}")
def update_my_order(site_id: int, order_id: int, body: UpdateOrderBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    existing = get_order(site_id, order_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    updated = update_order(site_id, order_id, body.model_dump(exclude_none=True))
    # Cancelling an order returns reserved stock; re-opening a cancelled order
    # re-reserves it (when the stock is still there).
    if body.status and body.status != existing.get("status"):
        for it in existing.get("items") or []:
            qty = it.get("qty", 0)
            if qty > 0:
                if body.status == "cancelled":
                    adjust_product_stock(site_id, it["product_id"], qty)
                elif existing.get("status") == "cancelled" and body.status in ("new", "confirmed"):
                    adjust_product_stock(site_id, it["product_id"], -qty)
    return updated


# ─────────────── exports (CSV / calendar) ───────────────

def _csv_safe(value):
    """Neutralize CSV/Excel formula injection: visitor-supplied fields are
    exported verbatim, so a leading formula character must be defanged."""
    s = "" if value is None else str(value)
    if s[:1] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s.replace("\r", " ").replace("\n", " ")


def _csv_response(filename, rows, headers):
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    w.writerows([[_csv_safe(cell) for cell in row] for row in rows])
    from fastapi import Response as _Resp
    return _Resp(buf.getvalue(), media_type="text/csv",
                 headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/my/{site_id}/leads/export.csv")
def export_leads(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    leads = list_leads(site_id)
    rows = [(l.get("created_at"), l.get("name"), l.get("phone"), l.get("email"), l.get("tool"), (l.get("details") or "")) for l in leads]
    return _csv_response("leads.csv", rows, ["created_at", "name", "phone", "email", "tool", "details"])


@router.get("/my/{site_id}/bookings/export.csv")
def export_bookings(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    bookings = list_bookings(site_id)
    rows = [(b.get("created_at"), b.get("client_name"), b.get("client_phone"), b.get("date"),
             b.get("start_time"), b.get("service_name"), b.get("amount"), b.get("status"), b.get("payment_status")) for b in bookings]
    return _csv_response("bookings.csv", rows,
                         ["created_at", "name", "phone", "date", "time", "service", "amount", "status", "payment"])


@router.get("/my/{site_id}/orders/export.csv")
def export_orders(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    orders = list_orders(site_id)
    rows = [(o.get("created_at"), o.get("client_name"), o.get("client_phone"), o.get("items"), o.get("amount"), o.get("status")) for o in orders]
    return _csv_response("orders.csv", rows, ["created_at", "name", "phone", "items", "amount", "status"])


@router.get("/my/{site_id}/bookings.ics")
def bookings_ics(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    bookings = list_bookings(site_id)
    def _fmt(d, t):
        import re as _re
        t = _re.sub(r"[^\d:]", "", str(t or "00:00"))[:5]
        return f"{(d or '').replace('-', '')}T{t.replace(':', '')}00"
    def _ics_escape(value):
        # ICS text escaping: backslash, semicolons, commas, newlines
        return (str(value or "").replace("\\", "\\\\").replace(";", "\\;")
                .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AstroVakta//Bookings//EN"]
    for b in bookings:
        if (b.get("status") or "new") == "cancelled":
            continue
        lines += ["BEGIN:VEVENT",
                  f"UID:booking-{b.get('id')}@astrovakta",
                  f"DTSTART:{_fmt(b.get('date'), b.get('start_time'))}",
                  f"SUMMARY:{_ics_escape((b.get('service_name') or 'Consultation') + ' — ' + (b.get('client_name') or ''))}",
                  f"DESCRIPTION:{_ics_escape((b.get('client_phone') or '') + ' payment:' + str(b.get('payment_status', 'none')))}",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    from fastapi import Response as _Resp
    return _Resp("\r\n".join(lines), media_type="text/calendar",
                 headers={"Content-Disposition": 'attachment; filename="bookings.ics"'})


@router.post("/admin/visitor-google-auth")
def set_visitor_google_auth(body: dict, user: dict = Depends(require_admin)):
    """Superadmin: enable/disable Google sign-in for visitors of a site
    (by slug or site id). body: {"slug": "..."} or {"site_id": 6}, {"enabled": true}"""
    slug = body.get("slug")
    site_id = body.get("site_id")
    if not site_id and slug:
        site = get_site_by_slug(slug)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        site_id = site["id"]
    if not site_id:
        raise HTTPException(status_code=400, detail="slug or site_id required")
    site = get_site_by_id(site_id)
    settings = dict(site.get("settings") or {})
    settings["visitorGoogleAuth"] = bool(body.get("enabled"))
    from ..tenants import update_site
    update_site(site_id, {"settings": settings})
    return {"ok": True, "site": site["slug"], "visitorGoogleAuth": settings["visitorGoogleAuth"]}


# ─────────────── dropshipping master catalog (superadmin) ───────────────

class MasterCategoryBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    slug: Optional[str] = Field(None, max_length=80)
    sort_order: Optional[int] = 0


class MasterProductBody(BaseModel):
    category_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=2000)
    image: Optional[str] = None
    images: Optional[list[str]] = None
    attributes: Optional[list[dict]] = None
    mrp: int = Field(0, ge=0)
    margin: int = Field(0, ge=0)
    active: Optional[bool] = None


def _admin(user):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/admin/master/categories")
def admin_master_categories(user: dict = Depends(get_current_user)):
    _admin(user)
    return {"categories": list_master_categories()}


@router.post("/admin/master/categories")
def admin_create_master_category(body: MasterCategoryBody, user: dict = Depends(get_current_user)):
    _admin(user)
    slug = (body.slug or body.name).lower().strip().replace(" ", "-")
    import re as _re
    slug = _re.sub(r"[^a-z0-9-]", "", slug)
    return create_master_category(body.name, slug, body.sort_order or 0)


@router.put("/admin/master/categories/{cid}")
def admin_update_master_category(cid: int, body: MasterCategoryBody, user: dict = Depends(get_current_user)):
    _admin(user)
    update_master_category(cid, {"name": body.name, "sort_order": body.sort_order})
    return {"ok": True}


@router.delete("/admin/master/categories/{cid}")
def admin_delete_master_category(cid: int, user: dict = Depends(get_current_user)):
    _admin(user)
    delete_master_category(cid)
    return {"ok": True}


@router.get("/admin/master/products")
def admin_master_products(user: dict = Depends(get_current_user)):
    _admin(user)
    return {"products": list_master_products()}


@router.post("/admin/master/products")
def admin_create_master_product(body: MasterProductBody, user: dict = Depends(get_current_user)):
    _admin(user)
    if body.margin > body.mrp:
        raise HTTPException(status_code=400, detail="Margin cannot exceed MRP")
    data = body.model_dump()
    if data.get("images"):
        import json as _json
        data["images"] = _json.dumps(data["images"][:8])
    if data.get("attributes"):
        import json as _json2
        data["attributes"] = [
            {"name": str(a.get("name", ""))[:60], "value": str(a.get("value", ""))[:200]}
            for a in data["attributes"] if a.get("name") and a.get("value") is not None
        ][:20]
    return create_master_product(data)


@router.put("/admin/master/products/{mid}")
def admin_update_master_product(mid: int, body: MasterProductBody, user: dict = Depends(get_current_user)):
    _admin(user)
    if body.margin > body.mrp:
        raise HTTPException(status_code=400, detail="Margin cannot exceed MRP")
    data = body.model_dump()
    if data.get("images"):
        import json as _json
        data["images"] = _json.dumps(data["images"][:8])
    if data.get("attributes"):
        import json as _json2
        data["attributes"] = [
            {"name": str(a.get("name", ""))[:60], "value": str(a.get("value", ""))[:200]}
            for a in data["attributes"] if a.get("name") and a.get("value") is not None
        ][:20]
    update_master_product(mid, data)
    return get_master_product(mid)


@router.delete("/admin/master/products/{mid}")
def admin_delete_master_product(mid: int, user: dict = Depends(get_current_user)):
    _admin(user)
    delete_master_product(mid)
    return {"ok": True}


# ─────────────── tenant catalog import ───────────────

class ImportBody(BaseModel):
    price: Optional[int] = Field(None, ge=0)


@router.get("/my/{site_id}/catalog")
def my_catalog(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    mine = {p.get("master_product_id"): p for p in list_products(site_id) if p.get("master_product_id")}
    products = []
    for mp in list_master_products(active_only=True):
        mine_p = mine.get(mp["id"])
        products.append({
            "id": mp["id"], "name": mp["name"], "description": mp["description"], "image": mp["image"],
            "category": mp.get("category_name"), "mrp": mp["mrp"], "margin": mp["margin"],
            "cost": max(0, mp["mrp"] - mp["margin"]),
            "imported": bool(mine_p), "site_product_id": mine_p["id"] if mine_p else None,
            "current_price": mine_p["price"] if mine_p else None,
        })
    return {"categories": list_master_categories(), "products": products}


@router.post("/my/{site_id}/catalog/{master_id}/import")
def import_catalog_product(site_id: int, master_id: int, body: ImportBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    mp = get_master_product(master_id)
    if not mp or not mp.get("active", True):
        raise HTTPException(status_code=404, detail="Master product not found")
    # attach the category name for the import copy
    if mp.get("category_id"):
        cat = next((c for c in list_master_categories() if c["id"] == mp["category_id"]), None)
        if cat:
            mp["category_name"] = cat["name"]
    cost = max(0, mp.get("mrp", 0) - mp.get("margin", 0))
    price = body.price if body.price is not None else mp.get("mrp", 0)
    if price < cost:
        raise HTTPException(status_code=400,
                            detail=f"Price must be at least your cost ₹{cost} (MRP ₹{mp['mrp']} − margin ₹{mp['margin']})")
    already = [p for p in list_products(site_id) if p.get("master_product_id") == master_id]
    if already:
        raise HTTPException(status_code=409, detail="Already imported — edit its price in Products")
    prod = import_master_product(site_id, mp, price)
    return {"product": prod, "cost": cost}


# ─────────────── external store integrations (Shopify / WooCommerce) ───────────────
# One-click flow: begin → provider approval screen → callback (creates the
# connection automatically). The legacy paste-credentials path remains as a
# fallback for stores that cannot use the one-click flow (e.g. a Woo store on
# plain http, where WordPress refuses to hand out application passwords).

class ConnectStoreBody(BaseModel):
    provider: str = Field(..., pattern="^(shopify|woocommerce)$")
    shop_domain: str = Field(..., max_length=200)
    api_key: Optional[str] = Field(None, max_length=200)
    api_secret: Optional[str] = Field(None, max_length=200)
    access_token: Optional[str] = Field(None, max_length=300)


def _clean_shop_domain(domain: str) -> str:
    from ..store_integrations import _normalize_shop_domain
    d = _normalize_shop_domain(domain)
    if not d or "." not in d:
        raise HTTPException(status_code=400, detail="Enter your store's domain, e.g. mystore.myshopify.com or mystore.com")
    return d


@router.get("/my/{site_id}/integrations")
def my_integrations(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    conns = list_store_connections(site_id)
    for c in conns:
        c["has_credentials"] = bool(c.get("access_token") or (c.get("api_key") and c.get("api_secret")))
        c.pop("api_key", None); c.pop("api_secret", None); c.pop("access_token", None)
    return {"integrations": conns}


@router.get("/my/{site_id}/integrations/providers")
def integration_providers(site_id: int, user: dict = Depends(get_current_user)):
    """Which one-click flows this deployment supports."""
    _require_owned_site(site_id, user)
    from ..store_integrations import shopify_oauth_configured, public_base_url
    return {
        "shopify_one_click": shopify_oauth_configured(),
        "woocommerce_one_click": True,
        "callback_base": public_base_url(),
    }


class BeginConnectBody(BaseModel):
    provider: str = Field(..., pattern="^(shopify|woocommerce)$")
    shop_domain: str = Field(..., max_length=200)


@router.post("/my/{site_id}/integrations/begin")
def begin_store_connect(site_id: int, body: BeginConnectBody, user: dict = Depends(get_current_user)):
    """Create a single-use handshake state and return the provider's approval
    URL — the tenant clicks once, approves on the provider's own screen, and
    the callback wires everything up."""
    _require_owned_site(site_id, user)
    shop = _clean_shop_domain(body.shop_domain)
    from ..store_integrations import (
        shopify_oauth_configured, shopify_authorize_url, woo_authorize_url, public_base_url,
    )
    if body.provider == "shopify" and not shopify_oauth_configured():
        raise HTTPException(status_code=400, detail="One-click Shopify connect is not configured on this deployment yet — use the manual token option instead")
    base = public_base_url()
    if body.provider == "shopify":
        redirect_uri = f"{base}/sites/integrations/callback/shopify"
        state = create_oauth_state(site_id, body.provider, shop)
        url = shopify_authorize_url(shop, state, redirect_uri)
    else:
        # WordPress does not forward a state param through its approval
        # screen — embed it in the success/reject URL instead.
        state = create_oauth_state(site_id, body.provider, shop)
        redirect_uri = f"{base}/sites/integrations/callback/woocommerce?state={state}"
        url = woo_authorize_url(shop, redirect_uri)
    return {"authorize_url": url, "state": state, "redirect_uri": redirect_uri}


def _frontend_result_url(status: str, message: str) -> str:
    from urllib.parse import urlencode
    base = os.getenv("FRONTEND_URL", "https://dev.astrovakta.com").strip().rstrip("/") or "https://dev.astrovakta.com"
    return f"{base}/mysite/store?{urlencode({'status': status, 'message': message})}"


def _shopify_redirect_uri() -> str:
    from ..store_integrations import public_base_url
    return f"{public_base_url()}/sites/integrations/callback/shopify"


@router.get("/integrations/callback/shopify")
def shopify_callback(code: str = None, state: str = None, shop: str = None, hmac_sig: str = None, host: str = None, timestamp: str = None):
    """Shopify redirects here after the tenant approves. Public by design —
    the single-use state (created under the owner's JWT) is the auth. The
    store domain always comes from the stored state, never from the query
    string, so a tampered link can't re-point the OAuth exchange."""
    from ..store_integrations import shopify_exchange_code, test_connection
    hs = get_oauth_state(state) if state else None
    if not hs:
        return RedirectResponse(_frontend_result_url("error", "This connect link has expired — please try connecting again"), status_code=302)
    delete_oauth_state(state)
    shop_domain = _clean_shop_domain(hs["shop_domain"])
    result = shopify_exchange_code(shop_domain, code or "", _shopify_redirect_uri())
    if not result.get("ok"):
        return RedirectResponse(_frontend_result_url("error", f"Shopify did not grant access: {str(result.get('error', ''))[:150]}"), status_code=302)
    conn = create_store_connection(hs["site_id"], {
        "provider": "shopify", "shop_domain": shop_domain,
        "access_token": result["access_token"],
    })
    check = test_connection(conn)
    if not check.get("ok"):
        delete_store_connection(hs["site_id"], conn["id"])
        return RedirectResponse(_frontend_result_url("error", "The token was rejected by your Shopify store — please try connecting again"), status_code=302)
    return RedirectResponse(_frontend_result_url("ok", f"Shopify store {shop_domain} connected — push products and pull orders from the Integrations tab"), status_code=302)


@router.get("/integrations/callback/woocommerce")
def woocommerce_callback(request: Request, state: str = None, user_login: str = None, password: str = None, site_url: str = None):
    """WordPress core authorize_application.php returns the tenant with a
    fresh Application Password (user_login + password) appended to the
    success_url (which carries our state). Store it as Basic-auth
    credentials, verify, drop the state."""
    hs = get_oauth_state(state) if state else None
    if not hs:
        return RedirectResponse(_frontend_result_url("error", "This connect link has expired — please try connecting again"), status_code=302)
    delete_oauth_state(state)
    if not (user_login and password):
        # WordPress bounces to reject_url (the user cancelled or the store
        # refused). No connection is created.
        return RedirectResponse(_frontend_result_url("error", "Approval was not completed — the store owner must click Approve"), status_code=302)
    shop_domain = _clean_shop_domain(hs["shop_domain"])
    conn = create_store_connection(hs["site_id"], {
        "provider": "woocommerce", "shop_domain": shop_domain,
        "api_key": user_login, "api_secret": password,
    })
    from ..store_integrations import test_connection
    check = test_connection(conn)
    if not check.get("ok"):
        err = str(check.get("error", "") or "unknown error")
        status_code_ = str(check.get("status", ""))
        hint = "WordPress only hands out application passwords to HTTPS callbacks — is your store on plain http? Use the manual key option." if status_code_ in ("401", "404") or "https" in err.lower() else err
        delete_store_connection(hs["site_id"], conn["id"])
        return RedirectResponse(_frontend_result_url("error", f"Could not reach the store: {hint[:180]}"), status_code=302)
    return RedirectResponse(_frontend_result_url("ok", f"WooCommerce store {shop_domain} connected — push products and pull orders from the Integrations tab"), status_code=302)


@router.post("/my/{site_id}/integrations")
def connect_store(site_id: int, body: ConnectStoreBody, user: dict = Depends(get_current_user)):
    """Manual fallback: paste a Shopify token / Woo consumer keys directly."""
    _require_owned_site(site_id, user)
    if body.provider == "woocommerce" and not (body.api_key and body.api_secret):
        raise HTTPException(status_code=400, detail="WooCommerce needs the consumer key and secret")
    if body.provider == "shopify" and not body.access_token:
        raise HTTPException(status_code=400, detail="Shopify needs the Admin API access token")
    conn = create_store_connection(site_id, {"provider": body.provider, "shop_domain": _clean_shop_domain(body.shop_domain),
                                             "api_key": body.api_key, "api_secret": body.api_secret,
                                             "access_token": body.access_token})
    from ..store_integrations import test_connection
    result = test_connection(conn)
    if not result.get("ok"):
        delete_store_connection(site_id, conn["id"])
        raise HTTPException(status_code=400, detail=f"Could not reach the store: {result.get('error', '')[:150]}")
    return {"ok": True, "integration": {"id": conn["id"], "provider": conn["provider"], "shop_domain": conn["shop_domain"]}}


@router.delete("/my/{site_id}/integrations/{cid}")
def disconnect_store(site_id: int, cid: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    delete_store_connection(site_id, cid)
    return {"ok": True}


class PushBody(BaseModel):
    product_ids: list[int] = Field(..., min_length=1)


@router.post("/my/{site_id}/integrations/{cid}/push")
def push_to_store(site_id: int, cid: int, body: PushBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    conn = get_store_connection(site_id, cid)
    if not conn:
        raise HTTPException(status_code=404, detail="Integration not found")
    from ..store_integrations import push_product, test_connection
    check = test_connection(conn)
    if not check.get("ok"):
        raise HTTPException(status_code=400, detail="Store unreachable — check the credentials")
    pmap = get_integration_product_map(cid)
    results = []
    for pid in body.product_ids:
        prod = next((p for p in list_products(site_id) if p["id"] == pid), None)
        if not prod:
            results.append({"product_id": pid, "ok": False, "error": "product not found"}); continue
        r = push_product(conn, prod)
        if r.get("ok"):
            record_integration_product(cid, pid, r["external_id"])
        results.append({"product_id": pid, "name": prod["name"], **r})
    return {"results": results}


@router.post("/my/{site_id}/integrations/{cid}/pull-orders")
def pull_store_orders(site_id: int, cid: int, user: dict = Depends(get_current_user)):
    """Shopify orders are pulled (no webhook secret needed). New orders are
    imported into the normal Orders tab."""
    _require_owned_site(site_id, user)
    conn = get_store_connection(site_id, cid)
    if not conn or conn["provider"] != "shopify":
        raise HTTPException(status_code=404, detail="Shopify integration not found")
    from ..store_integrations import pull_shopify_orders
    pulled = pull_shopify_orders(conn)
    imported, skipped = 0, 0
    for o in pulled:
        if o.get("error"):
            continue
        existing = [x for x in [get_order(site_id, i["id"]) for i in []] if x]
        from ..tenants import list_orders
        ref_note = o.get("external_ref")
        if any(ref_note in (x.get("notes") or "") for x in list_orders(site_id, limit=100)):
            skipped += 1; continue
        create_order(site_id, o)
        imported += 1
    return {"imported": imported, "skipped": skipped}


# ─────────────── one-click store connect (OAuth / activation key) ───────────────

import secrets as _secrets


class WooActivateBody(BaseModel):
    activation_key: str = Field(..., min_length=8)


@router.post("/my/{site_id}/integrations/woocommerce/activate")
def woo_activate(site_id: int, body: WooActivateBody, user: dict = Depends(get_current_user)):
    """One-click WooCommerce connect (activation-key flow): the astrologer
    installs our small WP plugin (or pastes a snippet in functions.php) which
    registers the consumer keys against this activation key — no manual
    key/secret copying. Returns the snippet to paste."""
    _require_owned_site(site_id, user)
    key = body.activation_key.strip()
    from ..database import get_db
    row = get_db().execute(_tc("SELECT id FROM store_connections WHERE site_id = ? AND api_key = ?"),
                           (site_id, key)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Activation key not recognised — copy it again from the dashboard")
    # the plugin already pushed the consumer key/secret keyed by this activation key
    conn_id = row[0] if not isinstance(row, dict) else row["id"]
    conn = get_store_connection(site_id, conn_id)
    from ..store_integrations import test_connection
    ok = test_connection(conn).get("ok")
    return {"ok": bool(ok), "integration": {"id": conn_id, "shop_domain": conn["shop_domain"]}}


@router.get("/my/{site_id}/integrations/woocommerce/start")
def woo_start(site_id: int, user: dict = Depends(get_current_user)):
    """Begin one-click WooCommerce connect: returns the activation key and the
    ready-to-install WP plugin the merchant clicks through."""
    _require_owned_site(site_id, user)
    key = "avk_" + _secrets.token_urlsafe(18)
    from ..database import get_db
    from ..tenants import _convert as _tc
    db = get_db()
    db.execute(_tc("INSERT INTO store_connections (site_id, provider, shop_domain, api_key) VALUES (?, 'woocommerce', 'pending', ?)"),
               (site_id, key))
    db.commit()
    plugin_url = f"{_plugin_base()}/wp-content/plugins/astrovakta-connect/astrovakta-connect.php"
    return {"activation_key": key, "plugin_instructions": [
        "1. Download the AstroVakta Connect plugin from the link below and install it in WordPress (Plugins → Add New → Upload).",
        "2. Open the plugin settings and paste your activation key.",
        "3. Click Connect — the plugin creates the API keys and links your store automatically. Done.",
    ], "plugin_download": plugin_url}


@router.post("/integrations/woocommerce/claim")
async def woo_claim(request: Request):
    """Called by the WP plugin after it creates the keys: registers them
    against the pending connection for this activation key."""
    import json as _json
    body = await request.json()
    key = (body.get("activation_key") or "").strip()
    shop_domain = (body.get("shop_domain") or "").strip()
    api_key = (body.get("api_key") or "").strip()
    api_secret = (body.get("api_secret") or "").strip()
    if not (key and shop_domain and api_key and api_secret):
        raise HTTPException(status_code=400, detail="activation_key, shop_domain, api_key, api_secret required")
    from ..database import get_db
    db = get_db()
    from ..tenants import _convert as _tc
    row = db.execute(_tc("SELECT id, site_id FROM store_connections WHERE api_key = ? AND shop_domain = 'pending'"), (key,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Unknown activation key")
    conn_id, site_id = (row[0], row[1]) if not isinstance(row, dict) else (row["id"], row["site_id"])
    db.execute(_tc("UPDATE store_connections SET shop_domain = ?, api_key = ?, api_secret = ? WHERE id = ?"),
               (shop_domain, api_key, api_secret, conn_id))
    db.commit()
    return {"ok": True}


def _plugin_base():
    import os as _os
    return _os.getenv("PUBLIC_WEB_BASE", _os.getenv("FRONTEND_URL", "https://astrovakta.com"))


# ─────────────── credits & analytics ───────────────

CREDIT_PACKS = [
    {"id": "starter", "credits": 1000, "price": 499},
    {"id": "growth", "credits": 5000, "price": 1999},
    {"id": "pro", "credits": 20000, "price": 6999},
]


@router.get("/my/{site_id}/credits")
def my_credits(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    from ..tenants import ensure_starter_credits
    ensure_starter_credits(site_id)
    return {
        "balance": site_credit_balance(site_id),
        "history": site_credit_history(site_id),
        "packs": CREDIT_PACKS,
        "costs": {
            "kundli": 2, "kundli_basic": 1, "matching": 3, "dosha": 2,
            "horoscope": 1, "panchang": 1, "ai_content": 5, "media_render": 2,
        },
    }


class RechargeBody(BaseModel):
    pack_id: str


@router.post("/my/{site_id}/credits/recharge")
def recharge_credits(site_id: int, body: RechargeBody, user: dict = Depends(get_current_user)):
    """Create a Dodo checkout for a credit pack; webhook credits the balance."""
    _require_owned_site(site_id, user)
    pack = next((p for p in CREDIT_PACKS if p["id"] == body.pack_id), None)
    if not pack:
        raise HTTPException(status_code=400, detail="Unknown pack")
    if not os.getenv("DODO_API_KEY"):
        # no gateway configured — credit instantly in dev (flagged in reason)
        bal = adjust_site_credits(site_id, pack["credits"], f"recharge:{pack['id']}:dev-instant")
        return {"ok": True, "balance": bal, "devInstant": True}
    import httpx
    from ..tenants import get_site_by_id
    site = get_site_by_id(site_id)
    r = httpx.post("https://live.dodopayments.com/payments",
        headers={"Authorization": f"Bearer {os.getenv('DODO_API_KEY')}"},
        json={
            "amount": pack["price"] * 100,
            "currency": "INR",
            "product_name": f"AstroVakta credits — {pack['credits']}",
            "customer_name": user.get("name") or "Astrologer",
            "customer_email": user["email"],
            "metadata": {"site_id": site_id, "pack_id": pack["id"], "credits": pack["credits"]},
        }, timeout=20)
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Payment gateway error")
    return {"checkout_url": r.json().get("payment_link") or r.json().get("checkout_url"), "pack": pack}


@router.get("/my/{site_id}/analytics")
def my_analytics(site_id: int, days: int = 30, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return site_analytics(site_id, days)
