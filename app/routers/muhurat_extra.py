from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pytz
import swisseph as swe

from ..utils import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS, planet_status, sunrise_sunset

router = APIRouter()

class CesareanRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    preferredDate: Optional[str] = Field(None, example="2026-08-15", description="Preferred date for C-section")
    preferredTime: Optional[str] = Field(None, example="09:00", description="Preferred time window")


_AUSPICIOUS_NAKSHATRAS = ['Ashwini', 'Pushya', 'Hasta', 'Swati', 'Anuradha', 'Mrigashira', 'Revati', 'Shatabhisha']
_INAuspicious_NAKSHATRAS = ['Ashlesha', 'Jyeshtha', 'Moola', 'Bharani', 'Krittika', 'Magha', 'Vishakha']
_BENEFIC_SIGNS = ['Taurus', 'Cancer', 'Leo', 'Libra', 'Sagittarius', 'Pisces', 'Gemini']
_MALEFIC_SIGNS = ['Aries', 'Scorpio', 'Capricorn', 'Aquarius']


def _check_muhurat(jd, latitude, longitude, tz_name):
    """Check a Julian day for cesarean muhurat quality."""
    score = 0
    reasons = []

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    # Moon nakshatra
    try:
        xm = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        moon_lon = xm[0][0]
        nk_idx = int(moon_lon // 13.333333) % 27
        nak = NAKSHATRAS[nk_idx][0]
        if nak in _AUSPICIOUS_NAKSHATRAS:
            score += 30
            reasons.append(f"Moon in auspicious Nakshatra: {nak}")
        elif nak in _INAuspicious_NAKSHATRAS:
            score -= 20
            reasons.append(f"Moon in inauspicious Nakshatra: {nak}")
        else:
            score += 10
            reasons.append(f"Moon in neutral Nakshatra: {nak}")
    except Exception:
        nak = "Unknown"

    # Ascendant sign
    try:
        hs = swe.houses(jd, latitude, longitude, b'W')
        asc_lon = hs[1][0]
        asc_sign_idx = int(asc_lon // 30)
        asc_sign = ZODIAC_SIGNS[asc_sign_idx]
        if asc_sign in _BENEFIC_SIGNS:
            score += 20
            reasons.append(f"Ascendant in benefic sign: {asc_sign}")
        elif asc_sign in _MALEFIC_SIGNS:
            score -= 10
            reasons.append(f"Ascendant in malefic sign: {asc_sign}")
        else:
            score += 5
    except Exception:
        asc_sign = "Unknown"

    # Tithi
    try:
        xm = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        xs = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        diff = (xm[0][0] - xs[0][0]) % 360
        tithi = int(diff / 12) + 1
        if tithi in [2, 3, 5, 7, 10, 11, 13]:
            score += 15
            reasons.append(f"Auspicious Tithi: {tithi}")
        elif tithi in [4, 8, 9, 14]:
            score -= 10
            reasons.append(f"Inauspicious Tithi: {tithi}")
        else:
            score += 5
    except Exception:
        tithi = 0

    # Day lord
    try:
        dt_utc = swe.jdet_to_datetime(jd)
        weekday = int(swe.day_of_week(jd))
        day_lords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        day_lord = day_lords[weekday]
        if day_lord in ['Jupiter', 'Venus', 'Mercury', 'Moon']:
            score += 15
            reasons.append(f"{day_lord} day is favorable")
        elif day_lord in ['Saturn', 'Mars']:
            score -= 10
            reasons.append(f"{day_lord} day is less favorable")
        else:
            score += 5
    except Exception:
        day_lord = "Unknown"

    # Rahu Kaal check (avoid)
    try:
        sr, ss, sr_jd, ss_jd = sunrise_sunset(
            swe.jdet_to_datetime(jd).strftime('%Y-%m-%d'), tz_name, latitude, longitude
        )
        if sr_jd and ss_jd:
            day_duration = (ss_jd - sr_jd) / 8.0
            weekday = int(swe.day_of_week(sr_jd))
            rahu_start_idx = [1, 7, 6, 5, 4, 3, 2][weekday]
            rahu_start = sr_jd + rahu_start_idx * day_duration
            rahu_end = rahu_start + day_duration
            if not (rahu_start <= jd <= rahu_end):
                score += 10
                reasons.append("Time is outside Rahu Kaal")
            else:
                score -= 15
                reasons.append("Time falls in Rahu Kaal — avoid")
    except Exception:
        pass

    if score >= 50:
        quality = "Excellent"
    elif score >= 30:
        quality = "Good"
    elif score >= 10:
        quality = "Moderate"
    else:
        quality = "Not Recommended"

    return {"score": score, "quality": quality, "reasons": reasons, "nakshatra": nak, "ascendant": asc_sign}


@router.post("/horoscope/muhurat/cesarean")
def cesarean_muhurat(body: CesareanRequest) -> Dict[str, Any]:
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    tz = pytz.timezone(body.timezone)

    if body.preferredDate:
        target_date = datetime.strptime(body.preferredDate, "%Y-%m-%d").date()
    else:
        now = datetime.now(tz)
        target_date = now.date() + timedelta(days=7)

    # Find best 2-hour windows across 5 days starting from target date
    best_windows = []
    for day_offset in range(5):
        check_date = target_date + timedelta(days=day_offset)
        for hour in range(6, 20, 2):  # 6am to 8pm
            check_dt = tz.localize(datetime.combine(check_date, datetime.min.time().replace(hour=hour)))
            check_jd = to_julian(check_date.isoformat(), f"{hour:02d}:00", body.timezone)
            result = _check_muhurat(check_jd, body.latitude, body.longitude, body.timezone)
            best_windows.append({
                "date": check_date.isoformat(),
                "timeWindow": f"{hour:02d}:00 - {hour+2:02d}:00",
                **result
            })

    best_windows.sort(key=lambda x: x['score'], reverse=True)
    top_windows = best_windows[:5]

    return {
        "success": True,
        "data": {
            "searchPeriod": {"from": target_date.isoformat(), "to": (target_date + timedelta(days=4)).isoformat()},
            "bestWindows": top_windows,
            "overallBest": top_windows[0] if top_windows else None,
            "note": "This muhurat is based on Vedic astrological principles. Always consult your medical team for medical decisions.",
            "factors": ["Nakshatra", "Tithi", "Ascendant", "Day Lord", "Rahu Kaal avoidance"]
        }
    }
