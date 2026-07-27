from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

# ── Request model ────────────────────────────────────────────────────────────

class MuhuratRequest(BaseModel):
    dateOfBirth: str = Field(..., example="2025-07-15")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


# ── Constants ────────────────────────────────────────────────────────────────

WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Rahu Kaal: index = weekday (0=Sun). Values are position among 8 day-parts (0-based).
RAHU_KAAL_POSITION = [4, 2, 7, 5, 6, 3, 1]  # Sun..Sat

# Gulika Kaal: index = weekday (0=Sun). Values are position among 8 day-parts (0-based).
GULIKA_POSITION = [6, 5, 4, 3, 2, 1, 7]

# Yamaganda: index = weekday (0=Sun). Values are position among 8 day-parts (0-based).
YAMAGANDA_POSITION = [2, 7, 5, 6, 3, 1, 4]

# Choghadiya sequence starts per weekday (0=Sun). Order of 8 choghadiya types.
CHOGHADIYA_SEQUENCE = [
    ["Amrit", "Shubh", "Labh", "Char", "Rog", "Kaal", "Udveg", "Shubh"],
    ["Shubh", "Amrit", "Labh", "Char", "Rog", "Kaal", "Udveg", "Char"],
    ["Amrit", "Shubh", "Labh", "Char", "Rog", "Kaal", "Udveg", "Shubh"],
    ["Labh", "Amrit", "Shubh", "Char", "Rog", "Kaal", "Udveg", "Labh"],
    ["Udveg", "Char", "Labh", "Amrit", "Shubh", "Rog", "Kaal", "Udveg"],
    ["Char", "Labh", "Amrit", "Shubh", "Char", "Rog", "Kaal", "Shubh"],
    ["Labh", "Char", "Amrit", "Shubh", "Char", "Rog", "Kaal", "Udveg"],
]

# Benefic / Malefic choghadiya ratings
CHOGHADIYA_RATING = {
    "Amrit": "excellent",
    "Shubh": "excellent",
    "Labh": "good",
    "Char": "good",
    "Udveg": "avoid",
    "Rog": "avoid",
    "Kaal": "avoid",
}

# Favorable tithis (numbered 1-30, waxing 1-15, waning 16-30)
# For muhurat we map tithi number mod 15 (0=15th=Poornima/Amavasya)
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddhartha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]


# ── Helper utilities ─────────────────────────────────────────────────────────

def _parse_local(date_str: str, time_str: str, tz_name: str):
    import pytz
    from dateutil import parser as _p
    tz = pytz.timezone(tz_name)
    dt = tz.localize(_p.parse(f"{date_str} {time_str}"))
    return dt


def _weekday_index(date_str: str) -> int:
    from dateutil import parser as _p
    d = _p.parse(date_str).date()
    # Monday=0 .. Sunday=6 for Python; we want Sunday=0
    return (d.weekday() + 1) % 7


def _sunrise_sunset_jd(date_str: str, tz_name: str, lat: float, lon: float):
    from ..main import sunrise_sunset
    return sunrise_sunset(date_str, tz_name, lat, lon)


def _to_julian(date_str: str, time_str: str, tz_name: str) -> float:
    from ..main import to_julian
    return to_julian(date_str, time_str, tz_name)


def _panchang_at_jd(jd: float) -> Dict[str, Any]:
    from ..main import panchang_at_jd
    return panchang_at_jd(jd)


def _calc_planets(jd: float, node_mode: str = "mean"):
    from ..main import calc_planets
    return calc_planets(jd, None, node_mode)


def _get_nakshatra(lon: float) -> Dict[str, Any]:
    from ..main import get_nakshatra
    return get_nakshatra(lon)


def _get_sign(lon: float) -> str:
    from ..main import get_sign
    return get_sign(lon)


def _minutes_to_hhmm(minutes: float) -> str:
    h = int(minutes // 60)
    m = int(round(minutes - h * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"


def _time_str_to_minutes(t: str) -> float:
    parts = t.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _minutes_to_time_str(minutes: float) -> str:
    total = int(round(minutes))
    h = (total // 60) % 24
    m = total % 60
    return f"{h:02d}:{m:02d}"


# ── Core muhurat calculations ────────────────────────────────────────────────

def _calc_rahu_kaal(sunset_min: float, sunrise_min: float, weekday: int) -> Dict[str, str]:
    """Calculate Rahu Kaal window for the day."""
    day_duration = sunset_min - sunrise_min
    part = day_duration / 8.0
    pos = RAHU_KAAL_POSITION[weekday]
    start = sunrise_min + pos * part
    end = start + part
    return {
        "name": "Rahu Kaal",
        "startTime": _minutes_to_time_str(start),
        "endTime": _minutes_to_time_str(end),
        "rating": "avoid",
        "type": "inauspicious"
    }


def _calc_gulika_kaal(sunset_min: float, sunrise_min: float, weekday: int) -> Dict[str, str]:
    """Calculate Gulika Kaal window for the day."""
    day_duration = sunset_min - sunrise_min
    part = day_duration / 8.0
    pos = GULIKA_POSITION[weekday]
    start = sunrise_min + pos * part
    end = start + part
    return {
        "name": "Gulika Kaal",
        "startTime": _minutes_to_time_str(start),
        "endTime": _minutes_to_time_str(end),
        "rating": "avoid",
        "type": "inauspicious"
    }


def _calc_yamaganda(sunset_min: float, sunrise_min: float, weekday: int) -> Dict[str, str]:
    """Calculate Yamaganda Kaal."""
    day_duration = sunset_min - sunrise_min
    part = day_duration / 8.0
    pos = YAMAGANDA_POSITION[weekday]
    start = sunrise_min + pos * part
    end = start + part
    return {
        "name": "Yamaganda",
        "startTime": _minutes_to_time_str(start),
        "endTime": _minutes_to_time_str(end),
        "rating": "avoid",
        "type": "inauspicious"
    }


def _calc_choghadiya(sunset_min: float, sunrise_min: float, weekday: int) -> List[Dict[str, str]]:
    """Calculate all 8 day choghadiya windows."""
    day_duration = sunset_min - sunrise_min
    part = day_duration / 8.0
    seq = CHOGHADIYA_SEQUENCE[weekday]
    windows = []
    for i, name in enumerate(seq):
        start = sunrise_min + i * part
        end = start + part
        windows.append({
            "name": f"{name} Choghadiya",
            "startTime": _minutes_to_time_str(start),
            "endTime": _minutes_to_time_str(end),
            "rating": CHOGHADIYA_RATING[name],
            "type": "choghadiya"
        })
    return windows


def _is_favorable_tithi(tithi_num: int, favorables: List[int]) -> bool:
    """Check if a tithi number (1-30) is in the favorable list."""
    t = tithi_num if tithi_num <= 15 else tithi_num - 15
    return t in favorables


def _tithi_name_from_num(tithi_num: int) -> str:
    idx = (tithi_num - 1) % 15
    return TITHI_NAMES[idx]


def _paksha_from_num(tithi_num: int) -> str:
    return "Shukla" if tithi_num <= 15 else "Krishna"


def _build_muhurat_window(
    start_min: float,
    end_min: float,
    tithi: str,
    nakshatra: str,
    yoga: str,
    name: str,
    rating: str,
    reason: str = ""
) -> Dict[str, Any]:
    return {
        "name": name,
        "startTime": _minutes_to_time_str(start_min),
        "endTime": _minutes_to_time_str(end_min),
        "tithi": tithi,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "rating": rating,
        "reason": reason
    }


def _evaluate_day_for_muhurat(
    date_str: str, tz_name: str, lat: float, lon: float,
    favorable_tithis: List[int] = None,
    favorable_nakshatras: List[str] = None,
    favorable_choghadiya: List[str] = None,
    avoid_tithis: List[int] = None,
    avoid_nakshatras: List[str] = None,
    avoid_yogas: List[str] = None,
    extra_good_nakshatras: List[str] = None,
    avoid_yamaganda: bool = False,
) -> Dict[str, Any]:
    """
    Core muhurat engine.
    Evaluates the day and returns muhurat windows.
    """
    sr, ss, sr_jd, ss_jd = _sunrise_sunset_jd(date_str, tz_name, lat, lon)
    if sr is None or ss is None:
        return {"error": "Could not calculate sunrise/sunset for the given location and date"}

    weekday = _weekday_index(date_str)
    sunrise_min = _time_str_to_minutes(sr)
    sunset_min = _time_str_to_minutes(ss)

    rahu_kaal = _calc_rahu_kaal(sunset_min, sunrise_min, weekday)
    gulika = _calc_gulika_kaal(sunset_min, sunrise_min, weekday)
    yamaganda = _calc_yamaganda(sunset_min, sunrise_min, weekday)
    choghadiya_list = _calc_choghadiya(sunset_min, sunrise_min, weekday)

    # Panchang at sunrise
    panch = _panchang_at_jd(sr_jd)
    tithi_num = panch["tithiNumber"]
    tithi_name = panch["tithi"]
    nak_name = panch["nakshatra"]
    yoga_name = panch["yoga"]
    paksha = panch["paksha"]

    avoid = [rahu_kaal, gulika]
    if avoid_yamaganda:
        avoid.append(yamaganda)

    # Identify time segments (choghadiya-based) that overlap with panchang checks
    favorable_chog = favorable_choghadiya or ["Amrit", "Shubh", "Labh"]
    muhurats = []

    for chog in choghadiya_list:
        chog_name_base = chog["name"].replace(" Choghadiya", "")
        chog_start = _time_str_to_minutes(chog["startTime"])
        chog_end = _time_str_to_minutes(chog["endTime"])

        # Check tithi favorability
        tithi_ok = True
        if favorable_tithis and not _is_favorable_tithi(tithi_num, favorable_tithis):
            tithi_ok = False
        if avoid_tithis and _is_favorable_tithi(tithi_num, avoid_tithis):
            tithi_ok = False

        # Check nakshatra favorability
        nak_ok = True
        if favorable_nakshatras and nak_name not in favorable_nakshatras:
            nak_ok = False
        if avoid_nakshatras and nak_name in avoid_nakshatras:
            nak_ok = False

        # Check choghadiya favorability
        chog_ok = chog_name_base in favorable_chog

        # Check yoga
        yoga_ok = True
        if avoid_yogas and yoga_name in avoid_yogas:
            yoga_ok = False

        # Overall rating
        if chog_ok and tithi_ok and nak_ok and yoga_ok:
            rating = "excellent"
            reason_parts = []
            if extra_good_nakshatras and nak_name in extra_good_nakshatras:
                reason_parts.append(f"favorable nakshatra {nak_name}")
            if chog_ok:
                reason_parts.append(f"{chog_name_base} choghadiya")
            reason = "; ".join(reason_parts) if reason_parts else f"{chog_name_base} choghadiya"
        elif chog_ok and (tithi_ok or nak_ok):
            rating = "good"
            reason = f"{chog_name_base} choghadiya"
        elif not chog_ok:
            rating = "avoid"
            reason = f"{chog_name_base} choghadiya is inauspicious"
        else:
            rating = "avoid"
            reason = "unfavorable panchang"

        muhurats.append(_build_muhurat_window(
            chog_start, chog_end,
            tithi_name, nak_name, yoga_name,
            f"{chog_name_base} Muhurat",
            rating, reason
        ))

    # Filter out choghadiya that overlap Rahu Kaal or Gulika
    for m in muhurats:
        m_start = _time_str_to_minutes(m["startTime"])
        m_end = _time_str_to_minutes(m["endTime"])
        for a in avoid:
            a_start = _time_str_to_minutes(a["startTime"])
            a_end = _time_str_to_minutes(a["endTime"])
            if m_start < a_end and m_end > a_start:
                m["rating"] = "avoid"
                m["reason"] = f"overlaps {a['name']}"
                break

    # Build notes
    favorable_count = sum(1 for m in muhurats if m["rating"] in ["excellent", "good"])
    notes_parts = [
        f"Sunrise: {sr}, Sunset: {ss}",
        f"Tithi: {tithi_name} ({paksha})",
        f"Nakshatra: {nak_name}",
        f"Yoga: {yoga_name}",
        f"Rahu Kaal: {rahu_kaal['startTime']}-{rahu_kaal['endTime']}",
        f"Gulika Kaal: {gulika['startTime']}-{gulika['endTime']}",
    ]
    if favorable_count > 0:
        notes_parts.append(f"{favorable_count} favorable muhurat window(s) found")
    else:
        notes_parts.append("No favorable muhurat windows found for this day; consider adjacent days")

    return {
        "status": 200,
        "date": date_str,
        "sunrise": sr,
        "sunset": ss,
        "panchang": {
            "tithi": tithi_name,
            "tithiNumber": tithi_num,
            "paksha": paksha,
            "nakshatra": nak_name,
            "yoga": yoga_name,
        },
        "muhurat": muhurats,
        "avoid": avoid,
        "choghadiya": choghadiya_list,
        "notes": " | ".join(notes_parts),
    }


# ── Helper to build the standard response envelope ───────────────────────────

def _envelope(data: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in data:
        return {"status": 400, "error": data["error"]}
    return data


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/muhurat/marriage")
def marriage_muhurat(body: MuhuratRequest):
    """
    Marriage muhurat:
    - Avoid Rahu Kaal, Gulika Kaal
    - Avoid Tithis: Chaturthi(4), Ashtami(8), Chaturdashi(14)
    - Avoid Nakshatras: Rohini, Mrigashira, Ardra, Revati, Moola
    - Avoid Yoga: Atiganda, Shoola, Vyatipata, Ganda, Vishkambha
    - Favorable: Amrit/Shubh/Labh Choghadiya
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 15],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Ashwini", "Bharani", "Krittika", "Punarvasu", "Pushya",
            "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
            "Jyeshtha", "Purva Ashadha", "Uttara Ashadha", "Shravana",
            "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada"
        ],
        avoid_nakshatras=["Rohini", "Mrigashira", "Ardra", "Revati", "Moola"],
        avoid_yogas=["Atiganda", "Shoola", "Vyatipata", "Ganda", "Vishkambha"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Marriage"
    result["description"] = "Auspicious time for marriage ceremonies. Rahu Kaal, Gulika, and Yamaganda are avoided. Only favorable Tithis, Nakshatras, and Choghadiya are recommended."
    return _envelope(result)


@router.post("/muhurat/vehicle-purchase")
def vehicle_purchase_muhurat(body: MuhuratRequest):
    """
    Vehicle purchase muhurat:
    - Favorable: Shubh/Amrit/Labh Choghadiya
    - Avoid Rahu Kaal
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 15],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Ashwini", "Bharani", "Pushya", "Hasta", "Swati",
            "Anuradha", "Uttara Ashadha", "Uttara Bhadrapada",
            "Rohini", "Mrigashira"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Revati"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Vehicle Purchase"
    result["description"] = "Auspicious time for purchasing vehicles. Shubh/Amrit/Labh Choghadiya are preferred. Rahu Kaal and Yamaganda are avoided."
    return _envelope(result)


@router.post("/muhurat/house-warming")
def house_warming_muhurat(body: MuhuratRequest):
    """
    Griha Pravesh muhurat:
    - Favorable Tithis: 2,3,5,7,10,11,12 (both waxing/waning)
    - Avoid: Chaturthi(4), Ashtami(8), Chaturdashi(14)
    - Favorable Nakshatras: Pushya, Hasta, Swati, Anuradha, Uttarashada, Uttarabhadrapada
    - Favorable: Amrit/Shubh/Labh Choghadiya
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[2, 3, 5, 7, 10, 11, 12],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Pushya", "Hasta", "Swati", "Anuradha",
            "Uttara Ashadha", "Uttara Bhadrapada",
            "Rohini", "Ashwini", "Punarvasu"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Revati", "Jyeshtha"],
        avoid_yogas=["Atiganda", "Shoola", "Vyatipata", "Ganda"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "House Warming (Griha Pravesh)"
    result["description"] = "Auspicious time for Griha Pravesh (house warming). Tithis 2,3,5,7,10,11,12 are favorable. Chaturthi, Ashtami, and Chaturdashi are strictly avoided."
    return _envelope(result)


@router.post("/muhurat/property-purchase")
def property_purchase_muhurat(body: MuhuratRequest):
    """
    Property purchase muhurat:
    - Favorable Nakshatras: Rohini, Mrigashira, Pushya, Hasta, Swati, Anuradha,
      Uttarashada, Uttarabhadrapada
    - Avoid Rahu Kaal, Gulika
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 15],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Rohini", "Mrigashira", "Pushya", "Hasta", "Swati",
            "Anuradha", "Uttara Ashadha", "Uttara Bhadrapada"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Revati", "Jyeshtha"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Property Purchase"
    result["description"] = "Auspicious time for buying property/land. Favorable Nakshatras include Rohini, Pushya, Hasta, Swati, Anuradha, Uttarashada, and Uttarabhadrapada."
    return _envelope(result)


@router.post("/muhurat/business-opening")
def business_opening_muhurat(body: MuhuratRequest):
    """
    Business opening muhurat:
    - Favorable: Amrit/Shubh Choghadiya
    - Avoid Rahu Kaal and Yamaganda
    - Favorable Tithis: 2,3,5,7,10,11,12
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[2, 3, 5, 7, 10, 11, 12],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Ashwini", "Rohini", "Pushya", "Hasta", "Swati",
            "Anuradha", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Jyeshtha"],
        avoid_yogas=["Atiganda", "Shoola", "Vyatipata", "Ganda"],
        favorable_choghadiya=["Amrit", "Shubh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Business Opening"
    result["description"] = "Auspicious time for starting a new business or venture. Amrit and Shubh Choghadiya are preferred. Rahu Kaal and Yamaganda are avoided."
    return _envelope(result)


@router.post("/muhurat/naming-ceremony")
def naming_ceremony_muhurat(body: MuhuratRequest):
    """
    Naming ceremony muhurat:
    - Favorable Nakshatras: Pushya, Hasta, Swati, Shravana, Revati
    - Favorable Tithis: 2,3,5,7,10,11,12
    - Favorable: Amrit/Shubh/Labh Choghadiya
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[2, 3, 5, 7, 10, 11, 12],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Pushya", "Hasta", "Swati", "Shravana", "Revati"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Jyeshtha"],
        avoid_yogas=["Atiganda", "Shoola", "Vyatipata", "Ganda"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Naming Ceremony"
    result["description"] = "Auspicious time for naming ceremony (Namkaran). Pushya, Hasta, Swati, Shravana, and Revati nakshatras are especially favorable."
    return _envelope(result)


@router.post("/muhurat/griha-pravesh")
def griha_pravesh_muhurat(body: MuhuratRequest):
    """
    Griha Pravesh (extended) muhurat:
    - Extended rules similar to house-warming
    - Favorable Tithis: 2,3,5,7,10,11,12
    - Avoid: Chaturthi(4), Ashtami(8), Chaturdashi(14), Amavasya(30)
    - Favorable Nakshatras: Pushya, Hasta, Swati, Anuradha, Uttarashada,
      Uttarabhadrapada, Ashwini, Rohini, Revati
    - Favorable: Amrit/Shubh/Labh Choghadiya
    - Avoid Rahu Kaal, Gulika, Yamaganda
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[2, 3, 5, 7, 10, 11, 12],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Pushya", "Hasta", "Swati", "Anuradha",
            "Uttara Ashadha", "Uttara Bhadrapada",
            "Ashwini", "Rohini", "Revati", "Punarvasu"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Jyeshtha"],
        avoid_yogas=["Atiganda", "Shoola", "Vyatipata", "Ganda", "Vishkambha"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Griha Pravesh (Extended)"
    result["description"] = "Extended Griha Pravesh muhurat with comprehensive checks. Tithis 2,3,5,7,10,11,12 are favorable. Amavasya and Purnima tithis should also be avoided. Rahu Kaal, Gulika, and Yamaganda are all avoided."
    return _envelope(result)


@router.post("/muhurat/engagement")
def engagement_muhurat(body: MuhuratRequest):
    """
    Engagement muhurat:
    - Favorable Tithis: 2,3,5,7,10,11,12
    - Avoid: Chaturthi(4), Ashtami(8), Chaturdashi(14)
    - Favorable Nakshatras: Rohini, Pushya, Hasta, Swati, Anuradha,
      Uttarashada, Uttarabhadrapada, Ashwini, Revati
    - Favorable: Amrit/Shubh/Labh Choghadiya
    """
    result = _evaluate_day_for_muhurat(
        date_str=body.dateOfBirth,
        tz_name=body.timezone,
        lat=body.latitude,
        lon=body.longitude,
        favorable_tithis=[2, 3, 5, 7, 10, 11, 12],
        avoid_tithis=[4, 8, 14],
        favorable_nakshatras=[
            "Rohini", "Pushya", "Hasta", "Swati", "Anuradha",
            "Uttara Ashadha", "Uttara Bhadrapada", "Ashwini", "Revati"
        ],
        avoid_nakshatras=["Ardra", "Moola", "Jyeshtha"],
        avoid_yogas=["Atiganda", "Shoola", "Vyatipata", "Ganda"],
        favorable_choghadiya=["Amrit", "Shubh", "Labh"],
        avoid_yamaganda=True,
    )
    result["muhuratType"] = "Engagement"
    result["description"] = "Auspicious time for engagement ceremony. Favorable tithis and nakshatras are checked. Rahu Kaal and Yamaganda are avoided."
    return _envelope(result)
