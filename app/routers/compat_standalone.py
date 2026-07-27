from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

router = APIRouter()


class CompatRequest(BaseModel):
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

NAKSHATRA_GANA = {
    'Ashwini': 'Deva', 'Bharani': 'Manushya', 'Krittika': 'Rakshasa',
    'Rohini': 'Manushya', 'Mrigashira': 'Deva', 'Ardra': 'Manushya',
    'Punarvasu': 'Deva', 'Pushya': 'Deva', 'Ashlesha': 'Rakshasa',
    'Magha': 'Rakshasa', 'Purva Phalguni': 'Manushya', 'Uttara Phalguni': 'Manushya',
    'Hasta': 'Deva', 'Chitra': 'Rakshasa', 'Swati': 'Deva',
    'Vishakha': 'Rakshasa', 'Anuradha': 'Deva', 'Jyeshtha': 'Rakshasa',
    'Mula': 'Rakshasa', 'Purva Ashadha': 'Manushya', 'Uttara Ashadha': 'Manushya',
    'Shravana': 'Deva', 'Dhanishta': 'Rakshasa', 'Shatabhisha': 'Rakshasa',
    'Purva Bhadrapada': 'Manushya', 'Uttara Bhadrapada': 'Manushya', 'Revati': 'Deva',
}

GANA_COMPAT = {
    ('Deva', 'Deva'): 6, ('Deva', 'Manushya'): 5, ('Deva', 'Rakshasa'): 1,
    ('Manushya', 'Deva'): 5, ('Manushya', 'Manushya'): 6, ('Manushya', 'Rakshasa'): 0,
    ('Rakshasa', 'Deva'): 1, ('Rakshasa', 'Manushya'): 0, ('Rakshasa', 'Rakshasa'): 6,
}

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


def _compute_moon_positions(body: CompatRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS

    jd_male = to_julian(body.maleDateOfBirth, body.maleTimeOfBirth, body.maleTimezone)
    planets_male = calc_planets(jd_male, None, body.nodeMode or 'mean')
    house_male = calc_houses(jd_male, body.maleLatitude, body.maleLongitude, planets_male, 'W')
    male_moon = next((p for p in planets_male if p['name'] == 'Moon'), None)
    male_asc = house_male['ascendant']

    jd_female = to_julian(body.femaleDateOfBirth, body.femaleTimeOfBirth, body.femaleTimezone)
    planets_female = calc_planets(jd_female, None, body.nodeMode or 'mean')
    house_female = calc_houses(jd_female, body.femaleLatitude, body.femaleLongitude, planets_female, 'W')
    female_moon = next((p for p in planets_female if p['name'] == 'Moon'), None)
    female_asc = house_female['ascendant']

    return male_moon, female_moon, male_asc, female_asc, ZODIAC_SIGNS


def _varna_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    varna_order = {'Brahmin': 4, 'Kshatriya': 3, 'Vaishya': 2, 'Shudra': 1}
    male_varna_map = {
        'Ashwini': 'Kshatriya', 'Bharani': 'Shudra', 'Krittika': 'Brahmin',
        'Rohini': 'Shudra', 'Mrigashira': 'Vaishya', 'Ardra': 'Shudra',
        'Punarvasu': 'Brahmin', 'Pushya': 'Kshatriya', 'Ashlesha': 'Shudra',
        'Magha': 'Shudra', 'Purva Phalguni': 'Brahmin', 'Uttara Phalguni': 'Kshatriya',
        'Hasta': 'Vaishya', 'Chitra': 'Shudra', 'Swati': 'Brahmin',
        'Vishakha': 'Shudra', 'Anuradha': 'Shudra', 'Jyeshtha': 'Kshatriya',
        'Mula': 'Vaishya', 'Purva Ashadha': 'Brahmin', 'Uttara Ashadha': 'Kshatriya',
        'Shravana': 'Shudra', 'Dhanishta': 'Shudra', 'Shatabhisha': 'Shudra',
        'Purva Bhadrapada': 'Brahmin', 'Uttara Bhadrapada': 'Kshatriya', 'Revati': 'Shudra',
    }
    m_varna = male_varna_map.get(male_nakshatra, 'Shudra')
    f_varna = male_varna_map.get(female_nakshatra, 'Shudra')
    m_score = varna_order.get(m_varna, 1)
    f_score = varna_order.get(f_varna, 1)
    score = 1 if m_score >= f_score else 0
    return {'name': 'Varna', 'score': score, 'maxScore': 1, 'male': m_varna, 'female': f_varna,
            'description': f'Male {m_varna} vs Female {f_varna} - {"compatible" if score else "not ideal"}'}


def _vashya_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    vashya_types = {
        'Ashwini': 'Chatushpada', 'Bharani': 'Chatushpada', 'Krittika': 'Chatushpada',
        'Rohini': 'Chatushpada', 'Mrigashira': 'Chatushpada', 'Ardra': 'Manav',
        'Punarvasu': 'Manav', 'Pushya': 'Jalachar', 'Ashlesha': 'Jalachar',
        'Magha': 'Chatushpada', 'Purva Phalguni': 'Chatushpada', 'Uttara Phalguni': 'Manav',
        'Hasta': 'Manav', 'Chitra': 'Manav', 'Swati': 'Manav',
        'Vishakha': 'Vanchar', 'Anuradha': 'Vanchar', 'Jyeshtha': 'Vanchar',
        'Mula': 'Chatushpada', 'Purva Ashadha': 'Manav', 'Uttara Ashadha': 'Manav',
        'Shravana': 'Manav', 'Dhanishta': 'Manav', 'Shatabhisha': 'Manav',
        'Purva Bhadrapada': 'Manav', 'Uttara Bhadrapada': 'Manav', 'Revati': 'Jalachar',
    }
    m_type = vashya_types.get(male_nakshatra, 'Manav')
    f_type = vashya_types.get(female_nakshatra, 'Manav')
    same_type = m_type == f_type
    score = 2 if same_type else (1 if 'Manav' in [m_type, f_type] else 0)
    return {'name': 'Vashya', 'score': score, 'maxScore': 2, 'male': m_type, 'female': f_type,
            'description': f'Male {m_type} vs Female {f_type} - {"mutual attraction" if score >= 1 else "less compatibility"}'}


def _tara_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    m_idx = NAKSHATRAS_ORDER.index(male_nakshatra) if male_nakshatra in NAKSHATRAS_ORDER else 0
    f_idx = NAKSHATRAS_ORDER.index(female_nakshatra) if female_nakshatra in NAKSHATRAS_ORDER else 0
    diff = (f_idx - m_idx) % 27 + 1
    remainder = diff % 9
    score = 3 if remainder in [1, 4, 6, 7] else (0 if remainder in [2, 5, 8] else 1)
    return {'name': 'Tara', 'score': score, 'maxScore': 3, 'difference': diff,
            'description': f'Tara difference {diff} (rem {remainder}) - {"very compatible" if score == 3 else "challenging" if score == 0 else "moderate"}'}


def _yoni_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    m_animal = YONI_ANIMALS.get(male_nakshatra, 'Unknown')
    f_animal = YONI_ANIMALS.get(female_nakshatra, 'Unknown')
    if m_animal == f_animal:
        score = 3
        nature = 'Same animal - excellent'
    else:
        pair = (m_animal, f_animal) if (m_animal, f_animal) in YONI_FRIENDSHIP else (f_animal, m_animal)
        friendship = YONI_FRIENDSHIP.get(pair, 1)
        score = 2 if friendship == 2 else (1 if friendship == 1 else 0)
        nature = 'Friendly' if score >= 2 else ('Neutral' if score == 1 else 'Enemy')
    return {'name': 'Yoni', 'score': score, 'maxScore': 4, 'maleAnimal': m_animal, 'femaleAnimal': f_animal,
            'nature': nature, 'description': f'Male {m_animal}, Female {f_animal} - {nature}'}


def _graha_maitri_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    from ..main import DASHA_SEQUENCE
    m_lord_idx = NAKSHATRAS_ORDER.index(male_nakshatra) % 9 if male_nakshatra in NAKSHATRAS_ORDER else 0
    f_lord_idx = NAKSHATRAS_ORDER.index(female_nakshatra) % 9 if female_nakshatra in NAKSHATRAS_ORDER else 0
    m_lord = DASHA_SEQUENCE[m_lord_idx % 9]
    f_lord = DASHA_SEQUENCE[f_lord_idx % 9]

    if m_lord == f_lord:
        friendship_score = 5
    elif f_lord in ['Sun', 'Moon']:
        friendship_score = 4
    else:
        friendship_score = 3
    return {'name': 'Graha Maitri', 'score': friendship_score, 'maxScore': 5, 'malePlanet': m_lord, 'femalePlanet': f_lord,
            'description': f'Male nakshatra lord {m_lord}, Female {f_lord} - {"excellent" if friendship_score >= 4 else "moderate"} compatibility'}


def _gana_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    m_gana = NAKSHATRA_GANA.get(male_nakshatra, 'Manushya')
    f_gana = NAKSHATRA_GANA.get(female_nakshatra, 'Manushya')
    score = GANA_COMPAT.get((m_gana, f_gana), 0)
    return {'name': 'Gana', 'score': score, 'maxScore': 6, 'male': m_gana, 'female': f_gana,
            'description': f'Male {m_gana}, Female {f_gana} - {"compatible" if score >= 4 else "challenging"}'}


def _bhakoot_score(male_sign_idx: int, female_sign_idx: int) -> Dict[str, Any]:
    diff = (female_sign_idx - male_sign_idx) % 12 + 1
    score = 7 if diff not in [2, 12, 1, 5, 6] else 0
    return {'name': 'Bhakoot', 'score': score, 'maxScore': 7, 'signDifference': diff,
            'description': f'Sign difference {diff} - {"compatible" if score else "Dosha present - needs remedies"}'}


def _nadi_score(male_nakshatra: str, female_nakshatra: str) -> Dict[str, Any]:
    m_nadi = NAKSHATRA_NADI.get(male_nakshatra, 'Aadi')
    f_nadi = NAKSHATRA_NADI.get(female_nakshatra, 'Aadi')
    score = 0 if m_nadi == f_nadi else 8
    return {'name': 'Nadi', 'score': score, 'maxScore': 8, 'male': m_nadi, 'female': f_nadi,
            'description': f'Male {m_nadi}, Female {f_nadi} - {"Nadi Dosha - health concerns for offspring" if score == 0 else "No Nadi Dosha - excellent"}'}


def _full_guna_milan(body: CompatRequest) -> Dict[str, Any]:
    male_moon, female_moon, male_asc, female_asc, ZODIAC_SIGNS = _compute_moon_positions(body)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    male_moon_sign_idx = ZODIAC_SIGNS.index(male_moon['sign'])
    female_moon_sign_idx = ZODIAC_SIGNS.index(female_moon['sign'])

    varna = _varna_score(male_nakshatra, female_nakshatra)
    vashya = _vashya_score(male_nakshatra, female_nakshatra)
    tara = _tara_score(male_nakshatra, female_nakshatra)
    yoni = _yoni_score(male_nakshatra, female_nakshatra)
    graha_maitri = _graha_maitri_score(male_nakshatra, female_nakshatra)
    gana = _gana_score(male_nakshatra, female_nakshatra)
    bhakoot = _bhakoot_score(male_moon_sign_idx, female_moon_sign_idx)
    nadi = _nadi_score(male_nakshatra, female_nakshatra)

    gunas = [varna, vashya, tara, yoni, graha_maitri, gana, bhakoot, nadi]
    total_score = sum(g['score'] for g in gunas)

    if total_score >= 30:
        verdict = 'Excellent Match'
        verdict_detail = 'Highly compatible match with strong mutual understanding.'
    elif total_score >= 25:
        verdict = 'Very Good Match'
        verdict_detail = 'Strong compatibility with minor areas for adjustment.'
    elif total_score >= 18:
        verdict = 'Good Match'
        verdict_detail = 'Moderate compatibility. Some compromise needed.'
    elif total_score >= 12:
        verdict = 'Average Match'
        verdict_detail = 'Below average compatibility. Significant adjustments needed.'
    else:
        verdict = 'Not Recommended'
        verdict_detail = 'Low compatibility score. Strong remedies required.'

    return {
        'status': 200,
        'summary': {
            'totalScore': total_score,
            'maxScore': 36,
            'percentage': round(total_score / 36 * 100, 1),
            'verdict': verdict,
            'verdictDetail': verdict_detail,
        },
        'maleProfile': {
            'moonSign': male_moon['sign'],
            'moonNakshatra': male_nakshatra,
            'moonNakshatraPada': male_moon['nakshatraPada'],
            'ascendant': male_asc['sign'],
        },
        'femaleProfile': {
            'moonSign': female_moon['sign'],
            'moonNakshatra': female_nakshatra,
            'moonNakshatraPada': female_moon['nakshatraPada'],
            'ascendant': female_asc['sign'],
        },
        'ashtakootaGunas': gunas,
    }


@router.post('/compat/gun-milan')
def gun_milan(body: CompatRequest) -> Dict[str, Any]:
    return _full_guna_milan(body)


@router.post('/compat/nadi')
def nadi_only(body: CompatRequest) -> Dict[str, Any]:
    male_moon, female_moon, _, _, _ = _compute_moon_positions(body)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    result = _nadi_score(male_nakshatra, female_nakshatra)

    return {
        'status': 200,
        'maleProfile': {'moonNakshatra': male_nakshatra, 'moonSign': male_moon['sign']},
        'femaleProfile': {'moonNakshatra': female_nakshatra, 'moonSign': female_moon['sign']},
        'nadi': result,
    }


@router.post('/compat/bhakoot')
def bhakoot_only(body: CompatRequest) -> Dict[str, Any]:
    male_moon, female_moon, _, _, ZODIAC_SIGNS = _compute_moon_positions(body)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_moon_sign_idx = ZODIAC_SIGNS.index(male_moon['sign'])
    female_moon_sign_idx = ZODIAC_SIGNS.index(female_moon['sign'])
    result = _bhakoot_score(male_moon_sign_idx, female_moon_sign_idx)

    return {
        'status': 200,
        'maleProfile': {'moonSign': male_moon['sign']},
        'femaleProfile': {'moonSign': female_moon['sign']},
        'bhakoot': result,
    }


@router.post('/compat/yoni')
def yoni_only(body: CompatRequest) -> Dict[str, Any]:
    male_moon, female_moon, _, _, _ = _compute_moon_positions(body)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    result = _yoni_score(male_nakshatra, female_nakshatra)

    return {
        'status': 200,
        'maleProfile': {'moonNakshatra': male_nakshatra, 'moonSign': male_moon['sign']},
        'femaleProfile': {'moonNakshatra': female_nakshatra, 'moonSign': female_moon['sign']},
        'yoni': result,
    }


@router.post('/compat/gana')
def gana_only(body: CompatRequest) -> Dict[str, Any]:
    male_moon, female_moon, _, _, _ = _compute_moon_positions(body)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    result = _gana_score(male_nakshatra, female_nakshatra)

    return {
        'status': 200,
        'maleProfile': {'moonNakshatra': male_nakshatra, 'moonSign': male_moon['sign']},
        'femaleProfile': {'moonNakshatra': female_nakshatra, 'moonSign': female_moon['sign']},
        'gana': result,
    }


@router.post('/compat/tara')
def tara_only(body: CompatRequest) -> Dict[str, Any]:
    male_moon, female_moon, _, _, _ = _compute_moon_positions(body)

    if not male_moon or not female_moon:
        return {'status': 400, 'error': 'Could not compute Moon positions'}

    male_nakshatra = male_moon['nakshatra']
    female_nakshatra = female_moon['nakshatra']
    result = _tara_score(male_nakshatra, female_nakshatra)

    return {
        'status': 200,
        'maleProfile': {'moonNakshatra': male_nakshatra, 'moonSign': male_moon['sign']},
        'femaleProfile': {'moonNakshatra': female_nakshatra, 'moonSign': female_moon['sign']},
        'tara': result,
    }
