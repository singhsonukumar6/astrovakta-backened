from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import swisseph as swe
import pytz
from dateutil import parser

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status, ayanamsa_value,
)

router = APIRouter()

PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

SPECIAL_ASPECTS = {
    'Mars': [4, 7, 8],
    'Jupiter': [5, 7, 9],
    'Saturn': [3, 7, 10],
}

ASPECT_STRENGTH = {
    'Conjunction': {'strength': 1.0, 'nature': 'Very Strong'},
    'Opposition': {'strength': 0.9, 'nature': 'Strong'},
    'Trine': {'strength': 0.8, 'nature': 'Benefic'},
    'Square': {'strength': 0.7, 'nature': 'Challenging'},
    'Sextile': {'strength': 0.5, 'nature': 'Moderate'},
    'Quincunx': {'strength': 0.3, 'nature': 'Weak'},
    'Semi-Sextile': {'strength': 0.2, 'nature': 'Very Weak'},
}

TRANSIT_EFFECTS = {
    'Sun': {
        1: {'summary': 'Vitality boost, increased confidence, leadership opportunities', 'nature': 'positive', 'intensity': 'high'},
        2: {'summary': 'Financial gains, improved speech, family support', 'nature': 'positive', 'intensity': 'medium'},
        3: {'summary': 'Courage and initiative, success in competitions', 'nature': 'positive', 'intensity': 'medium'},
        4: {'summary': 'Domestic harmony, property gains, mother\'s health improves', 'nature': 'positive', 'intensity': 'medium'},
        5: {'summary': 'Creative success, romance, children prosper', 'nature': 'positive', 'intensity': 'high'},
        6: {'summary': 'Victory over enemies, health improvement', 'nature': 'positive', 'intensity': 'medium'},
        7: {'summary': 'Partnership prominence, public recognition', 'nature': 'mixed', 'intensity': 'medium'},
        8: {'summary': 'Health caution, hidden matters surface, transformation', 'nature': 'challenging', 'intensity': 'high'},
        9: {'summary': 'Spiritual growth, long travel, blessings of elders', 'nature': 'positive', 'intensity': 'high'},
        10: {'summary': 'Career authority, professional recognition, status elevation', 'nature': 'positive', 'intensity': 'high'},
        11: {'summary': 'Gains, social networking, fulfilled ambitions', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses, foreign connections, spiritual retreat', 'nature': 'mixed', 'intensity': 'medium'},
    },
    'Moon': {
        1: {'summary': 'Emotional peace, mental clarity, public favor', 'nature': 'positive', 'intensity': 'high'},
        2: {'summary': 'Financial comfort, family happiness, good food', 'nature': 'positive', 'intensity': 'medium'},
        3: {'summary': 'Courage fluctuates, short journeys, sibling support', 'nature': 'mixed', 'intensity': 'low'},
        4: {'summary': 'Domestic peace, property comfort, mother\'s blessings', 'nature': 'positive', 'intensity': 'high'},
        5: {'summary': 'Creative inspiration, romantic fulfillment, children happy', 'nature': 'positive', 'intensity': 'high'},
        6: {'summary': 'Emotional stress, health fluctuations, enemy troubles', 'nature': 'challenging', 'intensity': 'medium'},
        7: {'summary': 'Partnership harmony, marriage proposals, public relations', 'nature': 'positive', 'intensity': 'high'},
        8: {'summary': 'Emotional turbulence, hidden fears surface, intuitions strong', 'nature': 'challenging', 'intensity': 'high'},
        9: {'summary': 'Spiritual peace, good fortune, pilgrimages', 'nature': 'positive', 'intensity': 'high'},
        10: {'summary': 'Career satisfaction, professional recognition', 'nature': 'positive', 'intensity': 'medium'},
        11: {'summary': 'Social gains, friendship growth, wish fulfillment', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses, foreign travel, spiritual dreams, isolation', 'nature': 'mixed', 'intensity': 'medium'},
    },
    'Mars': {
        1: {'summary': 'Physical energy surge, courage, new initiatives', 'nature': 'positive', 'intensity': 'high'},
        2: {'summary': 'Financial disputes, harsh speech, family conflicts', 'nature': 'challenging', 'intensity': 'medium'},
        3: {'summary': 'Courage peaks, success in competitions, short travel', 'nature': 'positive', 'intensity': 'high'},
        4: {'summary': 'Property disputes, domestic unrest, vehicle issues', 'nature': 'challenging', 'intensity': 'high'},
        5: {'summary': 'Romantic intensity, children need attention, creative drive', 'nature': 'mixed', 'intensity': 'medium'},
        6: {'summary': 'Victory over enemies, health recovery, litigation success', 'nature': 'positive', 'intensity': 'high'},
        7: {'summary': 'Partnership friction, marital discord, business conflicts', 'nature': 'challenging', 'intensity': 'high'},
        8: {'summary': 'Health caution, accidents risk, surgery possible, transformation', 'nature': 'challenging', 'intensity': 'very high'},
        9: {'summary': 'Travel challenges, disagreement with father/elders', 'nature': 'challenging', 'intensity': 'medium'},
        10: {'summary': 'Career ambition, professional authority, action-oriented', 'nature': 'positive', 'intensity': 'high'},
        11: {'summary': 'Gains through courage, social influence, strong network', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses, foreign travel, secret enemies, hospital visits', 'nature': 'challenging', 'intensity': 'medium'},
    },
    'Mercury': {
        1: {'summary': 'Intellectual sharpness, communication skills, business acumen', 'nature': 'positive', 'intensity': 'high'},
        2: {'summary': 'Financial gains, eloquent speech, family harmony', 'nature': 'positive', 'intensity': 'high'},
        3: {'summary': 'Communication skills peak, writing success, sibling support', 'nature': 'positive', 'intensity': 'high'},
        4: {'summary': 'Domestic harmony, property deals, educational success', 'nature': 'positive', 'intensity': 'medium'},
        5: {'summary': 'Creative intelligence, romantic communication, children excel', 'nature': 'positive', 'intensity': 'high'},
        6: {'summary': 'Victory in disputes, health improvement, service success', 'nature': 'positive', 'intensity': 'medium'},
        7: {'summary': 'Partnership communication, marriage negotiations, business deals', 'nature': 'positive', 'intensity': 'high'},
        8: {'summary': 'Hidden matters revealed, analytical depth, research success', 'nature': 'mixed', 'intensity': 'medium'},
        9: {'summary': 'Educational success, philosophical discussions, travel plans', 'nature': 'positive', 'intensity': 'high'},
        10: {'summary': 'Career communication, professional networking, business growth', 'nature': 'positive', 'intensity': 'high'},
        11: {'summary': 'Social connections, financial gains, intellectual network', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses, foreign communication, spiritual studies, isolation', 'nature': 'mixed', 'intensity': 'medium'},
    },
    'Jupiter': {
        1: {'summary': 'Wisdom, good fortune, spiritual growth, physical well-being', 'nature': 'positive', 'intensity': 'very high'},
        2: {'summary': 'Wealth increase, family happiness, eloquent speech', 'nature': 'positive', 'intensity': 'very high'},
        3: {'summary': 'Courage and determination, success in short ventures', 'nature': 'mixed', 'intensity': 'medium'},
        4: {'summary': 'Domestic happiness, property gains, mother\'s blessings', 'nature': 'positive', 'intensity': 'very high'},
        5: {'summary': 'Children prosper, romantic fulfillment, creative success', 'nature': 'positive', 'intensity': 'very high'},
        6: {'summary': 'Victory over enemies, health improvement, litigation success', 'nature': 'positive', 'intensity': 'high'},
        7: {'summary': 'Marriage possibilities, partnership harmony, social respect', 'nature': 'positive', 'intensity': 'very high'},
        8: {'summary': 'Spiritual transformation, hidden wisdom, health caution', 'nature': 'mixed', 'intensity': 'high'},
        9: {'summary': 'Maximum fortune, spiritual blessings, long travel, education', 'nature': 'positive', 'intensity': 'very high'},
        10: {'summary': 'Career elevation, professional respect, authority gains', 'nature': 'positive', 'intensity': 'very high'},
        11: {'summary': 'Maximum gains, wish fulfillment, social prominence', 'nature': 'positive', 'intensity': 'very high'},
        12: {'summary': 'Expenses, foreign travel, spiritual retreat, charity', 'nature': 'mixed', 'intensity': 'high'},
    },
    'Venus': {
        1: {'summary': 'Beauty, charm, romantic inclinations, luxury', 'nature': 'positive', 'intensity': 'high'},
        2: {'summary': 'Wealth, family happiness, artistic pursuits, good food', 'nature': 'positive', 'intensity': 'high'},
        3: {'summary': 'Creative communication, sibling harmony, artistic success', 'nature': 'positive', 'intensity': 'medium'},
        4: {'summary': 'Domestic comfort, property luxury, vehicle comfort', 'nature': 'positive', 'intensity': 'high'},
        5: {'summary': 'Romance peaks, creative success, children happy, love affairs', 'nature': 'positive', 'intensity': 'very high'},
        6: {'summary': 'Health issues, relationship disputes, indulgence problems', 'nature': 'challenging', 'intensity': 'medium'},
        7: {'summary': 'Marriage possibilities, partnership harmony, social charm', 'nature': 'positive', 'intensity': 'very high'},
        8: {'summary': 'Secret affairs, hidden pleasures, transformation through love', 'nature': 'mixed', 'intensity': 'high'},
        9: {'summary': 'Spiritual love, artistic fortune, long travel with partner', 'nature': 'positive', 'intensity': 'high'},
        10: {'summary': 'Career in arts, professional charm, creative recognition', 'nature': 'positive', 'intensity': 'high'},
        11: {'summary': 'Social gains, friendship growth, financial comfort', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses on luxury, foreign travel, romantic escapades', 'nature': 'mixed', 'intensity': 'high'},
    },
    'Saturn': {
        1: {'summary': 'Health caution, delays, discipline, maturity through hardship', 'nature': 'challenging', 'intensity': 'very high'},
        2: {'summary': 'Financial restrictions, family responsibilities, harsh speech', 'nature': 'challenging', 'intensity': 'high'},
        3: {'summary': 'Courage tested, success through persistence, sibling issues', 'nature': 'mixed', 'intensity': 'medium'},
        4: {'summary': 'Domestic challenges, property delays, mother\'s health caution', 'nature': 'challenging', 'intensity': 'very high'},
        5: {'summary': 'Children delays, creative blocks, romantic obstacles', 'nature': 'challenging', 'intensity': 'high'},
        6: {'summary': 'Victory over enemies, health improvement, discipline pays', 'nature': 'positive', 'intensity': 'high'},
        7: {'summary': 'Partnership delays, marriage obstacles, business restructuring', 'nature': 'challenging', 'intensity': 'very high'},
        8: {'summary': 'Health crisis, transformation, hidden fears, spiritual depth', 'nature': 'challenging', 'intensity': 'very high'},
        9: {'summary': 'Spiritual discipline, long delays in fortune, elder conflicts', 'nature': 'challenging', 'intensity': 'high'},
        10: {'summary': 'Career authority through hard work, professional responsibility', 'nature': 'mixed', 'intensity': 'very high'},
        11: {'summary': 'Gains through persistence, social responsibility, network building', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses, foreign settlement, spiritual isolation, hospital visits', 'nature': 'challenging', 'intensity': 'high'},
    },
    'Rahu': {
        1: {'summary': 'Unconventional identity, foreign connections, material ambitions', 'nature': 'mixed', 'intensity': 'very high'},
        2: {'summary': 'Unconventional wealth, foreign speech, family disruptions', 'nature': 'mixed', 'intensity': 'high'},
        3: {'summary': 'Courage through unconventional means, sibling issues', 'nature': 'mixed', 'intensity': 'medium'},
        4: {'summary': 'Domestic unrest, foreign property, mother\'s health issues', 'nature': 'challenging', 'intensity': 'high'},
        5: {'summary': 'Unconventional romance, obsessive creativity, children issues', 'nature': 'mixed', 'intensity': 'high'},
        6: {'summary': 'Victory over enemies through cunning, health fluctuations', 'nature': 'positive', 'intensity': 'high'},
        7: {'summary': 'Unconventional partnerships, foreign marriage, business changes', 'nature': 'mixed', 'intensity': 'very high'},
        8: {'summary': 'Obsessive transformation, hidden matters, health crises', 'nature': 'challenging', 'intensity': 'very high'},
        9: {'summary': 'Unconventional beliefs, foreign travel, spiritual confusion', 'nature': 'mixed', 'intensity': 'high'},
        10: {'summary': 'Career changes, foreign opportunities, unconventional profession', 'nature': 'mixed', 'intensity': 'very high'},
        11: {'summary': 'Gains through networking, foreign connections, ambitious pursuits', 'nature': 'positive', 'intensity': 'high'},
        12: {'summary': 'Expenses, foreign settlement, spiritual awakening, isolation', 'nature': 'mixed', 'intensity': 'very high'},
    },
    'Ketu': {
        1: {'summary': 'Spiritual detachment, health confusion, past-life karma', 'nature': 'mixed', 'intensity': 'high'},
        2: {'summary': 'Financial detachment, family separation, spiritual speech', 'nature': 'mixed', 'intensity': 'medium'},
        3: {'summary': 'Courage through detachment, sibling issues, spiritual courage', 'nature': 'mixed', 'intensity': 'medium'},
        4: {'summary': 'Domestic detachment, property issues, mother\'s spiritual growth', 'nature': 'mixed', 'intensity': 'high'},
        5: {'summary': 'Spiritual creativity, detachment from romance, children distant', 'nature': 'mixed', 'intensity': 'high'},
        6: {'summary': 'Victory through surrender, health confusion, enemy dissolution', 'nature': 'positive', 'intensity': 'medium'},
        7: {'summary': 'Partnership detachment, spiritual marriage, business dissolution', 'nature': 'mixed', 'intensity': 'high'},
        8: {'summary': 'Spiritual transformation, hidden wisdom, health detachment', 'nature': 'positive', 'intensity': 'very high'},
        9: {'summary': 'Spiritual liberation, detachment from fortune, past-life karma', 'nature': 'positive', 'intensity': 'very high'},
        10: {'summary': 'Career detachment, professional changes, spiritual calling', 'nature': 'mixed', 'intensity': 'high'},
        11: {'summary': 'Social detachment, gains through spirituality, network dissolution', 'nature': 'mixed', 'intensity': 'medium'},
        12: {'summary': 'Spiritual liberation, detachment from material world, foreign settlement', 'nature': 'positive', 'intensity': 'very high'},
    },
}

EVENT_TRANSIT_TRIGGERS = {
    'marriage': {
        'primary': ['Jupiter', 'Venus'],
        'houses': [1, 2, 4, 5, 7, 8, 11],
        'description': 'Jupiter transit through 1st, 2nd, 5th, 7th, 9th, or 11th house often triggers marriage. Venus transit through these houses enhances romantic prospects.',
        'timing_note': 'Jupiter transit takes about 1 year per house. Venus transits quickly (about 25 days per sign).',
    },
    'job change': {
        'primary': ['Saturn', 'Jupiter', 'Rahu'],
        'houses': [1, 2, 6, 10, 11],
        'description': 'Saturn transit through 1st, 2nd, 6th, 10th, or 11th house triggers career changes. Jupiter brings opportunities. Rahu brings unconventional changes.',
        'timing_note': 'Saturn takes about 2.5 years per sign. Jupiter takes about 1 year per house.',
    },
    'foreign travel': {
        'primary': ['Rahu', 'Jupiter', 'Saturn'],
        'houses': [3, 4, 7, 8, 9, 12],
        'description': 'Rahu transit through 3rd, 7th, 9th, or 12th house strongly indicates foreign travel. Jupiter and Saturn transits through these houses also support it.',
        'timing_note': 'Rahu takes about 1.5 years per sign. Look for conjunctions with natal planets.',
    },
    'property': {
        'primary': ['Jupiter', 'Saturn', 'Mars'],
        'houses': [1, 2, 4, 7, 10, 11],
        'description': 'Jupiter transit through 4th or 11th house brings property gains. Saturn transit through these houses brings property through persistence.',
        'timing_note': 'Jupiter and Saturn transits are the primary indicators for property matters.',
    },
    'children': {
        'primary': ['Jupiter', 'Venus'],
        'houses': [1, 2, 4, 5, 7, 9, 11],
        'description': 'Jupiter transit through 5th or 9th house strongly indicates conception. Venus transit through 5th house enhances fertility.',
        'timing_note': 'Jupiter transit through 5th house is the most significant indicator.',
    },
    'health': {
        'primary': ['Saturn', 'Mars', 'Rahu'],
        'houses': [1, 6, 8, 12],
        'description': 'Saturn transit through 1st, 6th, or 8th house indicates health challenges. Mars transit through these houses indicates accidents or surgery.',
        'timing_note': 'Saturn transit through 1st house (Sade Sati) is the most significant health indicator.',
    },
    'education': {
        'primary': ['Jupiter', 'Mercury'],
        'houses': [1, 2, 4, 5, 9, 11],
        'description': 'Jupiter transit through 1st, 5th, or 9th house brings educational success. Mercury transit through these houses enhances intellectual pursuits.',
        'timing_note': 'Jupiter transit through 9th house is the most significant for higher education.',
    },
    'promotion': {
        'primary': ['Saturn', 'Jupiter', 'Sun'],
        'houses': [1, 2, 6, 10, 11],
        'description': 'Saturn transit through 10th or 11th house brings promotion through hard work. Jupiter transit through these houses brings recognition.',
        'timing_note': 'Saturn transit through 10th house is the most significant for career elevation.',
    },
    'legal': {
        'primary': ['Saturn', 'Jupiter', 'Mars'],
        'houses': [1, 3, 6, 7, 10, 11],
        'description': 'Saturn transit through 6th or 10th house brings legal resolution. Mars transit through these houses brings victory in disputes.',
        'timing_note': 'Saturn transit through 6th house is the most significant for legal matters.',
    },
    'spiritual': {
        'primary': ['Jupiter', 'Ketu', 'Saturn'],
        'houses': [1, 5, 8, 9, 12],
        'description': 'Jupiter transit through 9th or 12th house brings spiritual growth. Ketu transit through these houses brings spiritual awakening.',
        'timing_note': 'Ketu transit through 9th or 12th house is the most significant for spiritual matters.',
    },
}


class TransitPredRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    transitDate: Optional[str] = Field(None, example="2025-07-15", description="Transit date (defaults to today)")
    transitTime: Optional[str] = Field('12:00', example='12:00')
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


class TransitByPlanetRequest(TransitPredRequest):
    planet: str = Field(..., example="Jupiter")


class TransitTimingRequest(TransitPredRequest):
    event: str = Field(..., example="marriage")


def _get_aspects(transit_lon: float, natal_planets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    aspects_found = []
    for np in natal_planets:
        if np['name'] in ['Rahu', 'Ketu']:
            continue
        diff = abs(transit_lon - np['longitude'])
        diff = min(diff, 360 - diff)

        aspect_degrees = {
            0: 'Conjunction',
            6: 'Semi-Sextile',
            30: 'Semi-Sextile',
            60: 'Sextile',
            90: 'Square',
            120: 'Trine',
            150: 'Quincunx',
            180: 'Opposition',
        }

        orb = 8.0
        matched_aspect = None
        for deg, name in sorted(aspect_degrees.items(), key=lambda x: abs(diff - x[0])):
            if abs(diff - deg) <= orb:
                matched_aspect = name
                orb_used = abs(diff - deg)
                break

        if matched_aspect:
            strength_info = ASPECT_STRENGTH.get(matched_aspect, {'strength': 0.5, 'nature': 'Moderate'})
            aspects_found.append({
                'planet': np['name'],
                'aspectType': matched_aspect,
                'orb': round(abs(diff - (deg if matched_aspect else 0)), 2),
                'nature': strength_info['nature'],
                'strength': strength_info['strength'],
                'natalHouse': np.get('house', 0),
                'natalSign': np.get('sign', ''),
            })

    return aspects_found


def _get_special_aspects(planet: str, transit_lon: float, natal_planets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    special = SPECIAL_ASPECTS.get(planet, [])
    if not special:
        return []

    aspects_found = []
    for np in natal_planets:
        if np['name'] in ['Rahu', 'Ketu']:
            continue
        diff = abs(transit_lon - np['longitude'])
        diff = min(diff, 360 - diff)
        sign = 1 if transit_lon >= np['longitude'] else -1
        houses_away = int(round(diff / 30)) % 12

        for special_house in special:
            if houses_away == special_house or (12 - houses_away) == special_house:
                aspects_found.append({
                    'planet': np['name'],
                    'aspectType': f'Special Aspect ({planet} {special_house}th)',
                    'orb': round(abs(diff - special_house * 30), 2),
                    'nature': 'Challenging' if planet in ['Mars', 'Saturn'] else 'Benefic',
                    'strength': 0.6 if planet == 'Saturn' else 0.5,
                    'natalHouse': np.get('house', 0),
                    'natalSign': np.get('sign', ''),
                })

    return aspects_found


def _get_transit_house(transit_sign: str, asc_sign: str) -> int:
    transit_idx = ZODIAC_SIGNS.index(transit_sign)
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    return ((transit_idx - asc_idx + 12) % 12) + 1


def _get_planet_effect(planet: str, house: int, retrograde: bool) -> Dict[str, Any]:
    effects = TRANSIT_EFFECTS.get(planet, {}).get(house, {})
    if not effects:
        return {
            'summary': f'{planet} transit through house {house}',
            'nature': 'neutral',
            'intensity': 'medium',
        }

    if retrograde and planet not in ['Sun', 'Moon', 'Rahu', 'Ketu']:
        effects = effects.copy()
        if effects['nature'] == 'positive':
            effects['nature'] = 'mixed'
            effects['summary'] += ' (Retrograde - effects may be delayed or internalized)'
        elif effects['nature'] == 'challenging':
            effects['nature'] = 'mixed'
            effects['summary'] += ' (Retrograde - challenges may be lessened or revisited)'

    return effects


def _compute_transit_analysis(natal_planets: List[Dict[str, Any]], transit_planets: List[Dict[str, Any]],
                               asc_sign: str) -> List[Dict[str, Any]]:
    results = []
    for tp in transit_planets:
        pname = tp['name']
        transit_house = _get_transit_house(tp['sign'], asc_sign)

        aspects = _get_aspects(tp['longitude'], natal_planets)
        special_aspects = _get_special_aspects(pname, tp['longitude'], natal_planets)
        all_aspects = aspects + special_aspects

        effect = _get_planet_effect(pname, transit_house, tp.get('isRetrograde', False))

        status = planet_status(pname, tp['sign'])

        results.append({
            'planet': pname,
            'transitSign': tp['sign'],
            'transitDegree': tp['degree'],
            'transitDegreeDMS': tp['degreeDMS'],
            'transitLongitude': tp['longitude'],
            'isRetrograde': tp.get('isRetrograde', False),
            'signLord': tp.get('signLord', ''),
            'nakshatra': tp.get('nakshatra', ''),
            'nakshatraLord': tp.get('nakshatraLord', ''),
            'planetStatus': status,
            'transitHouse': transit_house,
            'effects': effect,
            'aspects': all_aspects,
            'aspectSummary': {
                'totalAspects': len(all_aspects),
                'beneficAspects': len([a for a in all_aspects if a['nature'] == 'Benefic']),
                'challengingAspects': len([a for a in all_aspects if a['nature'] == 'Challenging']),
                'strongAspects': len([a for a in all_aspects if a['strength'] >= 0.7]),
            },
        })

    return results


def _build_natal_context(natal_planets: List[Dict[str, Any]], house_data: Dict[str, Any]) -> Dict[str, Any]:
    asc_sign = house_data['ascendant']['sign']
    houses = house_data['houses']
    house_map = {}
    for h in houses:
        house_map[h['number']] = {
            'sign': h['sign'],
            'lord': h.get('signLord', SIGN_LORDS.get(h['sign'], '')),
            'planets': h.get('planets', []),
        }

    return {
        'ascendant': house_data['ascendant'],
        'houses': house_map,
        'natalPlanets': {p['name']: {
            'sign': p['sign'],
            'house': p.get('house', 0),
            'degree': p['degree'],
            'longitude': p['longitude'],
            'isRetrograde': p.get('isRetrograde', False),
            'signLord': p.get('signLord', ''),
            'nakshatra': p.get('nakshatra', ''),
        } for p in natal_planets},
    }


@router.post('/horoscope/transit/prediction')
def transit_prediction(body: TransitPredRequest) -> Dict[str, Any]:
    tz = pytz.timezone(body.timezone)

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    natal_planets = calc_planets(jd_birth, None, body.nodeMode or 'mean')
    natal_houses = calc_houses(jd_birth, body.latitude, body.longitude, natal_planets, body.houseSystem or 'W')
    asc_sign = natal_houses['ascendant']['sign']

    if body.transitDate:
        transit_dt = parser.parse(body.transitDate)
        if body.transitTime:
            t_parts = body.transitTime.split(':')
            transit_dt = transit_dt.replace(hour=int(t_parts[0]), minute=int(t_parts[1]))
    else:
        transit_dt = datetime.now(tz).replace(tzinfo=None)

    transit_dt_local = tz.localize(transit_dt) if transit_dt.tzinfo is None else transit_dt
    jd_transit = to_julian(transit_dt.strftime('%Y-%m-%d'), transit_dt.strftime('%H:%M'), body.timezone)
    transit_planets = calc_planets(jd_transit, None, body.nodeMode or 'mean')
    calc_houses(jd_transit, body.latitude, body.longitude, transit_planets, body.houseSystem or 'W')

    transit_analysis = _compute_transit_analysis(natal_planets, transit_planets, asc_sign)
    natal_context = _build_natal_context(natal_planets, natal_houses)

    overall_nature_counts = {'positive': 0, 'challenging': 0, 'mixed': 0, 'neutral': 0}
    for ta in transit_analysis:
        nature = ta['effects'].get('nature', 'neutral')
        overall_nature_counts[nature] = overall_nature_counts.get(nature, 0) + 1

    if overall_nature_counts['positive'] > overall_nature_counts['challenging']:
        overall_outlook = 'favorable'
    elif overall_nature_counts['challenging'] > overall_nature_counts['positive']:
        overall_outlook = 'challenging'
    else:
        overall_outlook = 'mixed'

    return {
        'status': 200,
        'message': 'Transit prediction computed successfully',
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'transitTime': transit_dt.strftime('%H:%M'),
        'timezone': body.timezone,
        'natalChart': natal_context,
        'transits': transit_analysis,
        'overallOutlook': overall_outlook,
        'overallNatureCounts': overall_nature_counts,
        'keyTransits': [
            ta for ta in transit_analysis
            if ta['effects'].get('intensity') in ['high', 'very high']
        ],
    }


@router.post('/horoscope/transit/by-planet')
def transit_by_planet(body: TransitByPlanetRequest) -> Dict[str, Any]:
    planet_name = body.planet.strip().capitalize()
    if planet_name not in PLANETS:
        return {
            'status': 400,
            'message': f'Invalid planet: {body.planet}. Valid planets: {", ".join(PLANETS)}',
        }

    tz = pytz.timezone(body.timezone)

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    natal_planets = calc_planets(jd_birth, None, body.nodeMode or 'mean')
    natal_houses = calc_houses(jd_birth, body.latitude, body.longitude, natal_planets, body.houseSystem or 'W')
    asc_sign = natal_houses['ascendant']['sign']

    if body.transitDate:
        transit_dt = parser.parse(body.transitDate)
        if body.transitTime:
            t_parts = body.transitTime.split(':')
            transit_dt = transit_dt.replace(hour=int(t_parts[0]), minute=int(t_parts[1]))
    else:
        transit_dt = datetime.now(tz).replace(tzinfo=None)

    jd_transit = to_julian(transit_dt.strftime('%Y-%m-%d'), transit_dt.strftime('%H:%M'), body.timezone)
    transit_planets = calc_planets(jd_transit, None, body.nodeMode or 'mean')
    calc_houses(jd_transit, body.latitude, body.longitude, transit_planets, body.houseSystem or 'W')

    transit_map = {p['name']: p for p in transit_planets}
    target_transit = transit_map.get(planet_name)

    if not target_transit:
        return {
            'status': 404,
            'message': f'{planet_name} transit position not found',
        }

    transit_house = _get_transit_house(target_transit['sign'], asc_sign)
    status = planet_status(planet_name, target_transit['sign'])
    effect = _get_planet_effect(planet_name, transit_house, target_transit.get('isRetrograde', False))

    aspects = _get_aspects(target_transit['longitude'], natal_planets)
    special_aspects = _get_special_aspects(planet_name, target_transit['longitude'], natal_planets)
    all_aspects = aspects + special_aspects

    natal_map = {p['name']: p for p in natal_planets}
    natal_p = natal_map.get(planet_name, {})

    retrograde_note = ''
    if target_transit.get('isRetrograde', False):
        retrograde_note = f'{planet_name} is currently retrograde. Effects may be internalized or delayed.'

    next_transits = []
    if planet_name in ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']:
        current_lon = target_transit['longitude']
        current_sign = target_transit['sign']
        current_sign_idx = ZODIAC_SIGNS.index(current_sign)
        next_signs = []
        for i in range(1, 4):
            next_idx = (current_sign_idx + i) % 12
            next_house = ((next_idx - ZODIAC_SIGNS.index(asc_sign) + 12) % 12) + 1
            next_effect = _get_planet_effect(planet_name, next_house, False)
            next_signs.append({
                'sign': ZODIAC_SIGNS[next_idx],
                'house': next_house,
                'effects': next_effect,
            })
        next_transits = next_signs

    return {
        'status': 200,
        'message': f'{planet_name} transit analysis computed successfully',
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'transitTime': transit_dt.strftime('%H:%M'),
        'timezone': body.timezone,
        'planet': planet_name,
        'transitPosition': {
            'sign': target_transit['sign'],
            'degree': target_transit['degree'],
            'degreeDMS': target_transit['degreeDMS'],
            'longitude': target_transit['longitude'],
            'isRetrograde': target_transit.get('isRetrograde', False),
            'signLord': target_transit.get('signLord', ''),
            'nakshatra': target_transit.get('nakshatra', ''),
            'nakshatraLord': target_transit.get('nakshatraLord', ''),
            'planetStatus': status,
        },
        'transitHouse': transit_house,
        'natalPosition': {
            'sign': natal_p.get('sign', ''),
            'house': natal_p.get('house', 0),
            'degree': natal_p.get('degree', 0),
        },
        'effects': effect,
        'aspects': all_aspects,
        'retrogradeNote': retrograde_note,
        'upcomingTransits': next_transits,
        'affectedHouses': list(set(
            [a['natalHouse'] for a in all_aspects if a['natalHouse'] > 0] + [transit_house]
        )),
    }


@router.post('/horoscope/transit/timing')
def transit_timing(body: TransitTimingRequest) -> Dict[str, Any]:
    event_key = body.event.strip().lower()
    if event_key not in EVENT_TRANSIT_TRIGGERS:
        available = list(EVENT_TRANSIT_TRIGGERS.keys())
        return {
            'status': 400,
            'message': f'Unknown event: {body.event}. Available events: {", ".join(available)}',
        }

    event_config = EVENT_TRANSIT_TRIGGERS[event_key]
    primary_planets = event_config['primary']
    target_houses = event_config['houses']

    tz = pytz.timezone(body.timezone)

    jd_birth = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    natal_planets = calc_planets(jd_birth, None, body.nodeMode or 'mean')
    natal_houses = calc_houses(jd_birth, body.latitude, body.longitude, natal_planets, body.houseSystem or 'W')
    asc_sign = natal_houses['ascendant']['sign']

    if body.transitDate:
        transit_dt = parser.parse(body.transitDate)
        if body.transitTime:
            t_parts = body.transitTime.split(':')
            transit_dt = transit_dt.replace(hour=int(t_parts[0]), minute=int(t_parts[1]))
    else:
        transit_dt = datetime.now(tz).replace(tzinfo=None)

    jd_transit = to_julian(transit_dt.strftime('%Y-%m-%d'), transit_dt.strftime('%H:%M'), body.timezone)
    transit_planets = calc_planets(jd_transit, None, body.nodeMode or 'mean')
    calc_houses(jd_transit, body.latitude, body.longitude, transit_planets, body.houseSystem or 'W')

    transit_map = {p['name']: p for p in transit_planets}
    natal_map = {p['name']: p for p in natal_planets}

    current_triggers = []
    future_windows = []

    for pname in primary_planets:
        tp = transit_map.get(pname)
        if not tp:
            continue

        transit_house = _get_transit_house(tp['sign'], asc_sign)
        is_triggering = transit_house in target_houses
        effect = _get_planet_effect(pname, transit_house, tp.get('isRetrograde', False))
        status = planet_status(pname, tp['sign'])

        aspects_to_natal = _get_aspects(tp['longitude'], natal_planets)
        special = _get_special_aspects(pname, tp['longitude'], natal_planets)
        all_aspects = aspects_to_natal + special

        current_triggers.append({
            'planet': pname,
            'currentSign': tp['sign'],
            'currentHouse': transit_house,
            'isRetrograde': tp.get('isRetrograde', False),
            'planetStatus': status,
            'isTriggeringEvent': is_triggering,
            'effects': effect,
            'aspects': all_aspects,
            'triggeringHouses': target_houses,
        })

        if not is_triggering:
            transit_sign_idx = ZODIAC_SIGNS.index(tp['sign'])
            asc_idx = ZODIAC_SIGNS.index(asc_sign)
            houses_to_trigger = []

            for th in target_houses:
                target_sign_idx = (asc_idx + th - 1) % 12
                diff = (target_sign_idx - transit_sign_idx) % 12
                estimated_months = diff * (30 / 30)
                if pname in ['Saturn', 'Rahu', 'Ketu']:
                    estimated_months = diff * (30 / 12)
                elif pname in ['Jupiter', 'Mars']:
                    estimated_months = diff * (30 / 30)

                houses_to_trigger.append({
                    'house': th,
                    'sign': ZODIAC_SIGNS[target_sign_idx],
                    'estimatedMonths': round(estimated_months, 1),
                })

            future_windows.append({
                'planet': pname,
                'currentSign': tp['sign'],
                'upcomingTriggerHouses': sorted(houses_to_trigger, key=lambda x: x['estimatedMonths']),
            })

    active_triggers = [t for t in current_triggers if t['isTriggeringEvent']]
    dormant_triggers = [t for t in current_triggers if not t['isTriggeringEvent']]

    probability = 'low'
    if len(active_triggers) >= 2:
        probability = 'high'
    elif len(active_triggers) == 1:
        probability = 'medium'

    if any(t['effects'].get('intensity') == 'very high' for t in active_triggers):
        probability = 'high'
    if any(t['isRetrograde'] for t in active_triggers):
        probability = 'medium' if probability == 'low' else 'medium'

    return {
        'status': 200,
        'message': f'Transit timing analysis for "{body.event}" computed successfully',
        'transitDate': transit_dt.strftime('%Y-%m-%d'),
        'transitTime': transit_dt.strftime('%H:%M'),
        'timezone': body.timezone,
        'event': body.event,
        'eventDescription': event_config['description'],
        'timingNote': event_config['timing_note'],
        'probability': probability,
        'activeTriggers': active_triggers,
        'dormantTriggers': dormant_triggers,
        'futureWindows': future_windows,
        'overallAssessment': {
            'activeTriggerCount': len(active_triggers),
            'dormantTriggerCount': len(dormant_triggers),
            'bestPlanetForEvent': active_triggers[0]['planet'] if active_triggers else primary_planets[0],
            'recommendedAction': (
                'Favorable time - take action now' if probability == 'high'
                else 'Moderately favorable - proceed with caution' if probability == 'medium'
                else 'Not yet favorable - wait for better transits'
            ),
        },
    }
