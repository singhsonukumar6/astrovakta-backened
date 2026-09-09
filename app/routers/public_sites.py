"""Public endpoints for tenant websites: site resolution + booking flow.

These are unauthenticated (the visitor is the astrologer's client). Sites are
resolved by subdomain slug or custom domain; only published sites are visible.
"""
import json
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from ..tenants import (
    get_site_by_slug, get_site_by_domain, public_site_bundle,
    list_availability, get_service, list_bookings, create_booking,
    create_lead,
)

router = APIRouter()


def _resolve_site(slug: str = None, domain: str = None):
    """Resolve a site from ?site=<slug> or ?domain=<custom-domain>."""
    if domain:
        site = get_site_by_domain(domain)
        if site:
            return site
        raise HTTPException(status_code=404, detail="No site found for this domain")
    if slug:
        site = get_site_by_slug(slug, published_only=True)
        if site:
            return site
        raise HTTPException(status_code=404, detail="Site not found or not published")
    raise HTTPException(status_code=400, detail="Provide ?site=<slug> or ?domain=<domain>")


@router.get("/site")
def get_public_site(slug: str = None, domain: str = None):
    """Full render bundle: site meta + theme + published pages + services."""
    site = _resolve_site(slug, domain)
    return public_site_bundle(site)


@router.get("/site/availability")
def get_public_availability(slug: str = None, domain: str = None, date_from: str = None, weeks: int = Query(2, ge=1, le=8)):
    """Availability window for the booking widget: weekly hours + booked slots."""
    site = _resolve_site(slug, domain)
    today = date.fromisoformat(date_from) if date_from else date.today()
    days = []
    # weekday(): Monday=0 … Sunday=6 — matches site_availability.weekday
    for i in range(weeks * 7):
        d = today + timedelta(days=i)
        days.append({"date": d.isoformat(), "weekday": d.weekday()})
    rules = list_availability(site["id"])
    booked = list_bookings(site["id"], date_from=today.isoformat(),
                           date_to=(today + timedelta(days=weeks * 7)).isoformat(),
                           status="confirmed")
    return {
        "days": days,
        "weekly_hours": rules,
        "booked": [{"date": b["date"], "start_time": b["start_time"], "end_time": b["end_time"]} for b in booked],
    }


class PublicBookingBody(BaseModel):
    service_id: Optional[int] = None
    client_name: str = Field(..., min_length=1, max_length=120)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")

    class Config:
        extra = "forbid"


@router.post("/site/book")
def public_book(body: PublicBookingBody, slug: str = None, domain: str = None):
    """Client books a slot on a tenant site. Slot is validated against the
    astrologer's weekly hours and existing bookings (no double-booking)."""
    site = _resolve_site(slug, domain)
    site_id = site["id"]

    # service duration drives the end time
    duration = 30
    amount = 0
    currency = "INR"
    if body.service_id:
        svc = get_service(site_id, body.service_id)
        if not svc or not svc["is_active"]:
            raise HTTPException(status_code=404, detail="Selected service is not available")
        duration = svc["duration_minutes"] or 30
        amount = svc["price"] or 0
        currency = svc["currency"] or "INR"

    # validate date/weekday against weekly hours
    rules = list_availability(site_id)
    try:
        d = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    if d < date.today():
        raise HTTPException(status_code=400, detail="Cannot book a date in the past")
    day_rules = [r for r in rules if r["weekday"] == d.weekday()]
    if not day_rules:
        raise HTTPException(status_code=400, detail="The astrologer is not available on this day")

    def to_min(t: str) -> int:
        h, m = t.split(":")[:2]
        return int(h) * 60 + int(m)

    start = to_min(body.start_time)
    end = start + duration
    ok = any(to_min(r["start_time"]) <= start and end <= to_min(r["end_time"]) for r in day_rules)
    if not ok:
        raise HTTPException(status_code=400, detail="This time is outside the astrologer's working hours")

    # no double-booking: overlap check against confirmed bookings
    existing = list_bookings(site_id, date_from=body.date, date_to=body.date, status="confirmed")
    for b in existing:
        if start < to_min(b["end_time"]) and to_min(b["start_time"]) < end:
            raise HTTPException(status_code=409, detail="That slot was just booked — please pick another time")

    booking = create_booking(site_id, {
        "service_id": body.service_id,
        "client_name": body.client_name,
        "client_phone": body.client_phone,
        "client_email": body.client_email,
        "notes": body.notes,
        "date": body.date,
        "start_time": body.start_time,
        "end_time": f"{(start + duration) // 60:02d}:{(start + duration) % 60:02d}",
        "amount": amount,
        "currency": currency,
        "status": "confirmed",
    })
    # WhatsApp alert / payment hook point: integrations attach here later.
    return {"booking": {k: v for k, v in booking.items() if k != "id" and k != "site_id"},
            "message": "Your appointment is confirmed. The astrologer has been notified."}


# ─────────────── free tools (lead magnets on tenant sites) ───────────────

_GEMSTONE_BY_LORD = {
    "Sun": "Ruby", "Moon": "Pearl", "Mars": "Red Coral", "Mercury": "Emerald",
    "Jupiter": "Yellow Sapphire", "Venus": "Diamond", "Saturn": "Blue Sapphire",
    "Rahu": "Hessonite", "Ketu": "Cat's Eye",
}

_DEFAULT_PLACE = {"lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata", "label": "Delhi"}


def _sign_lord_of(sign: str) -> str:
    from ..utils import SIGN_LORDS
    return SIGN_LORDS.get(sign, "")


class KundliToolBody(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    tz: Optional[str] = Field(None, max_length=60)
    place: Optional[str] = Field(None, max_length=120)

    class Config:
        extra = "forbid"


@router.post("/site/tools/kundli")
def tenant_kundli_tool(body: KundliToolBody, slug: str = None, domain: str = None):
    """Free kundli snapshot for a tenant site's visitors: ascendant, moon/sun
    sign, nakshatra and planetary positions — computed on the platform engine.
    Contact details, when given, become a lead for the astrologer."""
    site = _resolve_site(slug, domain)

    try:
        d = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    if not (1900 <= d.year <= 2100):
        raise HTTPException(status_code=400, detail="Year must be between 1900 and 2100")

    lat = body.lat if body.lat is not None else _DEFAULT_PLACE["lat"]
    lon = body.lon if body.lon is not None else _DEFAULT_PLACE["lon"]
    tz = body.tz or _DEFAULT_PLACE["tz"]

    # Imported lazily so the router loads fast and stays decoupled from the
    # ephemeris module in tests.
    from ..utils import to_julian, calc_planets, calc_houses
    try:
        jd = to_julian(body.date, body.time, tz)
        planets = calc_planets(jd, None, "mean")
        houses = calc_houses(jd, lat, lon, planets, "W")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not compute the chart — check the birth details")

    asc = houses["ascendant"]
    moon = next((p for p in planets if p["name"] == "Moon"), None)
    sun = next((p for p in planets if p["name"] == "Sun"), None)
    asc_lord = _sign_lord_of(asc["sign"])

    lead_created = False
    if body.phone or body.email:
        create_lead(site["id"], {
            "tool": "kundli",
            "name": body.name,
            "phone": body.phone,
            "email": body.email,
            "details": {
                "date": body.date, "time": body.time,
                "place": body.place or _DEFAULT_PLACE["label"],
                "ascendant": asc["sign"], "moonSign": moon["sign"] if moon else None,
            },
        })
        lead_created = True

    return {
        "ascendant": {"sign": asc["sign"], "lord": asc_lord, "nakshatra": asc["nakshatra"]},
        "moonSign": moon["sign"] if moon else None,
        "moonNakshatra": moon["nakshatra"] if moon else None,
        "sunSign": sun["sign"] if sun else None,
        "gemstone": {"forLord": asc_lord, "stone": _GEMSTONE_BY_LORD.get(asc_lord)} if asc_lord else None,
        "planets": [
            {"name": p["name"], "sign": p["sign"], "nakshatra": p["nakshatra"], "house": p["house"],
             "retrograde": p["isRetrograde"]}
            for p in planets
        ],
        "leadCreated": lead_created,
        "astrologer": site["name"],
    }


@router.get("/site/tools/panchang")
def tenant_panchang_tool(slug: str = None, domain: str = None, date_str: str = None):
    """Today's panchang for a tenant site's daily widget."""
    site = _resolve_site(slug, domain)
    from ..utils import compute_panchang
    d = date_str or date.today().isoformat()
    try:
        date.fromisoformat(d)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    p = compute_panchang(d, "12:00", _DEFAULT_PLACE["tz"], _DEFAULT_PLACE["lat"], _DEFAULT_PLACE["lon"])
    return {"date": d, "panchang": p, "astrologer": site["name"]}
