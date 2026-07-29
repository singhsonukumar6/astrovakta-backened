from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ..response import success

router = APIRouter()


class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


LAL_KITAB_HOUSE_SIGNIFICATIONS = {
    1: {
        'name': 'Body & Personality',
        'description': 'Physical appearance, health, nature, honor, and general well-being',
        'elements': ['Head', 'Soul', 'Character', 'Happiness', 'Honor'],
        'remedies': ['Respect parents', 'Keep your promises', 'Avoid ego conflicts']
    },
    2: {
        'name': 'Wealth & Family',
        'description': 'Financial status, family, speech, eyesight, and charitable nature',
        'elements': ['Money', 'Family', 'Speech', 'Right Eye', 'Charity'],
        'remedies': ['Donate food', 'Help the needy', 'Speak truthfully']
    },
    3: {
        'name': 'Courage & Siblings',
        'description': 'Courage, brothers, sisters, short journeys, and communication',
        'elements': ['Courage', 'Siblings', 'Right Ear', 'Hands', 'Writing'],
        'remedies': ['Honor siblings', 'Be courageous', 'Avoid gambling']
    },
    4: {
        'name': 'Home & Comfort',
        'description': 'Mother, home, vehicles, property, education, and domestic happiness',
        'elements': ['Mother', 'Vehicles', 'Real Estate', 'Heart', 'Domestic Peace'],
        'remedies': ['Serve your mother', 'Maintain home harmony', 'Respect teachers']
    },
    5: {
        'name': 'Children & Intelligence',
        'description': 'Children, intelligence, creativity, romance, and speculative gains',
        'elements': ['Children', 'Wisdom', 'Fame', 'Stomach', 'Mantra'],
        'remedies': ['Educate children well', 'Chant mantras', 'Avoid speculation']
    },
    6: {
        'name': 'Health & Debts',
        'description': 'Health, debts, enemies, daily work, service, and litigation',
        'elements': ['Debts', 'Diseases', 'Enemies', 'Service', 'Legal Matters'],
        'remedies': ['Serve humanity', 'Pay debts on time', 'Practice forgiveness']
    },
    7: {
        'name': 'Marriage & Partnerships',
        'description': 'Spouse, business partners, marriage, public relations, and contracts',
        'elements': ['Spouse', 'Partnership', 'Marriage', 'Trade', 'Public Image'],
        'remedies': ['Respect your spouse', 'Maintain partnerships', 'Avoid adultery']
    },
    8: {
        'name': 'Longevity & Obstacles',
        'description': 'Longevity, obstacles, inheritance, chronic illnesses, and transformation',
        'elements': ['Life Span', 'Obstacles', 'Inheritance', 'Chronic Disease', 'Occult'],
        'remedies': ['Practice spirituality', 'Help the helpless', 'Avoid harmful habits']
    },
    9: {
        'name': 'Fortune & Religion',
        'description': 'Luck, religion, guru, father, pilgrimage, and higher knowledge',
        'elements': ['Fortune', 'Faith', 'Guru', 'Father', 'Pilgrimage'],
        'remedies': ['Honor your father', 'Respect gurus', 'Practice charity']
    },
    10: {
        'name': 'Career & Status',
        'description': 'Profession, social status, authority, honor from government',
        'elements': ['Career', 'Status', 'Authority', 'Right Leg', 'Government'],
        'remedies': ['Work with integrity', 'Fulfill responsibilities', 'Be punctual']
    },
    11: {
        'name': 'Gains & Aspirations',
        'description': 'Income, gains, fulfillment of desires, friendships, and elder siblings',
        'elements': ['Gains', 'Desires', 'Friends', 'Left Ear', 'Social Circle'],
        'remedies': ['Cultivate good friendships', 'Be generous', 'Avoid greed']
    },
    12: {
        'name': 'Expenses & Liberation',
        'description': 'Expenditure, foreign travel, spirituality, liberation, and left eye',
        'elements': ['Losses', 'Foreign Travel', 'Spirituality', 'Left Eye', 'Liberation'],
        'remedies': ['Practice charity', 'Meditate regularly', 'Detach from materialism']
    },
}

LAL_KITAB_PLANET_INTERPRETATIONS = {
    'Sun': {
        'nature': 'Royal, authoritative, soul',
        'positive': 'Leadership, confidence, vitality, government favor',
        'negative': 'Ego, dominance, health issues, conflicts with authority',
        'remedies': 'Offer water to Sun daily, donate wheat on Sundays'
    },
    'Moon': {
        'nature': 'Mind, emotions, mother',
        'positive': 'Emotional intelligence, intuition, popularity, mental peace',
        'negative': 'Mood swings, anxiety, emotional instability, mother issues',
        'remedies': 'Offer milk on Mondays, wear pearl, observe Monday fast'
    },
    'Mars': {
        'nature': 'Energy, courage, property',
        'positive': 'Bravery, strength, property gains, technical skills',
        'negative': 'Anger, accidents, debts, conflicts, blood-related issues',
        'remedies': 'Chant Hanuman Chalisa, donate red lentils on Tuesdays'
    },
    'Mercury': {
        'nature': 'Intellect, speech, business',
        'positive': 'Intelligence, communication skills, business acumen, wit',
        'negative': 'Nervousness, speech defects, deceit, financial losses',
        'remedies': 'Feed green vegetables to cows, donate green items on Wednesdays'
    },
    'Jupiter': {
        'nature': 'Wisdom, wealth, children',
        'positive': 'Wisdom, knowledge, wealth, children, spiritual growth',
        'negative': 'Overconfidence, laziness, financial extravagance, child delays',
        'remedies': 'Feed Brahmins, donate yellow items on Thursdays, chant Guru mantra'
    },
    'Venus': {
        'nature': 'Love, luxury, arts',
        'positive': 'Romance, artistic talent, luxury, marital happiness, vehicles',
        'negative': 'Overindulgence, relationship issues, kidney problems, vanity',
        'remedies': 'Donate white items on Fridays, respect women, practice moderation'
    },
    'Saturn': {
        'nature': 'Karma, discipline, service',
        'positive': 'Discipline, longevity, wisdom through experience, leadership',
        'negative': 'Delays, obstacles, poverty, chronic illness, isolation',
        'remedies': 'Serve the elderly, donate iron/black items on Saturdays, feed crows'
    },
    'Rahu': {
        'nature': 'Illusion, obsession, foreign',
        'positive': 'Innovation, foreign connections, research, occult knowledge',
        'negative': 'Confusion, addiction, scandals, legal issues, snakes',
        'remedies': 'Go to cremation ground, feed dogs, chant Rahu mantra'
    },
    'Ketu': {
        'nature': 'Detachment, spirituality, past life',
        'positive': 'Spiritual insight, detachment, wisdom, healing abilities',
        'negative': 'Confusion, accidents, isolation, skin issues, relationship breakage',
        'remedies': 'Feed crows, worship Lord Ganesha, practice meditation'
    },
}


def _get_lal_kitab_planet_analysis(planet_name, house, sign, is_retrograde, is_combust):
    base = LAL_KITAB_PLANET_INTERPRETATIONS.get(planet_name, {})
    house_info = LAL_KITAB_HOUSE_SIGNIFICATIONS.get(house, {})

    effects = []
    if is_retrograde:
        effects.append(f'{planet_name} is retrograde - results may be delayed but intensified')
    if is_combust:
        effects.append(f'{planet_name} is combust - its energy is weakened')
    if house <= 6:
        effects.append(f'Planet in {house}th house (lower hemisphere) - results manifest early in life')
    else:
        effects.append(f'Planet in {house}th house (upper hemisphere) - results manifest later in life')

    return {
        'planet': planet_name,
        'nature': base.get('nature', ''),
        'house': house,
        'houseSignification': house_info.get('name', ''),
        'positiveTraits': base.get('positive', ''),
        'negativeTraits': base.get('negative', ''),
        'effects': effects,
        'remedies': base.get('remedies', ''),
    }


@router.post('/lal-kitab/house-significations')
def lal_kitab_houses():
    return success({
        'houses': [
            {
                'number': num,
                'name': info['name'],
                'description': info['description'],
                'elements': info['elements'],
                'remedies': info['remedies'],
            }
            for num, info in LAL_KITAB_HOUSE_SIGNIFICATIONS.items()
        ]
    })


@router.post('/lal-kitab/planet-interpretations')
def lal_kitab_planet_interpretations():
    return success({
            'planets': [
                {
                    'name': name,
                    'nature': info['nature'],
                    'positiveTraits': info['positive'],
                    'negativeTraits': info['negative'],
                    'remedies': info['remedies'],
                }
                for name, info in LAL_KITAB_PLANET_INTERPRETATIONS.items()
            ]
        }
    )


@router.post('/lal-kitab/chart-analysis')
def lal_kitab_chart_analysis(body: BirthRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS
    from datetime import datetime
    import pytz

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    houses = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')

    house_list = houses.get('houses', [])
    asc_sign = houses.get('ascendant', {}).get('sign', 'Aries')
    asc_idx = ZODIAC_SIGNS.index(asc_sign)

    ordered = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    planet_analyses = []

    for pname in ordered:
        p = next((pl for pl in planets if pl['name'] == pname), None)
        if not p:
            continue
        ph = p.get('house', 0)
        ps = p.get('sign', '')
        is_ret = p.get('isRetrograde', False)
        is_cmb = p.get('isCombust', False)
        analysis = _get_lal_kitab_planet_analysis(pname, ph, ps, is_ret, is_cmb)
        analysis['sign'] = ps
        analysis['signLord'] = SIGN_LORDS.get(ps, '')
        analysis['degree'] = round(p.get('degree', 0), 2)
        planet_analyses.append(analysis)

    house_analyses = []
    for h in house_list:
        hnum = h['number']
        info = LAL_KITAB_HOUSE_SIGNIFICATIONS.get(hnum, {})
        planets_in_house = h.get('planets', [])
        hp_analyses = []
        for pname in planets_in_house:
            p = next((pl for pl in planets if pl['name'] == pname), None)
            if p:
                st = 'Retrograde' if p.get('isRetrograde') else 'Direct'
                hp_analyses.append({'planet': pname, 'status': st, 'degree': round(p.get('degree', 0), 2)})
        house_analyses.append({
            'house': hnum,
            'name': info.get('name', ''),
            'description': info.get('description', ''),
            'elements': info.get('elements', []),
            'planets': hp_analyses,
            'generalRemedies': info.get('remedies', []),
            'sign': h.get('sign', ''),
            'signLord': h.get('signLord', ''),
        })

    return success({
        'ascendant': {
            'sign': asc_sign,
            'degree': round(houses.get('ascendant', {}).get('degree', 0), 2),
        },
        'planets': planet_analyses,
        'houses': house_analyses,
        'note': 'Lal Kitab analysis based on house placement, retrograde/combust status, and classical Lal Kitab significations'
    })
