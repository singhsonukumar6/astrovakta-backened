from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import math
import pytz

from ..utils import to_julian, calc_planets, sunrise_sunset, ZODIAC_SIGNS
import swisseph as swe

router = APIRouter()


class AyanamsaRequest(BaseModel):
    date: str = Field(..., example="2025-01-15")
    time: Optional[str] = Field("12:00", example="12:00")
    timezone: Optional[str] = Field("Asia/Kolkata", example="Asia/Kolkata")


class EphemerisRequest(BaseModel):
    date: str = Field(..., example="2025-06-15")
    time: Optional[str] = Field("12:00", example="12:00")
    timezone: Optional[str] = Field("Asia/Kolkata", example="Asia/Kolkata")
    nodeMode: Optional[str] = Field("mean", example="mean")


class PlanetSpeedRequest(BaseModel):
    date: str = Field(..., example="2025-06-15")
    time: Optional[str] = Field("12:00", example="12:00")
    timezone: Optional[str] = Field("Asia/Kolkata", example="Asia/Kolkata")
    nodeMode: Optional[str] = Field("mean", example="mean")


class LunarPhaseRequest(BaseModel):
    date: str = Field(..., example="2025-06-15")
    time: Optional[str] = Field("12:00", example="12:00")
    timezone: Optional[str] = Field("Asia/Kolkata", example="Asia/Kolkata")


class EclipseRequest(BaseModel):
    date: str = Field(..., example="2025-06-15")
    time: Optional[str] = Field("12:00", example="12:00")
    timezone: Optional[str] = Field("Asia/Kolkata", example="Asia/Kolkata")
    rangeDays: Optional[int] = Field(30, ge=1, le=90, example=30)


class SunriseSunsetRequest(BaseModel):
    date: str = Field(..., example="2025-06-15")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


class JulianDayRequest(BaseModel):
    date: str = Field(..., example="2025-06-15")
    time: str = Field(..., example="12:00")
    timezone: str = Field(..., example="Asia/Kolkata")


def get_moon_phase_name(moon_age: float) -> str:
    if moon_age < 1.84566:
        return "New Moon (Amavasya)"
    elif moon_age < 5.53699:
        return "Waxing Crescent (Shukla Pratipada to Panchami)"
    elif moon_age < 9.22831:
        return "First Quarter (Shukla Shashthi to Dashami)"
    elif moon_age < 12.91963:
        return "Waxing Gibbous (Shukla Ekadashi to Chaturdashi)"
    elif moon_age < 14.76530:
        return "Full Moon (Purnima)"
    elif moon_age < 18.45662:
        return "Waning Gibbous (Krishna Pratipada to Chaturthi)"
    elif moon_age < 22.14794:
        return "Last Quarter (Krishna Panchami to Dashami)"
    elif moon_age < 25.83927:
        return "Waning Crescent (Krishna Ekadashi to Chaturdashi)"
    elif moon_age < 29.53059:
        return "Balsamic Moon (Approaching New Moon)"
    else:
        return "New Moon (Amavasya)"


@router.post("/utility/ayanamsa")
def calculate_ayanamsa(req: AyanamsaRequest):
    try:
        jd = to_julian(req.date, req.time or "12:00", req.timezone or "Asia/Kolkata")
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        ayan = swe.get_ayanamsa(jd)

        return {
            "status": 200,
            "data": {
                "date": req.date,
                "time": req.time or "12:00",
                "timezone": req.timezone or "Asia/Kolkata",
                "julianDay": jd,
                "ayanamsa": "Lahiri",
                "ayanamsaValue": round(ayan, 6),
                "ayanamsaDMS": f"{int(ayan)}°{int((ayan % 1) * 60)}'{int(((ayan * 60) % 1) * 60)}\"",
                "note": "Lahiri ayanamsa is used for sidereal zodiac calculations in Vedic astrology"
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error calculating ayanamsa"}


@router.post("/utility/ephemeris")
def ephemeris_positions(req: EphemerisRequest):
    try:
        jd = to_julian(req.date, req.time or "12:00", req.timezone or "Asia/Kolkata")
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        planets = []
        planet_ids = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO
        }

        for name, pid in planet_ids.items():
            try:
                xx, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
                lon, lat, dist, lon_spd, lat_spd, dist_spd = xx[0], xx[1], xx[2], xx[3], xx[4], xx[5]
                sign = ZODIAC_SIGNS[int(lon // 30) % 12]
                deg_in_sign = lon % 30

                planets.append({
                    "name": name,
                    "longitude": round(lon, 6),
                    "latitude": round(lat, 6),
                    "distance": round(dist, 6),
                    "longitudeSpeed": round(lon_spd, 6),
                    "latitudeSpeed": round(lat_spd, 6),
                    "distanceSpeed": round(dist_spd, 6),
                    "sign": sign,
                    "degreeInSign": round(deg_in_sign, 4),
                    "isRetrograde": lon_spd < 0 if name not in ['Sun', 'Moon'] else False,
                    "longitudeDMS": f"{int(lon % 360)}°{int((lon % 1) * 60)}'{int(((lon * 60) % 1) * 60)}\""
                })
            except Exception as ex:
                planets.append({"name": name, "error": str(ex)})

        ayan = swe.get_ayanamsa(jd)

        return {
            "status": 200,
            "data": {
                "date": req.date,
                "time": req.time or "12:00",
                "timezone": req.timezone or "Asia/Kolkata",
                "julianDay": jd,
                "ayanamsa": round(ayan, 6),
                "zodiacType": "Sidereal (Lahiri)",
                "planets": planets,
                "totalPlanets": len([p for p in planets if 'error' not in p])
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error calculating ephemeris"}


@router.post("/utility/planet-speed")
def planet_speed(req: PlanetSpeedRequest):
    try:
        jd = to_julian(req.date, req.time or "12:00", req.timezone or "Asia/Kolkata")
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        speeds = []
        planet_ids = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
            'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN
        }

        for name, pid in planet_ids.items():
            try:
                xx, _ = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
                lon_spd = xx[3]
                speeds.append({
                    "name": name,
                    "speedDegreesPerDay": round(lon_spd, 6),
                    "speedDMS": f"{int(abs(lon_spd))}°{int((abs(lon_spd) % 1) * 60)}'{int(((abs(lon_spd) * 60) % 1) * 60)}\"",
                    "isRetrograde": lon_spd < 0,
                    "motion": "Retrograde" if lon_spd < 0 else "Direct"
                })
            except Exception as ex:
                speeds.append({"name": name, "error": str(ex)})

        return {
            "status": 200,
            "data": {
                "date": req.date,
                "time": req.time or "12:00",
                "julianDay": jd,
                "planetSpeeds": speeds,
                "unit": "degrees per day"
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error calculating planet speeds"}


@router.post("/utility/lunar-phase")
def lunar_phase(req: LunarPhaseRequest):
    try:
        jd = to_julian(req.date, req.time or "12:00", req.timezone or "Asia/Kolkata")
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        xs, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        xm, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        sun_lon = xs[0]
        moon_lon = xm[0]

        diff = (moon_lon - sun_lon) % 360.0
        moon_age = diff / 12.7503  # approximately 29.53059 day cycle / 360 degrees
        illumination = (1 - math.cos(math.radians(diff))) / 2 * 100
        phase_name = get_moon_phase_name(moon_age)

        tithi_num = int(diff // 12) + 1
        paksha = 'Shukla' if tithi_num <= 15 else 'Krishna'

        return {
            "status": 200,
            "data": {
                "date": req.date,
                "time": req.time or "12:00",
                "julianDay": jd,
                "moonLongitude": round(moon_lon, 6),
                "sunLongitude": round(sun_lon, 6),
                "angularDifference": round(diff, 6),
                "moonAge": round(moon_age, 2),
                "illuminationPercentage": round(illumination, 2),
                "phaseName": phase_name,
                "tithi": tithi_num,
                "paksha": paksha,
                "isWaxing": diff < 180,
                "nextFullMoon": "Approximately when moon reaches 180° from Sun",
                "nextNewMoon": "Approximately when moon reaches 0°/360° from Sun"
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error calculating lunar phase"}


@router.post("/utility/eclipse")
def check_eclipse(req: EclipseRequest):
    try:
        jd = to_julian(req.date, req.time or "12:00", req.timezone or "Asia/Kolkata")
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        range_days = req.rangeDays or 30

        xs, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        xm, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        sun_lon = xs[0]
        moon_lon = xm[0]

        sun_moon_diff = (sun_lon - moon_lon) % 360.0
        if sun_moon_diff > 180:
            sun_moon_diff = 360 - sun_moon_diff

        solar_eclipse_possible = sun_moon_diff < 18
        lunar_eclipse_possible = abs(sun_moon_diff - 180) < 18

        eclipses = []
        if solar_eclipse_possible:
            eclipses.append({
                "type": "Solar Eclipse (Surya Grahan)",
                "possible": True,
                "angularSeparation": round(sun_moon_diff, 2),
                "description": "Sun and Moon are within 18 degrees - solar eclipse possible near this date",
                "intensity": "Strong" if sun_moon_diff < 10 else "Moderate"
            })
        if lunar_eclipse_possible:
            eclipses.append({
                "type": "Lunar Eclipse (Chandra Grahan)",
                "possible": True,
                "angularSeparation": round(abs(sun_moon_diff - 180), 2),
                "description": "Sun and Moon are approximately opposite (180 degrees) - lunar eclipse possible",
                "intensity": "Strong" if abs(sun_moon_diff - 180) < 10 else "Moderate"
            })

        if not eclipses:
            eclipses.append({
                "type": "No Eclipse",
                "possible": False,
                "angularSeparation": round(sun_moon_diff, 2),
                "description": "No solar or lunar eclipse alignment detected near this date"
            })

        return {
            "status": 200,
            "data": {
                "date": req.date,
                "time": req.time or "12:00",
                "julianDay": jd,
                "sunLongitude": round(sun_lon, 6),
                "moonLongitude": round(moon_lon, 6),
                "sunMoonDifference": round(sun_moon_diff, 2),
                "eclipses": eclipses,
                "checkRange": f"{range_days} days",
                "note": "This is a simplified check based on angular alignment. Precise eclipse predictions require Besselian elements and topocentric calculations."
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error checking eclipse"}


@router.post("/utility/sunrise-sunset")
def get_sunrise_sunset(req: SunriseSunsetRequest):
    try:
        result = sunrise_sunset(req.date, req.timezone, req.latitude, req.longitude)
        sr, ss, sr_jd, ss_jd = result

        return {
            "status": 200,
            "data": {
                "date": req.date,
                "location": {
                    "latitude": req.latitude,
                    "longitude": req.longitude,
                    "timezone": req.timezone
                },
                "sunrise": sr,
                "sunset": ss,
                "sunriseJulianDay": round(sr_jd, 6) if sr_jd else None,
                "sunsetJulianDay": round(ss_jd, 6) if ss_jd else None,
                "note": "Times are in local timezone. Calculations based on Swiss Ephemeris with atmospheric refraction correction."
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error calculating sunrise/sunset"}


@router.post("/utility/julian-day")
def julian_day_conversion(req: JulianDayRequest):
    try:
        jd = to_julian(req.date, req.time, req.timezone)

        return {
            "status": 200,
            "data": {
                "input": {
                    "date": req.date,
                    "time": req.time,
                    "timezone": req.timezone
                },
                "julianDayNumber": jd,
                "julianDayInteger": int(jd),
                "fractionalDay": round(jd % 1, 6),
                "julianCentury": round((jd - 2451545.0) / 36525.0, 6),
                "modifiedJulianDay": round(jd - 2400000.5, 6),
                "note": "Julian Day Number starts at noon (12:00 UTC) on January 1, 4713 BC"
            }
        }
    except Exception as e:
        return {"status": 500, "error": str(e), "message": "Error converting to Julian Day"}
