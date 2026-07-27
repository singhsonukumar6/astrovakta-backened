from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import pytz

router = APIRouter()


class TransitRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    transitDate: Optional[str] = Field(None, example="2025-07-15", description="Transit date (defaults to today)")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


class TransitPlanet:
    def __init__(self, name: str, natal_sign: str, natal_house: int, transit_sign: str, transit_house: int,
                 is_retrograde: bool, degree: float):
        self.name = name
        self.natal_sign = natal_sign
        self.natal_house = natal_house
        self.transit_sign = transit_sign
        self.transit_house = transit_house
        self.is_retrograde = is_retrograde
        self.degree = degree


def _get_transit_aspects(transit_house: int, natal_house: int) -> List[Dict[str, Any]]:
    diff = (transit_house - natal_house) % 12
    aspects = []
    aspect_map = {
        0: {'name': 'Conjunction', 'nature': 'Strong', 'effect': 'Intensifies natal house themes'},
        2: {'name': 'Trine (120)', 'nature': 'Benefic', 'effect': 'Harmonious flow, ease, support'},
        3: {'name': 'Square (90)', 'nature': 'Challenging', 'effect': 'Tension, action needed, growth through friction'},
        4: {'name': 'Opposition (180)', 'nature': 'Mixed', 'effect': 'Awareness, confrontation, balance needed'},
        6: {'name': 'Sextile (60)', 'nature': 'Opportunity', 'effect': 'Gentle support, new possibilities'},
        10: {'name': 'Sextile (300)', 'nature': 'Opportunity', 'effect': 'Minor harmony, easy flow'},
    }
    if diff in aspect_map:
        aspects.append({
            'aspect': aspect_map[diff]['name'],
            'nature': aspect_map[diff]['nature'],
            'effect': aspect_map[diff]['effect'],
        })
    return aspects


def _transit_prediction(planet: str, transit_house: int, natal_house: int) -> str:
    house_meanings = {
        1: "self, personality, appearance",
        2: "wealth, family, speech",
        3: "courage, siblings, communication",
        4: "home, property, mother, comfort",
        5: "children, education, creativity, romance",
        6: "enemies, disease, service, competition",
        7: "marriage, partnership, business, travel",
        8: "longevity, transformation, hidden matters",
        9: "luck, dharma, father, long travel, wisdom",
        10: "career, status, authority, karma",
        11: "gains, income, fulfillment, friends",
        12: "losses, expenses, foreign lands, moksha",
    }
    natal_themes = house_meanings.get(natal_house, f"house {natal_house}")
    transit_themes = house_meanings.get(transit_house, f"house {transit_house}")

    planet_effects = {
        'Sun': {'positive': 'vitality, recognition, leadership', 'negative': 'ego clashes, authority issues'},
        'Moon': {'positive': 'emotional peace, intuition, nurturing', 'negative': 'mood fluctuations, mental unrest'},
        'Mars': {'positive': 'energy, initiative, courage', 'negative': 'conflicts, accidents, impulsive actions'},
        'Mercury': {'positive': 'communication, learning, business', 'negative': 'miscommunication, nervousness, delays'},
        'Jupiter': {'positive': 'expansion, wisdom, fortune, blessings', 'negative': 'overextension, complacency'},
        'Venus': {'positive': 'love, harmony, luxury, creativity', 'negative': 'indulgence, relationship friction'},
        'Saturn': {'positive': 'discipline, structure, maturity', 'negative': 'delays, restrictions, hardships, lessons'},
        'Rahu': {'positive': 'ambition, unconventional growth, breakthrough', 'negative': 'confusion, obsession, karmic debt'},
        'Ketu': {'positive': 'spiritual insight, detachment, liberation', 'negative': 'isolation, confusion, loss of direction'},
    }

    effect = planet_effects.get(planet, {'positive': 'general influence', 'negative': 'challenges'})
    is_benefic_house = transit_house in [1, 5, 9, 11]
    base_effect = effect['positive'] if is_benefic_house else effect['negative']

    return f"Transit of {planet} through house {transit_house} ({transit_themes}) activating natal {natal_themes} - {base_effect}"


@router.post('/transit')
def compute_transit(body: TransitRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS,
                        get_nakshatra, to_dms)

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets_birth = calc_planets(jd_birth, None, body.nodeMode or 'mean')
    house_data_birth = calc_houses(jd_birth, body.latitude, body.longitude, planets_birth, body.houseSystem or 'W')
    asc_sign = house_data_birth['ascendant']['sign']
    asc_idx = ZODIAC_SIGNS.index(asc_sign)

    # Transit date
    tz = pytz.timezone(body.timezone)
    if body.transitDate:
        transit_dt = parser.parse(body.transitDate)
    else:
        transit_dt = datetime.now(tz).replace(tzinfo=None)
    transit_dt_local = tz.localize(transit_dt)

    from ..main import parse_local_datetime
    transit_local = transit_dt_local
    jd_transit = to_julian(transit_dt.strftime('%Y-%m-%d'), transit_dt.strftime('%H:%M'), body.timezone)

    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')
    house_data_transit = calc_houses(jd_transit, body.latitude, body.longitude, planets_transit, body.houseSystem or 'W')

    natal_map = {p['name']: p for p in planets_birth}
    transit_map = {p['name']: p for p in planets_transit}

    transit_results = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        natal_p = natal_map.get(pname)
        transit_p = transit_map.get(pname)
        if not natal_p or not transit_p:
            continue

        transit_house = transit_p.get('house', 0)
        natal_house = natal_p.get('house', 0)

        aspects = _get_transit_aspects(transit_house, natal_house)
        prediction = _transit_prediction(pname, transit_house, natal_house)

        transit_results.append({
            'planet': pname,
            'natalSign': natal_p['sign'],
            'natalHouse': natal_house,
            'transitSign': transit_p['sign'],
            'transitHouse': transit_house,
            'transitDegree': transit_p['degree'],
            'transitDegreeDMS': transit_p['degreeDMS'],
            'isRetrograde': transit_p['isRetrograde'],
            'aspects': aspects,
            'prediction': prediction,
        })

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'ascendant': house_data_birth['ascendant'],
        'transits': transit_results,
    }


@router.post('/transit/current')
def current_transits(body: TransitRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, ZODIAC_SIGNS, SIGN_LORDS

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets_birth = calc_planets(jd_birth, None, body.nodeMode or 'mean')

    tz = pytz.timezone(body.timezone)
    now = datetime.now(tz)
    jd_now = to_julian(now.strftime('%Y-%m-%d'), now.strftime('%H:%M'), body.timezone)
    planets_now = calc_planets(jd_now, None, body.nodeMode or 'mean')

    natal_map = {p['name']: p for p in planets_birth}
    now_map = {p['name']: p for p in planets_now}

    current = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        natal = natal_map.get(pname)
        transit = now_map.get(pname)
        if natal and transit:
            current.append({
                'planet': pname,
                'natalSign': natal['sign'],
                'transitSign': transit['sign'],
                'transitDegree': transit['degree'],
                'isRetrograde': transit['isRetrograde'],
                'signLord': transit['signLord'],
                'nakshatra': transit['nakshatra'],
            })

    return {
        'status': 200,
        'date': now.strftime('%Y-%m-%d %H:%M'),
        'timezone': body.timezone,
        'transits': current,
    }
