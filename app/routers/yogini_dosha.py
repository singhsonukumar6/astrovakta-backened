from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ..response import success, error

router = APIRouter()


class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


YOGINI_NAKSHATRA_MAP = [
    (0, 'Mangala'), (1, 'Mangala'), (2, 'Mangala'),
    (3, 'Pingala'), (4, 'Pingala'), (5, 'Pingala'),
    (6, 'Dhanya'), (7, 'Dhanya'), (8, 'Dhanya'),
    (9, 'Bhramari'), (10, 'Bhramari'), (11, 'Bhramari'),
    (12, 'Bhadrika'), (13, 'Bhadrika'), (14, 'Bhadrika'),
    (15, 'Ulka'), (16, 'Ulka'), (17, 'Ulka'),
    (18, 'Siddha'), (19, 'Siddha'), (20, 'Siddha'),
    (21, 'Sankata'), (22, 'Sankata'), (23, 'Sankata'),
    (24, 'Mangala'), (25, 'Pingala'), (26, 'Dhanya'),
]

YOGINI_DOSHA_RULES = {
    'Mangala': {
        'name': 'Mangala Yogini',
        'nature': 'Aggressive, fiery',
        'effects': 'Can cause obstacles in marriage, temperament issues, property disputes',
        'doshaType': 'Moderate',
        'remedies': ['Chant Mangala Yogini mantra', 'Offer red flowers on Tuesdays', 'Fast on Tuesdays']
    },
    'Pingala': {
        'name': 'Pingala Yogini',
        'nature': 'Passionate, authoritative',
        'effects': 'May cause dominance issues in relationships, power struggles',
        'doshaType': 'Moderate',
        'remedies': ['Chant Pingala Yogini mantra', 'Donate yellow items on Thursdays', 'Worship Lord Vishnu']
    },
    'Dhanya': {
        'name': 'Dhanya Yogini',
        'nature': 'Prosperous, abundant',
        'effects': 'Generally benefic, no major dosha effects. Brings material comfort.',
        'doshaType': 'Benefic',
        'remedies': []
    },
    'Bhramari': {
        'name': 'Bhramari Yogini',
        'nature': 'Industrious, disciplined',
        'effects': 'May cause delays in marriage, but good for career growth',
        'doshaType': 'Mild',
        'remedies': ['Chant Bhramari Yogini mantra', 'Worship Goddess Durga', 'Donate white items on Mondays']
    },
    'Bhadrika': {
        'name': 'Bhadrika Yogini',
        'nature': 'Noble, communicative',
        'effects': 'Benefic for communication and education. Slight delays in marriage.',
        'doshaType': 'Mild',
        'remedies': ['Chant Bhadrika Yogini mantra', 'Donate green items on Wednesdays']
    },
    'Ulka': {
        'name': 'Ulka Yogini',
        'nature': 'Mysterious, transformative',
        'effects': 'Can cause sudden changes in relationships, hidden enemies',
        'doshaType': 'Moderate',
        'remedies': ['Chant Ulka Yogini mantra', 'Perform Rahu-Ketu shanti', 'Worship Lord Shiva']
    },
    'Siddha': {
        'name': 'Siddha Yogini',
        'nature': 'Accomplished, mystical',
        'effects': 'Benefic - brings spiritual growth, success in occult sciences',
        'doshaType': 'Benefic',
        'remedies': []
    },
    'Sankata': {
        'name': 'Sankata Yogini',
        'nature': 'Challenging, karmic',
        'effects': 'Can cause major obstacles, delays in marriage, financial challenges',
        'doshaType': 'Severe',
        'remedies': ['Chant Sankata Yogini mantra', 'Perform Navagraha Shanti', 'Visit temples on Saturdays', 'Chant Hanuman Chalisa']
    },
}


@router.post('/yogini/dosha')
def yogini_dosha(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, NAKSHATRAS
    import pytz
    from datetime import datetime

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    if not moon:
        return error('Could not compute Moon position', 400)

    moon_lon = moon['longitude']
    nk_idx = int(moon_lon // 13.333333) % 27
    nakshatra_name = NAKSHATRAS[nk_idx][0]
    nakshatra_lord = NAKSHATRAS[nk_idx][1]

    yogini_name = None
    for nk_start, y_name in YOGINI_NAKSHATRA_MAP:
        if nk_start == nk_idx:
            yogini_name = y_name
            break

    dosha_info = YOGINI_DOSHA_RULES.get(yogini_name, {})
    is_dosha = dosha_info.get('doshaType') in ('Moderate', 'Severe')

    ascendant = houses.get('ascendant', {})
    asc_sign = ascendant.get('sign', 'Unknown')
    asc_lord = None
    from ..main import SIGN_LORDS
    asc_lord = SIGN_LORDS.get(asc_sign) if asc_sign != 'Unknown' else None

    from ..main import ZODIAC_SIGNS as zs
    sun = next((p for p in planets if p['name'] == 'Sun'), None)
    mars = next((p for p in planets if p['name'] == 'Mars'), None)
    saturn = next((p for p in planets if p['name'] == 'Saturn'), None)

    additional_factors = []
    if mars and mars.get('house') in [1, 4, 7, 8, 12]:
        additional_factors.append('Mars in dosha house - amplifies yogini effects')
    if saturn and saturn.get('house') in [1, 8]:
        additional_factors.append('Saturn in 1st/8th house - karmic amplification')
    if sun and sun.get('house') == 7:
        additional_factors.append('Sun in 7th house - affects marriage')

    severity = 'Mild'
    severity_score = 0
    if is_dosha:
        severity_score += 2 if dosha_info.get('doshaType') == 'Severe' else 1
        if additional_factors:
            severity_score += 1
        severity = 'High' if severity_score >= 3 else ('Moderate' if severity_score >= 2 else 'Mild')

    return success({
            'moonNakshatra': nakshatra_name,
            'moonNakshatraLord': nakshatra_lord,
            'moonNakshatraNumber': nk_idx + 1,
            'yogini': yogini_name,
            'yoginiNature': dosha_info.get('nature', ''),
            'isDosha': is_dosha,
            'doshaType': dosha_info.get('doshaType', 'None'),
            'severity': severity,
            'effects': dosha_info.get('effects', ''),
            'remedies': dosha_info.get('remedies', []),
            'additionalFactors': additional_factors,
            'ascendantSign': asc_sign,
            'ascendantLord': asc_lord,
    }, "Yogini Dosha")
