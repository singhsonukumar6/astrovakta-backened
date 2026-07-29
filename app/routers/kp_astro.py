from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List

from ..response import success, error

router = APIRouter()


class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('P', example='P')
    nodeMode: Optional[str] = Field('mean', example='mean')


class HoraryRequest(BaseModel):
    questionDate: str = Field(..., example="2025-07-29")
    questionTime: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    question: str = Field(..., example="Will I get a job this year?")
    houseSystem: Optional[str] = Field('P', example='P')
    nodeMode: Optional[str] = Field('mean', example='mean')


KP_SIGNIFICATORS = {
    'houses': {
        1: 'Body, personality, health, honor',
        2: 'Wealth, family, speech, eyes',
        3: 'Courage, siblings, short journeys',
        4: 'Mother, home, vehicles, education',
        5: 'Children, intelligence, creativity',
        6: 'Health, debts, enemies, service',
        7: 'Spouse, marriage, partnerships',
        8: 'Longevity, obstacles, inheritance',
        9: 'Fortune, religion, guru, father',
        10: 'Career, status, government',
        11: 'Gains, desires, friendships',
        12: 'Expenses, foreign travel, spirituality',
    }
}

DASHA_YEARS_KP = {'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17}
DASHA_SEQUENCE_KP = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']


def _kp_sub_lord_for(lon: float) -> str:
    nk_start = (int(lon // 13.333333)) * 13.333333
    pos = lon - nk_start
    total = 13.333333
    accum = 0.0
    for lord in DASHA_SEQUENCE_KP:
        portion = total * (DASHA_YEARS_KP[lord] / 120.0)
        if pos < accum + portion:
            return lord
        accum += portion
    return DASHA_SEQUENCE_KP[-1]


def _kp_cuspal_lord(sign: str) -> str:
    from ..main import SIGN_LORDS
    return SIGN_LORDS.get(sign, 'Unknown')


def _get_star_lord(lon: float) -> str:
    from ..main import NAKSHATRAS
    nk_idx = int(lon // 13.333333) % 27
    return NAKSHATRAS[nk_idx][1]


@router.post('/kp/planet-details')
def kp_planet_details(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'P')

    house_list = houses.get('houses', [])
    ordered = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    planet_details = []
    for pname in ordered:
        p = next((pl for pl in planets if pl['name'] == pname), None)
        if not p:
            continue
        ph = p.get('house', 0)
        sign = p.get('sign', '')
        cuspal_lord = _kp_cuspal_lord(sign) if ph and ph <= len(house_list) else None
        star_lord = _get_star_lord(p['longitude'])
        sub_lord = _kp_sub_lord_for(p['longitude'])
        planet_details.append({
            'planet': pname,
            'longitude': round(p['longitude'], 4),
            'sign': sign,
            'house': ph,
            'cuspalLord': cuspal_lord,
            'starLord': star_lord,
            'subLord': sub_lord,
            'degree': round(p['degree'], 4),
            'isRetrograde': p.get('isRetrograde', False),
        })

    return success({
        'system': 'KP Astrology',
        'planetDetails': planet_details,
    })


@router.post('/kp/cuspal-lords')
def kp_cuspal_lords(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'P')

    house_list = houses.get('houses', [])
    cusp_details = []
    for h in house_list:
        hnum = h['number']
        sign = h['sign']
        mid_point = (h.get('degree', 0) + 15) % 360
        cuspal_lord = _kp_cuspal_lord(sign)
        star_lord = _get_star_lord(mid_point)
        sub_lord = _kp_sub_lord_for(mid_point)
        cusp_details.append({
            'cusp': hnum,
            'sign': sign,
            'signLord': h.get('signLord', ''),
            'degree': round(h.get('degree', 0), 4),
            'midPoint': round(mid_point, 4),
            'cuspalLord': cuspal_lord,
            'starLord': star_lord,
            'subLord': sub_lord,
            'signification': KP_SIGNIFICATORS['houses'].get(hnum, ''),
            'planets': h.get('planets', []),
        })

    return success({
        'system': 'KP Astrology',
        'cusps': cusp_details,
    })


@router.post('/kp/bhav-chalit')
def kp_bhav_chalit(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'P')

    house_list = houses.get('houses', [])
    bhav_chalit = []
    for h in house_list:
        hnum = h['number']
        mid = (h.get('degree', 0) + 15) % 360
        bhav_chalit.append({
            'bhava': hnum,
            'startSign': h['sign'],
            'midPoint': round(mid, 4),
            'midPointSign': ZODIAC_SIGNS[int(mid // 30) % 12],
            'planets': h.get('planets', []),
        })

    return success({
        'system': 'KP Astrology',
        'bhavChalit': bhav_chalit,
    })


@router.post('/kp/ruling-planets')
def kp_ruling_planets(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, NAKSHATRAS
    from datetime import datetime
    import pytz

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'P')

    house_list = houses.get('houses', [])
    asc_sign = houses.get('ascendant', {}).get('sign', 'Aries')
    asc_degree = houses.get('ascendant', {}).get('degree', 0)

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    asc_lord = None
    for h in house_list:
        if h['number'] == 1:
            asc_lord = h.get('signLord', '')

    ruling_planets = []
    if asc_lord:
        ruling_planets.append({
            'planet': asc_lord,
            'role': 'Ascendant Lord (Lagna Lord)',
            'house': 1,
            'sign': asc_sign,
        })

    if moon:
        moon_star = _get_star_lord(moon['longitude'])
        moon_sub = _kp_sub_lord_for(moon['longitude'])
        ruling_planets.append({
            'planet': 'Moon',
            'role': 'Moon - Mind',
            'house': moon.get('house', 0),
            'sign': moon.get('sign', ''),
            'starLord': moon_star,
            'subLord': moon_sub,
        })
        if moon_star not in [rp['planet'] for rp in ruling_planets]:
            ruling_planets.append({
                'planet': moon_star,
                'role': 'Moon\'s Star Lord',
                'house': 0,
                'sign': '',
            })
        moon_sub_lord = moon_sub
        if moon_sub_lord not in [rp['planet'] for rp in ruling_planets]:
            ruling_planets.append({
                'planet': moon_sub_lord,
                'role': 'Moon\'s Sub Lord',
                'house': 0,
                'sign': '',
            })

    day_lord_map = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    try:
        tz = pytz.timezone(body.timezone)
        dt_local = tz.localize(datetime.strptime(f"{body.dateOfBirth} {body.timeOfBirth}", "%Y-%m-%d %H:%M"))
        weekday_idx = dt_local.weekday()
        day_lord = day_lord_map[(weekday_idx + 1) % 7]
        if day_lord not in [rp['planet'] for rp in ruling_planets]:
            ruling_planets.append({
                'planet': day_lord,
                'role': 'Day Lord (Weekday Lord)',
                'house': 0,
                'sign': '',
            })
    except Exception:
        pass

    return success({
        'system': 'KP Astrology',
        'rulingPlanets': ruling_planets,
        'note': 'Ruling planets are used in KP for electional and horary astrology.',
    })


@router.post('/kp/horary')
def kp_horary(body: HoraryRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, NAKSHATRAS
    from datetime import datetime
    import pytz

    jd = to_julian(body.questionDate, body.questionTime, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'P')

    house_list = houses.get('houses', [])
    asc_sign = houses.get('ascendant', {}).get('sign', 'Aries')
    asc_degree = houses.get('ascendant', {}).get('degree', 0)

    asc_lord = None
    for h in house_list:
        if h['number'] == 1:
            asc_lord = h.get('signLord', '')

    house_to_analyze = 1
    question_lower = body.question.lower()
    house_keywords = {
        1: ['me', 'my', 'i', 'personality', 'health', 'body', 'appearance'],
        2: ['wealth', 'money', 'finance', 'family', 'speech'],
        3: ['courage', 'sibling', 'brother', 'sister', 'short trip', 'communication'],
        4: ['home', 'mother', 'vehicle', 'property', 'education', 'comfort'],
        5: ['child', 'children', 'creativity', 'love', 'romance', 'speculation'],
        6: ['health', 'disease', 'debt', 'enemy', 'service', 'litigation'],
        7: ['marriage', 'spouse', 'partner', 'relationship', 'business', 'contract'],
        8: ['life', 'death', 'inheritance', 'obstacle', 'chronic'],
        9: ['luck', 'fortune', 'father', 'guru', 'religion', 'travel'],
        10: ['career', 'job', 'profession', 'status', 'government', 'promotion'],
        11: ['gain', 'profit', 'income', 'desire', 'friend', 'wish'],
        12: ['loss', 'expense', 'foreign', 'spirituality', 'hospital', 'seclusion'],
    }
    max_score = 0
    for hnum, keywords in house_keywords.items():
        score = sum(1 for kw in keywords if kw in question_lower)
        if score > max_score:
            max_score = score
            house_to_analyze = hnum

    target_house = next((h for h in house_list if h['number'] == house_to_analyze), None)
    target_sign = target_house['sign'] if target_house else asc_sign
    target_lord = _kp_cuspal_lord(target_sign)

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    moon_star = _get_star_lord(moon['longitude']) if moon else ''
    moon_sub = _kp_sub_lord_for(moon['longitude']) if moon else ''

    asc_star = _get_star_lord(asc_degree)
    asc_sub = _kp_sub_lord_for(asc_degree)

    significators = []
    for p in planets:
        p_star = _get_star_lord(p['longitude'])
        p_sub = _kp_sub_lord_for(p['longitude'])
        is_significator = (
            p.get('house', 0) == house_to_analyze or
            p['name'] == target_lord or
            p['name'] == asc_lord or
            p_star == target_lord or
            p_star == asc_lord
        )
        if is_significator:
            significators.append({
                'planet': p['name'],
                'house': p.get('house', 0),
                'sign': p.get('sign', ''),
                'starLord': p_star,
                'subLord': p_sub,
                'role': 'House significator' if p.get('house', 0) == house_to_analyze else (
                    'Cuspal lord' if p['name'] == target_lord else (
                        'Ascendant lord' if p['name'] == asc_lord else 'Star lord significator'
                    )
                ),
            })

    favorable = len(significators) >= 3 or (moon_star in [s['planet'] for s in significators])

    return success({
        'system': 'KP Horary',
        'question': body.question,
        'questionHouse': house_to_analyze,
        'houseSignification': KP_SIGNIFICATORS['houses'].get(house_to_analyze, ''),
        'ascendantSign': asc_sign,
        'ascendantLord': asc_lord,
        'ascendantStarLord': asc_star,
        'ascendantSubLord': asc_sub,
        'targetHouseSign': target_sign,
        'targetHouseLord': target_lord,
        'rulingSignificators': significators,
        'moonStarLord': moon_star,
        'favorable': favorable,
        'prediction': (
            'The significators indicate a favorable outcome for your question.' if favorable
            else 'The significators suggest challenges. Consider waiting for a more favorable time.'
        ),
    })


@router.post('/kp/star-lords')
def kp_star_lords(body: BirthRequest):
    from ..main import to_julian, calc_planets

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')

    ordered = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    result = []
    for pname in ordered:
        p = next((pl for pl in planets if pl['name'] == pname), None)
        if not p:
            continue
        star_lord = _get_star_lord(p['longitude'])
        sub_lord = _kp_sub_lord_for(p['longitude'])
        result.append({
            'planet': pname,
            'longitude': round(p['longitude'], 4),
            'nakshatra': p.get('nakshatra', ''),
            'starLord': star_lord,
            'subLord': sub_lord,
        })

    return success({
        'system': 'KP Astrology',
        'starLordDetails': result,
    })
