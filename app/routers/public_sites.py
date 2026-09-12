"""Public endpoints for tenant websites: site resolution, booking flow and store.

These are unauthenticated (the visitor is the astrologer's client). Sites are
resolved by subdomain slug or custom domain; only published sites are visible.
"""
import json
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from ..tenants import (
    get_site_by_slug, get_site_by_domain, public_site_bundle,
    list_availability, get_service, list_bookings, create_booking,
    create_lead, list_products, get_product, create_order, adjust_product_stock,
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


# ─────────────── store (public storefront) ───────────────

class PublicOrderItem(BaseModel):
    product_id: int
    qty: int = Field(1, ge=1, le=99)

    class Config:
        extra = "forbid"


class PublicOrderBody(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=120)
    client_phone: Optional[str] = Field(None, max_length=20)
    client_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    items: List[PublicOrderItem] = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        extra = "forbid"


@router.post("/site/order")
def public_place_order(body: PublicOrderBody, slug: str = None, domain: str = None):
    """A visitor places an order from the astrologer's store. Prices are taken
    from the database (never from the client), and stock is checked."""
    site = _resolve_site(slug, domain)
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
        "client_name": body.client_name,
        "client_phone": body.client_phone,
        "client_email": body.client_email,
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
def tenant_kundli_tool(body: KundliToolBody, slug: str = None, domain: str = None):
    """Free kundli for a tenant site's visitors. Basic mode returns a snapshot
    (ascendant, moon/sun sign, nakshatra, planets, gemstone); detail=true adds
    the full software view: houses, North-Indian chart SVG and Vimshottari
    dasha. Contact details, when given, become a lead for the astrologer."""
    site = _resolve_site(slug, domain)

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

    class Config:
        extra = "forbid"


class DoshaToolBody(_BirthCoords):
    pass


def _stub_request():
    """dosha/compat internals only read accept-language off the request."""
    from types import SimpleNamespace
    return SimpleNamespace(headers={"accept-language": "en"})


@router.post("/site/tools/matching")
async def tenant_matching_tool(body: MatchingToolBody, slug: str = None, domain: str = None):
    """Ashtakoota gun milan + manglik check for both partners, computed on the
    same Swiss-ephemeris engine the platform uses."""
    site = _resolve_site(slug, domain)
    from . import compat_standalone as _compat_mod
    from .compat_standalone import CompatRequest, _full_guna_milan
    from .dosha_standalone import DoshaStandaloneRequest

    # _full_guna_milan passes `request` through to translate_paragraphs; when
    # called outside its own route, provide the stub it expects (lang is 'en').
    if not hasattr(_compat_mod, "request"):
        _compat_mod.request = _stub_request()

    req = CompatRequest(
        maleDateOfBirth=body.boy.date, maleTimeOfBirth=body.boy.time,
        maleLatitude=body.boy.lat if body.boy.lat is not None else _DEFAULT_PLACE["lat"],
        maleLongitude=body.boy.lon if body.boy.lon is not None else _DEFAULT_PLACE["lon"],
        maleTimezone=body.boy.tz or _DEFAULT_PLACE["tz"],
        femaleDateOfBirth=body.girl.date, femaleTimeOfBirth=body.girl.time,
        femaleLatitude=body.girl.lat if body.girl.lat is not None else _DEFAULT_PLACE["lat"],
        femaleLongitude=body.girl.lon if body.girl.lon is not None else _DEFAULT_PLACE["lon"],
        femaleTimezone=body.girl.tz or _DEFAULT_PLACE["tz"],
        lang="en",
    )
    milan = await _full_guna_milan(req, "en")

    async def manglik(p):
        dsb = DoshaStandaloneRequest(
            dateOfBirth=p.date, timeOfBirth=p.time,
            latitude=p.lat if p.lat is not None else _DEFAULT_PLACE["lat"],
            longitude=p.lon if p.lon is not None else _DEFAULT_PLACE["lon"],
            timezone=p.tz or _DEFAULT_PLACE["tz"],
        )
        return await manglik_detailed(dsb, _stub_request())

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
async def tenant_dosha_tool(body: DoshaToolBody, slug: str = None, domain: str = None):
    """Dosha report (manglik analysis + grahan/shrapit checks) for a birth chart."""
    site = _resolve_site(slug, domain)
    from .dosha_standalone import DoshaStandaloneRequest, manglik_detailed, grahan_dosha, shrapit_dosha

    dsb = DoshaStandaloneRequest(
        dateOfBirth=body.date, timeOfBirth=body.time,
        latitude=body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
        longitude=body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
        timezone=body.tz or _DEFAULT_PLACE["tz"],
    )
    stub = _stub_request()
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


class _NoLangRequest:
    """Minimal stand-in for fastapi Request — daily_horoscope only reads the
    accept-language header."""

    headers = {"accept-language": "en"}


@router.get("/site/tools/horoscope")
def tenant_daily_horoscope(slug: str = None, domain: str = None, sign: str = Query(..., min_length=3, max_length=20)):
    """Daily rashi horoscope for a tenant site's widget, computed on the
    platform engine (template-based — no birth details needed)."""
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


def _call_internal(path: str, payload: dict):
    """Invoke one of the platform's own POST endpoints in-process (no HTTP),
    supplying a stub Request for language detection (lang='en')."""
    import asyncio
    import inspect
    from types import SimpleNamespace
    from ..main import app as _app

    stub = SimpleNamespace(headers={"accept-language": "en"})
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


@router.post("/site/tools/kundli-full")
def tenant_kundli_full(body: KundliToolBody, slug: str = None, domain: str = None):
    """Complete kundli analysis for a tenant site: everything the platform can
    compute for a birth chart — vimshottari (full), yogini, ashtottari,
    kalachakra & chara dashas, current dasha, doshas (manglik/grahan/shrapit/
    general/dhaiya), lal kitab, KP ruling planets and divisional charts."""
    site = _resolve_site(slug, domain)
    birth = {
        "dateOfBirth": body.date, "timeOfBirth": body.time,
        "latitude": body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
        "longitude": body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
        "timezone": body.tz or _DEFAULT_PLACE["tz"],
    }
    sections = {}
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
        "divisionalD9": "/chart/divisional-svg",
        "divisionalD10": "/chart/divisional-svg",
    }
    for key, path in targets.items():
        try:
            sections[key] = _call_internal(path, {**birth, "name": "D9" if key == "divisionalD9" else "D10", "width": 520, "height": 520, "theme": "light"})
        except Exception as e:
            sections[key] = {"error": str(e)[:200]}

    dosha = {}
    try:
        import asyncio as _asyncio
        stub = _stub_request()
        from .dosha_standalone import DoshaStandaloneRequest, manglik_detailed, grahan_dosha, shrapit_dosha
        dsb = DoshaStandaloneRequest(
            dateOfBirth=body.date, timeOfBirth=body.time,
            latitude=body.lat if body.lat is not None else _DEFAULT_PLACE["lat"],
            longitude=body.lon if body.lon is not None else _DEFAULT_PLACE["lon"],
            timezone=body.tz or _DEFAULT_PLACE["tz"],
        )
        dosha = {
            "manglik": _asyncio.run(manglik_detailed(dsb, stub)),
            "grahan": _asyncio.run(grahan_dosha(dsb, stub)),
            "shrapit": _asyncio.run(shrapit_dosha(dsb, stub)),
        }
    except Exception as e:
        dosha = {"error": str(e)[:200]}

    core = tenant_kundli_tool(body, slug=slug, domain=domain)
    return {"core": core, "doshas": dosha, **sections}
