from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import swisseph as swe

from ..utils import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, planet_status

router = APIRouter()


class CalculatorRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field("W", example="W")
    nodeMode: Optional[str] = Field("mean", example="mean")


class PlanetStrengthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field("W", example="W")
    nodeMode: Optional[str] = Field("mean", example="mean")


def get_house_of_planet(planets: list, planet_name: str) -> int:
    for p in planets:
        if p['name'] == planet_name:
            return p.get('house', 0)
    return 0


def get_sign_of_planet(planets: list, planet_name: str) -> str:
    for p in planets:
        if p['name'] == planet_name:
            return p.get('sign', '')
    return ''


def calculate_dignity_score(planet_name: str, sign: str) -> int:
    props = {
        'Sun': {'exalted':'Aries','debil':'Libra','own':['Leo'],'friends':['Moon','Mars','Jupiter'],'enemies':['Venus','Saturn'],'neutral':['Mercury']},
        'Moon': {'exalted':'Taurus','debil':'Scorpio','own':['Cancer'],'friends':['Sun','Mercury'],'enemies':[],'neutral':['Mars','Jupiter','Venus','Saturn']},
        'Mars': {'exalted':'Capricorn','debil':'Cancer','own':['Aries','Scorpio'],'friends':['Sun','Moon','Jupiter'],'enemies':['Mercury'],'neutral':['Venus','Saturn']},
        'Mercury': {'exalted':'Virgo','debil':'Pisces','own':['Gemini','Virgo'],'friends':['Sun','Venus'],'enemies':['Moon','Mars'],'neutral':['Jupiter','Saturn']},
        'Jupiter': {'exalted':'Cancer','debil':'Capricorn','own':['Sagittarius','Pisces'],'friends':['Sun','Moon','Mars'],'enemies':['Mercury','Venus'],'neutral':['Saturn']},
        'Venus': {'exalted':'Pisces','debil':'Virgo','own':['Taurus','Libra'],'friends':['Mercury','Saturn'],'enemies':['Sun','Moon'],'neutral':['Mars','Jupiter']},
        'Saturn': {'exalted':'Libra','debil':'Aries','own':['Capricorn','Aquarius'],'friends':['Mercury','Venus'],'enemies':['Sun','Moon','Mars'],'neutral':['Jupiter']},
    }
    p = props.get(planet_name)
    if not p:
        return 50
    if p['exalted'] == sign:
        return 100
    if p['debil'] == sign:
        return 10
    if sign in p['own']:
        return 75
    lord = SIGN_LORDS.get(sign, '')
    if lord in p.get('friends', []):
        return 65
    if lord in p.get('enemies', []):
        return 25
    return 50


def get_avastha_score(deg_in_sign: float, sign: str) -> int:
    odd = sign in ['Aries','Gemini','Leo','Libra','Sagittarius','Aquarius']
    zone = int(deg_in_sign // 6)
    scores = [20, 40, 60, 40, 20] if odd else [20, 40, 60, 40, 20]
    return scores[min(zone, 4)]


def calculate_ashtakavarga_points(planets: list, asc_sign_idx: int) -> List[Dict[str, Any]]:
    benefic_planets = ['Jupiter', 'Venus', 'Mercury', 'Moon']
    result = []
    for i in range(12):
        house_sign = ZODIAC_SIGNS[(asc_sign_idx + i) % 12]
        points = 0
        contributors = []
        for bp in benefic_planets:
            bp_data = next((p for p in planets if p['name'] == bp), None)
            if bp_data:
                bp_house = bp_data.get('house', 0)
                if bp_house > 0:
                    aspects_to_house = [(bp_house + 6) % 12 or 12]
                    if (i + 1) in aspects_to_house:
                        points += 1
                        contributors.append(bp)
                    if bp_house == i + 1:
                        points += 1
                        contributors.append(bp)
        result.append({
            "house": i + 1,
            "sign": house_sign,
            "points": min(points, 8),
            "contributors": contributors
        })
    return result


@router.post("/calculator/lagna")
def calculate_lagna(req: CalculatorRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    hsys = (req.houseSystem or 'W').encode('ascii')
    cusps, ascmc = swe.houses_ex(jd, req.latitude, req.longitude, hsys, swe.FLG_SIDEREAL)
    asc_lon = ascmc[0]
    asc_sign = ZODIAC_SIGNS[int(asc_lon // 30) % 12]
    asc_deg_in_sign = asc_lon % 30

    return {
        "status": 200,
        "data": {
            "ascendant": {
                "longitude": asc_lon,
                "sign": asc_sign,
                "signLord": SIGN_LORDS[asc_sign],
                "degreeInSign": asc_deg_in_sign,
                "degreeDMS": f"{int(asc_deg_in_sign)}°{int((asc_deg_in_sign % 1) * 60)}'{int(((asc_deg_in_sign * 60) % 1) * 60)}\""
            }
        }
    }


@router.post("/calculator/moon-sign")
def calculate_moon_sign(req: CalculatorRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xx, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
    moon_lon = xx[0]
    moon_sign = ZODIAC_SIGNS[int(moon_lon // 30) % 12]
    moon_deg = moon_lon % 30

    return {
        "status": 200,
        "data": {
            "moonSign": {
                "longitude": moon_lon,
                "sign": moon_sign,
                "signLord": SIGN_LORDS[moon_sign],
                "degreeInSign": moon_deg,
                "rashi": moon_sign
            }
        }
    }


@router.post("/calculator/sun-sign")
def calculate_sun_sign(req: CalculatorRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
    sun_lon = xx[0]
    sun_sign = ZODIAC_SIGNS[int(sun_lon // 30) % 12]
    sun_deg = sun_lon % 30

    return {
        "status": 200,
        "data": {
            "sunSign": {
                "longitude": sun_lon,
                "sign": sun_sign,
                "signLord": SIGN_LORDS[sun_sign],
                "degreeInSign": sun_deg
            }
        }
    }


@router.post("/calculator/planet-strength")
def calculate_planet_strength(req: PlanetStrengthRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode)
    hs_code = req.houseSystem or 'W'
    house_data = calc_houses(jd, req.latitude, req.longitude, planets, hs_code)

    strength_results = []
    for p in planets:
        if p['name'] in ['Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto']:
            continue
        dignity = planet_status(p['name'], p['sign'])
        dignity_score = calculate_dignity_score(p['name'], p['sign'])
        avastha_score = get_avastha_score(p['degree'], p['sign'])
        house = p.get('house', 0)
        house_score = 0
        if house in [1, 4, 7, 10]:
            house_score = 20
        elif house in [5, 9]:
            house_score = 15
        elif house in [3, 6, 11]:
            house_score = 10
        elif house in [2, 12]:
            house_score = 5
        elif house in [8]:
            house_score = 0
        speed = abs(p.get('speed', 0))
        speed_score = min(20, int(speed * 5)) if speed > 0 else 5
        total = (dignity_score * 0.4 + avastha_score * 0.15 + house_score * 0.25 + speed_score * 0.2)
        total = min(100, max(0, int(total)))

        strength_results.append({
            "planet": p['name'],
            "sign": p['sign'],
            "house": house,
            "dignity": dignity,
            "dignityScore": dignity_score,
            "avastha": p.get('avastha', ''),
            "avasthaScore": avastha_score,
            "houseScore": house_score,
            "speedScore": speed_score,
            "overallStrength": total
        })

    return {
        "status": 200,
        "data": {
            "planets": strength_results,
            "methodology": "Dignity 40% + House 25% + Speed 20% + Avastha 15%"
        }
    }


@router.post("/calculator/shadbala")
def calculate_shadbala(req: PlanetStrengthRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode)
    hs_code = req.houseSystem or 'W'
    house_data = calc_houses(jd, req.latitude, req.longitude, planets, hs_code)

    shadbala_results = []
    for p in planets:
        if p['name'] in ['Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto']:
            continue
        house = p.get('house', 0)
        dignity = planet_status(p['name'], p['sign'])
        positional = calculate_dignity_score(p['name'], p['sign'])
        temporal = 0
        if house in [1, 4, 7, 10]:
            temporal = 60
        elif house in [3, 6, 9, 12]:
            temporal = 45
        elif house in [2, 5, 8, 11]:
            temporal = 50
        speed = abs(p.get('speed', 0))
        motional = min(60, int(speed * 15)) if speed > 0 else 20
        aspect_score = 0
        for other in planets:
            if other['name'] == p['name'] or other['name'] in ['Rahu', 'Ketu']:
                continue
            diff = abs(p['longitude'] - other['longitude'])
            diff = min(diff, 360 - diff)
            if abs(diff - 180) < 10:
                aspect_score += 10
            elif abs(diff - 120) < 10:
                aspect_score += 8
            elif abs(diff - 90) < 10:
                aspect_score += 5
            elif diff < 10:
                aspect_score += 3
        aspect_score = min(60, aspect_score)
        total_shadbala = (positional + temporal + motional + aspect_score) / 4

        shadbala_results.append({
            "planet": p['name'],
            "positionalStrength": positional,
            "temporalStrength": temporal,
            "motionalStrength": motional,
            "aspectStrength": aspect_score,
            "totalShadbala": round(total_shadbala, 2),
            "dignity": dignity
        })

    return {
        "status": 200,
        "data": {
            "shadbala": shadbala_results,
            "scale": "0-100 for each component, total is average",
            "components": ["Positional (dignity)", "Temporal (house)", "Motional (speed)", "Aspect (mutual aspects)"]
        }
    }


@router.post("/calculator/ashtakavarga")
def calculate_ashtakavarga(req: PlanetStrengthRequest):
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode)
    hs_code = req.houseSystem or 'W'
    house_data = calc_houses(jd, req.latitude, req.longitude, planets, hs_code)

    asc_sign = house_data['ascendant']['sign']
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    av_points = calculate_ashtakavarga_points(planets, asc_idx)

    total_points = sum(h['points'] for h in av_points)
    strong_houses = [h for h in av_points if h['points'] >= 4]
    weak_houses = [h for h in av_points if h['points'] <= 1]

    return {
        "status": 200,
        "data": {
            "ashtakavarga": {
                "houses": av_points,
                "totalPoints": total_points,
                "maxPossible": 56,
                "strongHouses": [{"house": h['house'], "sign": h['sign'], "points": h['points']} for h in strong_houses],
                "weakHouses": [{"house": h['house'], "sign": h['sign'], "points": h['points']} for h in weak_houses]
            },
            "methodology": "Count benefic aspects from Jupiter, Venus, Mercury, Moon to each house",
            "note": "Simplified calculation - full Ashtakavarga considers individual planet benefic status based on sign lord relationships"
        }
    }
