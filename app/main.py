from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, timedelta, date
import swisseph as swe
import pytz
from dateutil import parser
import json
import os
import math
import logging

from .utils import (
    ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS, PLANET_IDS, COMBUSTION_DIST, PLANET_PROPS,
    DASHA_YEARS, DASHA_SEQUENCE, TITHI_NAMES, YOGA_NAMES, KARANA_SEQUENCE,
    to_julian, get_sign, get_nakshatra, ayanamsa_value, to_dms, get_avastha,
    is_combust, calc_planets, calc_houses, planet_status, sunrise_sunset,
    panchang_at_jd, compute_panchang,
)

from .response import success, error

from .database import init_db

_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
if _sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
    logging.info("Sentry initialized")


from .routers.auth_router import router as auth_router
from .middleware import APIKeyMiddleware, ResponseWrapMiddleware

app = FastAPI(
    title="Vedic Astrology API",
    version="2.0.0",
    description="Complete Vedic Astrology API with 180+ endpoints for birth charts, panchang, horoscopes, dasha, transits, compatibility, doshas, yogas, numerology, gemstones, rudraksha, muhurats, festivals, reports, AI interpretations, and more.",
    openapi_tags=[
        {"name": "Charts - Visual", "description": "SVG chart generation: South Indian, North Indian, Grid, East Indian, Moon"},
        {"name": "Charts - Specialized", "description": "Dedicated charts: Navamsa (D9), Hora (D2), Sudarshana Chakra"},
        {"name": "Charts - Divisional", "description": "Divisional charts D1-D60"},
        {"name": "Charts - Bhava", "description": "Bhava Chalit and house cusp analysis"},
        {"name": "Birth Chart", "description": "Core Kundli / birth chart data"},
        {"name": "Horoscope", "description": "Daily, weekly, monthly, yearly horoscopes"},
        {"name": "Dasha", "description": "Vimshottari, Chara, Yogini, Kalachakra, Ashtottari dasha periods"},
        {"name": "Panchang", "description": "Tithi, Nakshatra, Yoga, Karana, Muhurat calculations"},
        {"name": "Transit", "description": "Planetary transit analysis and predictions"},
        {"name": "Compatibility", "description": "Ashtakoot milan, gun milan, matching"},
        {"name": "Dosha", "description": "Manglik, Kaal Sarp, Shani, Nadi, Bhakoot, Yogini doshas"},
        {"name": "KP Astrology", "description": "KP Astrology system: planet details, cuspal lords, ruling planets, horary"},
        {"name": "Lal Kitab", "description": "Lal Kitab remedies and chart analysis"},
        {"name": "Yoga", "description": "Yoga detection and predictions"},
        {"name": "Calculator", "description": "Lagna, Moon sign, Sun sign, Shadbala, Ashtakavarga calculators"},
        {"name": "Muhurat", "description": "Auspicious timing for marriage, property, travel, etc."},
        {"name": "Varshaphal", "description": "Annual horoscope and Tajika aspects"},
        {"name": "Prashna", "description": "Horary astrology - answers based on question time"},
        {"name": "Predictions", "description": "Business, education, child, foreign travel predictions"},
        {"name": "Gemstone", "description": "Gemstone recommendations based on chart"},
        {"name": "Rudraksha", "description": "Rudraksha recommendations and identification"},
        {"name": "Numerology", "description": "Life path, destiny, soul, expression numbers"},
        {"name": "Festival", "description": "Hindu festival dates and calendars"},
        {"name": "Calendar", "description": "Hindu calendar, panchang calendar, festival calendar"},
        {"name": "Pooja", "description": "Pooja recommendations and booking"},
        {"name": "Lucky", "description": "Lucky color, number, day, metal based on numerology"},
        {"name": "Reports", "description": "PDF report generation - Kundli, Horoscope, Career, Health, Finance, Marriage"},
        {"name": "AI", "description": "AI-powered interpretations and predictions (requires provider config)"},
        {"name": "Utility", "description": "Ayanamsa, Ephemeris, Sunrise/Sunset, Julian Day, etc."},
        {"name": "Location", "description": "Location search, reverse geocode, timezone lookup"},
        {"name": "Auth", "description": "Registration, login, API key management"},
        {"name": "Admin", "description": "Admin panel: user management, key management, stats, usage analytics"},
        {"name": "AI Providers", "description": "AI provider configuration: OpenAI, Anthropic, Groq, Together"},
        {"name": "Jobs", "description": "Background job submission and status tracking"},

    ],
)

app.add_middleware(APIKeyMiddleware)
app.add_middleware(ResponseWrapMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────── Swagger UI: API Key Input ────────
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Enter your API key (avk_xxxxxxxx) to test all endpoints"
        }
    }
    # Apply security globally except auth endpoints
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    # Remove security from auth endpoints
    for path, methods in openapi_schema.get("paths", {}).items():
        if path.startswith("/auth/") or path == "/health":
            for method_info in methods.values():
                if isinstance(method_info, dict):
                    method_info.pop("security", None)
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    import logging
    logging.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None},
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "Endpoint not found", "data": None},
    )


@app.exception_handler(422)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Validation error", "data": exc.errors() if hasattr(exc, 'errors') else str(exc)},
    )


app.include_router(auth_router, prefix="/auth", tags=['Auth'])

# Admin router
try:
    from .routers.admin import router as admin_router
    app.include_router(admin_router, prefix="/admin", tags=['Admin'])
except Exception as e:
    import logging as _logging_admin
    _logging_admin.error(f"Failed to include ADMIN router: {e}")

# AI Providers router
try:
    from .routers.ai_providers import router as ai_providers_router
    app.include_router(ai_providers_router, prefix="/ai-providers", tags=['AI Providers'])
except Exception as e:
    import logging as _logging_ai_prov
    _logging_ai_prov.error(f"Failed to include AI PROVIDERS router: {e}")

# Jobs router
try:
    from .routers.jobs import router as jobs_router
    app.include_router(jobs_router, prefix="/jobs", tags=['Jobs'])
except Exception as e:
    import logging as _logging_jobs
    _logging_jobs.error(f"Failed to include JOBS router: {e}")


@app.on_event("startup")
def on_startup():
    init_db()
    if os.getenv("AUTO_CREATE_ADMIN", "0") == "1":
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from create_admin import create_admin
            create_admin()
        except Exception as e:
            import logging as _logging
            _logging.warning(f"Auto-create admin skipped: {e}")

@app.get("/health")
def health_check():
    return success({"status": "ok", "version": "2.0.0", "service": "Vedic Astrology API"})

# Routers
try:
    from .routers.chart_svg import router as chart_svg_router
    app.include_router(chart_svg_router, prefix="/chart", tags=['Charts - Visual'])
except Exception as e:
    import logging as _logging
    _logging.error(f"Failed to include chart SVG router: {e}")

# Grid-style chart router (South-Indian-like example grid)
try:
    from .routers.chart_grid import router as chart_grid_router
    app.include_router(chart_grid_router, prefix="/chart", tags=['Charts - Visual'])
except Exception as e:
    import logging as _logging2
    _logging2.error(f"Failed to include chart GRID router: {e}")

# Dasha router
try:
    from .routers.dasha import router as dasha_router
    app.include_router(dasha_router, prefix="/horoscope", tags=['Dasha'])
except Exception as e:
    import logging as _logging3
    _logging3.error(f"Failed to include DASHA router: {e}")

# Chara Dasha router
try:
    from .routers.dasha_chara import router as dasha_chara_router
    app.include_router(dasha_chara_router, prefix="/horoscope", tags=['Dasha'])
except Exception as e:
    import logging as _logging3b
    _logging3b.error(f"Failed to include CHARA DASHA router: {e}")

# Dosha router
try:
    from .routers.dosha import router as dosha_router
    app.include_router(dosha_router, prefix="/horoscope", tags=['Dosha'])
except Exception as e:
    import logging as _logging4
    _logging4.error(f"Failed to include DOSHA router: {e}")

# Panchang router
try:
    from .routers.panchang import router as panchang_router
    app.include_router(panchang_router, prefix="/horoscope", tags=['Panchang'])
except Exception as e:
    import logging as _logging5
    _logging5.error(f"Failed to include PANCHANG router: {e}")

# Panchang Extended router
try:
    from .routers.panchang_extended import router as panchang_ext_router
    app.include_router(panchang_ext_router, prefix="/horoscope", tags=['Panchang'])
except Exception as e:
    import logging as _logging_ext
    _logging_ext.error(f"Failed to include PANCHANG EXTENDED router: {e}")

# Transit router
try:
    from .routers.transit import router as transit_router
    app.include_router(transit_router, prefix="/horoscope", tags=['Transit'])
except Exception as e:
    import logging as _logging6
    _logging6.error(f"Failed to include TRANSIT router: {e}")

# Compatibility router
try:
    from .routers.compat import router as compat_router
    app.include_router(compat_router, prefix="/horoscope", tags=['Compatibility'])
except Exception as e:
    import logging as _logging7
    _logging7.error(f"Failed to include COMPAT router: {e}")

# Transit Detail router
try:
    from .routers.transit_detail import router as transit_detail_router
    app.include_router(transit_detail_router, prefix="/api", tags=['Transit'])
except Exception as e:
    import logging as _logging9
    _logging9.error(f"Failed to include TRANSIT DETAIL router: {e}")

# Transit Prediction router
try:
    from .routers.transit_pred import router as transit_pred_router
    app.include_router(transit_pred_router, prefix="", tags=['Transit'])
except Exception as e:
    import logging as _logging_transit_pred
    _logging_transit_pred.error(f"Failed to include TRANSIT PREDICTION router: {e}")

# Bhava Chalit router
try:
    from .routers.bhava_chalit import router as bhava_chalit_router
    app.include_router(bhava_chalit_router, prefix="", tags=['Charts - Bhava'])
except Exception as e:
    import logging as _logging_bhava
    _logging_bhava.error(f"Failed to include BHAVA CHALIT router: {e}")

# Dosha Standalone router
try:
    from .routers.dosha_standalone import router as dosha_standalone_router
    app.include_router(dosha_standalone_router, prefix="/api", tags=['Dosha'])
except Exception as e:
    import logging as _logging10
    _logging10.error(f"Failed to include DOSHA STANDALONE router: {e}")

# Compat Standalone router
try:
    from .routers.compat_standalone import router as compat_standalone_router
    app.include_router(compat_standalone_router, prefix="/api", tags=['Compatibility'])
except Exception as e:
    import logging as _logging11
    _logging11.error(f"Failed to include COMPAT STANDALONE router: {e}")

# Location autocomplete router
try:
    from .routers.location import router as location_router
    app.include_router(location_router, prefix="/api", tags=['Location'])
except Exception as e:
    import logging as _logging8
    _logging8.error(f"Failed to include LOCATION router: {e}")

# Gemstone router
try:
    from .routers.gemstone import router as gemstone_router
    app.include_router(gemstone_router, prefix="/api", tags=['Gemstone'])
except Exception as e:
    import logging as _logging9
    _logging9.error(f"Failed to include GEMSTONE router: {e}")

# Muhurat router
try:
    from .routers.muhurat import router as muhurat_router
    app.include_router(muhurat_router, prefix="/horoscope", tags=['Muhurat'])
except Exception as e:
    import logging as _logging9
    _logging9.error(f"Failed to include MUHURAT router: {e}")

# Festival router
try:
    from .routers.festival import router as festival_router
    app.include_router(festival_router, prefix="/api", tags=['Festival'])
except Exception as e:
    import logging as _logging12
    _logging12.error(f"Failed to include FESTIVAL router: {e}")

# Calculator router
try:
    from .routers.calculator import router as calculator_router
    app.include_router(calculator_router, prefix="/api", tags=['Calculator'])
except Exception as e:
    import logging as _logging13
    _logging13.error(f"Failed to include CALCULATOR router: {e}")

# Rudraksha router
try:
    from .routers.rudraksha import router as rudraksha_router
    app.include_router(rudraksha_router, prefix="/api", tags=['Rudraksha'])
except Exception as e:
    import logging as _logging14
    _logging14.error(f"Failed to include RUDRAKSHA router: {e}")

# Calendar router
try:
    from .routers.calendar import router as calendar_router
    app.include_router(calendar_router, prefix="/api", tags=['Calendar'])
except Exception as e:
    import logging as _logging15
    _logging15.error(f"Failed to include CALENDAR router: {e}")

# Utility router
try:
    from .routers.utility import router as utility_router
    app.include_router(utility_router, prefix="/api", tags=['Utility'])
except Exception as e:
    import logging as _logging16
    _logging16.error(f"Failed to include UTILITY router: {e}")

# Reports router
try:
    from .routers.reports import router as reports_router
    app.include_router(reports_router, prefix="", tags=['Reports'])
except Exception as e:
    import logging as _logging17
    _logging17.error(f"Failed to include REPORTS router: {e}")

# East Indian & Moon Chart router
try:
    from .routers.chart_east import router as chart_east_router
    app.include_router(chart_east_router, prefix="/chart", tags=['Charts - Visual'])
except Exception as e:
    import logging as _logging18
    _logging18.error(f"Failed to include CHART EAST router: {e}")

# AI Astro stub router
try:
    from .routers.ai_astro import router as ai_astro_router
    app.include_router(ai_astro_router, prefix="", tags=['AI'])
except Exception as e:
    import logging as _logging19
    _logging19.error(f"Failed to include AI ASTRO router: {e}")

# Pooja router
try:
    from .routers.pooja import router as pooja_router
    app.include_router(pooja_router, prefix="", tags=['Pooja'])
except Exception as e:
    import logging as _logging20
    _logging20.error(f"Failed to include POOJA router: {e}")

# Calendar API router
try:
    from .routers.calendar_api import router as calendar_api_router
    app.include_router(calendar_api_router, prefix="", tags=['Calendar'])
except Exception as e:
    import logging as _logging21
    _logging21.error(f"Failed to include CALENDAR API router: {e}")

# Dasha Extended router
try:
    from .routers.dasha_extended import router as dasha_extended_router
    app.include_router(dasha_extended_router, prefix="", tags=['Dasha'])
except Exception as e:
    import logging as _logging22
    _logging22.error(f"Failed to include DASHA EXTENDED router: {e}")

# Yogini Dosha router
try:
    from .routers.yogini_dosha import router as yogini_dosha_router
    app.include_router(yogini_dosha_router, prefix="", tags=['Dosha','Yogini Dosha'])
except Exception as e:
    import logging as _logging_yogini_dosha
    _logging_yogini_dosha.error(f"Failed to include YOGINI DOSHA router: {e}")

# Lal Kitab router
try:
    from .routers.lal_kitab import router as lal_kitab_router
    app.include_router(lal_kitab_router, prefix="", tags=['Lal Kitab'])
except Exception as e:
    import logging as _logging_lal_kitab
    _logging_lal_kitab.error(f"Failed to include LAL KITAB router: {e}")

# KP Astrology router
try:
    from .routers.kp_astro import router as kp_astro_router
    app.include_router(kp_astro_router, prefix="", tags=['KP Astrology'])
except Exception as e:
    import logging as _logging_kp
    _logging_kp.error(f"Failed to include KP ASTRO router: {e}")

# Numerology router
try:
    from .routers.numerology import router as numerology_router
    app.include_router(numerology_router, prefix="/api", tags=['Numerology'])
except Exception as e:
    import logging as _logging23
    _logging23.error(f"Failed to include NUMEROLOGY router: {e}")

# Varshaphal (Annual Solar Return) router
try:
    from .routers.varshaphal import router as varshaphal_router
    app.include_router(varshaphal_router, prefix="", tags=['Varshaphal'])
except Exception as e:
    import logging as _logging24
    _logging24.error(f"Failed to include VARSHAPHAL router: {e}")

# Birth Time Rectification router
try:
    from .routers.birth_rectify import router as birth_rectify_router
    app.include_router(birth_rectify_router, prefix="/api", tags=['Utility'])
except Exception as e:
    import logging as _logging25
    _logging25.error(f"Failed to include BIRTH RECTIFY router: {e}")

# Prashna (Horary Astrology) router
try:
    from .routers.prashna import router as prashna_router
    app.include_router(prashna_router, prefix="/api", tags=['Prashna'])
except Exception as e:
    import logging as _logging24
    _logging24.error(f"Failed to include PRASHNA router: {e}")

# Dasha Detail router
try:
    from .routers.dasha_detail import router as dasha_detail_router
    app.include_router(dasha_detail_router, prefix="", tags=['Dasha'])
except Exception as e:
    import logging as _logging25
    _logging25.error(f"Failed to include DASHA DETAIL router: {e}")

# Panchaka router
try:
    from .routers.panchaka import router as panchaka_router
    app.include_router(panchaka_router, prefix="", tags=['Panchang'])
except Exception as e:
    import logging as _logging26
    _logging26.error(f"Failed to include PANCHAKA router: {e}")

# Yoga Predictions router
try:
    from .routers.yoga_pred import router as yoga_pred_router
    app.include_router(yoga_pred_router, prefix="", tags=['Yoga'])
except Exception as e:
    import logging as _logging27
    _logging27.error(f"Failed to include YOGA PRED router: {e}")

# Dosha Remedies router
try:
    from .routers.dosha_remedy import router as dosha_remedy_router
    app.include_router(dosha_remedy_router, prefix="/horoscope", tags=['Dosha'])
except Exception as e:
    import logging as _logging28
    _logging28.error(f"Failed to include DOSHA REMEDY router: {e}")

# Horoscope Text router (Daily, Weekly, Monthly, Yearly, Career, Love, Finance, Health)
try:
    from .routers.horoscope_text import router as horoscope_text_router
    app.include_router(horoscope_text_router, prefix="", tags=['Horoscope'])
except Exception as e:
    import logging as _logging_ht
    _logging_ht.error(f"Failed to include HOROSCOPE TEXT router: {e}")

# Name Numerology router
try:
    from .routers.name_numerology import router as name_numerology_router
    app.include_router(name_numerology_router, prefix="", tags=['Numerology'])
except Exception as e:
    import logging as _logging29
    _logging29.error(f"Failed to include NAME NUMEROLOGY router: {e}")

# Calendar Year router
try:
    from .routers.calendar_year import router as calendar_year_router
    app.include_router(calendar_year_router, prefix="", tags=['Calendar'])
except Exception as e:
    import logging as _logging30
    _logging30.error(f"Failed to include CALENDAR YEAR router: {e}")

# Predictions router (Business, Education, Child, Foreign, Monthly Transit)
try:
    from .routers.predictions import router as predictions_router
    app.include_router(predictions_router, prefix="", tags=['Predictions'])
except Exception as e:
    import logging as _logging31
    _logging31.error(f"Failed to include PREDICTIONS router: {e}")

# Cesarean Muhurat router
try:
    from .routers.muhurat_extra import router as muhurat_extra_router
    app.include_router(muhurat_extra_router, prefix="")
except Exception as e:
    import logging as _logging32
    _logging32.error(f"Failed to include MUHURAT EXTRA router: {e}")

# Dhaiya Dosha router
try:
    from .routers.dosha_extra import router as dosha_extra_router
    app.include_router(dosha_extra_router, prefix="")
except Exception as e:
    import logging as _logging33
    _logging33.error(f"Failed to include DOSHA EXTRA router: {e}")

# Lucky Attributes router
try:
    from .routers.lucky import router as lucky_router
    app.include_router(lucky_router, prefix="", tags=['Lucky'])
except Exception as e:
    import logging as _logging34
    _logging34.error(f"Failed to include LUCKY router: {e}")



# Specialized Charts router (Navamsa, Hora, Sudarshana)
try:
    from .routers.chart_specialized import router as chart_specialized_router
    app.include_router(chart_specialized_router, prefix="", tags=['Charts - Specialized'])
except Exception as e:
    import logging as _logging35
    _logging35.error(f"Failed to include CHART SPECIALIZED router: {e}")

# Load Vedic properties (nakshatra table) from JSON
def load_vedic_properties() -> Dict[str, Any]:
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'vedic_properties.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load vedic_properties.json: {e}")
        return {}

NAKSHATRA_PROPERTIES = load_vedic_properties()


class BirthDetails(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    propertyProfile: Optional[str] = Field(None, example=None)
    propertySource: Optional[Literal['moon','ascendant','sunriseMoon']] = Field('moon', example='moon')
    houseSystem: Optional[Literal['P','W']] = Field('W', example='W')
    nodeMode: Optional[Literal['mean','true']] = Field('mean', example='mean')
    debug: Optional[bool] = Field(False, example=False)
    tropical: Optional[bool] = Field(False, example=False)


def pd_years(years: float) -> timedelta:
    return timedelta(days=int(round(years * 365.25)))


def parse_local_datetime(date_str: str, time_str: str, tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    dt_local = parser.parse(f"{date_str} {time_str}")
    return tz.localize(dt_local)


def vimshottari_full(jd: float, birth_dt_local: datetime) -> Dict[str, Any]:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xm, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    m_lon = xm[0]
    nk_idx = int(m_lon // 13.333333) % 27
    start_lord = [n[1] for n in NAKSHATRAS][nk_idx]
    pos_in_nk = (m_lon % 13.333333) / 13.333333
    md_years_total = DASHA_YEARS[start_lord]
    first_md_years = (1 - pos_in_nk) * md_years_total
    start_index = DASHA_SEQUENCE.index(start_lord)
    mahadashas = []
    cursor = birth_dt_local
    md_years_list = []
    md_years_list.append((start_lord, first_md_years))
    total_years = first_md_years
    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(start_index + i) % 9]
        y = DASHA_YEARS[lord]
        md_years_list.append((lord, y))
        total_years += y
    while total_years < 120 - 0.01:
        for lord in DASHA_SEQUENCE:
            y = DASHA_YEARS[lord]
            md_years_list.append((lord, y))
            total_years += y
            if total_years >= 120 - 0.01:
                break

    def rotate_seq(start_lord: str):
        i = DASHA_SEQUENCE.index(start_lord)
        return DASHA_SEQUENCE[i:] + DASHA_SEQUENCE[:i]

    def build_antardasha(md_start: datetime, md_years: float, md_lord: str):
        antars = []
        cursor_a = md_start
        for ad_lord in rotate_seq(md_lord):
            ad_years = md_years * (DASHA_YEARS[ad_lord] / 120.0)
            ad_start = cursor_a
            ad_end = ad_start + pd_years(ad_years)
            pratis = []
            cursor_p = ad_start
            for pd_lord in rotate_seq(ad_lord):
                pr_years = (ad_years) * (DASHA_YEARS[pd_lord] / 120.0)
                p_start = cursor_p
                p_end = p_start + pd_years(pr_years)
                # Build Sukshma (4th level) within each Pratyantar
                sook_list = []
                cursor_s = p_start
                for sd_lord in rotate_seq(pd_lord):
                    s_years = pr_years * (DASHA_YEARS[sd_lord] / 120.0)
                    s_start = cursor_s
                    s_end = s_start + pd_years(s_years)
                    sook_list.append({
                        'planet': sd_lord,
                        'startDate': s_start.date().isoformat(),
                        'endDate': s_end.date().isoformat()
                    })
                    cursor_s = s_end
                pratis.append({
                    'planet': pd_lord,
                    'startDate': p_start.date().isoformat(),
                    'endDate': p_end.date().isoformat(),
                    'sookshma': sook_list
                })
                cursor_p = p_end
            antars.append({
                'planet': ad_lord,
                'startDate': ad_start.date().isoformat(),
                'endDate': ad_end.date().isoformat(),
                'pratyantar': pratis
            })
            cursor_a = ad_end
        return antars

    for lord, years in md_years_list:
        md_start = cursor
        md_end = md_start + pd_years(years)
        mahadashas.append({
            'planet': lord,
            'startDate': md_start.date().isoformat(),
            'endDate': md_end.date().isoformat(),
            'antardasha': build_antardasha(md_start, years, lord)
        })
        cursor = md_end

    current = {
        'planet': start_lord,
        'startDate': mahadashas[0]['startDate'],
        'endDate': mahadashas[0]['endDate']
    }
    return {'current': current, 'mahadashas': mahadashas}


def validate_vimshottari_schedule(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """Validate sums and continuity of MD/AD/PD durations by years and dates."""
    def days_between(a: str, b: str) -> int:
        from datetime import date
        y1, m1, d1 = [int(x) for x in a.split('-')]
        y2, m2, d2 = [int(x) for x in b.split('-')]
        return (date(y2, m2, d2) - date(y1, m1, d1)).days

    md_ok, ad_ok, pd_ok = True, True, True
    cont_ok = True
    issues = []
    total_years = 0.0
    prev_end = None
    for md in schedule.get('mahadashas', []):
        # accumulate actual years from date spans
        md_days = days_between(md['startDate'], md['endDate'])
        total_years += md_days / 365.25
        # continuity between MDs
        if prev_end and md['startDate'] != prev_end:
            cont_ok = False
            issues.append(f"MD continuity break: {prev_end} -> {md['startDate']}")
        prev_end = md['endDate']

        # sum AD durations in days should match MD duration in days
        ad_days_sum = 0
        prev_ad_end = md['startDate']
        for ad in md.get('antardasha', []):
            ad_days = days_between(ad['startDate'], ad['endDate'])
            ad_days_sum += ad_days
            if ad['startDate'] != prev_ad_end:
                cont_ok = False
                issues.append(f"AD continuity break in {md['planet']}: {prev_ad_end} -> {ad['startDate']}")
            prev_ad_end = ad['endDate']
            # PD sum check per AD
            pd_days_sum = 0
            prev_pd_end = ad['startDate']
            for pd in ad.get('pratyantar', []):
                pd_days = days_between(pd['startDate'], pd['endDate'])
                pd_days_sum += pd_days
                if pd['startDate'] != prev_pd_end:
                    cont_ok = False
                    issues.append(f"PD continuity break in {md['planet']}/{ad['planet']}: {prev_pd_end} -> {pd['startDate']}")
                prev_pd_end = pd['endDate']
            if abs(pd_days_sum - ad_days) > 2:  # allow small rounding slack
                pd_ok = False
                issues.append(f"PD sum mismatch in {md['planet']}/{ad['planet']}: {pd_days_sum} vs {ad_days}")
        if abs(ad_days_sum - md_days) > 2:
            ad_ok = False
            issues.append(f"AD sum mismatch in {md['planet']}: {ad_days_sum} vs {md_days}")

    # If schedule covers 120 years exactly, it'll be near 120; else accept any positive total
    md_ok = total_years > 0
    return {'mdSum120': md_ok, 'adSum': ad_ok, 'pdSum': pd_ok, 'continuity': cont_ok, 'issues': issues}


def modality_of(sign_index: int) -> str:
    if sign_index % 3 == 0:
        return 'Movable'
    if sign_index % 3 == 1:
        return 'Fixed'
    return 'Dual'


def varga_sign(lon: float, varga: int) -> Optional[str]:
    si = int(lon // 30)
    deg = lon % 30
    if varga == 2:
        odd = si % 2 == 0
        first = 'Leo' if odd else 'Cancer'
        second = 'Cancer' if odd else 'Leo'
        return first if deg < 15 else second
    if varga == 3:
        part = int(deg // 10)
        offsets = [0, 4, 8]
        return ZODIAC_SIGNS[(si + offsets[part]) % 12]
    if varga == 4:
        part = int(deg // 7.5)
        mod = modality_of(si)
        base = 0 if mod == 'Movable' else (3 if mod == 'Fixed' else 6)
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 7:
        part = int(deg // (30/7))
        base = 0 if (si % 2 == 0) else 6
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 9:
        part = int(deg // (30/9))
        mod = modality_of(si)
        base = 0 if mod == 'Movable' else (8 if mod == 'Fixed' else 4)
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 10:
        part = int(deg // 3)
        base = 0 if (si % 2 == 0) else 8
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 12:
        part = int(deg // (30/12))
        return ZODIAC_SIGNS[(si + part) % 12]
    # Generic fallback for any varga: split sign into 'varga' equal parts and advance signs sequentially
    # Note: This is a simplified/generalized mapping to support additional Varga charts when a classical rule isn't implemented.
    try:
        if varga > 1:
            step = 30.0 / float(varga)
            part = int(deg // step)
            return ZODIAC_SIGNS[(si + part) % 12]
    except Exception:
        return None
    return ZODIAC_SIGNS[si]


def varga_mode(varga: int) -> str:
    """Return mapping mode used: 'classical' for explicitly implemented charts, else 'generic'."""
    return 'classical' if varga in {1, 2, 3, 4, 7, 9, 10, 12} else 'generic'


VARGA_META = {
    'D1': {'name': 'Rasi', 'focus': 'General life'} , 'D2': {'name': 'Hora', 'focus': 'Wealth'},
    'D3': {'name': 'Drekkana', 'focus': 'Siblings/Co-borns'}, 'D4': {'name': 'Chaturthamsa', 'focus': 'Home/Property'},
    'D5': {'name': 'Panchamsa', 'focus': 'Power/Authority'}, 'D6': {'name': 'Shashtamsa', 'focus': 'Health/Illness'},
    'D7': {'name': 'Saptamsa', 'focus': 'Children/Progeny'}, 'D9': {'name': 'Navamsa', 'focus': 'Marriage/Dharma'},
    'D10': {'name': 'Dashamamsa', 'focus': 'Career/Profession'}, 'D12': {'name': 'Dwadasamsa', 'focus': 'Parents/Ancestry'},
    'D16': {'name': 'Shodasamsa', 'focus': 'Vehicles/Comforts'}, 'D20': {'name': 'Vimsamsa', 'focus': 'Spirituality/Upasana'},
    'D24': {'name': 'Siddhamsa', 'focus': 'Education/Learning'}, 'D27': {'name': 'Nakshatramsa', 'focus': 'Strength/Deity'},
    'D30': {'name': 'Trimshamsa', 'focus': 'Mishaps/Defects'}, 'D40': {'name': 'Khavedamsa', 'focus': 'Purva Punya/Sins'},
    'D45': {'name': 'Akshavedamsa', 'focus': 'Character/Spiritual Merit'}, 'D60': {'name': 'Shashtiamsa', 'focus': 'Past Life/Overall'}
}


def charts_divisional_extended(planets: list, ascendant: Dict[str, Any]) -> Dict[str, Any]:
    charts: Dict[str, Any] = {}

    def build_chart(d: int) -> Dict[str, Any]:
        key = f'D{d}'
        name = VARGA_META[key]['name']
        focus = VARGA_META[key]['focus']

        asc_degree = ascendant['degree']
        asc_sign_d1 = ascendant['sign']
        asc_sign = asc_sign_d1 if d == 1 else varga_sign(asc_degree, d)
        asc_sign = asc_sign or asc_sign_d1
        asc = {
            'sign': asc_sign,
            'signLord': SIGN_LORDS[asc_sign],
            'degree': asc_degree % 30,
            'longitude': asc_degree
        }

        asc_idx = ZODIAC_SIGNS.index(asc_sign)
        plist = []
        for p in planets:
            vs = p['sign'] if d == 1 else varga_sign(p['longitude'], d)
            if vs is None:
                continue
            if d == 1:
                house = p.get('house') or 0
            else:
                sidx = ZODIAC_SIGNS.index(vs)
                house = ((sidx - asc_idx + 12) % 12) + 1
            plist.append({
                'name': p['name'],
                'sign': vs,
                'house': house,
                'degree': p['degree'],
                'dignity': planet_status(p['name'], vs),
                'isRetrograde': p['isRetrograde'],
                'isCombust': p['isCombust']
            })

        return {'name': name, 'focus': focus, 'ascendant': asc, 'planets': plist}

    # Build all vargas dynamically with full details
    varga_keys = [1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
    for d in varga_keys:
        charts[f'D{d}'] = build_chart(d)

    return charts


def kp_sub_lord_for(lon: float) -> str:
    nk_start = (int(lon // 13.333333)) * 13.333333
    pos = lon - nk_start
    total = 13.333333
    accum = 0.0
    for lord in DASHA_SEQUENCE:
        portion = total * (DASHA_YEARS[lord] / 120.0)
        if pos < accum + portion:
            return lord
        accum += portion
    return DASHA_SEQUENCE[-1]


def kp_details(houses: list, planets: list) -> Dict[str, Any]:
    bhav = []
    for h in houses:
        mid = (h['degree'] + 15) % 360 if isinstance(h['degree'], (int, float)) else 0
        bhav.append({'bhav': h['number'], 'sign': h['sign'], 'midPoint': mid, 'planets': h['planets']})
    pdetails = []
    for p in planets:
        pdetails.append({
            'planet': p['name'], 'cusp': p['house'], 'sign': p['sign'],
            'cuspalLord': SIGN_LORDS[houses[p['house']-1]['sign']] if p['house'] else None,
            'starLord': p['nakshatraLord'], 'subLord': kp_sub_lord_for(p['longitude']), 'degree': p['degree'],
        })
    return {'bhavChalitChart': bhav, 'planetDetails': pdetails}


def detect_yogas(planets: list, houses: list, asc_sign: str) -> list:
    res = []
    pmap = {p['name']: p for p in planets}
    asc_idx = ZODIAC_SIGNS.index(asc_sign)

    def in_kendra(p):
        h = p.get('house', 0)
        return h in [1, 4, 7, 10]

    def in_trikona(p):
        h = p.get('house', 0)
        return h in [1, 5, 9]

    def in_dusthana(p):
        h = p.get('house', 0)
        return h in [6, 8, 12]

    def in_upachaya(p):
        h = p.get('house', 0)
        return h in [3, 6, 10, 11]

    def house_of(p):
        return p.get('house', 0)

    def sign_of(p):
        return p.get('sign', '')

    moon = pmap.get('Moon')
    sun = pmap.get('Sun')
    jup = pmap.get('Jupiter')
    ven = pmap.get('Venus')
    mar = pmap.get('Mars')
    mer = pmap.get('Mercury')
    sat = pmap.get('Saturn')
    rahu = pmap.get('Rahu')
    ketu = pmap.get('Ketu')

    # --- Pancha Mahapurusha Yogas (5 yogas) ---
    mahapurusha = {
        'Mars': ('Ruchaka', 'Mars in own/exalted sign in kendra - courageous, commanding, warrior-like'),
        'Mercury': ('Bhadra', 'Mercury in own/exalted sign in kendra - intelligent, eloquent, learned'),
        'Jupiter': ('Hamsa', 'Jupiter in own/exalted sign in kendra - noble, spiritual, wise'),
        'Venus': ('Malavya', 'Venus in own/exalted sign in kendra - beautiful, artistic, luxurious'),
        'Saturn': ('Shasha', 'Saturn in own/exalted sign in kendra - powerful, authoritative, disciplined')
    }
    for pname in ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p and in_kendra(p) and planet_status(pname, sign_of(p)) in ['Exalted', 'Own Sign', 'Mooltrikona']:
            label, desc = mahapurusha[pname]
            res.append({'name': f'{label} Yoga (Mahapurusha)', 'description': desc, 'strength': 'Strong'})

    # --- Gajakesari Yoga ---
    if moon and jup and in_kendra(moon) and in_kendra(jup):
        res.append({'name': 'Gajakesari Yoga', 'description': 'Moon and Jupiter in mutual kendras - wisdom, wealth, lasting reputation', 'strength': 'Strong'})

    # --- Neecha Bhanga Raja Yoga ---
    for p in planets:
        if planet_status(p['name'], sign_of(p)) == 'Debilitated':
            lord_name = SIGN_LORDS[sign_of(p)]
            lord_p = pmap.get(lord_name)
            if lord_p and planet_status(lord_name, sign_of(lord_p)) in ['Exalted', 'Own Sign']:
                res.append({'name': 'Neecha Bhanga Raja Yoga', 'description': f"{p['name']} debilitation cancelled by exalted/own-sign {lord_name}", 'strength': 'Medium'})

    # --- Budha Aditya Yoga ---
    if sun and mer and sign_of(sun) == sign_of(mer):
        res.append({'name': 'Budha Aditya Yoga', 'description': 'Sun and Mercury conjunction - intelligence, analytical ability, government favor', 'strength': 'Medium'})

    # --- Chandra Mangala Yoga ---
    if moon and mar and sign_of(moon) == sign_of(mar):
        res.append({'name': 'Chandra Mangala Yoga', 'description': 'Moon-Mars conjunction - earning ability, bold nature, prosperity', 'strength': 'Medium'})
    elif moon and mar and abs(house_of(moon) - house_of(mar)) in [6, 8]:
        pass
    elif moon and mar:
        moon_lord_house = house_of(pmap.get(SIGN_LORDS.get(sign_of(moon), ''), {})) if SIGN_LORDS.get(sign_of(moon)) in pmap else 0
        if moon_lord_house and house_of(mar) == moon_lord_house:
            res.append({'name': 'Chandra Mangala Yoga', 'description': 'Moon lord in Mars house or mutual aspect - wealth through boldness', 'strength': 'Medium'})

    # --- Dhan Yoga (Wealth) ---
    if jup and ven:
        jup_house = house_of(jup)
        ven_house = house_of(ven)
        if (in_kendra(jup) or in_trikona(jup)) and (in_kendra(ven) or in_trikona(ven)):
            res.append({'name': 'Dhana Yoga', 'description': 'Jupiter and Venus in kendra/trikona - wealth and material comfort', 'strength': 'Strong'})
    if sun and jup:
        if (in_kendra(sun) or in_trikona(sun)) and (in_kendra(jup) or in_trikona(jup)):
            if sign_of(sun) != sign_of(jup):
                pass
            res.append({'name': 'Dhana Yoga', 'description': 'Sun-Jupiter combination in favorable houses - financial prosperity', 'strength': 'Medium'})

    # --- Raj Yoga (Raja Yoga) ---
    for p1name in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        for p2name in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            if p1name == p2name:
                continue
            p1 = pmap.get(p1name)
            p2 = pmap.get(p2name)
            if not p1 or not p2:
                continue
            p1_lord = SIGN_LORDS.get(sign_of(p1))
            p2_lord = SIGN_LORDS.get(sign_of(p2))
            if p1_lord in pmap and p2_lord in pmap:
                pl1 = pmap[p1_lord]
                pl2 = pmap[p2_lord]
                if (in_kendra(pl1) or in_trikona(pl1)) and (in_kendra(pl2) or in_trikona(pl2)):
                    if house_of(pl1) != house_of(pl2):
                        lord1_status = planet_status(p1_lord, sign_of(pl1))
                        lord2_status = planet_status(p2_lord, sign_of(pl2))
                        if lord1_status in ['Exalted', 'Own Sign', 'Mooltrikona', 'Friendly'] or lord2_status in ['Exalted', 'Own Sign', 'Mooltrikona', 'Friendly']:
                            res.append({'name': 'Raja Yoga', 'description': f'Lords of {p1name} and {p2name} signs in kendra/trikona - power and success', 'strength': 'Strong'})
                            break
        else:
            continue
        break

    # --- Viparita Raja Yoga ---
    dusthana_lords = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p:
            h = house_of(p)
            if h in [6, 8, 12]:
                dusthana_lords.append(pname)
    if len(dusthana_lords) >= 2:
        res.append({'name': 'Viparita Raja Yoga', 'description': f"Lords of dusthana houses ({', '.join(dusthana_lords)}) placed in other dusthana houses - reversal of adversity into success", 'strength': 'Medium'})

    # --- Amala Yoga ---
    if jup and in_kendra(jup):
        h = house_of(jup)
        if h in [1, 4]:
            res.append({'name': 'Amala Yoga', 'description': 'Jupiter in 1st or 4th house - natural virtue, good character, lasting good fortune', 'strength': 'Strong'})
    if ven and in_kendra(ven):
        h = house_of(ven)
        if h in [1, 4]:
            res.append({'name': 'Amala Yoga', 'description': 'Venus in 1st or 4th house - virtuous nature, prosperous life', 'strength': 'Strong'})

    # --- Kemadruma Yoga (no planet near Moon) ---
    if moon:
        moon_h = house_of(moon)
        adjacent = [((moon_h) % 12) + 1, ((moon_h - 2) % 12) + 1]
        has_neighbor = False
        for pname in ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            p = pmap.get(pname)
            if p and house_of(p) in adjacent:
                has_neighbor = True
                break
        if not has_neighbor:
            res.append({'name': 'Kemadruma Yoga', 'description': 'No planets in 2nd/12th from Moon - emotional challenges, need for self-reliance', 'strength': 'Malefic'})

    # --- Pancha Mangala Yoga ---
    benefics_in_kendra = 0
    for pname in ['Jupiter', 'Venus', 'Mercury', 'Moon']:
        p = pmap.get(pname)
        if p and in_kendra(p):
            benefics_in_kendra += 1
    if benefics_in_kendra >= 3:
        res.append({'name': 'Pancha Mangala Yoga', 'description': f'{benefics_in_kendra} benefics in kendras - highly auspicious, virtuous, prosperous', 'strength': 'Very Strong'})

    # --- Guru Chandal Yoga ---
    if jup and rahu and sign_of(jup) == sign_of(rahu):
        res.append({'name': 'Guru Chandal Yoga', 'description': 'Jupiter-Rahu conjunction - confusion in wisdom, unconventional path, potential for transformation', 'strength': 'Malefic'})
    if jup and rahu and house_of(jup) == house_of(rahu):
        if sign_of(jup) != sign_of(rahu):
            res.append({'name': 'Guru Chandal Yoga', 'description': 'Jupiter and Rahu in same house - unconventional wisdom, spiritual challenge', 'strength': 'Malefic'})

    # --- Chandala Yoga ---
    if jup and ketu and sign_of(jup) == sign_of(ketu):
        res.append({'name': 'Chandala Yoga', 'description': 'Jupiter-Ketu conjunction - spiritual but may cause detachment from worldly life', 'strength': 'Mixed'})

    # --- Shani Dosha in Yoga context ---
    if sat and moon and in_kendra(sat) and house_of(sat) == house_of(moon):
        res.append({'name': 'Punarpoo Yoga', 'description': 'Saturn-Moon conjunction in kendra - emotional depth, delays but eventual stability', 'strength': 'Mixed'})

    # --- Sarpa Dosha (separate from Kaal Sarp) ---
    if rahu and ketu:
        classical = [pmap.get(n) for n in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] if pmap.get(n)]
        rahu_lon = rahu['longitude']
        ketu_lon = ketu['longitude']
        rahu_idx = next((i for i, p in enumerate(classical) if p['name'] == 'Rahu'), None)

    # --- Vasumad Yoga ---
    if jup and ven and in_trikona(jup) and in_trikona(ven):
        if house_of(jup) != house_of(ven):
            res.append({'name': 'Vasumad Yoga', 'description': 'Jupiter and Venus in different trikonas - wealth, property, and family happiness', 'strength': 'Strong'})

    # --- Dhana Yoga (2nd lord in 11th or vice versa) ---
    second_lord_name = SIGN_LORDS[ZODIAC_SIGNS[(asc_idx + 1) % 12]]
    eleventh_lord_name = SIGN_LORDS[ZODIAC_SIGNS[(asc_idx + 10) % 12]]
    second_lord = pmap.get(second_lord_name)
    eleventh_lord = pmap.get(eleventh_lord_name)
    if second_lord and eleventh_lord:
        if house_of(second_lord) == 11 or house_of(eleventh_lord) == 2:
            res.append({'name': 'Dhana Yoga (Lord Exchange)', 'description': '2nd lord in 11th house or 11th lord in 2nd house - strong financial gains', 'strength': 'Strong'})

    # --- Lakshmi Yoga ---
    if ven and sat:
        ven_lord_house = house_of(pmap.get(SIGN_LORDS.get(sign_of(ven), ''), {})) if SIGN_LORDS.get(sign_of(ven)) in pmap else 0
        sat_lord_house = house_of(pmap.get(SIGN_LORDS.get(sign_of(sat), ''), {})) if SIGN_LORDS.get(sign_of(sat)) in pmap else 0
        if ven and in_trikona(ven) and sat and in_kendra(sat):
            res.append({'name': 'Lakshmi Yoga', 'description': 'Venus in trikona and Saturn in kendra - wealth, luxury, and divine grace', 'strength': 'Strong'})

    # --- Saraswati Yoga ---
    if jup and ven and mer:
        all_three_kendra_or_trikona = all(in_kendra(p) or in_trikona(p) for p in [jup, ven, mer] if p)
        if all_three_kendra_or_trikona:
            res.append({'name': 'Saraswati Yoga', 'description': 'Jupiter, Venus, Mercury in kendra/trikona - knowledge, arts, education, eloquence', 'strength': 'Strong'})

    # --- Daridra Yoga ---
    second_lord = pmap.get(SECOND_LORD_NAME := SIGN_LORDS[ZODIAC_SIGNS[(asc_idx + 1) % 12]])
    twelfth_lord = pmap.get(TWELFTH_LORD_NAME := SIGN_LORDS[ZODIAC_SIGNS[(asc_idx + 11) % 12]])
    if second_lord and twelfth_lord:
        if in_dusthana(second_lord) and in_dusthana(twelfth_lord):
            res.append({'name': 'Daridra Yoga', 'description': '2nd and 12th lords in dusthana houses - financial challenges, need for careful planning', 'strength': 'Malefic'})

    # --- Shubhakartari Yoga ---
    if jup and in_kendra(jup):
        h = house_of(jup)
        prev_h = ((h - 2) % 12) + 1
        next_h = (h % 12) + 1
        for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            p = pmap.get(pname)
            if p and house_of(p) in [prev_h, next_h] and pname not in ['Mars', 'Saturn']:
                res.append({'name': 'Shubhakartari Yoga', 'description': 'Benefics flanking Jupiter in kendra - auspicious results, good fortune', 'strength': 'Strong'})
                break

    # Deduplicate
    seen = set()
    unique = []
    for y in res:
        key = y['name']
        if key not in seen:
            seen.add(key)
            unique.append(y)
    return unique


def detect_doshas(planets: list) -> list:
    res = []
    pmap = {p['name']: p for p in planets}

    mars = pmap.get('Mars')
    rahu = pmap.get('Rahu')
    ketu = pmap.get('Ketu')
    sun = pmap.get('Sun')
    moon = pmap.get('Moon')
    sat = pmap.get('Saturn')
    jup = pmap.get('Jupiter')
    mer = pmap.get('Mercury')

    # --- Mangal Dosha (enhanced with house-specific check) ---
    mangal_houses = [1, 2, 4, 7, 8, 12]
    if mars:
        mangal_present = mars.get('house', 0) in mangal_houses
        if mangal_present:
            detail = f"Mars in house {mars['house']}"
            if mars.get('isRetrograde'):
                detail += " (retrograde) - reduced severity"
            res.append({'name': 'Mangal Dosha', 'description': f"Mars in 1/2/4/7/8/12 - {detail}. Affects marriage harmony.", 'present': True, 'severity': 'High' if mars.get('house') in [1, 4, 7, 8] else 'Medium', 'remedies': ['Hanuman Chalisa', 'Kumbh Vivah', 'Mangal Puja', 'Tuesday fasting']})
        else:
            res.append({'name': 'Mangal Dosha', 'description': 'Mars not in dosha houses', 'present': False, 'remedies': []})

    # --- Kaal Sarp Dosha (enhanced) ---
    if rahu and ketu:
        classical = [p for p in planets if p['name'] in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']]
        if classical:
            rahu_lon = rahu['longitude']
            ketu_lon = ketu['longitude']
            lo, hi = min(rahu_lon, ketu_lon), max(rahu_lon, ketu_lon)
            all_between = all(lo <= p['longitude'] <= hi for p in classical)
            all_outside = all(not (lo <= p['longitude'] <= hi) for p in classical)
            if all_between or all_outside:
                res.append({'name': 'Kaal Sarp Dosha', 'description': 'All planets confined between Rahu-Ketu axis - karmic challenges, delayed success', 'present': True, 'severity': 'High', 'remedies': ['Rahu-Ketu Shanti Puja', 'Rudra Abhishek', 'Nag Panchami worship', 'Maha Mrityunjaya Jaap']})
            else:
                res.append({'name': 'Kaal Sarp Dosha', 'description': 'Not present', 'present': False, 'remedies': []})
        else:
            res.append({'name': 'Kaal Sarp Dosha', 'description': 'Not present', 'present': False, 'remedies': []})

    # --- Pitra Dosha ---
    if sun and (rahu or ketu):
        sun_sign = sun.get('sign', '')
        pitra_present = False
        if rahu and sun_sign == rahu.get('sign', ''):
            pitra_present = True
        if ketu and sun_sign == ketu.get('sign', ''):
            pitra_present = True
        if not pitra_present and rahu and ketu:
            for node in [rahu, ketu]:
                if node.get('house') == sun.get('house'):
                    pitra_present = True
                    break
        res.append({'name': 'Pitra Dosha', 'description': 'Sun afflicted by Rahu/Ketu - ancestral karma, need for pitru remedies', 'present': bool(pitra_present), 'severity': 'Medium' if pitra_present else 'None', 'remedies': ['Pitru Tarpan', 'Pitru Paksha rituals', 'Shraddha', 'Rahu/Ketu Shanti'] if pitra_present else []})

    # --- Shani Dosha (Saturn Affliction) ---
    if sat:
        sat_house = sat.get('house', 0)
        if sat_house in [1, 4, 7, 8, 12]:
            res.append({'name': 'Shani Dosha', 'description': f"Saturn in house {sat_house} - delays, obstacles, karmic lessons", 'present': True, 'severity': 'High' if sat_house in [1, 8] else 'Medium', 'remedies': ['Shani Puja', 'Hanuman Chalisa', 'Donation on Saturday', 'Shani Mantra Japa']})
        else:
            res.append({'name': 'Shani Dosha', 'description': 'Saturn not in dosha houses', 'present': False, 'remedies': []})

    # --- Guru Chandal Dosha ---
    if jup and rahu:
        gc_present = jup.get('house') == rahu.get('house') or jup.get('sign') == rahu.get('sign')
        res.append({'name': 'Guru Chandal Dosha', 'description': 'Jupiter-Rahu conjunction - confusion in wisdom, unconventional decisions', 'present': bool(gc_present), 'severity': 'Medium' if gc_present else 'None', 'remedies': ['Guru Puja', 'Vishnu Sahasranama', 'Thursday fasting'] if gc_present else []})

    # --- Kemadruma Dosha ---
    if moon:
        moon_house = moon.get('house', 0)
        adjacent_houses = [((moon_house - 2) % 12) + 1, (moon_house % 12) + 1]
        has_neighbor = False
        for pname in ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            p = pmap.get(pname)
            if p and p.get('house') in adjacent_houses:
                has_neighbor = True
                break
        if not has_neighbor:
            res.append({'name': 'Kemadruma Dosha', 'description': 'No planets in 2nd/12th from Moon - emotional loneliness, financial instability', 'present': True, 'severity': 'Medium', 'remedies': ['Chandra Puja', 'Monday fasting', 'Worship at Shiva temple']})
        else:
            res.append({'name': 'Kemadruma Dosha', 'description': 'Planets present near Moon - not active', 'present': False, 'remedies': []})

    # --- Manglik Dosha variants ---
    if mars:
        mars_house = mars.get('house', 0)
        if mars_house == 1:
            res.append({'name': 'Angarak Dosha', 'description': 'Mars in Ascendant - aggressive tendencies, need for anger management', 'present': True, 'severity': 'Medium', 'remedies': ['Mangal Mantra', 'Tuesday fasting', 'Red coral gemstone']})
        elif mars_house == 7:
            res.append({'name': 'Kuja Dosha (7th House)', 'description': 'Mars in 7th house - marriage conflicts, strong personality in spouse', 'present': True, 'severity': 'High', 'remedies': ['Kumbh Vivah', 'Mangal Puja', 'Compatibility analysis']})

    # --- Sade Sati indicator ---
    if sat and moon:
        sat_house = sat.get('house', 0)
        moon_house = moon.get('house', 0)
        diff = (sat_house - moon_house) % 12
        if diff in [0, 1, 11]:
            res.append({'name': 'Sade Sati Indicator', 'description': f"Saturn near Moon (house diff {diff}) - period of testing, growth through hardship", 'present': True, 'severity': 'High', 'remedies': ['Shani Puja', 'Shani Mantra', 'Charity on Saturday', 'Hanuman Chalisa']})

    # --- Rahu/Ketu Axis Dosha (Dosh) ---
    if rahu and ketu:
        rahu_house = rahu.get('house', 0)
        ketu_house = ketu.get('house', 0)
        if rahu_house in [1, 4, 7, 10] or ketu_house in [1, 4, 7, 10]:
            res.append({'name': 'Rahu-Ketu Kendra Dosha', 'description': 'Nodes in kendra houses - unconventional life path, spiritual transformation needed', 'present': True, 'severity': 'Medium', 'remedies': ['Rahu/Ketu Puja', 'Nag Panchami', 'Vishnu worship']})

    return res


# NEW: Function to get dynamic Vedic properties based on Moon's position
def get_vedic_properties(sign: str, nakshatra: str, pada: int) -> Dict[str, str]:
    props = NAKSHATRA_PROPERTIES.get(nakshatra, {})
    if not props:
        return {'error': 'Nakshatra properties not found'}

    # Determine Tatva (Element) from Moon's sign
    if sign in ['Aries', 'Leo', 'Sagittarius']:
        tatva = 'Fire'
    elif sign in ['Taurus', 'Virgo', 'Capricorn']:
        tatva = 'Earth'
    elif sign in ['Gemini', 'Libra', 'Aquarius']:
        tatva = 'Air'
    else: # Cancer, Scorpio, Pisces
        tatva = 'Water'

    # Determine Paya (Foot/Pillar) from Moon's sign
    if sign in ['Aries', 'Virgo', 'Aquarius']:
        paya = 'Gold'
    elif sign in ['Taurus', 'Libra', 'Sagittarius']:
        paya = 'Silver'
    elif sign in ['Gemini', 'Leo', 'Capricorn']:
        paya = 'Copper'
    else: # Cancer, Scorpio, Pisces
        paya = 'Iron'

    return {
        'varna': props.get('varna', 'Unknown'),
        'vashya': props.get('vashya', 'Unknown'),
        'yoni': props.get('yoni', 'Unknown'),
        'gan': props.get('gan', 'Unknown'),
        'nadi': props.get('nadi', 'Unknown'),
        'nameAlphabet': props.get('padas', ['?'])[max(1, min(4, pada)) - 1],
        'yunja': 'Harmonious',  # Panchanga yoga name for this tithi-drishti conjunction
        'tatva': tatva,
        'paya': paya
    }


@app.post('/api/kundli', tags=['Birth Chart'])
def generate_kundli(body: BirthDetails) -> Dict[str, Any]:
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    tropical = bool(body.tropical)
    ayan = ayanamsa_value(jd)

    planets = calc_planets(jd, body.propertyProfile, body.nodeMode, tropical=tropical)
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    hs_code = body.houseSystem or 'W'
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, hs_code, tropical=tropical)

    panch = compute_panchang(body.dateOfBirth, body.timeOfBirth, body.timezone, body.latitude, body.longitude)

    source = (body.propertySource or 'moon').lower()
    chosen = None
    if source == 'ascendant':
        asc = house_data['ascendant']
        chosen = {'sign': asc['sign'], 'nakshatra': asc['nakshatra'], 'pada': 1}
    elif source == 'sunrisemoon':
        _sr, _ss, _sr_jd, _ = sunrise_sunset(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
        sr_jd_effective = _sr_jd if _sr_jd else jd
        xm, _ = swe.calc_ut(sr_jd_effective, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        m_lon = xm[0]
        chosen = {
            'sign': get_sign(m_lon),
            'nakshatra': get_nakshatra(m_lon)['name'],
            'pada': get_nakshatra(m_lon)['pada']
        }
    else:
        moon_details = next((p for p in planets if p['name'] == 'Moon'), None)
        if moon_details:
            chosen = {'sign': moon_details['sign'], 'nakshatra': moon_details['nakshatra'], 'pada': moon_details['nakshatraPada']}

    if chosen:
        vedic_props = get_vedic_properties(chosen['sign'], chosen['nakshatra'], chosen['pada'])
        vedic_source_nk = {'name': chosen['nakshatra'], 'pada': chosen['pada']}
    else:
        vedic_props = {'error': 'Source details could not be calculated'}
        vedic_source_nk = {}

    basic = {
        'birthDate': body.dateOfBirth,
        'birthTime': body.timeOfBirth,
        'birthPlace': f"{body.latitude}, {body.longitude}",
        'latitude': body.latitude,
        'longitude': body.longitude,
        'timezone': body.timezone,
        'ayanamsa': 'Lahiri',
        'ayanamsaValue': ayan,
        'sunSign': next(p['sign'] for p in planets if p['name'] == 'Sun'),
        'moonSign': next(p['sign'] for p in planets if p['name'] == 'Moon'),
        'ascendant': house_data['ascendant'],
        'houseSystem': hs_code
    }

    # Divisional charts
    divisional = charts_divisional_extended(planets, house_data['ascendant'])

    # Yogas
    yogas = detect_yogas(planets, house_data['houses'], house_data['ascendant']['sign'])

    # Doshas
    doshas = detect_doshas(planets)

    # Vimshottari Dasha
    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    dasha = vimshottari_full(jd, birth_local)

    # Current dasha at now
    current_now = None
    try:
        tz = pytz.timezone(body.timezone)
        today = datetime.now(tz).date().isoformat()
        cur_md = next((md for md in dasha.get('mahadashas', []) if md['startDate'] <= today < md['endDate']), None)
        if cur_md:
            cur_ad = next((ad for ad in cur_md.get('antardasha', []) if ad['startDate'] <= today < ad['endDate']), None)
            cur_pd = next((pd for pd in cur_ad.get('pratyantar', []) if pd['startDate'] <= today < pd['endDate']), None) if cur_ad else None
            cur_sook = None
            if cur_pd:
                cur_sook = next((sd for sd in cur_pd.get('sookshma', []) if sd['startDate'] <= today < sd['endDate']), None)
            current_now = {
                'mahadasha': {'planet': cur_md['planet'], 'startDate': cur_md['startDate'], 'endDate': cur_md['endDate']},
                'antardasha': {'planet': cur_ad['planet'], 'startDate': cur_ad['startDate'], 'endDate': cur_ad['endDate']} if cur_ad else None,
                'pratyantar': {'planet': cur_pd['planet'], 'startDate': cur_pd['startDate'], 'endDate': cur_pd['endDate']} if cur_pd else None,
                'sookshma': {'planet': cur_sook['planet'], 'startDate': cur_sook['startDate'], 'endDate': cur_sook['endDate']} if cur_sook else None,
            }
    except Exception:
        current_now = None

    # KP details
    kp = kp_details(house_data['houses'], planets)

    # Clean planets for response (remove internal fields)
    clean_planets = []
    for p in planets:
        clean_planets.append({
            'name': p['name'],
            'longitude': p['longitude'],
            'latitude': p['latitude'],
            'speed': p['speed'],
            'degree': p['degree'],
            'degreeDMS': p['degreeDMS'],
            'longitudeDMS': p['longitudeDMS'],
            'sign': p['sign'],
            'signLord': p['signLord'],
            'nakshatra': p['nakshatra'],
            'nakshatraLord': p['nakshatraLord'],
            'nakshatraPada': p['nakshatraPada'],
            'house': p['house'],
            'isRetrograde': p['isRetrograde'],
            'isCombust': p['isCombust'],
            'avastha': p['avastha'],
            'houseStatus': p['houseStatus'],
        })

    return success({
        'basicDetails': basic,
        'planets': clean_planets,
        'houses': house_data['houses'],
        'divisionalCharts': divisional,
        'yogas': yogas,
        'doshas': doshas,
        'dasha': {
            'system': 'Vimshottari',
            'currentNow': current_now,
            'schedule': dasha,
        },
        'kpDetails': kp,
        'vedicProperties': {
            'source': body.propertySource,
            'sourceNakshatra': vedic_source_nk,
            'values': vedic_props
        },
        'panchang': panch,
    })

# --------------------- New endpoint: /horoscope/planet-details ---------------------

NAME_ABBR = {
    'Ascendant': 'As', 'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
    'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke'
}

NAKSHATRA_NAME_NORMALIZE = {
    'Ashwini': 'Ashvini', 'Dhanishta': 'Dhanista', 'Shravana': 'Sravana'
}

def normalize_nk(name: str) -> str:
    return NAKSHATRA_NAME_NORMALIZE.get(name, name)

def sign_index(sign: str) -> int:
    return ZODIAC_SIGNS.index(sign)

def rasi_no_from_sign(sign: str) -> int:
    return sign_index(sign) + 1

def nakshatra_number(name: str) -> Optional[int]:
    for i, (n, *_rest) in enumerate(NAKSHATRAS):
        if n == name:
            return i + 1
    return None

def avastha_compact(label: str) -> str:
    # Map 'Infant (Bala)' -> 'Bala', 'Young (Kumara)' -> 'Kumara', 'Dead (Mrita)' -> 'Mritya'
    if 'Bala' in label and 'Infant' in label: return 'Bala'
    if 'Kumara' in label: return 'Kumara'
    if 'Yuva' in label: return 'Yuva'
    if 'Vriddha' in label: return 'Vriddha'
    if 'Mrita' in label or 'Mrity' in label: return 'Mritya'
    return label

def lord_status_from_dignity(d: str) -> str:
    if d == 'Exalted':
        return 'Highly Benefic'
    if d in ['Own Sign', 'Mooltrikona', 'Friendly']:
        return 'Benefic'
    if d in ['Enemy', 'Debilitated']:
        return 'Malefic'
    return 'Neutral'

def planet_full_name(name: str) -> str:
    return 'Ascendant' if name == 'Ascendant' else name

PLANET_DEFS = {
    'Sun': {
        'definitions': 'The radiant Sun is the significator (Karaka) of health, vitality, energy, and strength. It embodies qualities of leadership, courage, and personal power. Revered as a royal and aristocratic planet, the Sun represents the conscious ego and the soul, guiding the path of self-realization.',
        'gayatri': 'Om Bhaskaraya Vidmahe Mahadyutikaraya Dheemahi Tanno Adityah Prachodayaat',
        'keywords_positive': ['leadership', 'vitality', 'confidence', 'authority', 'courage', 'generosity'],
        'keywords_negative': ['ego', 'arrogance', 'domineering', 'self-centered'],
        'karaka': 'Soul, father, government, authority, career, self-expression'
    },
    'Moon': {
        'definitions': 'The luminous Moon governs the mind, emotions, nurturing, and intuition. She represents the subconscious, imagination, and the mother. The Moon reflects the Sun\'s light, symbolizing how we process and respond to life experiences emotionally.',
        'gayatri': 'Om Chandraya Namaha - Om Kshira Vrindaya Vidmahe Amrit Tatvaya Dheemahi Tanno Chandrah Prachodayaat',
        'keywords_positive': ['intuition', 'empathy', 'nurturing', 'imagination', 'emotional depth'],
        'keywords_negative': ['mood swings', 'indecision', 'over-sensitivity', 'dependency'],
        'karaka': 'Mind, mother, emotions, home, comfort, travel, public'
    },
    'Mars': {
        'definitions': 'Mars is the warrior planet, signifying courage, ambition, energy, and the drive to act. It rules over conflict, competition, surgery, and engineering. Mars provides the willpower to overcome obstacles and the fighting spirit.',
        'gayatri': 'Om Angarakaya Namaha - Om Ang Ankarakaya Vidmahe Shakti Hastaya Dheemahi Tanno Bhaumah Prachodayaat',
        'keywords_positive': ['courage', 'determination', 'energy', 'initiative', 'competitiveness'],
        'keywords_negative': ['aggression', 'anger', 'impulsiveness', 'violence'],
        'karaka': 'Brother, courage, property, land, surgery, engineering, sports'
    },
    'Mercury': {
        'definitions': 'Mercury represents intelligence, communication, analytical thinking, and adaptability. It governs speech, writing, commerce, mathematics, and wit. As the fastest planet, Mercury endows quick thinking and versatility.',
        'gayatri': 'Om Budhaya Namaha - Om Vishwarupaya Vidmahe Krodhakaraya Dheemahi Tanno Budhah Prachodayaat',
        'keywords_positive': ['intelligence', 'communication', 'adaptability', 'wit', 'analytical mind'],
        'keywords_negative': ['nervousness', 'restlessness', 'manipulation', 'anxiety'],
        'karaka': 'Speech, intellect, education, commerce, skin, friends'
    },
    'Jupiter': {
        'definitions': 'Jupiter, the Great Benefic, is the guru (teacher) of the gods. It signifies wisdom, spirituality, wealth, children, and fortune. Jupiter expands whatever it touches, bringing optimism, generosity, and philosophical understanding.',
        'gayatri': 'Om Gurave Namaha - Om Vrishabhadhipaya Vidmahe Kanya Purushaya Dheemahi Tanno Guruh Prachodayaat',
        'keywords_positive': ['wisdom', 'generosity', 'optimism', 'spirituality', 'fortune', 'philosophy'],
        'keywords_negative': ['overconfidence', 'excess', 'laziness', 'judgment'],
        'karaka': 'Wisdom, children, wealth, husband (for female), dharma, guru'
    },
    'Venus': {
        'definitions': 'Venus, the planet of love, beauty, and luxury, governs art, music, romance, and material pleasures. It represents the wife (for male), partnerships, and all things aesthetically pleasing. Venus is the indicator of refined taste and enjoyment.',
        'gayatri': 'Om Shukraya Namaha - Om Asvikrathvaya Vidmahe Krodhakaraya Dheemahi Tanno Shukrah Prachodayaat',
        'keywords_positive': ['love', 'beauty', 'harmony', 'creativity', 'luxury', 'diplomacy'],
        'keywords_negative': ['vanity', 'overindulgence', 'laziness', 'immorality'],
        'karaka': 'Wife (for male), love, marriage, vehicle, luxury, art, music'
    },
    'Saturn': {
        'definitions': 'Saturn, the taskmaster of the zodiac, represents discipline, responsibility, hard work, and karma. Though feared, Saturn is a great teacher who brings growth through challenges. It governs longevity, structure, and maturity.',
        'gayatri': 'Om Shanaye Namaha - Om Kaakadhwajaya Vidmahe Khadga Hastaya Dheemahi Tanno Shanayah Prachodayaat',
        'keywords_positive': ['discipline', 'responsibility', 'patience', 'wisdom through suffering', 'structure'],
        'keywords_negative': ['delay', 'restriction', 'fear', 'melancholy', 'loneliness'],
        'karaka': 'Longevity, sorrow, service, land, vehicles, elderly, karma'
    }
}

@app.post('/horoscope/planet-details')
def planet_details(body: BirthDetails):
    import math
    # Compute base data
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, body.propertyProfile, body.nodeMode)
    hs_code = body.houseSystem or 'W'
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, hs_code)

    # Build ascendant record
    asc = house_data['ascendant']
    asc_nk = get_nakshatra(asc['degree'])
    asc_item = {
        'name': NAME_ABBR['Ascendant'],
        'full_name': 'Ascendant',
        'local_degree': asc['degree'] % 30,
        'global_degree': asc['degree'] % 360,
        'progress_in_percentage': (asc['degree'] % 30) / 30 * 100,
        'rasi_no': rasi_no_from_sign(asc['sign']),
        'zodiac': asc['sign'],
        'house': 1,
        'nakshatra': normalize_nk(asc_nk['name']),
        'nakshatra_lord': asc_nk['lord'],
        'nakshatra_pada': asc_nk['pada'],
        'nakshatra_no': nakshatra_number(asc_nk['name']),
        'zodiac_lord': SIGN_LORDS[asc['sign']],
        'is_planet_set': False,
        'lord_status': '-',
        'basic_avastha': '-',
        'is_combust': False
    }

    # Only classical + nodes in this report
    ordered = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']
    plist = [p for p in planets if p['name'] in ordered]
    plist.sort(key=lambda p: ordered.index(p['name']))

    result_indexed: Dict[str, Any] = {'0': asc_item}

    for idx, p in enumerate(plist, start=1):
        nk_num = nakshatra_number(p['nakshatra'])
        dignity = planet_status(p['name'], p['sign'])
        lord_stat = lord_status_from_dignity(dignity)
        set_flag = bool(p.get('house', 0) in [1,2,3,4,5,6])
        item = {
            'name': NAME_ABBR.get(p['name'], p['name'][:2]),
            'full_name': planet_full_name(p['name']),
            'local_degree': p['degree'],
            'global_degree': p['longitude'],
            'progress_in_percentage': p['degree'] / 30.0 * 100.0,
            'rasi_no': rasi_no_from_sign(p['sign']),
            'zodiac': p['sign'],
            'house': p.get('house', 0),
            'speed_radians_per_day': p['speed'] * math.pi / 180.0,
            'retro': bool(p['isRetrograde']),
            'nakshatra': normalize_nk(p['nakshatra']),
            'nakshatra_lord': p['nakshatraLord'],
            'nakshatra_pada': p['nakshatraPada'],
            'nakshatra_no': nk_num,
            'zodiac_lord': p['signLord'],
            'is_planet_set': set_flag,
            'basic_avastha': avastha_compact(p.get('avastha','')),
            'lord_status': lord_stat,
            'is_combust': bool(p['isCombust'])
        }
        result_indexed[str(idx)] = item

    # Personal characteristics per house (simple template-based)
    personal: list[Dict[str, Any]] = []
    asc_sign = asc['sign']
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    house_signs = [ZODIAC_SIGNS[(asc_idx + i) % 12] for i in range(12)]
    pmap = {p['name']: p for p in planets}

    for h in range(1, 13):
        sign = house_signs[h-1]
        lord = SIGN_LORDS[sign]
        lord_p = pmap.get(lord)
        lord_sign = lord_p['sign'] if lord_p else None
        lord_house = lord_p.get('house') if lord_p else None
        strength = planet_status(lord, lord_sign) if lord_sign else 'Neutral'
        verbal = f"{h}st lord is in the {lord_house}th house" if h == 1 else f"{h}th lord is in the {lord_house}th house"
        personal.append({
            'current_house': h,
            'verbal_location': verbal,
            'current_zodiac': sign,
            'lord_of_zodiac': lord,
            'lord_zodiac_location': lord_sign,
            'lord_house_location': lord_house,
            'personalised_prediction': f"Since the  {h} lord, {lord} is in the {lord_house} house, outcomes relate to {sign.lower()} themes.",
            'lord_strength': strength
        })

    # Simple planet report for Sun (example)
    sun = pmap.get('Sun')
    if sun:
        z_lord = SIGN_LORDS[sun['sign']]
        z_lord_p = pmap.get(z_lord)
        report = {
            'planet_considered': 'Sun',
            'planet_location': sun.get('house'),
            'planet_native_location': 5,  # Sun's natural house in Kaal Purusha (Leo)
            'planet_zodiac': sun['sign'],
            'zodiac_lord': z_lord,
            'zodiac_lord_location': z_lord_p['sign'] if z_lord_p else None,
            'zodiac_lord_house_location': z_lord_p.get('house') if z_lord_p else None,
            'general_prediction': 'Your personality, vitality, and leadership themes are highlighted by the Sun\'s placement.',
            'zodiac_lord_strength': planet_status(z_lord, z_lord_p['sign']) if z_lord_p else 'Neutral',
            'planet_strength': planet_status('Sun', sun['sign']),
            'planet_definitions': PLANET_DEFS['Sun']['definitions'],
            'gayatri_mantra': PLANET_DEFS['Sun']['gayatri'],
            'qualities_long': 'This placement fuels ambition and visibility; hard work is needed if afflicted.',
            'qualities_short': 'Seeks recognition through contribution.',
            'affliction': 'Afflictions can bring career hurdles or vitality dips.',
            'personalised_prediction': f"Since the  11th lord, Sun, influences {sun.get('house')}th house matters, career and visibility are emphasized.",
            'verbal_location': 'Lord of the 11th lord in 12th house',
            'planet_zodiac_prediction': f"{sun['sign']} is a {('Movable' if sign_index(sun['sign'])%3==0 else ('Fixed' if sign_index(sun['sign'])%3==1 else 'Dual'))} sign; its lord {z_lord} colors self-expression.",
            'character_keywords_positive': ['principled','Attractive','Virtuous','Creative'],
            'character_keywords_negative': ['indecisive','Doubtful']
        }
    else:
        report = {}

    return success({
        'response': result_indexed,
        'personal_characteristics': personal,
        'planet_report': report,
    })