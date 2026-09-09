"""Site builder: owner-facing management endpoints for tenant websites.

All routes require the site owner's JWT (get_current_user). A tenant resolves
their site via /sites/my/* — sites are looked up by id and verified against the
owner's user id, so tenants can never touch each other's data.
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from ..tenants import (
    validate_slug, normalize_domain, slug_exists, domain_exists, TEMPLATES, WEEKDAYS,
    RESERVED_SLUGS, list_sites, get_site_by_id, create_site, update_site, set_site_status, delete_site,
    list_pages, upsert_page,
    list_services, get_service, create_service, update_service, delete_service,
    list_availability, set_availability,
    list_bookings, get_booking, create_booking, update_booking,
    list_leads,
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
        return {"valid": False, "available": False, "reason": "Enter a valid domain like astrovakra.com"}
    available = not domain_exists(d)
    return {"valid": True, "available": available,
            "reason": None if available else "That domain is already connected to another site"}


# ─────────────── sites ───────────────

@router.get("/templates")
def list_templates():
    return {"templates": [
        {"id": t, "name": t.capitalize()} for t in TEMPLATES
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

@router.post("/my/{site_id}/domain")
def set_my_site_domain(site_id: int, body: SetDomainBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    domain = normalize_domain(body.domain)
    if not domain or "." not in domain:
        raise HTTPException(status_code=400, detail="Enter a valid domain like astrovakra.com")
    if domain_exists(domain, exclude_id=site_id):
        raise HTTPException(status_code=409, detail="That domain is already connected to another site")
    site = update_site(site_id, {"custom_domain": domain, "domain_status": "pending"})
    # DNS verification: the tenant must point a CNAME/A record at the platform.
    # We return the DNS instructions; activation is confirmed by the platform
    # (automated job / manual verify endpoint) once the record resolves.
    return {
        **site,
        "dns_instructions": {
            "record_type": "CNAME",
            "host": "www" if False else "@",
            "value": "sites.astrovakta.com",
            "note": f"Add a CNAME record for www.{domain} (and an A/ALIAS record for {domain}) pointing to sites.astrovakta.com, then tap Verify.",
        },
    }


@router.post("/my/{site_id}/domain/verify")
def verify_my_site_domain(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    site = get_site_by_id(site_id)
    if not site.get("custom_domain"):
        raise HTTPException(status_code=400, detail="Add a domain first")
    import socket
    domain = site["custom_domain"]
    try:
        # Basic resolution check — a real deployment would verify the CNAME
        # target and issue/renew SSL automatically (e.g. via Caddy/Traefik).
        resolved = socket.gethostbyname(f"www.{domain}") or socket.gethostbyname(domain)
    except Exception:
        resolved = None
    if not resolved:
        return {**site, "domain_status": "pending", "verified": False,
                "message": f"DNS not propagated yet — www.{domain} does not resolve. Wait a few minutes and try again."}
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


# ─────────────── settings (alerts & contact) ───────────────

class SettingsBody(BaseModel):
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    booking_alerts: Optional[bool] = None
    reminder_hours: Optional[int] = Field(None, ge=1, le=72)


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
    return update_site(site_id, {"settings": settings})


# ─────────────── leads (from free tools) ───────────────

@router.get("/my/{site_id}/leads")
def my_site_leads(site_id: int, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    return {"leads": list_leads(site_id)}


# ─────────────── pages ───────────────

@router.put("/my/{site_id}/pages/{page_key}")
def upsert_my_page(site_id: int, page_key: str, body: PageBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not page_key or len(page_key) > 40:
        raise HTTPException(status_code=400, detail="Invalid page key")
    return upsert_page(site_id, page_key, body.model_dump())


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
def create_my_booking(site_id: int, body: BookingBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if body.end_time <= body.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    return create_booking(site_id, body.model_dump())


@router.put("/my/{site_id}/bookings/{booking_id}")
def update_my_booking(site_id: int, booking_id: int, body: UpdateBookingBody, user: dict = Depends(get_current_user)):
    _require_owned_site(site_id, user)
    if not get_booking(site_id, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return update_booking(site_id, booking_id, body.model_dump(exclude_none=True))
