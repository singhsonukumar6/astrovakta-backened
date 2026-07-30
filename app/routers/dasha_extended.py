from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import timedelta


router = APIRouter()


class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


# ---- YOGINI DASHA ----
# Classical 8 Yoginis, 36-year cycle. Each yogini ruled by a planet:
YOGINI_SEQUENCE = [
    ('Mangala', 'Moon', 1),
    ('Pingala', 'Sun', 2),
    ('Dhanya', 'Jupiter', 3),
    ('Bhramari', 'Mars', 4),
    ('Bhadrika', 'Mercury', 5),
    ('Ulka', 'Saturn', 6),
    ('Siddha', 'Venus', 7),
    ('Sankata', 'Rahu', 8),
]


def _pd_years(years: float) -> timedelta:
    return timedelta(days=int(round(years * 365.25)))


def _compute_yogini_dasha(body):
    from ..main import to_julian, calc_planets, ZODIAC_SIGNS, get_nakshatra, NAKSHATRAS
    import pytz
    from datetime import datetime

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    if not moon:
        return None

    moon_lon = moon['longitude']
    nk_idx = int(moon_lon // 13.333333) % 27
    nakshatra_name = NAKSHATRAS[nk_idx][0]

    yogini_for_nakshatra = nk_idx % 8
    start_yogini_idx = yogini_for_nakshatra

    pos_in_nk = (moon_lon % 13.333333) / 13.333333
    total_cycle_years = 36.0
    yogini_durations = [y[2] for y in YOGINI_SEQUENCE]
    total_cycle_days = sum(yogini_durations) * 365.25

    remaining_fraction = 1.0 - pos_in_nk
    first_yogini_days = remaining_fraction * YOGINI_SEQUENCE[start_yogini_idx][2] * 365.25

    tz = pytz.timezone(body.timezone)
    birth_dt = tz.localize(datetime.strptime(f"{body.dateOfBirth} {body.timeOfBirth}", "%Y-%m-%d %H:%M"))

    mahadashas = []
    cursor = birth_dt

    for cycle in range(5):
        for offset in range(8):
            yogini_idx = (start_yogini_idx + cycle * 8 + offset) % 8
            yogini_name, ruling_planet, duration_years = YOGINI_SEQUENCE[yogini_idx]

            if cycle == 0 and offset == 0:
                md_days = first_yogini_days
            else:
                md_days = duration_years * 365.25

            md_start = cursor
            md_end = md_start + _pd_years(md_days / 365.25)
            mahadashas.append({
                'yogini': yogini_name,
                'rulingPlanet': ruling_planet,
                'durationYears': duration_years,
                'startDate': md_start.date().isoformat(),
                'endDate': md_end.date().isoformat(),
            })
            cursor = md_end

            if cursor.year > birth_dt.year + 80:
                break
        if cursor.year > birth_dt.year + 80:
            break

    today_str = datetime.now(tz).date().isoformat()
    current = None
    for md in mahadashas:
        if md['startDate'] <= today_str < md['endDate']:
            current = md
            break

    return {
        'moonNakshatra': nakshatra_name,
        'startYogini': YOGINI_SEQUENCE[start_yogini_idx][0],
        'cycleYears': 36,
        'mahadashas': mahadashas,
        'current': current,
    }


YOGINI_DESCRIPTIONS = {
    'Mangala': {'nature': 'Courageous, action-oriented', 'effects': 'Energy, leadership, conflicts resolved through courage'},
    'Pingala': {'nature': 'Authoritative, radiant', 'effects': 'Authority, recognition, government favor, ego expansion'},
    'Dhanya': {'nature': 'Prosperous, abundant', 'effects': 'Wealth, material comfort, property gains, generosity'},
    'Bhramari': {'nature': 'Industrious, hard-working', 'effects': 'Consistent effort, discipline, gradual success through labor'},
    'Bhadrika': {'nature': 'Intelligent, communicative', 'effects': 'Learning, business success, social influence, wisdom'},
    'Ulka': {'nature': 'Transformative, mysterious', 'effects': 'Sudden changes, upheavals, hidden gains, research success'},
    'Siddha': {'nature': 'Accomplished, refined', 'effects': 'Artistic success, relationships bloom, spiritual elevation'},
    'Sankata': {'nature': 'Challenging, karmic', 'effects': 'Obstacles, hardships, spiritual growth through challenges'},
}


@router.post('/dasha/yogini')
def yogini_dasha(body: BirthRequest):
    result = _compute_yogini_dasha(body)
    if not result:
        return {'status': 400, 'error': 'Could not compute Moon position'}

    for md in result['mahadashas']:
        yogini = md['yogini']
        desc = YOGINI_DESCRIPTIONS.get(yogini, {})
        md['description'] = desc.get('effects', '')
        md['nature'] = desc.get('nature', '')

    return {
        'status': 200,
        'system': 'Yogini',
        'cycleYears': 36,
        'data': result,
    }


# ---- KALACHAKRA DASHA ----
# Simplified placeholder - based on Moon's nakshatra padas
KALACHAKRA_SIGNS = [
    ('Aries', 7), ('Taurus', 8), ('Gemini', 9), ('Cancer', 10),
    ('Leo', 11), ('Virgo', 12), ('Libra', 1), ('Scorpio', 2),
    ('Sagittarius', 3), ('Capricorn', 4), ('Aquarius', 5), ('Pisces', 6),
]

KALACHAKRA_LORDS = ['Saturn', 'Jupiter', 'Mars', 'Rahu', 'Sun', 'Mercury', 'Ketu', 'Moon', 'Venus']

KALACHAKRA_YEARS = {
    'Saturn': 10, 'Jupiter': 12, 'Mars': 7, 'Rahu': 18, 'Sun': 6,
    'Mercury': 17, 'Ketu': 7, 'Moon': 10, 'Venus': 20,
}


@router.post('/dasha/kalachakra')
def kalachakra_dasha(body: BirthRequest):
    from ..main import to_julian, calc_planets, ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra, NAKSHATRAS
    import pytz
    from datetime import datetime

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    if not moon:
        return {'status': 400, 'error': 'Could not compute Moon position'}

    moon_lon = moon['longitude']
    moon_sign = moon['sign']
    moon_sign_idx = ZODIAC_SIGNS.index(moon_sign)
    nk_idx = int(moon_lon // 13.333333) % 27
    pada = int(((moon_lon % 13.333333) / 13.333333) * 4) + 1

    sign_start_age = KALACHAKRA_SIGNS[moon_sign_idx][1]

    tz = pytz.timezone(body.timezone)
    birth_dt = tz.localize(datetime.strptime(f"{body.dateOfBirth} {body.timeOfBirth}", "%Y-%m-%d %H:%M"))

    sequence = []
    for i in range(9):
        lord = KALACHAKRA_LORDS[(moon_sign_idx + i) % 9]
        years = KALACHAKRA_YEARS[lord]
        sequence.append({'lord': lord, 'years': years})

    mahadashas = []
    cursor = birth_dt
    for entry in sequence:
        md_start = cursor
        md_end = md_start + _pd_years(entry['years'])
        mahadashas.append({
            'lord': entry['lord'],
            'years': entry['years'],
            'startDate': md_start.date().isoformat(),
            'endDate': md_end.date().isoformat(),
        })
        cursor = md_end

    today_str = datetime.now(tz).date().isoformat()
    current = None
    for md in mahadashas:
        if md['startDate'] <= today_str < md['endDate']:
            current = md
            break

    return {
        'status': 200,
        'system': 'Kalachakra',
        'note': 'Kalachakra Dasha - based on Moon nakshatra pada',
        'data': {
            'moonSign': moon_sign,
            'moonNakshatra': NAKSHATRAS[nk_idx][0],
            'moonPada': pada,
            'signStartAge': sign_start_age,
            'mahadashas': mahadashas,
            'current': current,
            'sequence': [{'lord': s['lord'], 'years': s['years']} for s in sequence],
        },
    }


# ---- ASHTOTTARI DASHA ----
# 108-year cycle. Based on Moon's nakshatra.
ASHTOTTARI_SEQUENCE = [
    ('Sun', 6), ('Moon', 10), ('Mars', 7), ('Rahu', 18), ('Jupiter', 16),
    ('Saturn', 19), ('Mercury', 17), ('Ketu', 7), ('Venus', 20),
]


@router.post('/dasha/ashtottari')
def ashtottari_dasha(body: BirthRequest):
    from ..main import to_julian, calc_planets, ZODIAC_SIGNS, NAKSHATRAS
    import pytz
    from datetime import datetime

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    if not moon:
        return {'status': 400, 'error': 'Could not compute Moon position'}

    moon_lon = moon['longitude']
    nk_idx = int(moon_lon // 13.333333) % 27
    nakshatra_name = NAKSHATRAS[nk_idx][0]
    pos_in_nk = (moon_lon % 13.333333) / 13.333333

    start_lord_idx = nk_idx % 9
    lords_sequence = []
    for i in range(9):
        lord_name = ASHTOTTARI_SEQUENCE[(start_lord_idx + i) % 9][0]
        lord_years = ASHTOTTARI_SEQUENCE[(start_lord_idx + i) % 9][1]
        lords_sequence.append((lord_name, lord_years))

    tz = pytz.timezone(body.timezone)
    birth_dt = tz.localize(datetime.strptime(f"{body.dateOfBirth} {body.timeOfBirth}", "%Y-%m-%d %H:%M"))

    mahadashas = []
    cursor = birth_dt
    total_years = sum(y for _, y in lords_sequence)

    for cycle in range(3):
        for lord_name, lord_years in lords_sequence:
            md_start = cursor
            md_end = md_start + _pd_years(lord_years)
            mahadashas.append({
                'lord': lord_name,
                'years': lord_years,
                'startDate': md_start.date().isoformat(),
                'endDate': md_end.date().isoformat(),
                'cycle': cycle + 1,
            })
            cursor = md_end
            if cursor.year > birth_dt.year + 120:
                break
        if cursor.year > birth_dt.year + 120:
            break

    today_str = datetime.now(tz).date().isoformat()
    current = None
    for md in mahadashas:
        if md['startDate'] <= today_str < md['endDate']:
            current = md
            break

    return {
        'status': 200,
        'system': 'Ashtottari',
        'cycleYears': 108,
        'note': 'Ashtottari Dasha - 108-year cycle based on Moon nakshatra',
        'data': {
            'moonNakshatra': nakshatra_name,
            'startLord': lords_sequence[0][0],
            'cycleYears': 108,
            'sequence': [{'lord': l, 'years': y} for l, y in lords_sequence],
            'mahadashas': mahadashas,
            'current': current,
        },
    }
