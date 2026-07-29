from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional


router = APIRouter()


class BirthDetailRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


class WeightRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    bodyWeightKg: Optional[float] = Field(None, example=70)
    planet: Optional[str] = Field(None, example="Sun")


class ByPlanetRequest(BaseModel):
    planet: str = Field(..., example="Sun")
    bodyWeightKg: Optional[float] = Field(None, example=70)


GEMSTONE_DATA = {
    'Sun': {
        'name': 'Ruby',
        'hindiName': 'Manikya',
        'imageUrl': '/images/gemstones/ruby.webp',
        'finger': 'Ring Finger',
        'metal': 'Gold',
        'day': 'Sunday',
        'weightRange': '3-5 carats',
        'mantra': 'Om Hram Hreem Hraum Suryaya Namaha',
        'color': 'Red / Pinkish Red',
        'origin': 'Burma, India, Sri Lanka',
        'quality': 'Transparent, deep red with fluorescence',
        'dos': [
            'Wear on ring finger of right hand',
            'Worship Sun god before wearing',
            'Donate wheat on Sundays',
            'Recite Aditya Hridayam',
            'Wake up before sunrise and face east'
        ],
        'donts': [
            'Do not wear alongside Blue Sapphire or Hessonite',
            'Avoid wearing during Sun Antardasha if Sun is afflicted',
            'Do not wear if Sun is debilitated in the chart',
            'Avoid wearing on cloudy/inauspicious days',
            'Do not consume alcohol on Sundays'
        ]
    },
    'Moon': {
        'name': 'Pearl',
        'hindiName': 'Moti',
        'imageUrl': '/images/gemstones/pearl.webp',
        'finger': 'Little Finger',
        'metal': 'Silver',
        'day': 'Monday',
        'weightRange': '2-4 carats',
        'mantra': 'Om Shram Shreem Shraum Chandraya Namaha',
        'color': 'White / Cream',
        'origin': 'Persian Gulf, Australia, India',
        'quality': 'Smooth, lustrous, blemish-free',
        'dos': [
            'Wear on little finger of right hand',
            'Worship Lord Shiva or Moon',
            'Donate rice on Mondays',
            'Chant Om Namah Shivaya',
            'Maintain mental calm and emotional balance'
        ],
        'donts': [
            'Do not wear alongside Ruby or Red Coral',
            'Avoid wearing during Moon Antardasha if Moon is afflicted',
            'Do not wear if Moon is debilitated',
            'Avoid wearing on inauspicious tithis',
            'Do not consume non-vegetarian food on Mondays'
        ]
    },
    'Mars': {
        'name': 'Red Coral',
        'hindiName': 'Moonga',
        'imageUrl': '/images/gemstones/red-coral.webp',
        'finger': 'Ring Finger',
        'metal': 'Gold',
        'day': 'Tuesday',
        'weightRange': '3-6 carats',
        'mantra': 'Om Hram Hreem Hraum Mangalaya Namaha',
        'color': 'Red / Orange Red',
        'origin': 'Italy, Japan, Himalayas',
        'quality': 'Deep red, uniform color, no cracks',
        'dos': [
            'Wear on ring finger of right hand',
            'Worship Lord Hanuman',
            'Donate red lentils on Tuesdays',
            'Chant Hanuman Chalisa',
            'Practice physical exercise regularly'
        ],
        'donts': [
            'Do not wear alongside Pearl or Emerald',
            'Avoid wearing during Mars Antardasha if Mars is afflicted',
            'Do not wear if Mars is debilitated in the chart',
            'Avoid wearing if you have Mangal Dosha without remedy',
            'Do not engage in violent activities while wearing'
        ]
    },
    'Mercury': {
        'name': 'Emerald',
        'hindiName': 'Panna',
        'imageUrl': '/images/gemstones/emerald.webp',
        'finger': 'Little Finger',
        'metal': 'Gold',
        'day': 'Wednesday',
        'weightRange': '1-3 carats',
        'mantra': 'Om Bram Breem Braum Budhaya Namaha',
        'color': 'Green',
        'origin': 'Colombia, Zambia, Brazil',
        'quality': 'Vivid green, transparent, no inclusions',
        'dos': [
            'Wear on little finger of right hand',
            'Worship Lord Vishnu',
            'Donate green items on Wednesdays',
            'Chant Vishnu Sahasranama',
            'Engage in intellectual and business pursuits'
        ],
        'donts': [
            'Do not wear alongside Yellow Sapphire',
            'Avoid wearing during Mercury Antardasha if Mercury is afflicted',
            'Do not wear if Mercury is debilitated',
            'Avoid wearing if Budh is conjunct with malefics',
            'Do not eat non-vegetarian food on Wednesdays'
        ]
    },
    'Jupiter': {
        'name': 'Yellow Sapphire',
        'hindiName': 'Pukhraj',
        'imageUrl': '/images/gemstones/yellow-sapphire.webp',
        'finger': 'Index Finger',
        'metal': 'Gold',
        'day': 'Thursday',
        'weightRange': '2-5 carats',
        'mantra': 'Om Jram Jreem Jraum Gurave Namaha',
        'color': 'Yellow',
        'origin': 'Sri Lanka, Brazil, Africa',
        'quality': 'Bright yellow, transparent, unheated',
        'dos': [
            'Wear on index finger of right hand',
            'Worship Lord Vishnu or Guru',
            'Donate yellow items on Thursdays',
            'Chant Guru Beej Mantra',
            'Practice charity and wisdom'
        ],
        'donts': [
            'Do not wear alongside Emerald or Blue Sapphire',
            'Avoid wearing during Jupiter Antardasha if Jupiter is afflicted',
            'Do not wear if Jupiter is debilitated',
            'Avoid wearing if Guru is conjunct with Rahu',
            'Do not consume alcohol on Thursdays'
        ]
    },
    'Venus': {
        'name': 'Diamond',
        'hindiName': 'Heera',
        'imageUrl': '/images/gemstones/diamond.webp',
        'finger': 'Middle Finger',
        'metal': 'Silver / Platinum',
        'day': 'Friday',
        'weightRange': '1-3 carats',
        'mantra': 'Om Dram Dreem Draum Shukraya Namaha',
        'color': 'White / Colorless',
        'origin': 'South Africa, Russia, Belgium',
        'quality': 'Excellent cut, high clarity, colorless',
        'dos': [
            'Wear on middle finger of right hand',
            'Worship Goddess Lakshmi',
            'Donate white items on Fridays',
            'Chant Lakshmi Mantra',
            'Appreciate art, beauty, and luxury'
        ],
        'donts': [
            'Do not wear alongside Red Coral or Cat\'s Eye',
            'Avoid wearing during Venus Antardasha if Venus is afflicted',
            'Do not wear if Venus is debilitated',
            'Avoid wearing if Shukra is combust',
            'Do not engage in excessive indulgence while wearing'
        ]
    },
    'Saturn': {
        'name': 'Blue Sapphire',
        'hindiName': 'Neelam',
        'imageUrl': '/images/gemstones/blue-sapphire.webp',
        'finger': 'Middle Finger',
        'metal': 'Silver / Steel',
        'day': 'Saturday',
        'weightRange': '3-6 carats',
        'mantra': 'Om Shram Shreem Shraum Shanaye Namaha',
        'color': 'Blue',
        'origin': 'Sri Lanka, Kashmir, Burma',
        'quality': 'Velvety blue, transparent, unheated',
        'dos': [
            'Wear on middle finger of right hand',
            'Worship Lord Shani or Lord Shiva',
            'Donate iron/black items on Saturdays',
            'Chant Shani Mantra or Nilamani mantra',
            'Practice discipline and hard work'
        ],
        'donts': [
            'Do not wear alongside Diamond or Hessonite',
            'Avoid wearing during Saturn Antardasha if Saturn is afflicted',
            'NEVER wear if Saturn is debilitated or in enemy sign',
            'Always test before wearing permanently (keep under pillow for 3 days)',
            'Do not consume alcohol or non-veg on Saturdays'
        ]
    },
    'Rahu': {
        'name': 'Hessonite',
        'hindiName': 'Gomed',
        'imageUrl': '/images/gemstones/hessonite.webp',
        'finger': 'Middle Finger',
        'metal': 'Silver / Steel',
        'day': 'Saturday',
        'weightRange': '4-7 carats',
        'mantra': 'Om Ram Rahave Namaha',
        'color': 'Honey / Brownish Red',
        'origin': 'Sri Lanka, India, Thailand',
        'quality': 'Honey colored, transparent, free from black spots',
        'dos': [
            'Wear on middle finger of right hand',
            'Worship Lord Ganesha',
            'Donate blue/black items on Saturdays',
            'Chant Om Gam Ganapataye Namaha',
            'Practice spiritual disciplines'
        ],
        'donts': [
            'Do not wear alongside Blue Sapphire or Cat\'s Eye',
            'Avoid wearing during Rahu Antardasha if Rahu is afflicted',
            'Do not wear if Rahu is in a malefic position',
            'Avoid wearing during Rahu-Ketu transit periods',
            'Do not consume intoxicants while wearing'
        ]
    },
    'Ketu': {
        'name': 'Cat\'s Eye',
        'hindiName': 'Lehsunia',
        'imageUrl': '/images/gemstones/cats-eye.webp',
        'finger': 'Middle Finger',
        'metal': 'Silver',
        'day': 'Tuesday',
        'weightRange': '2-4 carats',
        'mantra': 'Om Kem Ketave Namaha',
        'color': 'Milky Green / Grey',
        'origin': 'Sri Lanka, India, Brazil',
        'quality': 'Sharp chatoyancy, milk-green, no black spots',
        'dos': [
            'Wear on middle finger of right hand',
            'Worship Lord Ganesha or Lord Kartikeya',
            'Donate brown/grey items on Tuesdays',
            'Chant Ketu Beej Mantra',
            'Practice meditation and spiritual sadhana'
        ],
        'donts': [
            'Do not wear alongside Diamond or Yellow Sapphire',
            'Avoid wearing during Ketu Antardasha if Ketu is afflicted',
            'Do not wear if Ketu is conjunct with malefics',
            'Avoid wearing during eclipse periods',
            'Do not engage in materialistic pursuits while wearing'
        ]
    }
}

PLANET_NAMES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

WEIGHT_RATTI_FACTOR = 10.67


def _get_ascendant_lord(planets, houses):
    asc_sign = houses.get('ascendant', {}).get('sign') if houses else None
    if not asc_sign:
        return None
    from ..main import SIGN_LORDS
    return SIGN_LORDS.get(asc_sign)


def _get_current_dasha_lord(timezone):
    try:
        import pytz
        from datetime import datetime
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now
    except Exception:
        return None


def _calc_birth_chart(date_of_birth, time_of_birth, latitude, longitude, timezone):
    from ..main import to_julian, calc_planets, calc_houses, vimshottari_full, parse_local_datetime
    jd = to_julian(date_of_birth, time_of_birth, timezone)
    planets = calc_planets(jd, None, 'mean')
    houses = calc_houses(jd, latitude, longitude, planets, 'W')
    birth_local = parse_local_datetime(date_of_birth, time_of_birth, timezone)
    dasha = vimshottari_full(jd, birth_local)
    return planets, houses, dasha


def _get_gemstone_info(planet_name, body_weight_kg=None):
    info = GEMSTONE_DATA.get(planet_name)
    if not info:
        return None
    result = dict(info)
    if body_weight_kg and body_weight_kg > 0:
        weight_ratti = round(body_weight_kg / WEIGHT_RATTI_FACTOR, 2)
        weight_ratti = max(1.0, min(weight_ratti, 15.0))
        parts = result['weightRange'].split('-')
        min_w = float(parts[0].replace(' carats', ''))
        max_w = float(parts[1].replace(' carats', ''))
        suggested_carat = round(weight_ratti * 0.8, 2)
        suggested_carat = max(min_w, min(suggested_carat, max_w))
        result['recommendedWeightRatti'] = weight_ratti
        result['recommendedWeightCarat'] = suggested_carat
    return result


def _build_response(planet, gemstone_info, wearing_info=None):
    if not gemstone_info:
        return {'status': 404, 'error': f'No gemstone data found for planet: {planet}'}
    resp = {
        'status': 200,
        'planet': planet,
        'gemstone': {
            'name': gemstone_info['name'],
            'hindiName': gemstone_info['hindiName'],
            'imageUrl': gemstone_info.get('imageUrl', ''),
            'color': gemstone_info.get('color', ''),
            'origin': gemstone_info.get('origin', ''),
            'quality': gemstone_info.get('quality', ''),
        },
        'wearing': wearing_info or {
            'finger': gemstone_info['finger'],
            'metal': gemstone_info['metal'],
            'day': gemstone_info['day'],
            'weightRange': gemstone_info['weightRange'],
            'mantra': gemstone_info['mantra'],
            'dos': gemstone_info['dos'],
            'donts': gemstone_info['donts'],
        }
    }
    if 'recommendedWeightRatti' in gemstone_info:
        resp['wearing']['recommendedWeightRatti'] = gemstone_info['recommendedWeightRatti']
        resp['wearing']['recommendedWeightCarat'] = gemstone_info['recommendedWeightCarat']
    return resp


@router.post('/gemstone/recommendation')
def gemstone_recommendation(body: BirthDetailRequest):
    planets, houses, dasha = _calc_birth_chart(
        body.dateOfBirth, body.timeOfBirth, body.latitude, body.longitude, body.timezone
    )
    asc_lord = _get_ascendant_lord(planets, houses)
    current_md_lord = None
    try:
        import pytz
        from datetime import datetime
        tz = pytz.timezone(body.timezone)
        today = datetime.now(tz).date().isoformat()
        for md in dasha.get('mahadashas', []):
            if md['startDate'] <= today < md['endDate']:
                current_md_lord = md['planet']
                break
    except Exception:
        current_md_lord = None

    primary_planet = current_md_lord or asc_lord or 'Sun'
    gemstone_info = _get_gemstone_info(primary_planet)
    reason = []
    if current_md_lord:
        reason.append(f'Current Mahadasha Lord ({current_md_lord})')
    if asc_lord:
        reason.append(f'Ascendant Lord ({asc_lord})')

    resp = _build_response(primary_planet, gemstone_info)
    resp['recommendationReason'] = ' + '.join(reason) if reason else 'Default recommendation'
    resp['ascendantLord'] = asc_lord
    resp['currentDashaLord'] = current_md_lord
    if asc_lord and current_md_lord and asc_lord != current_md_lord:
        alt_gemstone = _get_gemstone_info(asc_lord)
        if alt_gemstone:
            resp['alternateGemstone'] = {
                'planet': asc_lord,
                'name': alt_gemstone['name'],
                'hindiName': alt_gemstone['hindiName'],
                'reason': f'Ascendant Lord ({asc_lord})'
            }
    return resp


@router.post('/gemstone/by-planet')
def gemstone_by_planet(body: ByPlanetRequest):
    planet = body.planet.strip().title()
    if planet not in PLANET_NAMES:
        return {'status': 400, 'error': f'Invalid planet: {body.planet}. Valid planets: {", ".join(PLANET_NAMES)}'}
    gemstone_info = _get_gemstone_info(planet, body.bodyWeightKg)
    return _build_response(planet, gemstone_info)


@router.post('/gemstone/by-lagna')
def gemstone_by_lagna(body: BirthDetailRequest):
    planets, houses, _ = _calc_birth_chart(
        body.dateOfBirth, body.timeOfBirth, body.latitude, body.longitude, body.timezone
    )
    asc_lord = _get_ascendant_lord(planets, houses)
    if not asc_lord:
        return {'status': 404, 'error': 'Could not determine ascendant lord'}
    gemstone_info = _get_gemstone_info(asc_lord)
    resp = _build_response(asc_lord, gemstone_info)
    resp['lagnaSign'] = houses.get('ascendant', {}).get('sign', 'Unknown')
    resp['lagnaLord'] = asc_lord
    return resp


@router.post('/gemstone/by-dasha')
def gemstone_by_dasha(body: BirthDetailRequest):
    from ..main import to_julian, calc_planets, calc_houses, vimshottari_full, parse_local_datetime
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    dasha = vimshottari_full(jd, birth_local)
    import pytz
    from datetime import datetime
    tz = pytz.timezone(body.timezone)
    today = datetime.now(tz).date().isoformat()
    current_md_lord = None
    current_ad_lord = None
    for md in dasha.get('mahadashas', []):
        if md['startDate'] <= today < md['endDate']:
            current_md_lord = md['planet']
            for ad in md.get('antardasha', []):
                if ad['startDate'] <= today < ad['endDate']:
                    current_ad_lord = ad['planet']
                    break
            break
    if not current_md_lord:
        return {'status': 404, 'error': 'Could not determine current dasha'}
    gemstone_info = _get_gemstone_info(current_md_lord)
    resp = _build_response(current_md_lord, gemstone_info)
    resp['currentDasha'] = {
        'mahadasha': current_md_lord,
        'antardasha': current_ad_lord
    }
    if current_ad_lord and current_ad_lord != current_md_lord:
        ad_gemstone = _get_gemstone_info(current_ad_lord)
        if ad_gemstone:
            resp['antardashaGemstone'] = {
                'planet': current_ad_lord,
                'name': ad_gemstone['name'],
                'hindiName': ad_gemstone['hindiName']
            }
    return resp


@router.post('/gemstone/wearing')
def gemstone_wearing(body: BirthDetailRequest):
    planets, houses, dasha = _calc_birth_chart(
        body.dateOfBirth, body.timeOfBirth, body.latitude, body.longitude, body.timezone
    )
    asc_lord = _get_ascendant_lord(planets, houses)
    current_md_lord = None
    try:
        import pytz
        from datetime import datetime
        tz = pytz.timezone(body.timezone)
        today = datetime.now(tz).date().isoformat()
        for md in dasha.get('mahadashas', []):
            if md['startDate'] <= today < md['endDate']:
                current_md_lord = md['planet']
                break
    except Exception:
        current_md_lord = None

    primary_planet = current_md_lord or asc_lord or 'Sun'
    gemstone_info = _get_gemstone_info(primary_planet)
    if not gemstone_info:
        return {'status': 404, 'error': f'No wearing instructions found for planet: {primary_planet}'}

    wearing = {
        'finger': gemstone_info['finger'],
        'metal': gemstone_info['metal'],
        'day': gemstone_info['day'],
        'weightRange': gemstone_info['weightRange'],
        'mantra': gemstone_info['mantra'],
        'ringFingerNumber': {
            'Ring Finger': 4,
            'Little Finger': 5,
            'Index Finger': 2,
            'Middle Finger': 3
        }.get(gemstone_info['finger'], 4),
        'auspiciousTime': f"Early morning during {gemstone_info['day']} Hora",
        'instructions': [
            f"Wear on {gemstone_info['finger']} of the right hand",
            f"Best day to wear: {gemstone_info['day']}",
            f"Metal to be used: {gemstone_info['metal']}",
            f"Weight range: {gemstone_info['weightRange']}",
            f"Chant the mantra {gemstone_info['mantra']} 108 times before wearing",
            "Take a bath and wear clean clothes before wearing",
            "Face the direction associated with the planet",
            "Light a lamp and offer flowers before wearing"
        ],
        'dos': gemstone_info['dos'],
        'donts': gemstone_info['donts']
    }
    return _build_response(primary_planet, gemstone_info, wearing)


@router.post('/gemstone/weight')
def gemstone_weight(body: WeightRequest):
    planet = body.planet
    if not planet:
        planets, houses, _ = _calc_birth_chart(
            body.dateOfBirth, body.timeOfBirth, body.latitude, body.longitude, body.timezone
        )
        asc_lord = _get_ascendant_lord(planets, houses)
        planet = asc_lord or 'Sun'
    planet = planet.strip().title()
    if planet not in PLANET_NAMES:
        return {'status': 400, 'error': f'Invalid planet: {planet}. Valid planets: {", ".join(PLANET_NAMES)}'}

    gemstone_info = _get_gemstone_info(planet, body.bodyWeightKg)
    if not gemstone_info:
        return {'status': 404, 'error': f'No gemstone data found for planet: {planet}'}

    parts = gemstone_info['weightRange'].split('-')
    min_w = float(parts[0].replace(' carats', ''))
    max_w = float(parts[1].replace(' carats', ''))

    result = {
        'status': 200,
        'planet': planet,
        'gemstoneName': gemstone_info['name'],
        'standardWeightRange': gemstone_info['weightRange'],
        'minWeightCarat': min_w,
        'maxWeightCarat': max_w,
    }

    if body.bodyWeightKg and body.bodyWeightKg > 0:
        weight_ratti = round(body.bodyWeightKg / WEIGHT_RATTI_FACTOR, 2)
        weight_ratti = max(1.0, min(weight_ratti, 15.0))
        suggested_carat = round(weight_ratti * 0.8, 2)
        suggested_carat = max(min_w, min(suggested_carat, max_w))
        result['bodyWeightKg'] = body.bodyWeightKg
        result['weightInRatti'] = weight_ratti
        result['suggestedCarat'] = suggested_carat
        result['note'] = f'For body weight {body.bodyWeightKg}kg, recommended weight is ~{weight_ratti} ratti ({suggested_carat} carats). Always consult an astrologer before wearing.'
    else:
        result['note'] = 'Provide bodyWeightKg for personalized weight recommendation. Standard weight range is shown above.'

    return result


@router.post('/gemstone/metal')
def gemstone_metal(body: ByPlanetRequest):
    planet = body.planet.strip().title()
    if planet not in PLANET_NAMES:
        return {'status': 400, 'error': f'Invalid planet: {planet}. Valid planets: {", ".join(PLANET_NAMES)}'}
    gemstone_info = _get_gemstone_info(planet)
    if not gemstone_info:
        return {'status': 404, 'error': f'No gemstone data found for planet: {planet}'}

    metal_notes = {
        'Sun': 'Gold is the metal of the Sun. It enhances the solar energies of vitality, authority, and confidence.',
        'Moon': 'Silver is the metal of the Moon. It enhances emotional calmness, intuition, and mental peace.',
        'Mars': 'Gold is the metal of Mars. It amplifies courage, energy, and competitive spirit.',
        'Mercury': 'Gold is the metal of Mercury. It enhances communication, business acumen, and intelligence.',
        'Jupiter': 'Gold is the metal of Jupiter. It amplifies wisdom, prosperity, and spiritual growth.',
        'Venus': 'Silver or Platinum are metals of Venus. They enhance beauty, luxury, love, and artistic expression.',
        'Saturn': 'Silver or Steel are metals of Saturn. They help channel discipline, patience, and karmic lessons.',
        'Rahu': 'Silver or Steel are metals of Rahu. They help manage unconventional and karmic energies of Rahu.',
        'Ketu': 'Silver is the metal of Ketu. It enhances spiritual detachment, intuition, and liberation.'
    }

    return {
        'status': 200,
        'planet': planet,
        'gemstoneName': gemstone_info['name'],
        'recommendedMetal': gemstone_info['metal'],
        'metalNote': metal_notes.get(planet, ''),
        'alternativeMetals': _get_alternative_metals(planet)
    }


def _get_alternative_metals(planet):
    alternatives = {
        'Sun': ['Silver (if Gold is not affordable)'],
        'Moon': ['Platinum (for extra strength)'],
        'Mars': ['Silver (as alternative to Gold)'],
        'Mercury': ['Silver (as alternative to Gold)'],
        'Jupiter': ['Silver (as alternative to Gold)'],
        'Venus': ['White Gold'],
        'Saturn': ['Iron (traditional metal of Saturn)'],
        'Rahu': ['Iron (as alternative)'],
        'Ketu': ['Panchdhatu (five-metal alloy)']
    }
    return alternatives.get(planet, [])


@router.post('/gemstone/finger')
def gemstone_finger(body: ByPlanetRequest):
    planet = body.planet.strip().title()
    if planet not in PLANET_NAMES:
        return {'status': 400, 'error': f'Invalid planet: {planet}. Valid planets: {", ".join(PLANET_NAMES)}'}
    gemstone_info = _get_gemstone_info(planet)
    if not gemstone_info:
        return {'status': 404, 'error': f'No gemstone data found for planet: {planet}'}

    finger_map = {
        'Ring Finger': {
            'number': 4,
            'name': 'Anamika',
            'deity': 'Sun / Agni',
            'nerves': 'Connected to the heart via the ring finger nerve channel',
            'description': 'The ring finger is associated with the Sun and fire element. It governs creativity, vitality, and self-expression.'
        },
        'Little Finger': {
            'number': 5,
            'name': 'Kanishtha / Pinky',
            'deity': 'Mercury / Moon',
            'nerves': 'Connected to the brain via the smallest finger nerve',
            'description': 'The little finger is associated with Mercury and communication. It governs intelligence, business, and speech.'
        },
        'Index Finger': {
            'number': 2,
            'name': 'Tarjani',
            'deity': 'Jupiter',
            'nerves': 'Connected to the brain via the index finger nerve',
            'description': 'The index finger is associated with Jupiter and the ether element. It governs wisdom, ambition, and leadership.'
        },
        'Middle Finger': {
            'number': 3,
            'name': 'Madhyama',
            'deity': 'Saturn',
            'nerves': 'Connected to the brain via the middle finger nerve',
            'description': 'The middle finger is associated with Saturn and the air element. It governs discipline, responsibility, and patience.'
        }
    }

    finger_name = gemstone_info['finger']
    finger_detail = finger_map.get(finger_name, {})

    return {
        'status': 200,
        'planet': planet,
        'gemstoneName': gemstone_info['name'],
        'recommendedFinger': finger_name,
        'fingerNumber': finger_detail.get('number', 4),
        'fingerDeity': finger_detail.get('deity', ''),
        'fingerNerves': finger_detail.get('nerves', ''),
        'fingerDescription': finger_detail.get('description', ''),
        'hand': 'Right hand (for natives)',
        'note': 'Always wear on the right hand for males and left hand for females unless prescribed otherwise by an astrologer.'
    }
