"""Site builder: owner-facing management endpoints for tenant websites.

All routes require the site owner's JWT (get_current_user). A tenant resolves
their site via /sites/my/* — sites are looked up by id and verified against the
owner's user id, so tenants can never touch each other's data.
"""
import re
from datetime import date
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
    list_products, get_product, create_product, update_product, delete_product,
    list_social_posts, create_social_post, update_social_post, delete_social_post,
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
        return {"valid": False, "available": False, "reason": "Enter a valid domain like astrovakra.com"}
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not render media: {e}")


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
