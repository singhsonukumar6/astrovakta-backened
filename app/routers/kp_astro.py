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
        cusp_degree = h.get('degree', 0)
        cuspal_lord = _kp_cuspal_lord(sign)
        star_lord = _get_star_lord(cusp_degree)
        sub_lord = _kp_sub_lord_for(cusp_degree)
        cusp_details.append({
            'cusp': hnum,
            'sign': sign,
            'signLord': h.get('signLord', ''),
            'cuspDegree': round(cusp_degree, 4),
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
    cusp_degrees = [h.get('degree', 0) for h in house_list]
    bhav_chalit = []
    for i, h in enumerate(house_list):
        hnum = h['number']
        start_deg = h.get('degree', 0)
        next_deg = cusp_degrees[(i + 1) % 12]
        if next_deg < start_deg:
            next_deg += 360
        mid = (start_deg + next_deg) / 2 % 360
        bhav_chalit.append({
            'bhava': hnum,
            'cuspDegree': round(start_deg, 4),
            'startSign': h['sign'],
            'midPoint': round(mid, 4),
            'midPointSign': ZODIAC_SIGNS[int(mid // 30) % 12],
            'starLord': _get_star_lord(mid),
            'subLord': _kp_sub_lord_for(mid),
            'planets': h.get('planets', []),
        })

    return success({
        'system': 'KP Astrology',
        'bhavChalit': bhav_chalit,
    })


@router.post('/kp/ruling-planets')
def kp_ruling_planets(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, NAKSHATRAS, SIGN_LORDS
    from ..utils import planet_status
    from datetime import datetime
    import pytz

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'P')
    pmap = {p['name']: p for p in planets}

    house_list = houses.get('houses', [])
    asc_sign = houses.get('ascendant', {}).get('sign', 'Aries')
    asc_degree = houses.get('ascendant', {}).get('degree', 0)
    asc_lord = SIGN_LORDS.get(asc_sign, '')
    asc_star_lord = _get_star_lord(asc_degree)
    asc_sub_lord = _kp_sub_lord_for(asc_degree)

    moon = pmap.get('Moon')
    moon_sign_lord = SIGN_LORDS.get(moon['sign'], '') if moon else ''
    moon_star_lord = _get_star_lord(moon['longitude']) if moon else ''
    moon_sub_lord = _kp_sub_lord_for(moon['longitude']) if moon else ''

    tz = pytz.timezone(body.timezone)
    dt_local = tz.localize(datetime.strptime(f"{body.dateOfBirth} {body.timeOfBirth}", "%Y-%m-%d %H:%M"))
    day_lord_map = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    day_lord = day_lord_map[(dt_local.weekday() + 1) % 7]

    def _has_lord(lord_name):
        return any(rp['planet'] == lord_name for rp in ruling_planets)

    def _planet_details(pname):
        p = pmap.get(pname)
        if p:
            return {
                'planet': pname,
                'sign': p['sign'],
                'house': p['house'],
                'longitude': round(p['longitude'], 4),
                'degree': round(p['degree'], 4),
                'isRetrograde': p.get('isRetrograde', False),
                'isCombust': p.get('isCombust', False),
                'starLord': _get_star_lord(p['longitude']),
                'subLord': _kp_sub_lord_for(p['longitude']),
                'houseStatus': planet_status(pname, p['sign']),
            }
        return {
            'planet': pname,
            'sign': '',
            'house': 0,
            'longitude': 0,
            'degree': 0,
            'isRetrograde': False,
            'isCombust': False,
            'starLord': '',
            'subLord': '',
            'houseStatus': '',
        }

    ruling_planets = []

    ruling_planets.append({
        **_planet_details(asc_lord),
        'role': 'Lagna Lord',
        'source': f'Ascendant sign {asc_sign}',
    })
    ruling_planets.append({
        **_planet_details(asc_star_lord),
        'role': 'Lagna Star Lord',
        'source': f'Ascendant nakshatra star lord',
    })
    ruling_planets.append({
        **_planet_details(asc_sub_lord),
        'role': 'Lagna Sub Lord',
        'source': f'Ascendant KP sub lord',
    })

    if moon:
        ruling_planets.append({
            **_planet_details(moon_sign_lord),
            'role': 'Moon Sign Lord',
            'source': f'Moon in sign {moon["sign"]}',
        })
        ruling_planets.append({
            **_planet_details(moon_star_lord),
            'role': 'Moon Star Lord',
            'source': f'Moon nakshatra star lord',
        })
        ruling_planets.append({
            **_planet_details(moon_sub_lord),
            'role': 'Moon Sub Lord',
            'source': f'Moon KP sub lord',
        })

    if not _has_lord(day_lord):
        ruling_planets.append({
            **_planet_details(day_lord),
            'role': 'Day Lord',
            'source': f'Weekday {dt_local.strftime("%A")}',
        })

    deduped = []
    seen = set()
    for rp in ruling_planets:
        key = (rp['planet'], rp['role'])
        if key not in seen:
            seen.add(key)
            deduped.append(rp)

    return success({
        'system': 'KP Astrology',
        'ascendant': {
            'sign': asc_sign,
            'degree': round(asc_degree, 4),
            'lord': asc_lord,
            'starLord': asc_star_lord,
            'subLord': asc_sub_lord,
        },
        'moon': {
            'sign': moon['sign'] if moon else '',
            'longitude': round(moon['longitude'], 4) if moon else 0,
            'signLord': moon_sign_lord,
            'starLord': moon_star_lord,
            'subLord': moon_sub_lord,
        } if moon else None,
        'day': {
            'weekday': dt_local.strftime('%A'),
            'lord': day_lord,
        },
        'rulingPlanets': deduped,
        'note': 'The 6+1 classical KP ruling planets: Lagna Lord, Lagna Star Lord, Lagna Sub Lord, Moon Sign Lord, Moon Star Lord, Moon Sub Lord, and Day Lord. Used for KP electional (muhurat) and horary (prashna) astrology.',
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
