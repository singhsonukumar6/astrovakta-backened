from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import calendar

from ..utils import to_julian, panchang_at_jd, sunrise_sunset

router = APIRouter()


class HinduCalendarRequest(BaseModel):
    year: int = Field(..., example=2025)
    month: int = Field(..., ge=1, le=12, example=6)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


class PanchangRequest(BaseModel):
    year: int = Field(..., example=2025)
    month: int = Field(..., ge=1, le=12, example=6)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


class FestivalCalendarRequest(BaseModel):
    year: int = Field(..., example=2025)


class MuhuratRequest(BaseModel):
    year: int = Field(..., example=2025)
    month: int = Field(..., ge=1, le=12, example=6)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


NAKSHATRAS = [
    ('Ashwini', 'Ketu'), ('Bharani', 'Venus'), ('Krittika', 'Sun'),
    ('Rohini', 'Moon'), ('Mrigashira', 'Mars'), ('Ardra', 'Rahu'),
    ('Punarvasu', 'Jupiter'), ('Pushya', 'Saturn'), ('Ashlesha', 'Mercury'),
    ('Magha', 'Ketu'), ('Purva Phalguni', 'Venus'), ('Uttara Phalguni', 'Sun'),
    ('Hasta', 'Moon'), ('Chitra', 'Mars'), ('Swati', 'Rahu'),
    ('Vishakha', 'Jupiter'), ('Anuradha', 'Saturn'), ('Jyeshtha', 'Mercury'),
    ('Mula', 'Ketu'), ('Purva Ashadha', 'Venus'), ('Uttara Ashadha', 'Sun'),
    ('Shravana', 'Moon'), ('Dhanishta', 'Mars'), ('Shatabhisha', 'Rahu'),
    ('Purva Bhadrapada', 'Jupiter'), ('Uttara Bhadrapada', 'Saturn'), ('Revati', 'Mercury')
]

TITHI_NAMES = [
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
    'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
    'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'
]


FESTIVALS_DATA: Dict[int, List[Dict[str, str]]] = {
    2025: [
        {"date": "2025-01-14", "name": "Makar Sankranti", "type": "Sankranti"},
        {"date": "2025-01-26", "name": "Basant Panchami", "type": "Festival"},
        {"date": "2025-02-26", "name": "Maha Shivaratri", "type": "Major"},
        {"date": "2025-03-14", "name": "Holi", "type": "Major"},
        {"date": "2025-03-30", "name": "Ugadi", "type": "Regional"},
        {"date": "2025-04-06", "name": "Ram Navami", "type": "Festival"},
        {"date": "2025-04-12", "name": "Hanuman Jayanti", "type": "Festival"},
        {"date": "2025-04-30", "name": "Akshaya Tritiya", "type": "Festival"},
        {"date": "2025-06-05", "name": "Ganga Dussehra", "type": "Festival"},
        {"date": "2025-07-10", "name": "Guru Purnima", "type": "Festival"},
        {"date": "2025-08-15", "name": "Krishna Janmashtami", "type": "Major"},
        {"date": "2025-08-27", "name": "Ganesh Chaturthi", "type": "Major"},
        {"date": "2025-09-22", "name": "Navratri Start", "type": "Major"},
        {"date": "2025-10-01", "name": "Dussehra", "type": "Major"},
        {"date": "2025-10-20", "name": "Diwali", "type": "Major"},
        {"date": "2025-11-04", "name": "Guru Nanak Jayanti", "type": "Festival"},
    ],
    2024: [
        {"date": "2024-01-14", "name": "Makar Sankranti", "type": "Sankranti"},
        {"date": "2024-02-14", "name": "Vasant Panchami", "type": "Festival"},
        {"date": "2024-03-08", "name": "Maha Shivaratri", "type": "Major"},
        {"date": "2024-03-25", "name": "Holi", "type": "Major"},
        {"date": "2024-04-17", "name": "Ram Navami", "type": "Festival"},
        {"date": "2024-04-23", "name": "Hanuman Jayanti", "type": "Festival"},
        {"date": "2024-05-10", "name": "Akshaya Tritiya", "type": "Festival"},
        {"date": "2024-07-21", "name": "Guru Purnima", "type": "Festival"},
        {"date": "2024-08-26", "name": "Krishna Janmashtami", "type": "Major"},
        {"date": "2024-09-07", "name": "Ganesh Chaturthi", "type": "Major"},
        {"date": "2024-10-03", "name": "Navratri Start", "type": "Major"},
        {"date": "2024-10-12", "name": "Dussehra", "type": "Major"},
        {"date": "2024-11-01", "name": "Diwali", "type": "Major"},
        {"date": "2024-11-15", "name": "Guru Nanak Jayanti", "type": "Festival"},
    ],
}


def generate_muhurat_windows(date_str: str, sunrise_time: str, sunset_time: str, nakshatra: str) -> List[Dict[str, Any]]:
    if not sunrise_time or not sunset_time:
        return []

    try:
        sr_h, sr_m = map(int, sunrise_time.split(':'))
        ss_h, ss_m = map(int, sunset_time.split(':'))
        day_minutes = (ss_h * 60 + ss_m) - (sr_h * 60 + sr_m)
        if day_minutes <= 0:
            return []
    except (ValueError, AttributeError):
        return []

    muhurats = [
        {"name": "Abhijit Muhurta", "duration": "36 min", "description": "Most auspicious time for starting new ventures", "startOffset": int(day_minutes * 0.45), "endOffset": int(day_minutes * 0.45 + 36)},
        {"name": "Brahma Muhurta", "duration": "96 min", "description": "Ideal for spiritual practices and meditation", "startOffset": -96, "endOffset": 0},
        {"name": "Amrit Ghadi", "duration": "48 min", "description": "Good for travel and new beginnings", "startOffset": int(day_minutes * 0.25), "endOffset": int(day_minutes * 0.25 + 48)},
        {"name": "Shubh Muhurta", "duration": "60 min", "description": "Auspicious for important activities", "startOffset": int(day_minutes * 0.35), "endOffset": int(day_minutes * 0.35 + 60)},
        {"name": "Labh Ghadi", "duration": "48 min", "description": "Good for financial activities and investments", "startOffset": int(day_minutes * 0.6), "endOffset": int(day_minutes * 0.6 + 48)},
    ]

    result = []
    sr_total_min = sr_h * 60 + sr_m
    for m in muhurats:
        if m["startOffset"] < 0:
            start_h, start_m = divmod(sr_total_min + m["startOffset"], 60)
        else:
            start_h, start_m = divmod(sr_total_min + m["startOffset"], 60)
        end_h, end_m = divmod(sr_total_min + m["endOffset"], 60)
        result.append({
            "name": m["name"],
            "description": m["description"],
            "startTime": f"{int(start_h):02d}:{int(start_m):02d}",
            "endTime": f"{int(end_h):02d}:{int(end_m):02d}",
            "duration": m["duration"]
        })
    return result


@router.post("/calendar/hindu")
def hindu_calendar(req: HinduCalendarRequest):
    year = req.year
    month = req.month
    num_days = calendar.monthrange(year, month)[1]
    daily_data = []

    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        try:
            sr, ss, sr_jd, _ = sunrise_sunset(date_str, req.timezone, req.latitude, req.longitude)
            panch = panchang_at_jd(sr_jd) if sr_jd else {}
        except Exception:
            panch = {}

        daily_data.append({
            "date": date_str,
            "day": day,
            "tithi": panch.get('tithi', 'Unknown'),
            "tithiNumber": panch.get('tithiNumber', 0),
            "nakshatra": panch.get('nakshatra', 'Unknown'),
            "nakshatraNumber": panch.get('nakshatraNumber', 0),
            "yoga": panch.get('yoga', 'Unknown'),
            "karana": panch.get('karana', 'Unknown'),
            "paksha": panch.get('paksha', 'Unknown'),
            "sunrise": sr,
            "sunset": ss
        })

    month_names = ["", "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
                   "Ashwin", "Kartik", "Margashirsha", "Pausha", "Magha", "Phalguna"]

    return {
        "status": 200,
        "data": {
            "year": year,
            "month": month,
            "hinduMonth": month_names[month] if month <= 12 else "Unknown",
            "days": daily_data,
            "totalDays": len(daily_data),
            "note": "Hindu month names are approximate - actual Hindu calendar months may differ based on regional calendars"
        }
    }


@router.post("/calendar/panchang")
def panchang_calendar(req: PanchangRequest):
    year = req.year
    month = req.month
    num_days = calendar.monthrange(year, month)[1]
    panchang_data = []

    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        try:
            sr, ss, sr_jd, _ = sunrise_sunset(date_str, req.timezone, req.latitude, req.longitude)
            panch = panchang_at_jd(sr_jd) if sr_jd else {}
        except Exception:
            panch = {}

        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        try:
            dt = datetime(year, month, day)
            weekday = weekday_names[dt.weekday()]
        except ValueError:
            weekday = "Unknown"

        panchang_data.append({
            "date": date_str,
            "day": day,
            "weekday": weekday,
            "tithi": panch.get('tithi', 'Unknown'),
            "tithiNumber": panch.get('tithiNumber', 0),
            "nakshatra": panch.get('nakshatra', 'Unknown'),
            "nakshatraNumber": panch.get('nakshatraNumber', 0),
            "yoga": panch.get('yoga', 'Unknown'),
            "karana": panch.get('karana', 'Unknown'),
            "paksha": panch.get('paksha', 'Unknown'),
            "moonPhase": panch.get('moonPhase', 'Unknown'),
            "sunrise": sr,
            "sunset": ss
        })

    return {
        "status": 200,
        "data": {
            "year": year,
            "month": month,
            "panchang": panchang_data,
            "totalDays": len(panchang_data)
        }
    }


@router.post("/calendar/festival")
def festival_calendar(req: FestivalCalendarRequest):
    year = req.year
    festivals = FESTIVALS_DATA.get(year, FESTIVALS_DATA.get(2025, []))

    monthly_festivals: Dict[int, List[Dict[str, str]]] = {}
    for f in festivals:
        month = int(f["date"].split("-")[1])
        if month not in monthly_festivals:
            monthly_festivals[month] = []
        monthly_festivals[month].append(f)

    return {
        "status": 200,
        "data": {
            "year": year,
            "totalFestivals": len(festivals),
            "festivals": festivals,
            "monthlyBreakdown": {str(m): flist for m, flist in sorted(monthly_festivals.items())},
            "majorFestivals": [f for f in festivals if f["type"] == "Major"],
            "note": "Festival dates are approximate. Actual dates may vary based on regional calendars and local traditions."
        }
    }


@router.post("/calendar/muhurat")
def muhurat_calendar(req: MuhuratRequest):
    year = req.year
    month = req.month
    num_days = calendar.monthrange(year, month)[1]
    muhurat_data = []

    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        try:
            sr, ss, sr_jd, _ = sunrise_sunset(date_str, req.timezone, req.latitude, req.longitude)
            panch = panchang_at_jd(sr_jd) if sr_jd else {}
        except Exception:
            panch = {}
            sr, ss = None, None

        nakshatra = panch.get('nakshatra', 'Unknown')
        muhurats = generate_muhurat_windows(date_str, sr, ss, nakshatra)

        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        try:
            dt = datetime(year, month, day)
            weekday = weekday_names[dt.weekday()]
        except ValueError:
            weekday = "Unknown"

        muhurat_data.append({
            "date": date_str,
            "day": day,
            "weekday": weekday,
            "sunrise": sr,
            "sunset": ss,
            "nakshatra": nakshatra,
            "tithi": panch.get('tithi', 'Unknown'),
            "muhurats": muhurats
        })

    return {
        "status": 200,
        "data": {
            "year": year,
            "month": month,
            "muhurats": muhurat_data,
            "totalDays": len(muhurat_data),
            "note": "Muhurat times are approximate. For precise calculations, please consult a Vedic astrologer."
        }
    }
