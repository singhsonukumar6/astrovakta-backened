"""Public endpoints for tenant websites: site resolution, booking flow and store.

These are unauthenticated (the visitor is the astrologer's client). Sites are
resolved by subdomain slug or custom domain; only published sites are visible.
"""
import json
from datetime import date, timedelta
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List

from ..email_service import send_booking_emails
from ..tenants import (
    get_site_by_slug, get_site_by_domain, public_site_bundle,
    list_availability, get_service, list_bookings, create_booking,
    get_booking, update_booking,
    create_lead, list_products, get_product, create_order,
    get_order, update_order, list_orders, adjust_product_stock,
    charge_site_credits, record_site_event,
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
    client_name: Optional[str] = Field(None, max_length=120)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")

    class Config:
        extra = "forbid"


@router.post("/site/book")
def public_book(body: PublicBookingBody, request: Request, background_tasks: BackgroundTasks,
                slug: str = None, domain: str = None):
    """A signed-in visitor books a slot on a tenant site. Booking requires a
    tenant account (sign-in/sign-up) so the client can track the consultation.
    Slot is validated against the astrologer's weekly hours and existing
    bookings (no double-booking)."""
    site = _resolve_site(slug, domain)
    site_id = site["id"]
    user = _require_site_visitor(request, site_id)

    # service duration drives the end time
    duration = 30
    amount = 0
    currency = "INR"
    svc = None
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
        "tenant_user_id": user["id"],
        "client_name": (body.client_name or "").strip() or user.get("name") or user["email"].split("@")[0],
        "client_phone": (body.client_phone or "").strip() or user.get("phone"),
        "client_email": (body.client_email or "").strip() or user.get("email"),
        "notes": body.notes,
        "date": body.date,
        "start_time": body.start_time,
        "end_time": f"{(start + duration) // 60:02d}:{(start + duration) % 60:02d}",
        "amount": amount,
        "currency": currency,
        "status": "confirmed",
    })
    # White-label confirmation emails (client + astrologer), sent after the
    # response so the booking stays instant; failures never block a booking.
    background_tasks.add_task(send_booking_emails, site, booking, svc)
    return {"booking": {k: v for k, v in booking.items() if k not in ("id", "site_id", "tenant_user_id")},
            "message": "Your appointment is confirmed. The astrologer has been notified."}


# ─────────────── store (public storefront) ───────────────

class PublicOrderItem(BaseModel):
    product_id: int
    qty: int = Field(1, ge=1, le=99)

    class Config:
        extra = "forbid"


class PublicOrderBody(BaseModel):
    client_name: Optional[str] = Field(None, max_length=120)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    items: List[PublicOrderItem] = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        extra = "forbid"


@router.post("/site/order")
def public_place_order(body: PublicOrderBody, request: Request, slug: str = None, domain: str = None):
    """A signed-in visitor places an order from the astrologer's store. Orders
    belong to the visitor's account so they can track them under My Account.
    Prices are taken from the database (never from the client), and stock is
    checked."""
    site = _resolve_site(slug, domain)
    user = _require_site_visitor(request, site["id"])
    items_out = []
    total = 0
    for it in body.items:
        p = get_product(site["id"], it.product_id)
        if not p or not p["is_active"]:
            raise HTTPException(status_code=404, detail="A product in your cart is no longer available")
        if p["stock"] is not None and p["stock"] >= 0 and p["stock"] < it.qty:
            raise HTTPException(status_code=409, detail=f"Only {p['stock']} left of {p['name']}")
        total += (p["price"] or 0) * it.qty
        items_out.append({"product_id": p["id"], "name": p["name"], "price": p["price"], "qty": it.qty})
    order = create_order(site["id"], {
        "tenant_user_id": user["id"],
        "client_name": (body.client_name or "").strip() or user.get("name") or user["email"].split("@")[0],
        "client_phone": (body.client_phone or "").strip() or user.get("phone"),
        "client_email": (body.client_email or "").strip() or user.get("email"),
        "address": body.address,
        "items": items_out,
        "amount": total,
        "currency": "INR",
        "status": "new",
        "notes": body.notes,
    })
    # Reserve the ordered quantity right away; cancelling the order restores it.
    for it in items_out:
        if it["qty"] > 0:
            adjust_product_stock(site["id"], it["product_id"], -it["qty"])
    # Payment gateway / WhatsApp alert hook point.
    return {"order": {"id": order["id"], "amount": order["amount"], "currency": order["currency"],
                      "items": items_out},
            "message": f"Order placed! {site['name']} will contact you to confirm payment & delivery."}


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
    detail: bool = Field(False, description="Include houses, chart SVG, and Vimshottari dasha")
    chart_theme: Optional[str] = Field("light", pattern="^(light|dark)$")
    lang: Optional[str] = Field("en", max_length=10, description="Report language: en, hi, ta, te, kn, ml, bn, mr, gu, pa")

    class Config:
        extra = "forbid"


def _compute_chart(body) -> dict:
    """Shared planet/house computation for the tenant kundli tools."""
    from ..utils import to_julian, calc_planets, calc_houses
    lat = body.lat if body.lat is not None else _DEFAULT_PLACE["lat"]
    lon = body.lon if body.lon is not None else _DEFAULT_PLACE["lon"]
    tz = body.tz or _DEFAULT_PLACE["tz"]
    jd = to_julian(body.date, body.time, tz)
    planets = calc_planets(jd, None, "mean")
    houses = calc_houses(jd, lat, lon, planets, "W")
    return jd, lat, lon, tz, planets, houses


@router.post("/site/tools/kundli")
def tenant_kundli_tool(body: KundliToolBody, request: Request, slug: str = None, domain: str = None):
    """Free kundli for a tenant site's visitors. Basic mode returns a snapshot
    (ascendant, moon/sun sign, nakshatra, planets, gemstone); detail=true adds
    the full software view: houses, North-Indian chart SVG and Vimshottari
    dasha. Contact details, when given, become a lead for the astrologer."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    if not charge_site_credits(site["id"], "kundli" if body.detail else "kundli_basic"):
        raise HTTPException(status_code=402, detail="This site is out of credits — the astrologer needs to recharge")
    record_site_event(site["id"], "tool", "kundli")

    try:
        d = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    if not (1900 <= d.year <= 2100):
        raise HTTPException(status_code=400, detail="Year must be between 1900 and 2100")

    try:
        jd, lat, lon, tz, planets, houses = _compute_chart(body)
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
            "name": _strip_html(body.name),
            "phone": (body.phone or "").strip(),
            "email": (body.email or "").strip(),
            "details": {
                "date": body.date, "time": body.time,
                "place": body.place or _DEFAULT_PLACE["label"],
                "ascendant": asc["sign"], "moonSign": moon["sign"] if moon else None,
            },
        })
        lead_created = True

    resp = {
        "ascendant": {"sign": asc["sign"], "lord": asc_lord, "nakshatra": asc["nakshatra"],
                      "degreeDMS": None},
        "moonSign": moon["sign"] if moon else None,
        "moonNakshatra": moon["nakshatra"] if moon else None,
        "sunSign": sun["sign"] if sun else None,
        "gemstone": {"forLord": asc_lord, "stone": _GEMSTONE_BY_LORD.get(asc_lord)} if asc_lord else None,
        "planets": [
            {"name": p["name"], "sign": p["sign"], "nakshatra": p["nakshatra"], "house": p["house"],
             "degreeDMS": p["degreeDMS"], "retrograde": p["isRetrograde"], "combust": p["isCombust"]}
            for p in planets
        ],
        "leadCreated": lead_created,
        "astrologer": site["name"],
    }

    if body.detail:
        from ..routers.chart_svg import render_svg
        from ..main import parse_local_datetime, vimshottari_full
        try:
            svg = render_svg(560, 560, asc, planets, theme=body.chart_theme or "light",
                             include_outer=False, stack_threshold=2, lang="en")
        except Exception:
            svg = None
        dasha = None
        current_dasha = None
        try:
            birth_local = parse_local_datetime(body.date, body.time, tz)
            schedule = vimshottari_full(jd, birth_local)
            today = date.today().isoformat()
            mahas = schedule.get("mahadashas") or []
            for md in mahas:
                if md.get("startDate", "") <= today < md.get("endDate", "9999"):
                    current = {
                        "mahadasha": md.get("planet") or md.get("lord"),
                        "from": md.get("startDate"), "to": md.get("endDate"),
                    }
                    for ad in md.get("antardasha") or []:
                        if ad.get("startDate", "") <= today < ad.get("endDate", "9999"):
                            current["antardasha"] = ad.get("planet") or ad.get("lord")
                            current["antardashaFrom"] = ad.get("startDate")
                            current["antardashaTo"] = ad.get("endDate")
                            break
                    current_dasha = current
                    break
            # first 5 mahadashas keep the payload light
            dasha = [{"lord": md.get("planet") or md.get("lord"), "from": md.get("startDate"), "to": md.get("endDate")}
                     for md in mahas[:5]]
        except Exception:
            pass
        resp["houses"] = houses["houses"]
        resp["chartSvg"] = svg
        resp["dasha"] = dasha
        resp["currentDasha"] = current_dasha
        resp["birthPlace"] = body.place or _DEFAULT_PLACE["label"]

    return resp


# ─────────────── free tools: match making & dosha (public) ───────────────

class _BirthCoords(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    tz: Optional[str] = Field(None, max_length=60)
    place: Optional[str] = Field(None, max_length=120)


class MatchingToolBody(BaseModel):
    boy: _BirthCoords
    girl: _BirthCoords
    lang: Optional[str] = Field("en", max_length=10, description="Report language: en, hi, ta, te, kn, ml, bn, mr, gu, pa")

    class Config:
        extra = "forbid"


class DoshaToolBody(_BirthCoords):
    lang: Optional[str] = Field("en", max_length=10, description="Report language: en, hi, ta, te, kn, ml, bn, mr, gu, pa")

    class Config:
        extra = "forbid"


class HoroscopeToolBody(_BirthCoords):
    period: str = Field("daily", pattern="^(daily|weekly|monthly|yearly)$")
    lang: Optional[str] = Field("en", max_length=10)



# CPU-heavy public tools get a modest per-IP cap (shared limiter with location).
_tool_bucket = {}


def _tool_limit(request: Request, max_calls: int = 12, window: float = 60.0):
    from .location import _rate_limit as _loc_limit
    client_ip = request.client.host if request.client else "unknown"
    import time as _t
    now = _t.time()
    hits = [t for t in _tool_bucket.get(client_ip, []) if now - t < window]
    if len(hits) >= max_calls:
        from fastapi import HTTPException as _HE
        raise _HE(status_code=429, detail="Too many requests — please wait a minute.")
    hits.append(now)
    _tool_bucket[client_ip] = hits
    if len(_tool_bucket) > 10000:
        _tool_bucket.clear()
    del _loc_limit


def _stub_request(lang: str = "en"):
    """dosha/compat internals only read accept-language off the request."""
    from types import SimpleNamespace
    return SimpleNamespace(headers={"accept-language": lang})


@router.post("/site/tools/matching")
async def tenant_matching_tool(body: MatchingToolBody, request: Request, slug: str = None, domain: str = None):
    """Ashtakoota gun milan + manglik check for both partners, computed on the
    same Swiss-ephemeris engine the platform uses."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    if not charge_site_credits(site["id"], "matching"):
        raise HTTPException(status_code=402, detail="This site is out of credits — the astrologer needs to recharge")
    record_site_event(site["id"], "tool", "matching")
    from . import compat_standalone as _compat_mod
    from .compat_standalone import CompatRequest, _full_guna_milan
    from .dosha_standalone import DoshaStandaloneRequest

    # _full_guna_milan passes `request` through to translate_paragraphs; when
    # called outside its own route, provide the stub it expects. Always set it
    # so the language matches this request (concurrent calls share the module).
    _compat_mod.request = _stub_request(body.lang)

    req = CompatRequest(
        maleDateOfBirth=body.boy.date, maleTimeOfBirth=body.boy.time,
        maleLatitude=body.boy.lat if body.boy.lat is not None else _DEFAULT_PLACE["lat"],
        maleLongitude=body.boy.lon if body.boy.lon is not None else _DEFAULT_PLACE["lon"],
        maleTimezone=body.boy.tz or _DEFAULT_PLACE["tz"],
        femaleDateOfBirth=body.girl.date, femaleTimeOfBirth=body.girl.time,
        femaleLatitude=body.girl.lat if body.girl.lat is not None else _DEFAULT_PLACE["lat"],
        femaleLongitude=body.girl.lon if body.girl.lon is not None else _DEFAULT_PLACE["lon"],
        femaleTimezone=body.girl.tz or _DEFAULT_PLACE["tz"],
        lang=body.lang,
    )
    milan = await _full_guna_milan(req, body.lang)

    async def manglik(p):
        dsb = DoshaStandaloneRequest(
            dateOfBirth=p.date, timeOfBirth=p.time,
            latitude=p.lat if p.lat is not None else _DEFAULT_PLACE["lat"],
            longitude=p.lon if p.lon is not None else _DEFAULT_PLACE["lon"],
            timezone=p.tz or _DEFAULT_PLACE["tz"],
        )
        return await manglik_detailed(dsb, _stub_request(body.lang))

    from .dosha_standalone import manglik_detailed
    boy_manglik = await manglik(body.boy)
    girl_manglik = await manglik(body.girl)

    def _manglik_summary(m):
        return {
            "manglikPresent": m.get("manglikPresent"),
            "summary": m.get("summary"),
            "marsHouse": m.get("marsHouse"),
            "marsSign": m.get("marsSign"),
            "severityLabel": m.get("severityLabel"),
        }

    return {
        "summary": milan.get("summary"),
        "maleProfile": milan.get("maleProfile"),
        "femaleProfile": milan.get("femaleProfile"),
        "ashtakootaGunas": milan.get("ashtakootaGunas"),
        "boyManglik": _manglik_summary(boy_manglik),
        "girlManglik": _manglik_summary(girl_manglik),
        "astrologer": site["name"],
    }


@router.post("/site/tools/dosha")
async def tenant_dosha_tool(body: DoshaToolBody, request: Request, slug: str = None, domain: str = None):
    """Dosha report (manglik analysis + grahan/shrapit checks) for a birth chart."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    if not charge_site_credits(site["id"], "dosha"):
        raise HTTPException(status_code=402, detail="This site is out of credits — the astrologer needs to recharge")
    record_site_event(site["id"], "tool", "dosha")
    from .dosha_standalone import DoshaStandaloneRequest, manglik_detailed, grahan_dosha, shrapit_dosha

    dsb = DoshaStandaloneRequest(
        dateOfBirth=body.date, timeOfBirth=body.time,
        latitude=body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
        longitude=body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
        timezone=body.tz or _DEFAULT_PLACE["tz"],
    )
    stub = _stub_request(body.lang)
    manglik = await manglik_detailed(dsb, stub)
    try:
        grahan_res = await grahan_dosha(dsb, stub)
    except Exception:
        grahan_res = None
    try:
        shrapit_res = await shrapit_dosha(dsb, stub)
    except Exception:
        shrapit_res = None

    return {
        "manglik": manglik,
        "grahan": grahan_res,
        "shrapit": shrapit_res,
        "birthPlace": body.place or _DEFAULT_PLACE["label"],
        "astrologer": site["name"],
    }


@router.post("/site/tools/horoscope")
async def tenant_horoscope_tool(body: HoroscopeToolBody, request: Request, slug: str = None, domain: str = None):
    """Personal daily/weekly/monthly/yearly horoscope from the visitor's own
    birth chart (unlike the public widget, which is sign-only)."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    from .horoscope_text import HoroscopeRequest, daily_horoscope, weekly_horoscope, \
        monthly_horoscope, yearly_horoscope
    fn = {"daily": daily_horoscope, "weekly": weekly_horoscope,
          "monthly": monthly_horoscope, "yearly": yearly_horoscope}.get(body.period)
    try:
        result = fn(
            HoroscopeRequest(
                dateOfBirth=body.date, timeOfBirth=body.time,
                latitude=body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
                longitude=body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
                timezone=body.tz or _DEFAULT_PLACE["tz"],
            ),
            request=_stub_request(body.lang),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not generate the horoscope — {str(e)[:120]}")
    data = result.get("data", result) if isinstance(result, dict) else {}
    return {"period": body.period, "horoscope": data, "astrologer": site["name"]}


class NumerologyToolBody(BaseModel):
    fullName: Optional[str] = Field(None, max_length=120)
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    mobileNumber: Optional[str] = Field(None, max_length=20)
    lang: Optional[str] = Field("en", max_length=10)

    class Config:
        extra = "forbid"


@router.post("/site/tools/numerology")
async def tenant_numerology_tool(body: NumerologyToolBody, request: Request, slug: str = None, domain: str = None):
    """Numerology reading for a tenant site's visitor: life-path (birth date),
    destiny & soul numbers (name) and mobile-number analysis, in one call."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    from .numerology import LifePathRequest, DestinyRequest, SoulRequest, MobileRequest, \
        life_path_number, destiny_number, soul_number, mobile_number

    out = {"astrologer": site["name"]}
    for key, body_cls, fn, payload in [
        ("lifePath", LifePathRequest, life_path_number,
         {"dateOfBirth": body.date} if body.date else None),
        ("destiny", DestinyRequest, destiny_number,
         {"fullName": body.fullName} if body.fullName else None),
        ("soul", SoulRequest, soul_number,
         {"fullName": body.fullName} if body.fullName else None),
        ("mobile", MobileRequest, mobile_number,
         {"mobileNumber": body.mobileNumber} if body.mobileNumber else None),
    ]:
        if payload is None:
            continue
        payload["lang"] = body.lang
        try:
            out[key] = await fn(body_cls(**payload), _stub_request(body.lang))
        except Exception as e:
            out[key] = {"error": str(e)[:200]}
    return out


class GemstoneToolBody(_BirthCoords):
    lang: Optional[str] = Field("en", max_length=10)

    class Config:
        extra = "forbid"


@router.post("/site/tools/gemstone")
async def tenant_gemstone_tool(body: GemstoneToolBody, request: Request, slug: str = None, domain: str = None):
    """Personal gemstone recommendation computed from the visitor's chart
    (lagna lord + current mahadasha lord)."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    from .gemstone import BirthDetailRequest, gemstone_recommendation
    try:
        rec = await gemstone_recommendation(
            BirthDetailRequest(
                dateOfBirth=body.date, timeOfBirth=body.time,
                latitude=body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
                longitude=body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
                timezone=body.tz or _DEFAULT_PLACE["tz"], lang=body.lang,
            ),
            request=_stub_request(body.lang),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not recommend a gemstone — {str(e)[:120]}")
    return {"gemstone": rec, "astrologer": site["name"]}


class MuhuratToolBody(BaseModel):
    task: str = Field(..., pattern="^(marriage|engagement|business-opening|house-warming|property-purchase|vehicle-purchase|naming-ceremony)$")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    lang: Optional[str] = Field("en", max_length=10)

    class Config:
        extra = "forbid"


@router.post("/site/tools/muhurat")
async def tenant_muhurat_tool(body: MuhuratToolBody, request: Request, slug: str = None, domain: str = None):
    """Auspicious timings (shubh muhurat) for a task on a chosen date."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    path = {
        "marriage": "/horoscope/muhurat/marriage", "engagement": "/horoscope/muhurat/engagement",
        "business-opening": "/horoscope/muhurat/business-opening", "house-warming": "/horoscope/muhurat/griha-pravesh",
        "property-purchase": "/horoscope/muhurat/property-purchase", "vehicle-purchase": "/horoscope/muhurat/vehicle-purchase",
        "naming-ceremony": "/horoscope/muhurat/naming-ceremony",
    }[body.task]
    payload = {
        "dateOfBirth": body.date, "lang": body.lang,
        "latitude": _DEFAULT_PLACE["lat"], "longitude": _DEFAULT_PLACE["lon"],
        "timezone": _DEFAULT_PLACE["tz"],
    }
    result = await _acall_internal(path, payload, body.lang)
    if result is None or (isinstance(result, dict) and result.get("error")):
        raise HTTPException(status_code=400, detail="Could not compute the muhurat — check the date")
    return {"task": body.task, "date": body.date, "muhurat": result, "astrologer": site["name"]}


class LuckyToolBody(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    lang: Optional[str] = Field("en", max_length=10)

    class Config:
        extra = "forbid"


@router.post("/site/tools/lucky")
async def tenant_lucky_tool(body: LuckyToolBody, request: Request, slug: str = None, domain: str = None):
    """Lucky colors / numbers / days / metals for a birth date — quick daily guidance."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    out = {"astrologer": site["name"]}
    for key, path in [("colors", "/lucky/color"), ("numbers", "/lucky/number"),
                      ("days", "/lucky/day"), ("metals", "/lucky/metal")]:
        try:
            res = await _acall_internal(path, {"dateOfBirth": body.date, "lang": body.lang}, body.lang)
            data = res.get("data", res) if isinstance(res, dict) else {}
            out[key] = data
        except Exception as e:
            out[key] = {"error": str(e)[:200]}
    return out


@router.get("/site/tools/panchang")
def tenant_panchang_tool(
    request: Request,
    slug: str = None, domain: str = None, date_str: str = None,
    lat: float = Query(None, ge=-90, le=90), lon: float = Query(None, ge=-180, le=180),
    tz: str = Query(None, max_length=60), place: str = Query(None, max_length=120),
):
    """Today's panchang for a tenant site's daily widget. Defaults to Delhi;
    pass lat/lon/tz (from the location picker) to see another place's panchang."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    from ..utils import compute_panchang
    d = date_str or date.today().isoformat()
    try:
        date.fromisoformat(d)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    lat = lat if lat is not None else _DEFAULT_PLACE["lat"]
    lon = lon if lon is not None else _DEFAULT_PLACE["lon"]
    tz = tz or _DEFAULT_PLACE["tz"]
    place = place or _DEFAULT_PLACE["label"]
    p = compute_panchang(d, "12:00", tz, lat, lon)
    return {"date": d, "place": place, "latitude": lat, "longitude": lon, "panchang": p, "astrologer": site["name"]}


class _NoLangRequest:
    """Minimal stand-in for fastapi Request — daily_horoscope only reads the
    accept-language header."""

    headers = {"accept-language": "en"}


@router.get("/site/tools/horoscope")
def tenant_daily_horoscope(request: Request, slug: str = None, domain: str = None, sign: str = Query(..., min_length=3, max_length=20)):
    """Daily rashi horoscope for a tenant site's widget, computed on the
    platform engine (template-based — no birth details needed)."""
    _tool_limit(request, max_calls=30)
    site = _resolve_site(slug, domain)
    from ..utils import ZODIAC_SIGNS
    s = (sign or "").strip().capitalize()
    if s not in ZODIAC_SIGNS:
        raise HTTPException(status_code=400, detail="Unknown zodiac sign")
    from .horoscope_text import HoroscopeRequest, daily_horoscope
    try:
        result = daily_horoscope(
            HoroscopeRequest(
                dateOfBirth="1990-01-01", timeOfBirth="06:00",
                latitude=_DEFAULT_PLACE["lat"], longitude=_DEFAULT_PLACE["lon"],
                timezone=_DEFAULT_PLACE["tz"], zodiacSign=s,
            ),
            request=_NoLangRequest(),
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Could not generate the horoscope")
    data = result.get("data", result) if isinstance(result, dict) else {}
    return {"sign": s, "horoscope": data, "astrologer": site["name"]}


# ─────────────── comprehensive kundli (full analysis bundle) ───────────────

def _sanitize(obj, depth=0):
    """Make a route result JSON-safe: drop un-awaited coroutines (a few
    analysis endpoints return them when lang='en'), decode JSONResponse."""
    if depth > 12:
        return None
    if isinstance(obj, coroutine_type()):
        return None
    if hasattr(obj, "body"):  # starlette JSONResponse
        import json as _json
        return _json.loads(obj.body)
    if isinstance(obj, dict):
        return {k: _sanitize(v, depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v, depth + 1) for v in obj]
    try:
        import json as _json
        _json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def coroutine_type():
    import types
    return types.CoroutineType


def _call_internal(path: str, payload: dict, lang: str = "en"):
    """Invoke one of the platform's own POST endpoints in-process (no HTTP),
    supplying a stub Request carrying the requested report language. Safe from
    sync endpoints only; from async endpoints use _acall_internal."""
    import asyncio
    import inspect
    from types import SimpleNamespace
    from ..main import app as _app

    stub = SimpleNamespace(headers={"accept-language": lang})
    for route in _app.routes:
        if getattr(route, "path", None) == path and hasattr(route, "endpoint"):
            kwargs = {}
            for pname, param in inspect.signature(route.endpoint).parameters.items():
                if pname == "request":
                    kwargs[pname] = stub
                elif hasattr(param.annotation, "model_validate"):
                    kwargs[pname] = param.annotation.model_validate(payload)
            result = route.endpoint(**kwargs)
            if inspect.iscoroutine(result):
                result = asyncio.run(result)
            return _sanitize(result)
    return None


async def _acall_internal(path: str, payload: dict, lang: str = "en"):
    """Async variant of _call_internal — awaits coroutine endpoints instead of
    asyncio.run(), which is illegal inside a running event loop."""
    import inspect
    from types import SimpleNamespace
    from ..main import app as _app

    stub = SimpleNamespace(headers={"accept-language": lang})
    for route in _app.routes:
        if getattr(route, "path", None) == path and hasattr(route, "endpoint"):
            kwargs = {}
            for pname, param in inspect.signature(route.endpoint).parameters.items():
                if pname == "request":
                    kwargs[pname] = stub
                elif hasattr(param.annotation, "model_validate"):
                    kwargs[pname] = param.annotation.model_validate(payload)
            result = route.endpoint(**kwargs)
            if inspect.iscoroutine(result):
                result = await result
            return _sanitize(result)
    return None


@router.post("/site/tools/kundli-full")
def tenant_kundli_full(body: KundliToolBody, request: Request, slug: str = None, domain: str = None):
    """Complete kundli analysis for a tenant site: everything the platform can
    compute for a birth chart — vimshottari (full), yogini, ashtottari,
    kalachakra & chara dashas, current dasha, doshas (manglik/grahan/shrapit/
    general/dhaiya), lal kitab, KP ruling planets and divisional charts."""
    _tool_limit(request)
    site = _resolve_site(slug, domain)
    birth = {
        "dateOfBirth": body.date, "timeOfBirth": body.time,
        "latitude": body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
        "longitude": body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
        "timezone": body.tz or _DEFAULT_PLACE["tz"],
    }
    sections = {}
    # Classical Shodashavarga set (D1 is the birth chart already shown in the chart tab).
    classical_vargas = ["D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20",
                        "D24", "D27", "D30", "D40", "D45", "D60"]
    targets = {
        "yogini": "/dasha/yogini",
        "ashtottari": "/dasha/ashtottari",
        "kalachakra": "/dasha/kalachakra",
        "chara": "/horoscope/dasha/chara",
        "dashaCurrent": "/horoscope/dasha/current",
        "doshaCompute": "/horoscope/dosha/compute",
        "dhaiya": "/horoscope/dosha/dhaiya",
        "kpRulingPlanets": "/kp/ruling-planets",
        "lalKitab": "/lal-kitab/chart-analysis",
    }
    for v in classical_vargas:
        targets[f"divisional{v}"] = "/chart/divisional-svg"
    for key, path in targets.items():
        try:
            payload = {**birth, "lang": body.lang}
            if key.startswith("divisional"):
                payload.update({
                    "name": key[len("divisional"):],
                    "width": 460, "height": 460,
                    "theme": body.chart_theme or "light",
                })
            sections[key] = _call_internal(path, payload, body.lang)
        except Exception as e:
            sections[key] = {"error": str(e)[:200]}

    # Full Vimshottari tree (mahadasha → antardasha → pratyantardasha) for the
    # dasha explorer. Sookshma level is dropped to keep the payload light.
    try:
        from ..main import parse_local_datetime, vimshottari_full
        from ..utils import to_julian as _to_jd
        jd_v = _to_jd(body.date, body.time, birth["timezone"])
        sched = vimshottari_full(jd_v, parse_local_datetime(body.date, body.time, birth["timezone"]))
        sections["vimshottari"] = {
            "system": "Vimshottari",
            "mahadashas": [
                {
                    "planet": md.get("planet"),
                    "startDate": md.get("startDate"), "endDate": md.get("endDate"),
                    "antardasha": [
                        {
                            "planet": ad.get("planet"),
                            "startDate": ad.get("startDate"), "endDate": ad.get("endDate"),
                            "pratyantardasha": [
                                {"planet": pd.get("planet"), "startDate": pd.get("startDate"),
                                 "endDate": pd.get("endDate")}
                                for pd in (ad.get("pratyantar") or [])
                            ],
                        }
                        for ad in (md.get("antardasha") or [])
                    ],
                }
                for md in (sched.get("mahadashas") or [])
            ],
        }
    except Exception as e:
        sections["vimshottari"] = {"error": str(e)[:200]}

    dosha = {}
    try:
        import asyncio as _asyncio
        from .dosha_standalone import DoshaStandaloneRequest, manglik_detailed, grahan_dosha, shrapit_dosha
        dsb = DoshaStandaloneRequest(
            dateOfBirth=body.date, timeOfBirth=body.time,
            latitude=body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
            longitude=body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
            timezone=body.tz or _DEFAULT_PLACE["tz"],
        )
        dosha = {
            "manglik": _asyncio.run(manglik_detailed(dsb, _stub_request(body.lang))),
            "grahan": _asyncio.run(grahan_dosha(dsb, _stub_request(body.lang))),
            "shrapit": _asyncio.run(shrapit_dosha(dsb, _stub_request(body.lang))),
        }
    except Exception as e:
        dosha = {"error": str(e)[:200]}

    core = tenant_kundli_tool(body, request=request, slug=slug, domain=domain)
    return {"core": core, "doshas": dosha, **sections}


# ─────────────── tenant visitor accounts (per-site separation) ───────────────

class TenantFirebaseBody(BaseModel):
    idToken: str = Field(..., min_length=50)


def _upsert_tenant_user(site_id: int, claims: dict):
    from ..database import get_db
    email = (claims.get("email") or "").lower().strip()
    db = get_db()
    row = db.execute(
        _tenant_convert("SELECT * FROM tenant_users WHERE site_id = ? AND email = ?"),
        (site_id, email),
    ).fetchone()
    user = row if isinstance(row, dict) else dict(zip(
        ["id", "site_id", "firebase_uid", "email", "name", "phone", "avatar_url", "created_at"],
        row)) if row else None
    if user:
        db.execute(
            _convert("UPDATE tenant_users SET firebase_uid = ?, name = COALESCE(?, name), avatar_url = COALESCE(?, avatar_url) WHERE id = ?"),
            (claims.get("user_id"), claims.get("name"), claims.get("picture"), user["id"]),
        )
        db.commit()
        user = {**user, "firebase_uid": claims.get("user_id")}
        return user, False
    cur = db.execute(
        _tenant_convert("INSERT INTO tenant_users (site_id, firebase_uid, email, name, avatar_url) VALUES (?, ?, ?, ?, ?) RETURNING id"),
        (site_id, claims.get("user_id"), email, claims.get("name"), claims.get("picture")),
    )
    new_id = _tenant_first_col(cur.fetchone())
    db.commit()
    return {"id": new_id, "site_id": site_id, "email": email, "name": claims.get("name"),
            "avatar_url": claims.get("picture"), "firebase_uid": claims.get("user_id"), "created_at": None}, True


@router.post("/site/auth/firebase")
async def tenant_firebase_login(body: TenantFirebaseBody, slug: str = None, domain: str = None):
    """Visitor sign-in on a tenant site. The site comes from the host/slug, so
    the same Google account is a SEPARATE identity per astrologer. Returns a
    scoped tenant token (distinct from platform user tokens)."""
    from ..routers.auth_router import verify_firebase_id_token
    site = _resolve_site(slug, domain)
    claims = verify_firebase_id_token(body.idToken)
    if not claims.get("email_verified", True):
        raise HTTPException(status_code=401, detail="Provider email is not verified")
    user, created = _upsert_tenant_user(site["id"], claims)

    # tenant-scoped token: carries the tenant user + site, never platform powers
    import asyncio
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    from ..auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": f"tenant-user:{user['id']}", "site_id": site["id"],
        "email": user["email"], "exp": datetime.now(_tz.utc) + _td(days=30),
    }
    from jose import jwt as _jwt
    token = _jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"tenant_user": user, "tenant_token": token, "hasPassword": bool(user.get("password_hash")),
            "site": {"id": site["id"], "name": site["name"], "slug": site["slug"]}, "created": created, "new_user": created}


# ─────────────── tenant visitor email+password auth ───────────────

from ..tenants import _convert as _tenant_convert, _first_col as _tenant_first_col


class TenantRegisterBody(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=8, max_length=100)
    name: Optional[str] = Field(None, max_length=120)


def _tenant_token(user: dict, site: dict):
    from ..routers.auth_router import create_tenant_token
    return create_tenant_token(user["id"], site["id"])


@router.post("/site/auth/register")
def tenant_register(body: TenantRegisterBody, request: Request, slug: str = None, domain: str = None):
    """Visitor signs up on an astrologer's site with email+password.
    Stored per-tenant in tenant_users (bcrypt hash), never in platform users."""
    from ..rate_limit import rate_limit, client_ip
    rate_limit(f"treg:{client_ip(request)}", max_calls=20, window=3600)
    from ..auth import hash_password
    site = _resolve_site(slug, domain)
    email = body.email.lower().strip()
    from ..database import get_db
    db = get_db()
    row = db.execute(_tenant_convert("SELECT id FROM tenant_users WHERE site_id = ? AND email = ?"),
                     (site["id"], email)).fetchone()
    if row:
        raise HTTPException(status_code=409, detail="An account with this email already exists on this site — please sign in")
    cur = db.execute(
        _tenant_convert("INSERT INTO tenant_users (site_id, email, name, password_hash) VALUES (?, ?, ?, ?) RETURNING id"),
        (site["id"], email, body.name, hash_password(body.password)),
    )
    new_id = _tenant_first_col(cur.fetchone())
    db.commit()
    user = {"id": new_id, "site_id": site["id"], "email": email, "name": body.name,
            "avatar_url": None, "firebase_uid": None, "created_at": None}
    return {"tenant_user": user, "tenant_token": _tenant_token(user, site),
            "site": {"id": site["id"], "name": site["name"], "slug": site["slug"]}, "new_user": True}


@router.post("/site/auth/login")
def tenant_login(body: TenantRegisterBody, request: Request, slug: str = None, domain: str = None):
    from ..rate_limit import rate_limit, client_ip
    rate_limit(f"tlogin-ip:{client_ip(request)}", max_calls=20, window=300)
    rate_limit(f"tlogin-acct:{body.email.lower().strip()}", max_calls=10, window=300)
    from ..auth import verify_password
    site = _resolve_site(slug, domain)
    email = body.email.lower().strip()
    from ..database import get_db
    db = get_db()
    row = db.execute(_tenant_convert(
        "SELECT id, site_id, firebase_uid, email, name, phone, avatar_url, password_hash, created_at "
        "FROM tenant_users WHERE site_id = ? AND email = ?"), (site["id"], email)).fetchone()
    user = row if isinstance(row, dict) else dict(zip(
        ["id", "site_id", "firebase_uid", "email", "name", "phone", "avatar_url", "password_hash", "created_at"],
        row)) if row else None
    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password for this site")
    user = {k: v for k, v in user.items() if k != "password_hash"}
    return {"tenant_user": user, "tenant_token": _tenant_token(user, site),
            "site": {"id": site["id"], "name": site["name"], "slug": site["slug"]}, "new_user": False}


@router.get("/site/auth/config")
def tenant_auth_config(slug: str = None, domain: str = None):
    """Visitor sign-in capabilities for a tenant site. Google appears only
    when the superadmin has enabled it for this site."""
    site = _resolve_site(slug, domain)
    settings = site.get("settings") or {}
    return {
        "googleEnabled": settings.get("visitorGoogleAuth") is True,
        "siteName": site.get("name"),
    }


class SetPasswordBody(BaseModel):
    password: str = Field(..., min_length=8, max_length=100)


def _require_tenant_token(request_token: str, site_id: int):
    """Validate a tenant-scoped JWT and return the tenant user id."""
    from ..routers.auth_router import verify_tenant_token
    try:
        claims = verify_tenant_token(request_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")
    if not str(claims.get("sub", "")).startswith("tenant-user:") or claims.get("site_id") != site_id:
        raise HTTPException(status_code=403, detail="This session belongs to a different site")
    return int(str(claims["sub"]).split(":", 1)[1])


def _tenant_bearer(request: Request) -> str:
    return (request.headers.get("authorization") or "").replace("Bearer ", "").strip()


def _get_tenant_user(site_id: int, user_id: int):
    from ..database import get_db
    row = get_db().execute(
        _tenant_convert("SELECT id, site_id, email, name, phone, avatar_url FROM tenant_users WHERE site_id = ? AND id = ?"),
        (site_id, user_id),
    ).fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return row
    return dict(zip(["id", "site_id", "email", "name", "phone", "avatar_url"], row))


def _require_site_visitor(request: Request, site_id: int) -> dict:
    """Booking and store checkout require a signed-in visitor account on this
    site (email+password or Google). Returns the tenant_users row."""
    token = _tenant_bearer(request)
    if not token:
        raise HTTPException(status_code=401, detail="Please sign in or create an account to continue")
    user_id = _require_tenant_token(token, site_id)
    user = _get_tenant_user(site_id, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")
    return user


@router.post("/site/auth/set-password")
def tenant_set_password(body: SetPasswordBody, request: Request, slug: str = None, domain: str = None):
    """Let a Google/Firebase-signed-in visitor add a password so the email+
    password form also works for them in the future."""
    from ..auth import hash_password
    from ..database import get_db
    site = _resolve_site(slug, domain)
    token = (request.headers.get("authorization") or "").replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sign in first")
    user_id = _require_tenant_token(token, site["id"])
    db = get_db()
    row = db.execute(_tenant_convert("SELECT password_hash FROM tenant_users WHERE site_id = ? AND id = ?"),
                     (site["id"], user_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    current = row.get("password_hash") if isinstance(row, dict) else row[0]
    if current:
        return {"ok": True, "alreadySet": True}
    db.execute(_tenant_convert("UPDATE tenant_users SET password_hash = ? WHERE site_id = ? AND id = ?"),
               (hash_password(body.password), site["id"], user_id))
    db.commit()
    return {"ok": True, "alreadySet": False}


# ─────────────── visitor account: my consultations & orders ───────────────

def _booking_view(b: dict) -> dict:
    return {k: v for k, v in b.items() if k not in ("site_id", "tenant_user_id")}


def _order_view(o: dict) -> dict:
    return {k: v for k, v in o.items() if k not in ("site_id", "tenant_user_id")}


@router.get("/site/my/bookings")
def my_bookings(request: Request, slug: str = None, domain: str = None):
    """The signed-in visitor's consultations on this site (upcoming + past)."""
    site = _resolve_site(slug, domain)
    user = _require_site_visitor(request, site["id"])
    rows = list_bookings(site["id"], tenant_user_id=user["id"])
    return {"bookings": [_booking_view(b) for b in rows]}


@router.get("/site/my/orders")
def my_orders(request: Request, slug: str = None, domain: str = None):
    """The signed-in visitor's store orders on this site."""
    site = _resolve_site(slug, domain)
    user = _require_site_visitor(request, site["id"])
    rows = list_orders(site["id"], tenant_user_id=user["id"])
    return {"orders": [_order_view(o) for o in rows]}


@router.post("/site/my/bookings/{booking_id}/cancel")
def cancel_my_booking(booking_id: int, request: Request, slug: str = None, domain: str = None):
    """Visitor cancels their own upcoming consultation. Past appointments and
    already-changed bookings cannot be cancelled here."""
    site = _resolve_site(slug, domain)
    user = _require_site_visitor(request, site["id"])
    booking = get_booking(site["id"], booking_id)
    if not booking or booking.get("tenant_user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.get("status") != "confirmed":
        raise HTTPException(status_code=400, detail="This booking can no longer be cancelled")
    if booking.get("date", "") < date.today().isoformat():
        raise HTTPException(status_code=400, detail="Past appointments cannot be cancelled")
    update_booking(site["id"], booking_id, {"status": "cancelled"})
    return {"ok": True, "booking": _booking_view(get_booking(site["id"], booking_id))}


@router.post("/site/my/orders/{order_id}/cancel")
def cancel_my_order(order_id: int, request: Request, slug: str = None, domain: str = None):
    """Visitor cancels their own order before it is fulfilled. Reserved stock
    is returned to the shelf, same as when the astrologer cancels."""
    site = _resolve_site(slug, domain)
    user = _require_site_visitor(request, site["id"])
    order = get_order(site["id"], order_id)
    if not order or order.get("tenant_user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("status") not in ("new", "confirmed"):
        raise HTTPException(status_code=400, detail="This order can no longer be cancelled")
    update_order(site["id"], order_id, {"status": "cancelled"})
    for it in order.get("items") or []:
        qty = it.get("qty", 0)
        if qty > 0:
            adjust_product_stock(site["id"], it["product_id"], qty)
    return {"ok": True, "order": _order_view(get_order(site["id"], order_id))}


# ─────────────── public invoice view (shareable link) ───────────────

@router.get("/invoice/{token}")
def public_invoice(token: str):
    """The client-facing invoice behind the shareable link. No auth — the
    unguessable token IS the access. Returns the astrologer's public brand
    info plus the invoice; never site settings beyond contact details."""
    from ..tenants import get_invoice_by_token
    invoice = get_invoice_by_token(token)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # resolve the site (draft sites still need to show their invoices)
    from ..database import get_db
    from ..tenants import _convert as _tc, _site_row
    row = get_db().execute(_tc("SELECT * FROM sites WHERE id = ?"), (invoice["site_id"],)).fetchone()
    site = _site_row(row)
    if not site:
        raise HTTPException(status_code=404, detail="Invoice not found")
    settings = site.get("settings") or {}
    # only contact fields the client may see on an invoice
    contact = {k: settings.get(k) for k in ("email", "phone", "city", "whatsappNumber") if settings.get(k)}
    return {
        "invoice": {k: v for k, v in invoice.items() if k != "site_id"},
        "site": {"id": site["id"], "slug": site["slug"], "name": site["name"], "tagline": site["tagline"],
                 "logo_url": site.get("logo_url"), "custom_domain": site.get("custom_domain"),
                 "theme": site.get("theme"), "contact": contact},
    }


@router.post("/integrations/woocommerce/{connection_id}")
async def woocommerce_webhook(connection_id: int, request: Request):
    """Public WooCommerce order.created webhook. Signature verified with the
    connection's consumer secret; new orders land in the tenant's Orders tab."""
    import json as _json
    from ..database import get_db
    from ..tenants import get_store_connection, create_order, list_orders
    from ..store_integrations import verify_woo_webhook, woo_order_to_site_order

    raw = await request.body()
    db = get_db()
    from ..tenants import _convert
    row = db.execute(_convert("SELECT site_id, api_secret FROM store_connections WHERE id = ?"), (connection_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Unknown connection")
    site_id = row["site_id"] if isinstance(row, dict) else row[0]
    secret = row["api_secret"] if isinstance(row, dict) else row[1]
    sig = request.headers.get("X-WC-Webhook-Signature", "")
    if not verify_woo_webhook(raw, sig, secret or ""):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        woo_order = _json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")
    order_data = woo_order_to_site_order(woo_order)
    ref = order_data.get("external_ref")
    if any(ref in (x.get("notes") or "") for x in list_orders(site_id, limit=200)):
        return {"ok": True, "duplicate": True}
    created = create_order(site_id, order_data)
    return {"ok": True, "order_id": created.get("id")}


@router.post("/site/event")
def tenant_event(request: Request, body: dict, slug: str = None, domain: str = None):
    """Lightweight analytics beacon from tenant sites (pageviews)."""
    _tool_limit(request, max_calls=120)
    kind = str((body or {}).get("kind", "pageview"))[:40]
    if kind not in ("pageview", "tool"):
        kind = "pageview"
    site = _resolve_site(slug, domain)
    record_site_event(site["id"], kind, str((body or {}).get("path", ""))[:200])
    return {"ok": True}


class TenantLeadBody(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    message: Optional[str] = Field(None, max_length=1000)
    source: str = Field("enquiry", max_length=40)


_TAG_RE = None


def _strip_html(value):
    """Lead fields are plain text downstream (CSV, email bodies) — drop any
    markup the submitter tried to embed."""
    global _TAG_RE
    if _TAG_RE is None:
        import re
        _TAG_RE = re.compile(r"<[^>]*>")
    return _TAG_RE.sub(" ", str(value or "")).strip()


@router.post("/site/lead")
def tenant_lead(request: Request, body: TenantLeadBody, slug: str = None, domain: str = None):
    """Universal lead capture for tenant sites: newsletter, enquiries,
    callback requests, consult asks — any widget can post here."""
    _tool_limit(request, max_calls=10)
    site = _resolve_site(slug, domain)
    if not (body.phone or body.email):
        raise HTTPException(status_code=400, detail="A phone number or email is required")
    create_lead(site["id"], {
        "tool": _strip_html(body.source)[:40],
        "name": _strip_html(body.name),
        "phone": (body.phone or "").strip(),
        "email": (body.email or "").strip(),
        "details": _strip_html(body.message),
    })
    return {"ok": True, "message": "Got it — we'll be in touch soon."}
