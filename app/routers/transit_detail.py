from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import pytz
from dateutil import parser

router = APIRouter()


class TransitDetailRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    transitDate: Optional[str] = Field(None, example="2025-07-15")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


class PlanetTransitRequest(TransitDetailRequest):
    planetName: str = Field(..., example="Jupiter", description="Planet name to track transit")


class AspectRequest(TransitDetailRequest):
    pass


HOUSE_MEANINGS = {
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

PLANET_EFFECTS = {
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

ASPECT_MAP = {
    0: {'name': 'Conjunction (0)', 'nature': 'Strong', 'effect': 'Intensifies natal house themes'},
    2: {'name': 'Trine (120)', 'nature': 'Benefic', 'effect': 'Harmonious flow, ease, support'},
    3: {'name': 'Square (90)', 'nature': 'Challenging', 'effect': 'Tension, action needed, growth through friction'},
    4: {'name': 'Opposition (180)', 'nature': 'Mixed', 'effect': 'Awareness, confrontation, balance needed'},
    6: {'name': 'Sextile (60)', 'nature': 'Opportunity', 'effect': 'Gentle support, new possibilities'},
    10: {'name': 'Sextile (300)', 'nature': 'Opportunity', 'effect': 'Minor harmony, easy flow'},
}

COMBUSTION_RANGES = {'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11, 'Venus': 10, 'Saturn': 15}


def _resolve_transit_date(body: TransitDetailRequest) -> datetime:
    tz = pytz.timezone(body.timezone)
    if body.transitDate:
        return tz.localize(parser.parse(body.transitDate))
    return datetime.now(tz)


def _build_transit_jd(transit_dt: datetime, tz_name: str) -> float:
    from ..main import to_julian
    local_str = transit_dt.strftime('%Y-%m-%d')
    time_str = transit_dt.strftime('%H:%M')
    return to_julian(local_str, time_str, tz_name)


def _get_aspect_details(transit_house: int, natal_house: int) -> List[Dict[str, Any]]:
    diff = (transit_house - natal_house) % 12
    if diff in ASPECT_MAP:
        return [{'aspect': ASPECT_MAP[diff]['name'], 'nature': ASPECT_MAP[diff]['nature'],
                 'effect': ASPECT_MAP[diff]['effect']}]
    return []


def _transit_prediction(planet: str, transit_house: int, natal_house: int) -> str:
    natal_themes = HOUSE_MEANINGS.get(natal_house, f"house {natal_house}")
    transit_themes = HOUSE_MEANINGS.get(transit_house, f"house {transit_house}")
    effect = PLANET_EFFECTS.get(planet, {'positive': 'general influence', 'negative': 'challenges'})
    is_benefic_house = transit_house in [1, 5, 9, 11]
    base_effect = effect['positive'] if is_benefic_house else effect['negative']
    return f"Transit of {planet} through house {transit_house} ({transit_themes}) activating natal {natal_themes} - {base_effect}"


@router.post('/transit/planet-transit')
def planet_transit(body: PlanetTransitRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS,
                        planet_status, is_combust, COMBUSTION_DIST)

    valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    planet_name = body.planetName.capitalize()
    if planet_name not in valid_planets:
        return {'status': 400, 'error': f"Invalid planet. Must be one of: {', '.join(valid_planets)}"}

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets_birth = calc_planets(jd_birth, None, body.nodeMode or 'mean')
    house_data_birth = calc_houses(jd_birth, body.latitude, body.longitude, planets_birth, body.houseSystem or 'W')

    transit_dt = _resolve_transit_date(body)
    jd_transit = _build_transit_jd(transit_dt, body.timezone)
    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')
    house_data_transit = calc_houses(jd_transit, body.latitude, body.longitude, planets_transit, body.houseSystem or 'W')

    natal_p = next((p for p in planets_birth if p['name'] == planet_name), None)
    transit_p = next((p for p in planets_transit if p['name'] == planet_name), None)

    if not natal_p or not transit_p:
        return {'status': 400, 'error': f'Could not compute {planet_name} position'}

    transit_house = transit_p.get('house', 0)
    natal_house = natal_p.get('house', 0)
    aspects = _get_aspect_details(transit_house, natal_house)
    prediction = _transit_prediction(planet_name, transit_house, natal_house)

    natal_status = planet_status(planet_name, natal_p['sign'])
    transit_status = planet_status(planet_name, transit_p['sign'])

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'planet': planet_name,
        'natal': {
            'sign': natal_p['sign'],
            'signLord': natal_p['signLord'],
            'house': natal_house,
            'degree': natal_p['degree'],
            'degreeDMS': natal_p['degreeDMS'],
            'longitude': natal_p['longitude'],
            'nakshatra': natal_p['nakshatra'],
            'nakshatraLord': natal_p['nakshatraLord'],
            'dignity': natal_status,
            'isRetrograde': natal_p['isRetrograde'],
        },
        'transit': {
            'sign': transit_p['sign'],
            'signLord': transit_p['signLord'],
            'house': transit_house,
            'degree': transit_p['degree'],
            'degreeDMS': transit_p['degreeDMS'],
            'longitude': transit_p['longitude'],
            'nakshatra': transit_p['nakshatra'],
            'nakshatraLord': transit_p['nakshatraLord'],
            'dignity': transit_status,
            'isRetrograde': transit_p['isRetrograde'],
            'isCombust': transit_p['isCombust'],
            'speed': transit_p['speed'],
        },
        'aspects': aspects,
        'prediction': prediction,
    }


@router.post('/transit/retrograde')
def retrograde_planets(body: TransitDetailRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, ZODIAC_SIGNS, SIGN_LORDS)

    transit_dt = _resolve_transit_date(body)
    jd_transit = _build_transit_jd(transit_dt, body.timezone)
    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')

    retrograde_list = []
    for p in planets_transit:
        if p['isRetrograde']:
            retrograde_list.append({
                'planet': p['name'],
                'sign': p['sign'],
                'signLord': p['signLord'],
                'degree': p['degree'],
                'degreeDMS': p['degreeDMS'],
                'longitude': p['longitude'],
                'nakshatra': p['nakshatra'],
                'speed': p['speed'],
                'note': f"{p['name']} is retrograde in {p['sign']} at {p['degreeDMS']}",
            })

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'retrogradeCount': len(retrograde_list),
        'retrogradePlanets': retrograde_list,
    }


@router.post('/transit/combust')
def combust_planets(body: TransitDetailRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, ZODIAC_SIGNS, SIGN_LORDS,
                        is_combust, COMBUSTION_DIST)

    transit_dt = _resolve_transit_date(body)
    jd_transit = _build_transit_jd(transit_dt, body.timezone)
    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')

    combust_list = []
    for p in planets_transit:
        if p['isCombust']:
            sun_p = next((x for x in planets_transit if x['name'] == 'Sun'), None)
            if sun_p:
                dist = abs(p['longitude'] - sun_p['longitude'])
                dist = min(dist, 360 - dist)
            else:
                dist = 0
            max_dist = COMBUSTION_DIST.get(p['name'], 0)
            combust_list.append({
                'planet': p['name'],
                'sign': p['sign'],
                'degree': p['degree'],
                'degreeDMS': p['degreeDMS'],
                'longitude': p['longitude'],
                'sunLongitude': sun_p['longitude'] if sun_p else None,
                'angularDistance': round(dist, 2),
                'maxCombustionDistance': max_dist,
                'severity': 'Deep Combust' if dist < max_dist * 0.5 else 'Mild Combust',
            })

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'combustCount': len(combust_list),
        'combustPlanets': combust_list,
    }


@router.post('/transit/exalted')
def exalted_planets(body: TransitDetailRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, ZODIAC_SIGNS, SIGN_LORDS, planet_status)

    transit_dt = _resolve_transit_date(body)
    jd_transit = _build_transit_jd(transit_dt, body.timezone)
    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')

    exalted_list = []
    for p in planets_transit:
        dignity = planet_status(p['name'], p['sign'])
        if dignity == 'Exalted':
            exalted_list.append({
                'planet': p['name'],
                'sign': p['sign'],
                'signLord': p['signLord'],
                'house': p.get('house', 0),
                'degree': p['degree'],
                'degreeDMS': p['degreeDMS'],
                'longitude': p['longitude'],
                'nakshatra': p['nakshatra'],
                'dignity': dignity,
                'isRetrograde': p['isRetrograde'],
                'note': f"{p['name']} is exalted in {p['sign']} at {p['degreeDMS']}",
            })

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'exaltedCount': len(exalted_list),
        'exaltedPlanets': exalted_list,
    }


@router.post('/transit/debilitated')
def debilitated_planets(body: TransitDetailRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, ZODIAC_SIGNS, SIGN_LORDS, planet_status)

    transit_dt = _resolve_transit_date(body)
    jd_transit = _build_transit_jd(transit_dt, body.timezone)
    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')

    debilitated_list = []
    for p in planets_transit:
        dignity = planet_status(p['name'], p['sign'])
        if dignity == 'Debilitated':
            debilitated_list.append({
                'planet': p['name'],
                'sign': p['sign'],
                'signLord': p['signLord'],
                'house': p.get('house', 0),
                'degree': p['degree'],
                'degreeDMS': p['degreeDMS'],
                'longitude': p['longitude'],
                'nakshatra': p['nakshatra'],
                'dignity': dignity,
                'isRetrograde': p['isRetrograde'],
                'note': f"{p['name']} is debilitated in {p['sign']} at {p['degreeDMS']}",
            })

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'debilitatedCount': len(debilitated_list),
        'debilitatedPlanets': debilitated_list,
    }


@router.post('/transit/aspect')
def transit_aspects(body: AspectRequest) -> Dict[str, Any]:
    from ..main import (to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS)

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets_birth = calc_planets(jd_birth, None, body.nodeMode or 'mean')
    house_data_birth = calc_houses(jd_birth, body.latitude, body.longitude, planets_birth, body.houseSystem or 'W')

    transit_dt = _resolve_transit_date(body)
    jd_transit = _build_transit_jd(transit_dt, body.timezone)
    planets_transit = calc_planets(jd_transit, None, body.nodeMode or 'mean')
    house_data_transit = calc_houses(jd_transit, body.latitude, body.longitude, planets_transit, body.houseSystem or 'W')

    transit_aspect_results = []

    for t_planet in planets_transit:
        t_house = t_planet.get('house', 0)
        for n_planet in planets_birth:
            n_house = n_planet.get('house', 0)
            aspects = _get_aspect_details(t_house, n_house)
            if aspects:
                natal_themes = HOUSE_MEANINGS.get(n_house, f"house {n_house}")
                transit_themes = HOUSE_MEANINGS.get(t_house, f"house {t_house}")
                effect = PLANET_EFFECTS.get(t_planet['name'], {'positive': 'general', 'negative': 'challenges'})
                is_benefic = t_house in [1, 5, 9, 11]
                base_effect = effect['positive'] if is_benefic else effect['negative']

                for asp in aspects:
                    transit_aspect_results.append({
                        'transitingPlanet': t_planet['name'],
                        'transitSign': t_planet['sign'],
                        'transitHouse': t_house,
                        'natalPlanet': n_planet['name'],
                        'natalSign': n_planet['sign'],
                        'natalHouse': n_house,
                        'aspect': asp['aspect'],
                        'nature': asp['nature'],
                        'aspectEffect': asp['effect'],
                        'prediction': f"{t_planet['name']} transiting house {t_house} ({transit_themes}) aspects natal {n_planet['name']} in house {n_house} ({natal_themes}) - {base_effect}",
                    })

    return {
        'status': 200,
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'ascendant': house_data_birth['ascendant'],
        'aspectCount': len(transit_aspect_results),
        'aspects': transit_aspect_results,
    }
