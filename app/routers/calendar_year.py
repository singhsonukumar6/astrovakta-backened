"""Full Year Calendar router – panchang, muhurat, festivals, auspicious dates."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import swisseph as swe
import pytz
from dateutil import parser
import logging

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, planet_status, panchang_at_jd,
    sunrise_sunset, compute_panchang,
)

router = APIRouter()
logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
RAHU_POS = [4, 2, 7, 5, 6, 3, 1]
YAMAGANDA_POS = [2, 7, 5, 6, 3, 1, 4]
GULIKA_POS = [6, 5, 4, 3, 2, 1, 7]

# Pre-computed festival dates (key = year). Add more years as needed.
HINDU_FESTIVALS: Dict[int, Dict[str, str]] = {
    2025: {"Makar Sankranti":"2025-01-14","Vasant Panchami":"2025-02-02","Maha Shivaratri":"2025-02-26","Holi":"2025-03-14","Ugadi":"2025-03-30","Ram Navami":"2025-04-06","Hanuman Jayanti":"2025-04-12","Akshaya Tritiya":"2025-04-30","Ganga Dussehra":"2025-06-05","Guru Purnima":"2025-07-10","Nag Panchami":"2025-07-24","Raksha Bandhan":"2025-08-08","Krishna Janmashtami":"2025-08-15","Ganesh Chaturthi":"2025-08-27","Navratri Start":"2025-09-22","Dussehra":"2025-10-01","Diwali":"2025-10-20","Chhath Puja":"2025-10-26","Guru Nanak Jayanti":"2025-11-04"},
    2026: {"Makar Sankranti":"2026-01-14","Vasant Panchami":"2026-01-22","Maha Shivaratri":"2026-02-15","Holi":"2026-03-04","Ugadi":"2026-03-19","Ram Navami":"2026-03-26","Hanuman Jayanti":"2026-04-01","Akshaya Tritiya":"2026-04-19","Ganga Dussehra":"2026-05-25","Guru Purnima":"2026-06-29","Nag Panchami":"2026-07-13","Raksha Bandhan":"2026-07-28","Krishna Janmashtami":"2026-08-04","Ganesh Chaturthi":"2026-08-16","Navratri Start":"2026-09-11","Dussehra":"2026-09-20","Diwali":"2026-11-08","Chhath Puja":"2026-11-14","Guru Nanak Jayanti":"2026-11-23"},
    2027: {"Makar Sankranti":"2027-01-14","Vasant Panchami":"2027-02-11","Maha Shivaratri":"2027-03-05","Holi":"2027-03-24","Ugadi":"2027-04-08","Ram Navami":"2027-04-15","Hanuman Jayanti":"2027-04-21","Akshaya Tritiya":"2027-05-08","Ganga Dussehra":"2027-06-14","Guru Purnima":"2027-06-19","Nag Panchami":"2027-08-02","Raksha Bandhan":"2027-08-17","Krishna Janmashtami":"2027-08-24","Ganesh Chaturthi":"2027-09-05","Navratri Start":"2027-10-01","Dussehra":"2027-10-10","Diwali":"2027-10-28","Chhath Puja":"2027-11-03","Guru Nanak Jayanti":"2027-11-12"},
    2028: {"Makar Sankranti":"2028-01-14","Vasant Panchami":"2028-01-31","Maha Shivaratri":"2028-02-22","Holi":"2028-03-12","Ugadi":"2028-03-27","Ram Navami":"2028-04-03","Hanuman Jayanti":"2028-04-09","Akshaya Tritiya":"2028-04-27","Ganga Dussehra":"2028-06-13","Guru Purnima":"2028-07-08","Nag Panchami":"2028-07-22","Raksha Bandhan":"2028-08-06","Krishna Janmashtami":"2028-08-13","Ganesh Chaturthi":"2028-08-24","Navratri Start":"2028-09-19","Dussehra":"2028-09-28","Diwali":"2028-11-15","Chhath Puja":"2028-11-21","Guru Nanak Jayanti":"2028-12-01"},
}

PURPOSE_RULES: Dict[str, Dict[str, Any]] = {
    "marriage":       {"good_tithis":[2,3,5,7,10,11,13],"avoid_tithis":[4,8,14,30],"good_nakshatras":["Rohini","Mrigashira","Punarvasu","Pushya","Hasta","Swati","Anuradha","Shravana","Dhanishta","Uttara Bhadrapada","Revati"],"avoid_nakshatras":["Ardra","Magha","Jyeshtha","Mula","Purva Phalguni","Purva Ashadha","Purva Bhadrapada"],"avoid_weekdays":[1,6]},
    "house_warming":  {"good_tithis":[1,2,3,5,7,10,11,13],"avoid_tithis":[4,6,8,9,14,30],"good_nakshatras":["Ashwini","Rohini","Punarvasu","Pushya","Hasta","Anuradha","Shravana","Dhanishta","Revati"],"avoid_nakshatras":["Ardra","Magha","Jyeshtha","Mula","Purva Ashadha","Purva Bhadrapada"],"avoid_weekdays":[]},
    "business":       {"good_tithis":[1,2,3,5,7,10,11],"avoid_tithis":[4,8,9,14,30],"good_nakshatras":["Ashwini","Rohini","Mrigashira","Punarvasu","Hasta","Swati","Anuradha","Shravana","Dhanishta","Revati"],"avoid_nakshatras":["Ardra","Jyeshtha","Mula","Purva Bhadrapada"],"avoid_weekdays":[]},
    "vehicle_purchase":{"good_tithis":[1,2,3,5,7,10,11,13],"avoid_tithis":[4,8,14,30],"good_nakshatras":["Ashwini","Rohini","Mrigashira","Punarvasu","Hasta","Swati","Anuradha","Shravana","Revati"],"avoid_nakshatras":["Ardra","Magha","Jyeshtha","Mula","Purva Ashadha","Purva Bhadrapada"],"avoid_weekdays":[]},
    "general":        {"good_tithis":[1,2,3,5,7,10,11,13],"avoid_tithis":[4,8,14,30],"good_nakshatras":["Ashwini","Rohini","Punarvasu","Pushya","Hasta","Anuradha","Shravana","Revati"],"avoid_nakshatras":["Ardra","Magha","Jyeshtha","Mula","Purva Ashadha","Purva Bhadrapada"],"avoid_weekdays":[]},
}

GOOD_NAKSHATRAS_AMRIT = {"Rohini","Mrigashira","Punarvasu","Hasta","Swati","Anuradha","Shravana","Dhanishta","Revati"}


# ── Request models ───────────────────────────────────────────────────────────

class YearCalendarRequest(BaseModel):
    year: int = Field(..., example=2026)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    month: Optional[int] = Field(None, ge=1, le=12, example=3)

class MonthlySummaryRequest(BaseModel):
    year: int = Field(..., example=2026)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    month: int = Field(..., ge=1, le=12, example=10)

class AuspiciousDatesRequest(BaseModel):
    year: int = Field(..., example=2026)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    purpose: str = Field("general", example="marriage")
    month: Optional[int] = Field(None, ge=1, le=12)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _tm(t: str) -> float:
    p = t.strip().split(":")
    return int(p[0]) * 60 + int(p[1])

def _ft(m: float) -> str:
    v = int(round(m))
    return f"{(v // 60) % 24:02d}:{v % 60:02d}"

def _wk(date_str: str) -> int:
    return (parser.parse(date_str).date().weekday() + 1) % 7

def _month_end(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year + 1, 1, 1) - timedelta(days=1)
    return datetime(year, month + 1, 1) - timedelta(days=1)

def _sun_lon_at_jd(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    return xx[0]

def _detect_sankranti(prev_lon: float, curr_lon: float) -> Optional[str]:
    if int(curr_lon // 30) != int(prev_lon // 30):
        return ZODIAC_SIGNS[int(curr_lon // 30) % 12]
    return None

def _kaal(sunrise_min: float, sunset_min: float, position: int) -> str:
    part = (sunset_min - sunrise_min) / 8.0
    return _ft(sunrise_min + position * part)

def _day_score(tithi_num: int, nakshatra: str, weekday: int, rules: Dict[str, Any]) -> int:
    s = 0
    t = tithi_num if tithi_num <= 15 else tithi_num - 15
    if t in rules.get("good_tithis", []): s += 3
    if t in rules.get("avoid_tithis", []): s -= 4
    if nakshatra in rules.get("good_nakshatras", []): s += 3
    if nakshatra in rules.get("avoid_nakshatras", []): s -= 3
    if weekday in rules.get("avoid_weekdays", []): s -= 2
    if weekday in RAHU_POS: s -= 1
    return s

def _prev_sun_lon(year: int, month: int, timezone: str, lat: float, lon: float) -> Optional[float]:
    prev = datetime(year, month, 1) - timedelta(days=1)
    try:
        _, _, jd, _ = sunrise_sunset(prev.strftime("%Y-%m-%d"), timezone, lat, lon)
        return _sun_lon_at_jd(jd) if jd else None
    except Exception:
        return None


# ── Core day computation ─────────────────────────────────────────────────────

def _compute_day(date_str: str, tz: str, lat: float, lon: float,
                 prev_sun_lon: Optional[float] = None) -> Optional[Dict[str, Any]]:
    try:
        sr, ss, sr_jd, _ = sunrise_sunset(date_str, tz, lat, lon)
        if sr is None:
            return None
        panch = panchang_at_jd(sr_jd)
        wk = _wk(date_str)
        sr_min, ss_min = _tm(sr), _tm(ss)
        day_dur = ss_min - sr_min
        part = day_dur / 8.0

        sun_lon = _sun_lon_at_jd(sr_jd)
        sankranti = _detect_sankranti(prev_sun_lon, sun_lon) if prev_sun_lon is not None else None

        year = parser.parse(date_str).year
        festivals = [fn for fn, fd in HINDU_FESTIVALS.get(year, {}).items() if fd == date_str]
        t = panch["tithiNumber"]
        if t == 11:
            festivals.append(f"{panch['paksha']} Ekadashi")
        if t == 15:
            festivals.append("Purnima")
        elif t == 30:
            festivals.append("Amavasya")

        rahu_s = _kaal(sr_min, ss_min, RAHU_POS[wk])
        rahu_e = _kaal(sr_min + part, ss_min, RAHU_POS[wk])
        yama_s = _kaal(sr_min, ss_min, YAMAGANDA_POS[wk])
        yama_e = _kaal(sr_min + part, ss_min, YAMAGANDA_POS[wk])
        guli_s = _kaal(sr_min, ss_min, GULIKA_POS[wk])
        guli_e = _kaal(sr_min + part, ss_min, GULIKA_POS[wk])

        abh_s = _ft(sr_min + day_dur * 0.5 - 24)
        abh_e = _ft(sr_min + day_dur * 0.5 + 24)
        shubh = [{"name": "Abhijit", "startTime": abh_s, "endTime": abh_e}]
        if panch["nakshatra"] in GOOD_NAKSHATRAS_AMRIT:
            shubh.append({"name": "Amrit", "startTime": _ft(sr_min + day_dur * 0.75), "endTime": ss})

        return {
            "date": date_str, "weekday": WEEKDAY_NAMES[wk],
            "panchang": {
                "tithi": panch["tithi"], "tithiNumber": t,
                "nakshatra": panch["nakshatra"], "nakshatraNumber": panch["nakshatraNumber"],
                "yoga": panch["yoga"], "karana": panch["karana"],
                "paksha": panch["paksha"], "moonPhase": panch["moonPhase"],
            },
            "sunrise": sr, "sunset": ss,
            "rahuKaal": {"startTime": rahu_s, "endTime": rahu_e},
            "yamaganda": {"startTime": yama_s, "endTime": yama_e},
            "gulikaKaal": {"startTime": guli_s, "endTime": guli_e},
            "shubhMuhurats": shubh, "festivals": festivals, "sankranti": sankranti,
            "sunLongitude": round(sun_lon, 4),
        }
    except Exception as e:
        logger.error(f"Error computing day {date_str}: {e}", exc_info=True)
        return None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/api/calendar/year")
def year_calendar(body: YearCalendarRequest):
    months = [body.month] if body.month else list(range(1, 13))
    out: Dict[str, Any] = {}
    for m in months:
        end = _month_end(body.year, m)
        first = datetime(body.year, m, 1)
        prev_lon = _prev_sun_lon(body.year, m, body.timezone, body.latitude, body.longitude)
        days, cur = [], first
        while cur <= end:
            ds = cur.strftime("%Y-%m-%d")
            d = _compute_day(ds, body.timezone, body.latitude, body.longitude, prev_lon)
            if d:
                days.append(d)
                prev_lon = d.get("sunLongitude")
            cur += timedelta(days=1)
        out[f"{body.year}-{m:02d}"] = {
            "year": body.year, "month": m,
            "monthName": first.strftime("%B"),
            "totalDays": len(days), "days": days,
        }
    return {"status": 200, "data": out}


@router.post("/api/calendar/year/monthly-summary")
def monthly_summary(body: MonthlySummaryRequest):
    if body.month < 1 or body.month > 12:
        return {"status": 400, "data": {"error": "Invalid month"}}
    end = _month_end(body.year, body.month)
    first = datetime(body.year, body.month, 1)
    prev_lon = _prev_sun_lon(body.year, body.month, body.timezone, body.latitude, body.longitude)
    key_dates, ekadashi, purnima, amavasya, sankranti = [], [], [], [], []

    # Festival lookup for this month
    fests = [{"name": fn, "date": fd} for fn, fd in HINDU_FESTIVALS.get(body.year, {}).items()
             if parser.parse(fd).month == body.month]

    cur = first
    while cur <= end:
        ds = cur.strftime("%Y-%m-%d")
        try:
            sr, _, sr_jd, _ = sunrise_sunset(ds, body.timezone, body.latitude, body.longitude)
            if sr is None:
                cur += timedelta(days=1); continue
            panch = panchang_at_jd(sr_jd)
            t = panch["tithiNumber"]
            s_lon = _sun_lon_at_jd(sr_jd)
            sk = _detect_sankranti(prev_lon, s_lon)
            prev_lon = s_lon

            if t == 11:
                ekadashi.append({"date": ds, "name": f"{panch['paksha']} Ekadashi", "paksha": panch["paksha"]})
                key_dates.append({"date": ds, "type": "Ekadashi", "detail": f"{panch['paksha']} Ekadashi"})
            if t == 15:
                purnima.append({"date": ds}); key_dates.append({"date": ds, "type": "Purnima", "detail": "Full Moon"})
            elif t == 30:
                amavasya.append({"date": ds}); key_dates.append({"date": ds, "type": "Amavasya", "detail": "New Moon"})
            if sk:
                sankranti.append({"date": ds, "sign": sk, "detail": f"{sk} Sankranti"})
                key_dates.append({"date": ds, "type": "Sankranti", "detail": f"Sun enters {sk}"})
        except Exception as e:
            logger.error(f"Monthly summary error {ds}: {e}")
        cur += timedelta(days=1)

    key_dates.sort(key=lambda x: x["date"])
    return {"status": 200, "data": {
        "year": body.year, "month": body.month, "monthName": first.strftime("%B"),
        "summary": {"totalDays": (end - first).days + 1, "totalEkadashi": len(ekadashi),
                     "totalPurnima": len(purnima), "totalAmavasya": len(amavasya),
                     "totalSankranti": len(sankranti), "totalFestivals": len(fests)},
        "keyDates": key_dates, "ekadashi": ekadashi, "purnima": purnima,
        "amavasya": amavasya, "sankranti": sankranti, "festivals": fests,
    }}


@router.post("/api/calendar/year/auspicious-dates")
def auspicious_dates(body: AuspiciousDatesRequest):
    rules = PURPOSE_RULES.get(body.purpose.lower().strip(), PURPOSE_RULES["general"])
    months = [body.month] if body.month else list(range(1, 13))
    results: List[Dict[str, Any]] = []

    for m in months:
        if m < 1 or m > 12: continue
        end = _month_end(body.year, m)
        cur = datetime(body.year, m, 1)
        while cur <= end:
            ds = cur.strftime("%Y-%m-%d")
            wk = _wk(ds)
            try:
                sr, ss, sr_jd, _ = sunrise_sunset(ds, body.timezone, body.latitude, body.longitude)
                if sr is None:
                    cur += timedelta(days=1); continue
                panch = panchang_at_jd(sr_jd)
                t, nak = panch["tithiNumber"], panch["nakshatra"]
                sc = _day_score(t, nak, wk, rules)
                if sc >= 4:
                    sr_min, ss_min = _tm(sr), _tm(ss)
                    dur = ss_min - sr_min
                    # Two shubh windows (ghati 2-3 and 7-8)
                    wins = [{"startTime": _ft(sr_min + i * dur / 8), "endTime": _ft(sr_min + (i + 1) * dur / 8)} for i in [1, 6]]
                    reasons = []
                    pt = t if t <= 15 else t - 15
                    if pt in rules["good_tithis"]: reasons.append(f"Good tithi ({panch['tithi']})")
                    if nak in rules["good_nakshatras"]: reasons.append(f"Good nakshatra ({nak})")
                    if wk not in rules.get("avoid_weekdays", []): reasons.append(f"Good weekday ({WEEKDAY_NAMES[wk]})")
                    results.append({
                        "date": ds, "weekday": WEEKDAY_NAMES[wk], "score": sc,
                        "panchang": {"tithi": panch["tithi"], "paksha": panch["paksha"],
                                     "nakshatra": nak, "yoga": panch["yoga"], "karana": panch["karana"]},
                        "sunrise": sr, "sunset": ss,
                        "muhuratWindows": wins,
                        "rahuKaal": {"startTime": _kaal(sr_min, ss_min, RAHU_POS[wk]),
                                     "endTime": _kaal(sr_min + dur / 8, ss_min, RAHU_POS[wk])},
                        "reasons": reasons,
                    })
            except Exception as e:
                logger.error(f"Auspicious eval error {ds}: {e}")
            cur += timedelta(days=1)

    results.sort(key=lambda x: (-x["score"], x["date"]))
    return {"status": 200, "data": {"purpose": body.purpose, "totalFound": len(results), "dates": results[:50]}}
