from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import pytz

router = APIRouter()


class DoshaStandaloneRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


class NadiDoshaRequest(BaseModel):
    maleDateOfBirth: str = Field(..., example="1990-05-15")
    maleTimeOfBirth: str = Field(..., example="14:30")
    maleLatitude: float = Field(..., example=28.6139)
    maleLongitude: float = Field(..., example=77.2090)
    maleTimezone: str = Field(..., example="Asia/Kolkata")
    femaleDateOfBirth: str = Field(..., example="1992-08-20")
    femaleTimeOfBirth: str = Field(..., example="09:15")
    femaleLatitude: float = Field(..., example=19.0760)
    femaleLongitude: float = Field(..., example=72.8777)
    femaleTimezone: str = Field(..., example="Asia/Kolkata")
    nodeMode: Optional[str] = Field('mean', example='mean')


NAKSHATRAS_ORDER = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]

NAKSHATRA_NADI = {
    'Ashwini': 'Aadi', 'Bharani': 'Madhya', 'Krittika': 'Antya',
    'Rohini': 'Antya', 'Mrigashira': 'Madhya', 'Ardra': 'Aadi',
    'Punarvasu': 'Aadi', 'Pushya': 'Madhya', 'Ashlesha': 'Antya',
    'Magha': 'Antya', 'Purva Phalguni': 'Madhya', 'Uttara Phalguni': 'Aadi',
    'Hasta': 'Aadi', 'Chitra': 'Madhya', 'Swati': 'Antya',
    'Vishakha': 'Antya', 'Anuradha': 'Madhya', 'Jyeshtha': 'Aadi',
    'Mula': 'Aadi', 'Purva Ashadha': 'Madhya', 'Uttara Ashadha': 'Antya',
    'Shravana': 'Antya', 'Dhanishta': 'Madhya', 'Shatabhisha': 'Aadi',
    'Purva Bhadrapada': 'Aadi', 'Uttara Bhadrapada': 'Madhya', 'Revati': 'Antya',
}

YONI_ANIMALS = {
    'Ashwini': 'Horse', 'Bharani': 'Elephant', 'Krittika': 'Sheep',
    'Rohini': 'Serpent', 'Mrigashira': 'Serpent', 'Ardra': 'Dog',
    'Punarvasu': 'Cat', 'Pushya': 'Sheep', 'Ashlesha': 'Cat',
    'Magha': 'Rat', 'Purva Phalguni': 'Rat', 'Uttara Phalguni': 'Cow',
    'Hasta': 'Buffalo', 'Chitra': 'Tiger', 'Swati': 'Buffalo',
    'Vishakha': 'Tiger', 'Anuradha': 'Deer', 'Jyeshtha': 'Deer',
    'Mula': 'Dog', 'Purva Ashadha': 'Monkey', 'Uttara Ashadha': 'Mongoose',
    'Shravana': 'Monkey', 'Dhanishta': 'Lion', 'Shatabhisha': 'Horse',
    'Purva Bhadrapada': 'Lion', 'Uttara Bhadrapada': 'Cow', 'Revati': 'Elephant'
}

YONI_FRIENDSHIP = {
    ('Horse', 'Buffalo'): 0, ('Horse', 'Elephant'): 2, ('Horse', 'Horse'): 0,
    ('Elephant', 'Lion'): 0, ('Elephant', 'Monkey'): 2, ('Elephant', 'Elephant'): 0,
    ('Sheep', 'Tiger'): 0, ('Sheep', 'Sheep'): 0, ('Sheep', 'Dog'): 2,
    ('Serpent', 'Mongoose'): 0, ('Serpent', 'Dog'): 2, ('Serpent', 'Serpent'): 0,
    ('Dog', 'Deer'): 0, ('Dog', 'Dog'): 0, ('Dog', 'Lion'): 2,
    ('Cat', 'Deer'): 2, ('Cat', 'Cat'): 0, ('Cat', 'Mongoose'): 0,
    ('Rat', 'Cow'): 0, ('Rat', 'Cat'): 0, ('Rat', 'Rat'): 0,
    ('Cow', 'Lion'): 0, ('Cow', 'Cow'): 0, ('Cow', 'Tiger'): 2,
    ('Buffalo', 'Tiger'): 2, ('Buffalo', 'Buffalo'): 0,
    ('Tiger', 'Monkey'): 0, ('Tiger', 'Tiger'): 0,
    ('Deer', 'Monkey'): 2, ('Deer', 'Deer'): 0,
    ('Monkey', 'Lion'): 0, ('Monkey', 'Monkey'): 0,
    ('Mongoose', 'Lion'): 2, ('Mongoose', 'Mongoose'): 0,
    ('Lion', 'Lion'): 0,
}

YONI_GENDER = {
    'Horse': 'Male', 'Elephant': 'Male', 'Sheep': 'Female', 'Serpent': 'Male',
    'Dog': 'Male', 'Cat': 'Female', 'Rat': 'Male', 'Cow': 'Female',
    'Buffalo': 'Female', 'Tiger': 'Male', 'Deer': 'Female', 'Monkey': 'Male',
    'Mongoose': 'Male', 'Lion': 'Female',
}


def _get_planets_for(body: DoshaStandaloneRequest):
    from ..main import to_julian, calc_planets, calc_houses
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    return planets


def _get_moon_nakshatra(body: DoshaStandaloneRequest) -> Optional[str]:
    from ..main import to_julian, calc_planets
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    return moon['nakshatra'] if moon else None


@router.post('/dosha/grahan')
def grahan_dosha(body: DoshaStandaloneRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra
    import swisseph as swe

    planets = _get_planets_for(body)

    sun = next((p for p in planets if p['name'] == 'Sun'), None)
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    rahu = next((p for p in planets if p['name'] == 'Rahu'), None)
    ketu = next((p for p in planets if p['name'] == 'Ketu'), None)

    afflictions = []

    if sun and rahu:
        dist = abs(sun['longitude'] - rahu['longitude'])
        dist = min(dist, 360 - dist)
        if dist < 12:
            afflictions.append({
                'type': 'Surya Grahan (Solar Eclipse)',
                'description': f"Rahu conjunct Sun within {dist:.2f} degrees in {sun['sign']}",
                'distance': round(dist, 2),
                'sign': sun['sign'],
                'house': sun.get('house', 0),
                'severity': 'High' if dist < 6 else 'Medium',
                'effects': 'Ancestral karmic debt affecting father, eyes, health, government relations',
                'remedies': ['Surya Namaskar daily', 'Donate wheat on Sunday', 'Chant Aditya Hridayam', 'Worship Lord Shiva'],
            })

    if sun and ketu:
        dist = abs(sun['longitude'] - ketu['longitude'])
        dist = min(dist, 360 - dist)
        if dist < 12:
            afflictions.append({
                'type': 'Surya Grahan (Solar Eclipse - Ketu)',
                'description': f"Ketu conjunct Sun within {dist:.2f} degrees in {sun['sign']}",
                'distance': round(dist, 2),
                'sign': sun['sign'],
                'house': sun.get('house', 0),
                'severity': 'High' if dist < 6 else 'Medium',
                'effects': 'Spiritual karmic lessons, detachment from worldly pursuits, eye issues',
                'remedies': ['Worship Ganesh', 'Donate copper on Sunday', 'Chant Ganesh Atharvashirsha'],
            })

    if moon and rahu:
        dist = abs(moon['longitude'] - rahu['longitude'])
        dist = min(dist, 360 - dist)
        if dist < 12:
            afflictions.append({
                'type': 'Chandra Grahan (Lunar Eclipse)',
                'description': f"Rahu conjunct Moon within {dist:.2f} degrees in {moon['sign']}",
                'distance': round(dist, 2),
                'sign': moon['sign'],
                'house': moon.get('house', 0),
                'severity': 'High' if dist < 6 else 'Medium',
                'effects': 'Mental unrest, emotional turbulence, relationship with mother affected, anxiety',
                'remedies': ['Chandra Puja', 'Donate rice on Monday', 'Worship Lord Shiva on Monday', 'Moon stone gemstone'],
            })

    if moon and ketu:
        dist = abs(moon['longitude'] - ketu['longitude'])
        dist = min(dist, 360 - dist)
        if dist < 12:
            afflictions.append({
                'type': 'Chandra Grahan (Lunar Eclipse - Ketu)',
                'description': f"Ketu conjunct Moon within {dist:.2f} degrees in {moon['sign']}",
                'distance': round(dist, 2),
                'sign': moon['sign'],
                'house': moon.get('house', 0),
                'severity': 'High' if dist < 6 else 'Medium',
                'effects': 'Spiritual confusion, emotional detachment, intuitive but unstable mind',
                'remedies': ['Meditation practice', 'Chant Maha Mrityunjaya Mantra', 'Worship Shiva on Monday'],
            })

    present = len(afflictions) > 0
    return {
        'status': 200,
        'grahanPresent': present,
        'afflictionCount': len(afflictions),
        'afflictions': afflictions,
        'summary': 'Grahan Dosha present - significant karmic affliction' if present else 'No Grahan Dosha detected',
    }


@router.post('/dosha/shrapit')
def shrapit_dosha(body: DoshaStandaloneRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra

    planets = _get_planets_for(body)

    saturn = next((p for p in planets if p['name'] == 'Saturn'), None)
    rahu = next((p for p in planets if p['name'] == 'Rahu'), None)

    shrapit_present = False
    details = {}

    if saturn and rahu:
        if saturn['sign'] == rahu['sign']:
            shrapit_present = True
            details = {
                'type': 'Shrapit Dosha (Saturn-Rahu Conjunction)',
                'description': f"Saturn and Rahu conjunct in {saturn['sign']}",
                'sign': saturn['sign'],
                'house': saturn.get('house', 0),
                'saturnDegree': saturn['degree'],
                'rahuDegree': rahu['degree'],
                'saturnRetrograde': saturn['isRetrograde'],
                'rahuRetrograde': rahu['isRetrograde'],
                'severity': 'Very High',
                'effects': [
                    'Curses from past life manifesting as obstacles',
                    'Delays in all areas of life - career, marriage, property',
                    'Relationship with authority figures strained',
                    'Need for patience and persistent effort',
                    'Spiritual transformation through hardships',
                ],
                'remedies': [
                    'Shani Rahu Shanti Puja',
                    'Rudra Abhishek at Shiva temple',
                    'Donate mustard oil and black sesame on Saturday',
                    'Worship Lord Hanuman on Saturday',
                    'Chant Shani Stotra and Rahu Beej Mantra',
                    'Feed crows regularly',
                    'Visit Rahu/Ketu temple during Rahu Kaal',
                ],
            }

    return {
        'status': 200,
        'shrapitPresent': shrapit_present,
        'details': details if shrapit_present else None,
        'summary': 'Shrapit Dosha present - Saturn and Rahu in same sign' if shrapit_present else 'No Shrapit Dosha detected',
    }


@router.post('/dosha/manglik-detailed')
def manglik_detailed(body: DoshaStandaloneRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra

    planets = _get_planets_for(body)

    mars = next((p for p in planets if p['name'] == 'Mars'), None)

    if not mars:
        return {'status': 200, 'manglikPresent': False, 'summary': 'Mars position not found'}

    mars_house = mars.get('house', 0)
    manglik_houses = [1, 2, 4, 7, 8, 12]
    manglik_present = mars_house in manglik_houses

    HOUSE_AFFECTS = {
        1: {
            'area': 'Self & Personality',
            'description': 'Mars in ascendant creates aggressive personality, impulsiveness, dominance',
            'impact': 'Arguments with spouse, difficulty in married life, strong willpower',
            'severity': 8,
        },
        2: {
            'area': 'Family & Wealth',
            'description': 'Mars in 2nd creates harsh speech, family disputes, financial volatility',
            'impact': 'Speech-related issues in marriage, wealth fluctuations, family discord',
            'severity': 6,
        },
        4: {
            'area': 'Home & Property',
            'description': 'Mars in 4th creates restlessness at home, property disputes, mother health issues',
            'impact': 'Domestic unrest, property matters, lack of peace at home',
            'severity': 8,
        },
        7: {
            'area': 'Marriage & Partnership',
            'description': 'Mars in 7th is the strongest Manglik position - directly afflicts marriage house',
            'impact': 'Severe marital discord, spouse health concerns, delays in marriage, extra-marital tendencies',
            'severity': 10,
        },
        8: {
            'area': 'Longevity & Transformation',
            'description': 'Mars in 8th creates hidden dangers, accidents, sudden events, health issues',
            'impact': 'Health to spouse, sudden life changes, accidents, inheritance disputes',
            'severity': 9,
        },
        12: {
            'area': 'Losses & Foreign Lands',
            'description': 'Mars in 12th creates expenses, separation, sleep issues, foreign connections',
            'impact': 'Expenses on spouse, sleep disturbances, separation from family, hospitalization',
            'severity': 7,
        },
    }

    result = {
        'manglikPresent': manglik_present,
        'marsSign': mars['sign'],
        'marsHouse': mars_house,
        'marsDegree': mars['degree'],
        'marsRetrograde': mars['isRetrograde'],
        'marsNakshatra': mars['nakshatra'],
    }

    if manglik_present:
        house_info = HOUSE_AFFECTS.get(mars_house, {})
        severity_score = house_info.get('severity', 5)
        retro_modifier = -2 if mars['isRetrograde'] else 0
        final_severity = max(1, severity_score + retro_modifier)

        if final_severity >= 8:
            severity_label = 'Very High'
        elif final_severity >= 6:
            severity_label = 'High'
        elif final_severity >= 4:
            severity_label = 'Medium'
        else:
            severity_label = 'Low'

        result.update({
            'affectedArea': house_info.get('area', 'Unknown'),
            'description': house_info.get('description', ''),
            'impact': house_info.get('impact', ''),
            'severityScore': final_severity,
            'severityLabel': severity_label,
            'retrogradeNote': 'Retrograde Mars reduces Manglik severity by 2 points' if mars['isRetrograde'] else '',
            'remedies': [
                'Kumbh Vivah (marriage to banana plant before actual marriage)',
                'Mangal Puja at Mangalnath temple',
                'Tuesday fasting (eat only after sunset)',
                'Hanuman Chalisa recitation on Tuesday',
                'Donate red lentils (masoor dal) on Tuesday',
                'Chant Mangal Beej Mantra: "Om Ang Angarakaya Namah"',
                'Wear Red Coral (Moonga) after astrological consultation',
            ],
            'cancellationNotes': [
                'Mars in own sign (Aries/Scorpio) or exalted (Capricorn) - reduced effect',
                'Jupiter aspect on Mars - provides protective influence',
                'Saturn aspect on Mars - can reduce Manglik effect',
                'Mars in conjunction with benefics - softened impact',
                'Both partners are Manglik - dosha cancels mutually',
            ],
        })
    else:
        result.update({
            'summary': 'No Manglik Dosha - Mars not in dosha houses',
            'severityScore': 0,
            'severityLabel': 'None',
        })

    return {'status': 200, **result}


@router.post('/dosha/nadi-dosha')
def nadi_dosha(body: NadiDoshaRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra

    jd_male = to_julian(body.maleDateOfBirth, body.maleTimeOfBirth, body.maleTimezone)
    planets_male = calc_planets(jd_male, None, body.nodeMode or 'mean')
    male_moon = next((p for p in planets_male if p['name'] == 'Moon'), None)

    jd_female = to_julian(body.femaleDateOfBirth, body.femaleTimeOfBirth, body.femaleTimezone)
    planets_female = calc_planets(jd_female, None, body.nodeMode or 'mean')
    female_moon = next((p for p in planets_female if p['name'] == 'Moon'), None)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    male_nadi = NAKSHATRA_NADI.get(male_nakshatra, 'Aadi')
    female_nadi = NAKSHATRA_NADI.get(female_nakshatra, 'Aadi')

    nadi_dosha_present = male_nadi == female_nadi
    score = 0 if nadi_dosha_present else 8

    return {
        'status': 200,
        'nadiDoshaPresent': nadi_dosha_present,
        'maleNakshatra': male_nakshatra,
        'femaleNakshatra': female_nakshatra,
        'maleNadi': male_nadi,
        'femaleNadi': female_nadi,
        'score': score,
        'maxScore': 8,
        'description': f"Male Nadi: {male_nadi}, Female Nadi: {female_nadi} - {'Same Nadi detected' if nadi_dosha_present else 'Different Nadi - no dosha'}",
        'effects': [
            'Health issues in children if Nadi Dosha present',
            'Genetic incompatibility concerns',
            'Physical and mental health of offspring at risk',
            'Dosha is stronger when both belong to same Nadi and same nakshatra',
        ] if nadi_dosha_present else ['No Nadi Dosha - excellent for progeny health'],
        'remedies': [
            'Nadi Nivaran Puja at temple',
            'Maha Mrityunjaya Mantra japa (108 times daily)',
            'Visit Shiva temple on Monday',
            'Donate copper and rice',
            'Perform Nadi Dosha nivaran during auspicious muhurta',
        ] if nadi_dosha_present else [],
    }


@router.post('/dosha/bhakoot-dosha')
def bhakoot_dosha(body: NadiDoshaRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra

    jd_male = to_julian(body.maleDateOfBirth, body.maleTimeOfBirth, body.maleTimezone)
    planets_male = calc_planets(jd_male, None, body.nodeMode or 'mean')
    male_moon = next((p for p in planets_male if p['name'] == 'Moon'), None)

    jd_female = to_julian(body.femaleDateOfBirth, body.femaleTimeOfBirth, body.femaleTimezone)
    planets_female = calc_planets(jd_female, None, body.nodeMode or 'mean')
    female_moon = next((p for p in planets_female if p['name'] == 'Moon'), None)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_sign_idx = ZODIAC_SIGNS.index(male_moon['sign'])
    female_sign_idx = ZODIAC_SIGNS.index(female_moon['sign'])
    diff = (female_sign_idx - male_sign_idx) % 12 + 1

    bhakoot_dosha_present = diff in [2, 12, 1, 5, 6]
    score = 0 if bhakoot_dosha_present else 7

    dosha_type = ''
    if diff == 2:
        dosha_type = '2-12 Bhakoot Dosha'
    elif diff == 12:
        dosha_type = '2-12 Bhakoot Dosha'
    elif diff == 1:
        dosha_type = '1-7 Bhakoot Dosha'
    elif diff == 5:
        dosha_type = '5-9 Bhakoot Dosha'
    elif diff == 6:
        dosha_type = '6-8 Bhakoot Dosha'

    return {
        'status': 200,
        'bhakootDoshaPresent': bhakoot_dosha_present,
        'maleMoonSign': male_moon['sign'],
        'femaleMoonSign': female_moon['sign'],
        'signDifference': diff,
        'doshaType': dosha_type,
        'score': score,
        'maxScore': 7,
        'effects': [
            f"Sign difference {diff} creates Bhakoot Dosha",
            'Financial instability in family',
            'Disagreements on family values and priorities',
            'Health concerns for one partner',
            'Difficulty in maintaining harmony',
        ] if bhakoot_dosha_present else ['No Bhakoot Dosha - harmonious family life expected'],
        'remedies': [
            'Bhakoot Puja at temple',
            'Worship Lord Vishnu and Goddess Lakshmi on Fridays',
            'Observe Ekadashi fasts together',
            'Donate sugar and rice',
            'Visit Tirupati Balaji temple',
        ] if bhakoot_dosha_present else [],
    }


@router.post('/dosha/yoni-compatibility')
def yoni_compatibility(body: NadiDoshaRequest) -> Dict[str, Any]:
    from ..main import to_julian, calc_planets, get_nakshatra

    jd_male = to_julian(body.maleDateOfBirth, body.maleTimeOfBirth, body.maleTimezone)
    planets_male = calc_planets(jd_male, None, body.nodeMode or 'mean')
    male_moon = next((p for p in planets_male if p['name'] == 'Moon'), None)

    jd_female = to_julian(body.femaleDateOfBirth, body.femaleTimeOfBirth, body.femaleTimezone)
    planets_female = calc_planets(jd_female, None, body.nodeMode or 'mean')
    female_moon = next((p for p in planets_female if p['name'] == 'Moon'), None)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    male_animal = YONI_ANIMALS.get(male_nakshatra, 'Unknown')
    female_animal = YONI_ANIMALS.get(female_nakshatra, 'Unknown')
    male_gender = YONI_GENDER.get(male_animal, 'Unknown')
    female_gender = YONI_GENDER.get(female_animal, 'Unknown')

    if male_animal == female_animal:
        score = 4
        nature = 'Same Animal'
        compatibility = 'Excellent'
    else:
        pair = (male_animal, female_animal) if (male_animal, female_animal) in YONI_FRIENDSHIP else (female_animal, male_animal)
        friendship = YONI_FRIENDSHIP.get(pair, 1)
        score = 2 if friendship == 2 else (1 if friendship == 1 else 0)
        nature = 'Friendly' if score >= 2 else ('Neutral' if score == 1 else 'Enemy')
        compatibility = 'Good' if score >= 2 else ('Average' if score == 1 else 'Poor')

    return {
        'status': 200,
        'maleNakshatra': male_nakshatra,
        'femaleNakshatra': female_nakshatra,
        'maleYoniAnimal': male_animal,
        'femaleYoniAnimal': female_animal,
        'maleAnimalGender': male_gender,
        'femaleAnimalGender': female_gender,
        'score': score,
        'maxScore': 4,
        'nature': nature,
        'compatibility': compatibility,
        'description': f"Male {male_animal} ({male_gender}), Female {female_animal} ({female_gender}) - {nature} - {compatibility} compatibility",
    }
