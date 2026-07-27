from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import swisseph as swe
import pytz
import logging

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status, panchang_at_jd,
)

router = APIRouter()

logger = logging.getLogger(__name__)

QUESTION_HOUSE_MAP = {
    'career': 10, 'job': 10, 'work': 10, 'business': 7, 'promotion': 10,
    'marriage': 7, 'spouse': 7, 'love': 7, 'relationship': 7, 'partner': 7,
    'children': 5, 'child': 5, 'progeny': 5, 'pregnancy': 5,
    'health': 1, 'disease': 6, 'illness': 6, 'accident': 8, 'surgery': 8,
    'death': 8, 'longevity': 8,
    'money': 2, 'wealth': 2, 'finance': 2, 'property': 4, 'house': 4,
    'home': 4, 'land': 4, 'vehicle': 4,
    'education': 4, 'study': 4, 'exam': 4, 'knowledge': 9, 'spiritual': 9,
    'travel': 3, 'journey': 3, 'foreign': 12, 'abroad': 12, 'settle': 12,
    'litigation': 6, 'court': 6, 'case': 6, 'legal': 6,
    'loss': 12, 'expenditure': 12, 'debt': 6, 'loan': 6,
    'government': 10, 'authority': 10, 'power': 10,
    'father': 9, 'mother': 4, 'family': 2, 'siblings': 3, 'friend': 11,
    'enemy': 6, 'obstacle': 8, 'delay': 8,
    'fortune': 9, 'luck': 9, 'fate': 9, 'destiny': 9,
    'marriage': 7, 'divorce': 7, 'separation': 6,
    'success': 1, 'victory': 1, 'gain': 11, 'profit': 11,
}

BENEFICS = {'Jupiter', 'Venus', 'Moon', 'Mercury'}
MALEFICS = {'Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu'}

ASPECT_DEGREES = {
    1: 0, 2: 60, 3: 120, 4: 90, 5: 60, 6: 120,
    7: 180, 8: 120, 9: 60, 10: 90, 11: 120, 12: 60,
}


class PrashnaRequest(BaseModel):
    question: str = Field(..., example="Will I get the job?")
    dateOfBirth: Optional[str] = Field(None, example="1990-05-15")
    timeOfBirth: Optional[str] = Field(None, example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


def _resolve_question_time(
    body: PrashnaRequest,
) -> tuple:
    tz = pytz.timezone(body.timezone)
    now = datetime.now(tz)
    if body.dateOfBirth and body.timeOfBirth:
        date_str = body.dateOfBirth
        time_str = body.timeOfBirth
    else:
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M')
    return date_str, time_str, tz, now


def _detect_question_house(question: str) -> int:
    q_lower = question.lower()
    for keyword, house in QUESTION_HOUSE_MAP.items():
        if keyword in q_lower:
            return house
    return 1


def _find_planet_in_house(planets: list, house_num: int) -> list:
    return [p for p in planets if p.get('house') == house_num]


def _collect_aspects(planets: list, target_house: int) -> List[Dict[str, Any]]:
    aspects = []
    for p in planets:
        p_house = p.get('house', 0)
        if p_house == 0:
            continue
        diff = abs(p_house - target_house)
        diff = min(diff, 12 - diff)
        orb = ASPECT_DEGREES.get(diff, 0)
        if diff == 0:
            continue
        if diff == 1:
            aspects.append({
                'planet': p['name'],
                'type': 'Conjunction',
                'house': p_house,
                'toHouse': target_house,
                'nature': 'benefic' if p['name'] in BENEFICS else 'malefic',
            })
        elif diff == 6:
            aspects.append({
                'planet': p['name'],
                'type': 'Opposition',
                'house': p_house,
                'toHouse': target_house,
                'nature': 'benefic' if p['name'] in BENEFICS else 'malefic',
            })
        elif diff == 2:
            aspects.append({
                'planet': p['name'],
                'type': 'Trine',
                'house': p_house,
                'toHouse': target_house,
                'nature': 'benefic' if p['name'] in BENEFICS else 'malefic',
            })
        elif diff == 3:
            aspects.append({
                'planet': p['name'],
                'type': 'Square',
                'house': p_house,
                'toHouse': target_house,
                'nature': 'malefic',
            })

    special_aspects = {
        'Mars': [4, 8],
        'Jupiter': [5, 9],
        'Saturn': [3, 10],
    }
    for p in planets:
        p_house = p.get('house', 0)
        p_name = p['name']
        if p_name not in special_aspects:
            continue
        for offset in special_aspects[p_name]:
            target = ((p_house - 1 + offset) % 12) + 1
            if target == target_house and p_house != target_house:
                aspects.append({
                    'planet': p_name,
                    'type': f'{p_name} Special Aspect ({offset})',
                    'house': p_house,
                    'toHouse': target_house,
                    'nature': 'benefic' if p_name in BENEFICS else 'malefic',
                })

    return aspects


def _judge_outcome(aspects: List[Dict[str, Any]], asc_lord_status: str) -> Dict[str, Any]:
    benefic_count = sum(1 for a in aspects if a['nature'] == 'benefic')
    malefic_count = sum(1 for a in aspects if a['nature'] == 'malefic')

    lord_benefic = asc_lord_status in ('Exalted', 'Own Sign', 'Mooltrikona', 'Friendly')

    score = 0
    if lord_benefic:
        score += 30
    score += benefic_count * 15
    score -= malefic_count * 10

    if score >= 30:
        verdict = 'Favorable'
        summary = 'The chart strongly supports a positive outcome.'
    elif score >= 10:
        verdict = 'Moderately Favorable'
        summary = 'The outcome is likely positive but may require patience or effort.'
    elif score >= -10:
        verdict = 'Neutral / Mixed'
        summary = 'The outcome is uncertain; obstacles and support are balanced.'
    else:
        verdict = 'Unfavorable'
        summary = 'The chart indicates significant obstacles to a favorable outcome.'

    return {
        'verdict': verdict,
        'summary': summary,
        'score': score,
        'beneficAspects': benefic_count,
        'maleficAspects': malefic_count,
        'ascendantLordStrength': 'Strong' if lord_benefic else 'Weak',
    }


def _timing_from_asc_lord(asc_lord_planet: Dict[str, Any]) -> Dict[str, Any]:
    sign = asc_lord_planet.get('sign', '')
    house = asc_lord_planet.get('house', 0)
    retro = asc_lord_planet.get('isRetrograde', False)

    if retro:
        timing = 'Delayed; results will come after repeated attempts'
    elif house in (1, 4, 7, 10):
        timing = 'Quick; results within 1 to 3 months'
    elif house in (2, 5, 9, 11):
        timing = 'Moderate; results within 3 to 6 months'
    elif house in (3, 6):
        timing = 'Moderate to slow; results with sustained effort over 3 to 9 months'
    else:
        timing = 'Slow or obstructed; may take 6 to 12 months or more'

    return {
        'ascendantLordHouse': house,
        'ascendantLordSign': sign,
        'isRetrograde': retro,
        'predictedTimeframe': timing,
    }


def _timing_from_moon(moon: Dict[str, Any]) -> Dict[str, Any]:
    nk = moon.get('nakshatra', '')
    pada = moon.get('nakshatraPada', 1)
    sign = moon.get('sign', '')

    nk_lord = moon.get('nakshatraLord', '')
    sign_lord = moon.get('signLord', '')

    timing_unit = 'weeks'
    if nk_lord in ('Sun', 'Moon'):
        timing_unit = 'days'
    elif nk_lord in ('Mars', 'Saturn'):
        timing_unit = 'months'

    return {
        'moonNakshatra': nk,
        'moonNakshatraPada': pada,
        'moonSign': sign,
        'nakshatraLord': nk_lord,
        'signLord': sign_lord,
        'timingIndicator': timing_unit,
    }


def _suggest_remedies(verdict: str, malefic_aspects: List[Dict[str, Any]]) -> List[str]:
    if verdict != 'Unfavorable':
        return []

    remedies = []
    affected_planets = {a['planet'] for a in malefic_aspects}

    remedy_map = {
        'Saturn': ['Shani Puja on Saturday', 'Donate black sesame and mustard oil', 'Chant Shani Mantra: Om Sham Shanaishcharaya Namaha'],
        'Mars': ['Mangal Puja on Tuesday', 'Donate red lentils', 'Chant Mars Mantra: Om Ang Angarakaya Namaha'],
        'Rahu': ['Rahu-Ketu Shanti Puja', 'Donate blue/black cloth', 'Chant Rahu Mantra: Om Raam Rahave Namaha'],
        'Ketu': ['Naga Puja', 'Donate multi-colored cloth', 'Chant Ketu Mantra: Om Kem Ketave Namaha'],
        'Sun': ['Surya Namaskar at sunrise', 'Donate wheat and jaggery', 'Chant Gayatri Mantra'],
        'Moon': ['Chandra Puja on Monday', 'Donate rice and milk', 'Chant Chandra Mantra: Om Chandraya Namaha'],
        'Jupiter': ['Guru Puja on Thursday', 'Donate turmeric and yellow cloth', 'Chant Guru Mantra: Om Gram Greem Graum Sah Gurave Namaha'],
        'Venus': ['Lakshmi Puja on Friday', 'Donate white sweets', 'Chant Shukra Mantra: Om Draam Dreem Droum Sah Shukraya Namaha'],
        'Mercury': ['Budh Puja on Wednesday', 'Donate green gram', 'Chant Budh Mantra: Om Braam Breem Braum Sah Budhaya Namaha'],
    }

    for planet in affected_planets:
        if planet in remedy_map:
            remedies.extend(remedy_map[planet])

    if not remedies:
        remedies = [
            'Chant Mahamrityunjaya Mantra 108 times',
            'Offer water to Sun daily',
            'Visit a temple and seek blessings',
        ]

    return remedies


def _build_planet_summary(planets: list) -> Dict[str, Any]:
    summary = {}
    for p in planets:
        summary[p['name']] = {
            'sign': p['sign'],
            'signLord': p['signLord'],
            'house': p['house'],
            'degree': p['degree'],
            'retrograde': p['isRetrograde'],
            'combust': p['isCombust'],
            'status': planet_status(p['name'], p['sign']),
            'nakshatra': p['nakshatra'],
            'nakshatraLord': p['nakshatraLord'],
        }
    return summary


@router.post('/prashna/chart')
def prashna_chart(body: PrashnaRequest) -> Dict[str, Any]:
    try:
        date_str, time_str, tz, now = _resolve_question_time(body)
        jd = to_julian(date_str, time_str, body.timezone)

        planets = calc_planets(jd, None, body.nodeMode or 'mean')
        for p in planets:
            p['houseStatus'] = planet_status(p['name'], p['sign'])

        house_data = calc_houses(
            jd, body.latitude, body.longitude, planets, body.houseSystem or 'W'
        )

        asc = house_data['ascendant']
        asc_sign = asc['sign']
        asc_lord_name = SIGN_LORDS[asc_sign]
        asc_lord = next((p for p in planets if p['name'] == asc_lord_name), None)

        moon = next((p for p in planets if p['name'] == 'Moon'), None)

        question_house = _detect_question_house(body.question)
        question_house_sign = house_data['houses'][question_house - 1]['sign']
        question_house_lord = SIGN_LORDS[question_house_sign]
        question_lord_planet = next(
            (p for p in planets if p['name'] == question_house_lord), None
        )

        aspects_to_question_house = _collect_aspects(planets, question_house)

        judgement = _judge_outcome(
            aspects_to_question_house,
            planet_status(asc_lord_name, asc_lord['sign']) if asc_lord else 'Neutral',
        )

        panchang = panchang_at_jd(jd)

        return {
            'success': True,
            'data': {
                'question': body.question,
                'questionAnalysis': {
                    'detectedHouse': question_house,
                    'houseMeaning': _house_meaning(question_house),
                    'houseSign': question_house_sign,
                    'houseLord': question_house_lord,
                    'houseLordPosition': {
                        'house': question_lord_planet['house'] if question_lord_planet else None,
                        'sign': question_lord_planet['sign'] if question_lord_planet else None,
                        'retrograde': question_lord_planet['isRetrograde'] if question_lord_planet else None,
                        'status': planet_status(question_house_lord, question_lord_planet['sign']) if question_lord_planet else None,
                    } if question_lord_planet else None,
                },
                'querent': {
                    'ascendantSign': asc_sign,
                    'ascendantDegree': asc['degree'],
                    'ascendantNakshatra': asc['nakshatra'],
                    'ascendantLord': asc_lord_name,
                    'ascendantLordPosition': {
                        'house': asc_lord['house'] if asc_lord else None,
                        'sign': asc_lord['sign'] if asc_lord else None,
                        'retrograde': asc_lord['isRetrograde'] if asc_lord else None,
                        'status': planet_status(asc_lord_name, asc_lord['sign']) if asc_lord else None,
                    } if asc_lord else None,
                },
                'moon': {
                    'sign': moon['sign'] if moon else None,
                    'house': moon['house'] if moon else None,
                    'degree': moon['degree'] if moon else None,
                    'nakshatra': moon['nakshatra'] if moon else None,
                    'nakshatraPada': moon['nakshatraPada'] if moon else None,
                    'nakshatraLord': moon['nakshatraLord'] if moon else None,
                } if moon else None,
                'aspectsToRelevantHouse': aspects_to_question_house,
                'judgement': judgement,
                'planets': _build_planet_summary(planets),
                'houses': house_data['houses'],
                'panchang': panchang,
                'chartTime': f"{date_str} {time_str}",
                'chartLocation': {'latitude': body.latitude, 'longitude': body.longitude},
                'houseSystem': body.houseSystem or 'W',
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prashna chart error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compute prashna chart: {str(e)}")


@router.post('/prashna/judgement')
def prashna_judgement(body: PrashnaRequest) -> Dict[str, Any]:
    try:
        date_str, time_str, tz, now = _resolve_question_time(body)
        jd = to_julian(date_str, time_str, body.timezone)

        planets = calc_planets(jd, None, body.nodeMode or 'mean')
        for p in planets:
            p['houseStatus'] = planet_status(p['name'], p['sign'])

        house_data = calc_houses(
            jd, body.latitude, body.longitude, planets, body.houseSystem or 'W'
        )

        asc = house_data['ascendant']
        asc_sign = asc['sign']
        asc_lord_name = SIGN_LORDS[asc_sign]
        asc_lord = next((p for p in planets if p['name'] == asc_lord_name), None)

        moon = next((p for p in planets if p['name'] == 'Moon'), None)

        question_house = _detect_question_house(body.question)
        question_house_sign = house_data['houses'][question_house - 1]['sign']
        question_house_lord = SIGN_LORDS[question_house_sign]

        aspects = _collect_aspects(planets, question_house)
        asc_lord_status = planet_status(asc_lord_name, asc_lord['sign']) if asc_lord else 'Neutral'
        judgement = _judge_outcome(aspects, asc_lord_status)

        timing = _timing_from_asc_lord(asc_lord) if asc_lord else {
            'ascendantLordHouse': None,
            'ascendantLordSign': None,
            'isRetrograde': None,
            'predictedTimeframe': 'Unable to determine',
        }

        moon_timing = _timing_from_moon(moon) if moon else {
            'moonNakshatra': None,
            'moonNakshatraPada': None,
            'moonSign': None,
            'nakshatraLord': None,
            'signLord': None,
            'timingIndicator': None,
        }

        malefic_aspects = [a for a in aspects if a['nature'] == 'malefic']
        remedies = _suggest_remedies(judgement['verdict'], malefic_aspects)

        question_house_lord_planet = next(
            (p for p in planets if p['name'] == question_house_lord), None
        )
        qhl_status = (
            planet_status(question_house_lord, question_house_lord_planet['sign'])
            if question_house_lord_planet
            else 'Neutral'
        )

        return {
            'success': True,
            'data': {
                'question': body.question,
                'chartTime': f"{date_str} {time_str}",
                'querent': {
                    'ascendantSign': asc_sign,
                    'ascendantLord': asc_lord_name,
                    'ascendantLordStatus': asc_lord_status,
                },
                'relevantHouse': {
                    'houseNumber': question_house,
                    'sign': question_house_sign,
                    'lord': question_house_lord,
                    'lordStatus': qhl_status,
                },
                'overallJudgement': judgement,
                'timing': {
                    'ascendantLordTiming': timing,
                    'moonNakshatraTiming': moon_timing,
                    'combinedPrediction': _combine_timing(timing, moon_timing),
                },
                'aspects': aspects,
                'remedies': remedies,
                'detailedAnalysis': _detailed_analysis(
                    body.question, question_house, asc, asc_lord, moon, aspects, judgement
                ),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prashna judgement error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compute prashna judgement: {str(e)}")


def _house_meaning(house: int) -> str:
    meanings = {
        1: 'Self, identity, health, appearance, overall query',
        2: 'Wealth, family, speech, food, accumulated assets',
        3: 'Courage, siblings, short travels, communication, efforts',
        4: 'Home, property, mother, education, happiness, vehicles',
        5: 'Children, creativity, intellect, past merit, romance',
        6: 'Enemies, disease, debt, litigation, service, obstacles',
        7: 'Marriage, partnership, business, spouse, public dealings',
        8: 'Longevity, obstacles, hidden matters, transformation, sudden events',
        9: 'Fortune, dharma, father, higher learning, long travel, luck',
        10: 'Career, authority, reputation, karma, government, profession',
        11: 'Gains, income, friendships, aspirations, fulfillment',
        12: 'Loss, expenses, foreign lands, liberation, isolation, sleep',
    }
    return meanings.get(house, 'General')


def _combine_timing(lord_timing: Dict[str, Any], moon_timing: Dict[str, Any]) -> str:
    lord_tf = lord_timing.get('predictedTimeframe', '')
    moon_unit = moon_timing.get('timingIndicator', '')

    if '1 to 3 months' in lord_tf:
        return 'Results expected within 1 to 3 months'
    elif '3 to 6 months' in lord_tf:
        return 'Results expected within 3 to 6 months'
    elif '3 to 9 months' in lord_tf:
        return 'Results expected within 3 to 9 months'
    elif '6 to 12 months' in lord_tf:
        return 'Results may take 6 to 12 months or longer'
    elif 'Delayed' in lord_tf:
        return 'Results delayed; expect extended timeframe with persistent effort'
    else:
        return f'Timing based on Moon nakshatra ({moon_unit}): expect results in the near term'


def _detailed_analysis(
    question: str,
    question_house: int,
    asc: Dict[str, Any],
    asc_lord: Optional[Dict[str, Any]],
    moon: Optional[Dict[str, Any]],
    aspects: List[Dict[str, Any]],
    judgement: Dict[str, Any],
) -> str:
    parts = []

    parts.append(
        f"The querent is represented by the {asc['sign']} ascendant, "
        f"lorded by {SIGN_LORDS[asc['sign']]}."
    )

    if asc_lord:
        parts.append(
            f"The ascendant lord {asc_lord['name']} is placed in "
            f"house {asc_lord['house']} in {asc_lord['sign']}."
        )

    parts.append(
        f"The question pertains to house {question_house} ({_house_meaning(question_house)})."
    )

    if moon:
        parts.append(
            f"The Moon is in {moon['sign']}, nakshatra {moon['nakshatra']}, "
            f"pada {moon['nakshatraPada']}, in house {moon['house']}."
        )

    benefic_aspects = [a for a in aspects if a['nature'] == 'benefic']
    malefic_aspects = [a for a in aspects if a['nature'] == 'malefic']

    if benefic_aspects:
        bp = ', '.join(f"{a['planet']} ({a['type']})" for a in benefic_aspects)
        parts.append(f"Beneficial influences on the relevant house: {bp}.")

    if malefic_aspects:
        mp = ', '.join(f"{a['planet']} ({a['type']})" for a in malefic_aspects)
        parts.append(f"Adverse influences on the relevant house: {mp}.")

    parts.append(f"Overall judgement: {judgement['verdict']} - {judgement['summary']}")

    return ' '.join(parts)
