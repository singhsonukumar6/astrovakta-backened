from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timedelta
import swisseph as swe
import pytz

router = APIRouter()


class PanchangRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


def _get_sunrise_sunset_jd(date_str: str, tz_name: str, lat: float, lon: float):
    """Get sunrise and sunset as Julian Day values."""
    tz = pytz.timezone(tz_name)
    dt_local = tz.localize(datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0))
    dt_utc = dt_local.astimezone(pytz.utc)
    jd0 = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60.0)

    geopos = (lon, lat, 0.0)
    press = 1013.25
    temp = 15.0

    rsmi_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    rsmi_set = swe.CALC_SET | swe.BIT_DISC_CENTER

    res_rise, tret_rise = swe.rise_trans(jd0, swe.SUN, rsmi_rise, geopos, press, temp, swe.FLG_SWIEPH)
    res_set, tret_set = swe.rise_trans(jd0, swe.SUN, rsmi_set, geopos, press, temp, swe.FLG_SWIEPH)

    if res_rise != 0 or res_set != 0:
        return None, None
    return tret_rise[0], tret_set[0]


def _jd_to_local(jd: float, tz_name: str) -> datetime:
    """Convert Julian Day to local timezone-aware datetime."""
    tz = pytz.timezone(tz_name)
    y, m, d, h = swe.revjul(jd)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    dt_utc = datetime(y, m, d, hh, mm, tzinfo=pytz.utc)
    return dt_utc.astimezone(tz)


def _jd_to_time_str(jd: float, tz_name: str) -> str:
    """Convert Julian Day to HH:MM local time string."""
    dt_local = _jd_to_local(jd, tz_name)
    return dt_local.strftime("%H:%M")


def _get_weekday(date_str: str, tz_name: str) -> int:
    """Get weekday index (0=Sunday, 6=Saturday)."""
    tz = pytz.timezone(tz_name)
    dt = tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    return dt.weekday()  # Monday=0 ... Sunday=6


def _get_weekday_sun_first(date_str: str, tz_name: str) -> int:
    """Get weekday index with Sunday=0 (Indian convention)."""
    wd = _get_weekday(date_str, tz_name)
    return (wd + 1) % 7  # Sunday=0, Monday=1, ..., Saturday=6


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _jd_to_hhmmss(jd: float) -> str:
    """Convert Julian Day time portion to HH:MM:SS string."""
    y, m, d, h = swe.revjul(jd)
    hh = int(h)
    mm = int((h - hh) * 60)
    ss = int(((h - hh) * 60 - mm) * 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


# --- Rahu Kaal ---
def _calc_rahu_kaal(sunrise_jd: float, sunset_jd: float, weekday: int) -> Dict[str, Any]:
    """Calculate Rahu Kaal. Weekday: 0=Sunday ... 6=Saturday."""
    day_duration = (sunset_jd - sunrise_jd) * 86400.0
    part_duration = day_duration / 8.0

    rahu_part_map = {
        0: 3,  # Sunday -> 4th part (index 3)
        1: 1,  # Monday -> 2nd part (index 1)
        2: 6,  # Tuesday -> 7th part (index 6)
        3: 4,  # Wednesday -> 5th part (index 4)
        4: 5,  # Thursday -> 6th part (index 5)
        5: 2,  # Friday -> 3rd part (index 2)
        6: 7,  # Saturday -> 8th part (index 7)
    }

    part_idx = rahu_part_map[weekday]
    start_jd = sunrise_jd + (part_idx * part_duration) / 86400.0
    end_jd = start_jd + part_duration / 86400.0

    return {
        "start_jd": start_jd,
        "end_jd": end_jd,
        "partIndex": part_idx + 1,
        "totalParts": 8,
        "partDuration": part_duration,
    }


# --- Gulika Kaal ---
def _calc_gulika_kaal(sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, weekday: int) -> Dict[str, Any]:
    """Calculate Gulika Kaal. Based on sunset-to-next-sunrise division."""
    night_duration = (next_sunrise_jd - sunset_jd) * 86400.0
    part_duration = night_duration / 8.0

    gulika_part_map = {
        0: 6,  # Sunday -> 7th part (index 6)
        1: 5,  # Monday -> 6th part (index 5)
        2: 4,  # Tuesday -> 5th part (index 4)
        3: 3,  # Wednesday -> 4th part (index 3)
        4: 2,  # Thursday -> 3rd part (index 2)
        5: 1,  # Friday -> 2nd part (index 1)
        6: 0,  # Saturday -> 1st part (index 0)
    }

    part_idx = gulika_part_map[weekday]
    start_jd = sunset_jd + (part_idx * part_duration) / 86400.0
    end_jd = start_jd + part_duration / 86400.0

    return {
        "start_jd": start_jd,
        "end_jd": end_jd,
        "partIndex": part_idx + 1,
        "totalParts": 8,
        "partDuration": part_duration,
    }


# --- Yamaganda ---
def _calc_yamaganda(sunrise_jd: float, sunset_jd: float, weekday: int) -> Dict[str, Any]:
    """Calculate Yamaganda Kaal."""
    day_duration = (sunset_jd - sunrise_jd) * 86400.0
    part_duration = day_duration / 8.0

    yama_part_map = {
        0: 3,  # Sunday -> 4th part (index 3)
        1: 2,  # Monday -> 3rd part (index 2)
        2: 1,  # Tuesday -> 2nd part (index 1)
        3: 0,  # Wednesday -> 1st part (index 0)
        4: 7,  # Thursday -> 8th part (index 7)
        5: 6,  # Friday -> 7th part (index 6)
        6: 5,  # Saturday -> 6th part (index 5)
    }

    part_idx = yama_part_map[weekday]
    start_jd = sunrise_jd + (part_idx * part_duration) / 86400.0
    end_jd = start_jd + part_duration / 86400.0

    return {
        "start_jd": start_jd,
        "end_jd": end_jd,
        "partIndex": part_idx + 1,
        "totalParts": 8,
        "partDuration": part_duration,
    }


# --- Choghadiya ---
def _calc_choghadiya(sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, weekday: int) -> Dict[str, Any]:
    """Calculate Day and Night Choghadiya (8 periods each)."""
    day_names = ["Amrit", "Shubh", "Labh", "Char", "Kaal", "Rog", "Udveg", "Chog"]
    night_names = ["Shubh", "Amrit", "Char", "Labh", "Rog", "Kaal", "Udveg", "Chog"]

    # Rotate starting choghadiya based on weekday
    day_start_idx = weekday % 8
    night_start_idx = weekday % 8

    day_duration = (sunset_jd - sunrise_jd) * 86400.0
    night_duration = (next_sunrise_jd - sunset_jd) * 86400.0

    day_part = day_duration / 8.0
    night_part = night_duration / 8.0

    day_choghadiya = []
    for i in range(8):
        name_idx = (day_start_idx + i) % 8
        start_jd = sunrise_jd + (i * day_part) / 86400.0
        end_jd = start_jd + day_part / 86400.0
        day_choghadiya.append({
            "name": day_names[name_idx],
            "start": _jd_to_time_str(start_jd, "UTC"),
            "end": _jd_to_time_str(end_jd, "UTC"),
            "startJd": start_jd,
            "endJd": end_jd,
        })

    night_choghadiya = []
    for i in range(8):
        name_idx = (night_start_idx + i) % 8
        start_jd = sunset_jd + (i * night_part) / 86400.0
        end_jd = start_jd + night_part / 86400.0
        night_choghadiya.append({
            "name": night_names[name_idx],
            "start": _jd_to_time_str(start_jd, "UTC"),
            "end": _jd_to_time_str(end_jd, "UTC"),
            "startJd": start_jd,
            "endJd": end_jd,
        })

    return {
        "dayChoghadiya": day_choghadiya,
        "nightChoghadiya": night_choghadiya,
        "dayDuration": day_duration,
        "nightDuration": night_duration,
    }


# --- Hora ---
def _calc_hora(sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, weekday: int) -> List[Dict[str, Any]]:
    """Calculate 24 hora periods from sunrise. Planet sequence: Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars (repeating)."""
    hora_planets = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
    total_day_duration = (sunset_jd - sunrise_jd) * 86400.0
    total_night_duration = (next_sunrise_jd - sunset_jd) * 86400.0

    day_hora_duration = total_day_duration / 12.0
    night_hora_duration = total_night_duration / 12.0

    # First hora lord is determined by weekday
    first_lord_idx = weekday % 7

    horas = []
    for i in range(24):
        lord_idx = (first_lord_idx + i) % 7
        planet = hora_planets[lord_idx]

        if i < 12:
            # Day hora
            start_jd = sunrise_jd + (i * day_hora_duration) / 86400.0
            end_jd = start_jd + day_hora_duration / 86400.0
            period = "Day"
        else:
            # Night hora
            night_i = i - 12
            start_jd = sunset_jd + (night_i * night_hora_duration) / 86400.0
            end_jd = start_jd + night_hora_duration / 86400.0
            period = "Night"

        horas.append({
            "number": i + 1,
            "planet": planet,
            "period": period,
            "startJd": start_jd,
            "endJd": end_jd,
        })

    return horas


# --- Moonrise/Moonset ---
def _calc_moon_event(date_str: str, tz_name: str, lat: float, lon: float, is_rise: bool) -> Dict[str, Any]:
    """Calculate moonrise or moonset."""
    tz = pytz.timezone(tz_name)
    dt_local = tz.localize(datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0))
    dt_utc = dt_local.astimezone(pytz.utc)
    jd0 = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60.0)

    geopos = (lon, lat, 0.0)
    press = 1013.25
    temp = 15.0

    if is_rise:
        rsmi = swe.CALC_RISE | swe.BIT_DISC_CENTER
    else:
        rsmi = swe.CALC_SET | swe.BIT_DISC_CENTER

    res, tret = swe.rise_trans(jd0, swe.MOON, rsmi, geopos, press, temp, swe.FLG_SWIEPH)

    if res != 0:
        return {
            "found": False,
            "time": None,
            "julianDay": None,
            "message": "Moon does not rise/set on this day at this location (circumpolar)",
        }

    event_jd = tret[0]
    local_dt = _jd_to_local(event_jd, tz_name)

    return {
        "found": True,
        "time": local_dt.strftime("%H:%M:%S"),
        "timeFormatted": local_dt.strftime("%I:%M %p"),
        "julianDay": event_jd,
        "utcTime": local_dt.astimezone(pytz.utc).strftime("%H:%M:%S"),
    }


# --- Abhijit Muhurat ---
def _calc_abhijit_muhurat(sunrise_jd: float, sunset_jd: float) -> Dict[str, Any]:
    """Calculate Abhijit Muhurat window (midday auspicious period)."""
    day_duration_jd = sunset_jd - sunrise_jd
    day_duration_sec = day_duration_jd * 86400.0

    # Abhijit is the middle 1/15th of daytime
    abhijit_duration = day_duration_sec / 15.0
    half_abhijit = abhijit_duration / 2.0

    midday_jd = sunrise_jd + day_duration_jd / 2.0
    start_jd = midday_jd - half_abhijit / 86400.0
    end_jd = midday_jd + half_abhijit / 86400.0

    return {
        "startJd": start_jd,
        "endJd": end_jd,
        "duration": abhijit_duration,
        "durationFormatted": _format_duration(abhijit_duration),
    }


# --- Endpoints ---

@router.post("/panchang/rahu-kaal")
def rahu_kaal(body: PanchangRequest):
    sunrise_jd, sunset_jd = _get_sunrise_sunset_jd(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
    if sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate sunrise/sunset for given location"}

    weekday = _get_weekday_sun_first(body.dateOfBirth, body.timezone)
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    result = _calc_rahu_kaal(sunrise_jd, sunset_jd, weekday)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "weekday": weekday_names[weekday],
            "sunrise": _jd_to_time_str(sunrise_jd, body.timezone),
            "sunset": _jd_to_time_str(sunset_jd, body.timezone),
            "rahuKaalStart": _jd_to_time_str(result["start_jd"], body.timezone),
            "rahuKaalEnd": _jd_to_time_str(result["end_jd"], body.timezone),
            "partIndex": result["partIndex"],
            "totalParts": result["totalParts"],
            "duration": _format_duration(result["partDuration"]),
        },
    }


@router.post("/panchang/gulika-kaal")
def gulika_kaal(body: PanchangRequest):
    sunrise_jd, sunset_jd = _get_sunrise_sunset_jd(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
    if sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate sunrise/sunset for given location"}

    # Get next day sunrise for night division
    from datetime import timedelta as td
    next_date = (datetime.strptime(body.dateOfBirth, "%Y-%m-%d") + td(days=1)).strftime("%Y-%m-%d")
    next_sunrise_jd, _ = _get_sunrise_sunset_jd(next_date, body.timezone, body.latitude, body.longitude)
    if next_sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate next day sunrise"}

    weekday = _get_weekday_sun_first(body.dateOfBirth, body.timezone)
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    result = _calc_gulika_kaal(sunrise_jd, sunset_jd, next_sunrise_jd, weekday)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "weekday": weekday_names[weekday],
            "sunrise": _jd_to_time_str(sunrise_jd, body.timezone),
            "sunset": _jd_to_time_str(sunset_jd, body.timezone),
            "gulikaKaalStart": _jd_to_time_str(result["start_jd"], body.timezone),
            "gulikaKaalEnd": _jd_to_time_str(result["end_jd"], body.timezone),
            "partIndex": result["partIndex"],
            "totalParts": result["totalParts"],
            "duration": _format_duration(result["partDuration"]),
        },
    }


@router.post("/panchang/yamaganda")
def yamaganda(body: PanchangRequest):
    sunrise_jd, sunset_jd = _get_sunrise_sunset_jd(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
    if sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate sunrise/sunset for given location"}

    weekday = _get_weekday_sun_first(body.dateOfBirth, body.timezone)
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    result = _calc_yamaganda(sunrise_jd, sunset_jd, weekday)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "weekday": weekday_names[weekday],
            "sunrise": _jd_to_time_str(sunrise_jd, body.timezone),
            "sunset": _jd_to_time_str(sunset_jd, body.timezone),
            "yamagandaStart": _jd_to_time_str(result["start_jd"], body.timezone),
            "yamagandaEnd": _jd_to_time_str(result["end_jd"], body.timezone),
            "partIndex": result["partIndex"],
            "totalParts": result["totalParts"],
            "duration": _format_duration(result["partDuration"]),
        },
    }


@router.post("/panchang/choghadiya")
def choghadiya(body: PanchangRequest):
    sunrise_jd, sunset_jd = _get_sunrise_sunset_jd(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
    if sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate sunrise/sunset for given location"}

    from datetime import timedelta as td
    next_date = (datetime.strptime(body.dateOfBirth, "%Y-%m-%d") + td(days=1)).strftime("%Y-%m-%d")
    next_sunrise_jd, _ = _get_sunrise_sunset_jd(next_date, body.timezone, body.latitude, body.longitude)
    if next_sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate next day sunrise"}

    weekday = _get_weekday_sun_first(body.dateOfBirth, body.timezone)
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    result = _calc_choghadiya(sunrise_jd, sunset_jd, next_sunrise_jd, weekday)

    # Convert UTC times to local times
    for period in ["dayChoghadiya", "nightChoghadiya"]:
        for ch in result[period]:
            # Convert start/end JDs to local time
            ch["start"] = _jd_to_time_str(ch["startJd"], body.timezone)
            ch["end"] = _jd_to_time_str(ch["endJd"], body.timezone)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "weekday": weekday_names[weekday],
            "sunrise": _jd_to_time_str(sunrise_jd, body.timezone),
            "sunset": _jd_to_time_str(sunset_jd, body.timezone),
            "dayChoghadiya": result["dayChoghadiya"],
            "nightChoghadiya": result["nightChoghadiya"],
        },
    }


@router.post("/panchang/hora")
def hora(body: PanchangRequest):
    sunrise_jd, sunset_jd = _get_sunrise_sunset_jd(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
    if sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate sunrise/sunset for given location"}

    from datetime import timedelta as td
    next_date = (datetime.strptime(body.dateOfBirth, "%Y-%m-%d") + td(days=1)).strftime("%Y-%m-%d")
    next_sunrise_jd, _ = _get_sunrise_sunset_jd(next_date, body.timezone, body.latitude, body.longitude)
    if next_sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate next day sunrise"}

    weekday = _get_weekday_sun_first(body.dateOfBirth, body.timezone)
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    horas = _calc_hora(sunrise_jd, sunset_jd, next_sunrise_jd, weekday)

    # Convert to local time
    for hora_item in horas:
        hora_item["start"] = _jd_to_time_str(hora_item["startJd"], body.timezone)
        hora_item["end"] = _jd_to_time_str(hora_item["endJd"], body.timezone)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "weekday": weekday_names[weekday],
            "sunrise": _jd_to_time_str(sunrise_jd, body.timezone),
            "sunset": _jd_to_time_str(sunset_jd, body.timezone),
            "horas": horas,
        },
    }


@router.post("/panchang/moonrise")
def moonrise(body: PanchangRequest):
    result = _calc_moon_event(body.dateOfBirth, body.timezone, body.latitude, body.longitude, is_rise=True)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "location": {"latitude": body.latitude, "longitude": body.longitude},
            "moonrise": result,
        },
    }


@router.post("/panchang/moonset")
def moonset(body: PanchangRequest):
    result = _calc_moon_event(body.dateOfBirth, body.timezone, body.latitude, body.longitude, is_rise=False)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "location": {"latitude": body.latitude, "longitude": body.longitude},
            "moonset": result,
        },
    }


@router.post("/panchang/abhijit-muhurat")
def abhijit_muhurat(body: PanchangRequest):
    sunrise_jd, sunset_jd = _get_sunrise_sunset_jd(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
    if sunrise_jd is None:
        return {"status": 400, "error": "Unable to calculate sunrise/sunset for given location"}

    result = _calc_abhijit_muhurat(sunrise_jd, sunset_jd)

    return {
        "status": 200,
        "data": {
            "date": body.dateOfBirth,
            "sunrise": _jd_to_time_str(sunrise_jd, body.timezone),
            "sunset": _jd_to_time_str(sunset_jd, body.timezone),
            "abhijitStart": _jd_to_time_str(result["startJd"], body.timezone),
            "abhijitEnd": _jd_to_time_str(result["endJd"], body.timezone),
            "duration": result["durationFormatted"],
        },
    }
