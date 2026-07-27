from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


router = APIRouter()


class HinduCalendarRequest(BaseModel):
    year: int = Field(..., example=2026)
    month: int = Field(..., example=7)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


class PanchangRequest(BaseModel):
    year: int = Field(..., example=2026)
    month: int = Field(..., example=7)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


class FestivalRequest(BaseModel):
    year: int = Field(..., example=2026)
    latitude: Optional[float] = Field(28.6139, example=28.6139)
    longitude: Optional[float] = Field(77.2090, example=77.2090)
    timezone: Optional[str] = Field("Asia/Kolkata", example="Asia/Kolkata")


class MuhuratRequest(BaseModel):
    year: int = Field(..., example=2026)
    month: int = Field(..., example=7)
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    activity: Optional[str] = Field(None, example="marriage")


MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

HINDU_MONTH_NAMES = ['', 'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
                     'Ashwini', 'Kartik', 'Margashirsha', 'Pausa', 'Magha', 'Phalguna']

TITHI_NAMES_FULL = [
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami',
    'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami',
    'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'
]


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28
    if month in [4, 6, 9, 11]:
        return 30
    return 31


def _compute_panchang_for_day(year: int, month: int, day: int, lat: float, lon: float, tz: str) -> Dict[str, Any]:
    from ..main import to_julian, panchang_at_jd, sunrise_sunset
    date_str = f"{year}-{month:02d}-{day:02d}"
    jd = to_julian(date_str, '12:00', tz)
    panchang = panchang_at_jd(jd)
    sr, ss, sr_jd, _ = sunrise_sunset(date_str, tz, lat, lon)
    panchang['sunrise'] = sr
    panchang['sunset'] = ss
    panchang['date'] = date_str
    panchang['day'] = day
    return panchang


@router.post('/calendar-api/hindu')
def hindu_calendar(body: HinduCalendarRequest):
    days = _days_in_month(body.year, body.month)
    calendar_days = []

    for day in range(1, days + 1):
        panchang = _compute_panchang_for_day(body.year, body.month, day, body.latitude, body.longitude, body.timezone)
        tithi_num = panchang.get('tithiNumber', 1)
        paksha = panchang.get('paksha', 'Shukla')

        hindu_month_idx = (body.month - 1) % 12
        if tithi_num == 15 and paksha == 'Krishna':
            hindu_month_idx = (hindu_month_idx + 1) % 12
        if body.month == 3 and day <= 14:
            hindu_month_idx = 0

        calendar_days.append({
            'date': f"{body.year}-{body.month:02d}-{day:02d}",
            'day': day,
            'tithi': panchang['tithi'],
            'tithiNumber': tithi_num,
            'paksha': paksha,
            'nakshatra': panchang['nakshatra'],
            'yoga': panchang['yoga'],
            'karana': panchang['karana'],
            'sunrise': panchang.get('sunrise'),
            'sunset': panchang.get('sunset'),
            'moonPhase': panchang.get('moonPhase'),
            'hinduMonth': HINDU_MONTH_NAMES[hindu_month_idx + 1],
        })

    return {
        'status': 200,
        'data': {
            'year': body.year,
            'month': body.month,
            'monthName': MONTH_NAMES[body.month],
            'totalDays': days,
            'calendar': calendar_days,
        },
    }


@router.post('/calendar-api/panchang')
def panchang_month(body: PanchangRequest):
    days = _days_in_month(body.year, body.month)
    panchang_data = []

    for day in range(1, days + 1):
        panchang = _compute_panchang_for_day(body.year, body.month, day, body.latitude, body.longitude, body.timezone)
        panchang_data.append(panchang)

    tithi_summary = {}
    nakshatra_summary = {}
    for entry in panchang_data:
        t = entry['tithi']
        nk = entry['nakshatra']
        tithi_summary[t] = tithi_summary.get(t, 0) + 1
        nakshatra_summary[nk] = nakshatra_summary.get(nk, 0) + 1

    return {
        'status': 200,
        'data': {
            'year': body.year,
            'month': body.month,
            'monthName': MONTH_NAMES[body.month],
            'totalDays': days,
            'panchang': panchang_data,
            'summary': {
                'tithiDistribution': tithi_summary,
                'nakshatraDistribution': nakshatra_summary,
            },
        },
    }


@router.post('/calendar-api/festival')
def festival_list(body: FestivalRequest):
    festivals_by_month = {
        1: [
            {'name': 'Makar Sankranti', 'date': f'{body.year}-01-14', 'type': 'Sankranti', 'significance': 'Sun enters Capricorn'},
            {'name': 'Pongal', 'date': f'{body.year}-01-14', 'type': 'Harvest Festival', 'significance': 'Thanksgiving for harvest'},
        ],
        2: [
            {'name': 'Vasant Panchami', 'date': f'{body.year}-02-02', 'type': 'Puja', 'significance': 'Saraswati worship, spring onset'},
            {'name': 'Maha Shivaratri', 'date': f'{body.year}-02-26', 'type': 'Fasting', 'significance': 'Night of Lord Shiva'},
        ],
        3: [
            {'name': 'Holi', 'date': f'{body.year}-03-10', 'type': 'Festival', 'significance': 'Festival of colors'},
            {'name': 'Chaitra Navratri begins', 'date': f'{body.year}-03-28', 'type': 'Festival', 'significance': 'Nine nights of Goddess Durga'},
        ],
        4: [
            {'name': 'Ugadi / Gudi Padwa', 'date': f'{body.year}-04-06', 'type': 'New Year', 'significance': 'Hindu New Year'},
            {'name': 'Ram Navami', 'date': f'{body.year}-04-15', 'type': 'Puja', 'significance': 'Birth of Lord Rama'},
            {'name': 'Chaitra Navratri ends', 'date': f'{body.year}-04-06', 'type': 'Festival', 'significance': 'Completion of Navratri'},
        ],
        5: [
            {'name': 'Akshaya Tritiya', 'date': f'{body.year}-05-01', 'type': 'Auspicious Day', 'significance': 'Eternal day of prosperity'},
        ],
        6: [
            {'name': 'Ganga Dussehra', 'date': f'{body.year}-06-05', 'type': 'Holy Bath', 'significance': 'Descent of Ganga'},
            {'name': 'Jyeshtha Amavasya', 'date': f'{body.year}-06-24', 'type': 'Amavasya', 'significance': 'New moon day for ancestral worship'},
        ],
        7: [
            {'name': 'Ashadha Ekadashi', 'date': f'{body.year}-07-10', 'type': 'Fasting', 'significance': 'Devshayani Ekadashi'},
        ],
        8: [
            {'name': 'Nag Panchami', 'date': f'{body.year}-08-14', 'type': 'Puja', 'significance': 'Worship of serpent gods'},
            {'name': 'Raksha Bandhan', 'date': f'{body.year}-08-19', 'type': 'Festival', 'significance': 'Brother-sister bond'},
            {'name': 'Krishna Janmashtami', 'date': f'{body.year}-08-26', 'type': 'Festival', 'significance': 'Birth of Lord Krishna'},
        ],
        9: [
            {'name': 'Ganesh Chaturthi', 'date': f'{body.year}-09-17', 'type': 'Festival', 'significance': 'Birth of Lord Ganesha'},
        ],
        10: [
            {'name': 'Navratri begins', 'date': f'{body.year}-10-12', 'type': 'Festival', 'significance': 'Nine nights of Goddess Durga'},
            {'name': 'Dussehra', 'date': f'{body.year}-10-21', 'type': 'Festival', 'significance': 'Victory of good over evil'},
        ],
        11: [
            {'name': 'Diwali', 'date': f'{body.year}-11-08', 'type': 'Festival', 'significance': 'Festival of lights'},
            {'name': 'Govardhan Puja', 'date': f'{body.year}-11-09', 'type': 'Puja', 'significance': 'Worship of Govardhan Hill'},
            {'name': 'Bhai Dooj', 'date': f'{body.year}-11-10', 'type': 'Festival', 'significance': 'Brother-sister celebration'},
        ],
        12: [
            {'name': 'Margashirsha Purnima', 'date': f'{body.year}-12-04', 'type': 'Purnima', 'significance': 'Full moon for spiritual practices'},
        ],
    }

    all_festivals = []
    for month_num, fests in festivals_by_month.items():
        for f in fests:
            f['month'] = month_num
            all_festivals.append(f)

    return {
        'status': 200,
        'data': {
            'year': body.year,
            'totalFestivals': len(all_festivals),
            'festivals': all_festivals,
            'festivalsByMonth': {m: fests for m, fests in festivals_by_month.items()},
        },
    }


@router.post('/calendar-api/muhurat')
def muhurat_month(body: MuhuratRequest):
    from ..main import to_julian, sunrise_sunset
    days = _days_in_month(body.year, body.month)

    MUHURAT_TYPES = {
        'marriage': {'duration': '2-3 hours', 'avoidTithis': ['Dwadashi', 'Chaturdashi', 'Ashtami', 'Navami'], 'bestTithis': ['Dwitiya', 'Tritiya', 'Panchami', 'Saptami', 'Dashami']},
        'housewarming': {'duration': '1-2 hours', 'avoidTithis': ['Chaturdashi', 'Amavasya'], 'bestTithis': ['Panchami', 'Shashthi', 'Dashami', 'Ekadashi']},
        'vehicle': {'duration': '1 hour', 'avoidTithis': ['Chaturdashi', 'Amavasya'], 'bestTithis': ['Tritiya', 'Panchami', 'Saptami', 'Dashami']},
        'business': {'duration': '1-2 hours', 'avoidTithis': ['Ashtami', 'Chaturdashi', 'Amavasya'], 'bestTithis': ['Pratipada', 'Dwitiya', 'Panchami', 'Ekadashi']},
        'default': {'duration': '1-2 hours', 'avoidTithis': ['Chaturdashi', 'Amavasya', 'Ashtami'], 'bestTithis': ['Dwitiya', 'Panchami', 'Dashami', 'Ekadashi']},
    }

    activity = (body.activity or 'default').lower()
    muhurat_config = MUHURAT_TYPES.get(activity, MUHURAT_TYPES['default'])

    muhurat_data = []
    for day in range(1, days + 1):
        panchang = _compute_panchang_for_day(body.year, body.month, day, body.latitude, body.longitude, body.timezone)
        sr, ss, _, _ = sunrise_sunset(f"{body.year}-{body.month:02d}-{day:02d}", body.timezone, body.latitude, body.longitude)
        tithi = panchang['tithi']
        is_auspicious = tithi not in muhurat_config['avoidTithis'] and tithi in muhurat_config['bestTithis']

        muhurat_data.append({
            'date': f"{body.year}-{body.month:02d}-{day:02d}",
            'day': day,
            'tithi': tithi,
            'nakshatra': panchang['nakshatra'],
            'yoga': panchang['yoga'],
            'sunrise': sr,
            'sunset': ss,
            'isAuspicious': is_auspicious,
            'muhuratTime': f"{sr} - {sr}" if sr else 'Calculating...',
            'activity': activity,
        })

    auspicious_days = [m for m in muhurat_data if m['isAuspicious']]

    return {
        'status': 200,
        'data': {
            'year': body.year,
            'month': body.month,
            'monthName': MONTH_NAMES[body.month],
            'activity': activity,
            'muhuratConfig': muhurat_config,
            'totalDays': days,
            'auspiciousDays': len(auspicious_days),
            'calendar': muhurat_data,
            'bestDays': [{'date': m['date'], 'tithi': m['tithi'], 'nakshatra': m['nakshatra']} for m in auspicious_days[:5]],
        },
    }
