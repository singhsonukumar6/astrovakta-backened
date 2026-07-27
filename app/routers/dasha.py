from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


router = APIRouter()

DASHA_PREDICTIONS = {
    'Sun': {
        'general': 'Period of authority, recognition, and self-expression. Good for government matters, leadership roles, and career advancement.',
        'positive': 'Recognition, promotions, authority, fatherly support, vitality',
        'challenges': 'Ego clashes, conflicts with authority, eye/heart issues, overconfidence',
        'remedies': ['Worship Sun with water at sunrise', 'Chant Aditya Hridayam', 'Donate wheat on Sundays', 'Wear Ruby gemstone (after consultation)']
    },
    'Moon': {
        'general': 'Period of emotional growth, mental peace, and mother-related matters. Good for creativity, travel, and public interactions.',
        'positive': 'Mental peace, emotional fulfillment, travel, mother\'s support, public recognition',
        'challenges': 'Mood swings, mental stress, sleep issues, confusion, water-related problems',
        'remedies': ['Worship Lord Shiva', 'Chant Om Namah Shivaya', 'Donate rice on Mondays', 'Wear Pearl gemstone (after consultation)']
    },
    'Mars': {
        'general': 'Period of energy, courage, and competition. Good for property matters, siblings, and athletic pursuits.',
        'positive': 'Courage, property gains, sibling support, victory over enemies, engineering success',
        'challenges': 'Accidents, surgery, conflicts, legal disputes, blood-related issues, anger',
        'remedies': ['Worship Hanuman', 'Chant Hanuman Chalisa', 'Donate red lentils on Tuesdays', 'Wear Red Coral (after consultation)']
    },
    'Rahu': {
        'general': 'Period of unconventional growth, foreign connections, and karmic lessons. Can bring sudden gains or confusion.',
        'positive': 'Foreign travel/settlement, unexpected gains, technological breakthroughs, unconventional success',
        'challenges': 'Confusion, deception, addiction, health issues (skin, allergies), mental unrest, illusions',
        'remedies': ['Worship Lord Ganesha', 'Chant Om Gam Ganapataye Namaha', 'Donate blue/black items on Saturdays', 'Wear Hessonite garnet (after consultation)']
    },
    'Jupiter': {
        'general': 'Period of wisdom, expansion, children, and spiritual growth. Generally benefic period for education and wealth.',
        'positive': 'Wealth, children, education, spiritual growth, marriage (for eligible), mentorship',
        'challenges': 'Weight gain, liver issues, over-expansion, laziness, false confidence',
        'remedies': ['Worship Lord Vishnu', 'Chant Vishnu Sahasranama', 'Donate yellow items on Thursdays', 'Wear Yellow Sapphire (after consultation)']
    },
    'Saturn': {
        'general': 'Period of discipline, karmic lessons, and maturity through challenges. Slow but steady progress with hard work.',
        'positive': 'Discipline, long-term success, spiritual maturity, property gains, servant/worker support',
        'challenges': 'Delays, restrictions, depression, bone/joint issues, separation, poverty fears, hard work',
        'remedies': ['Worship Lord Shani', 'Chant Shani Mantra', 'Donate iron/black items on Saturdays', 'Wear Blue Sapphire (after consultation - only if compatible)']
    },
    'Mercury': {
        'general': 'Period of communication, intelligence, business, and education. Good for trade, writing, and analytical work.',
        'positive': 'Business success, communication skills, education, intellectual growth, skin health',
        'challenges': 'Nervousness, overthinking, speech issues, skin problems, anxiety, confusion in decisions',
        'remedies': ['Worship Lord Vishnu', 'Chant Vishnu Sahasranama', 'Donate green items on Wednesdays', 'Wear Emerald (after consultation)']
    },
    'Ketu': {
        'general': 'Period of spiritual detachment, intuition, and karmic release. Can bring both liberation and confusion.',
        'positive': 'Spiritual awakening, intuitive powers, liberation from attachments, mystical experiences',
        'challenges': 'Detachment from worldly life, confusion, isolation, health issues (nervous system), unexpected losses',
        'remedies': ['Worship Lord Ganesha', 'Chant Om Gan Ganapataye Namaha', 'Donate brown/grey items on Tuesdays', 'Wear Cat\'s Eye (after consultation)']
    },
    'Venus': {
        'general': 'Period of love, beauty, luxury, and creative fulfillment. Good for marriage, art, and material comforts.',
        'positive': 'Love, marriage, luxury vehicles, artistic success, beauty, romance, material comforts',
        'challenges': 'Indulgence, relationship conflicts, reproductive issues, over-spending, laziness',
        'remedies': ['Worship Goddess Lakshmi', 'Chant Lakshmi Mantra', 'Donate white items on Fridays', 'Wear Diamond (after consultation)']
    }
}

SUB_PERIOD_MODIFIERS = {
    'Sun': 'under Sun sub-period: authority and ego themes intensify',
    'Moon': 'under Moon sub-period: emotions and mental state are highlighted',
    'Mars': 'under Mars sub-period: energy and conflict themes are amplified',
    'Rahu': 'under Rahu sub-period: unconventional and karmic themes intensify',
    'Jupiter': 'under Jupiter sub-period: expansion and wisdom themes are highlighted',
    'Saturn': 'under Saturn sub-period: discipline and restriction themes intensify',
    'Mercury': 'under Mercury sub-period: communication and business themes are highlighted',
    'Ketu': 'under Ketu sub-period: spiritual and detachment themes intensify',
    'Venus': 'under Venus sub-period: love and luxury themes are highlighted',
}


class DashaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    timezone: str = Field(..., example="Asia/Kolkata")
    latitude: Optional[float] = Field(None, example=28.6139)
    longitude: Optional[float] = Field(None, example=77.2090)
    houseSystem: Optional[str] = Field(None, example='W')


@router.post('/dasha/vimshottari')
def vimshottari(body: DashaRequest):
    from ..main import to_julian, parse_local_datetime, vimshottari_full, calc_planets, calc_houses, sunrise_sunset
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    res = vimshottari_full(jd, birth_local)
    from ..main import validate_vimshottari_schedule
    validation = validate_vimshottari_schedule(res)

    # Determine current MD/AD/PD at 'now' in the provided timezone
    current_now = None
    current_prediction = None
    try:
        import pytz
        from datetime import datetime
        tz = pytz.timezone(body.timezone)
        today = datetime.now(tz).date().isoformat()
        cur_md = next((md for md in res.get('mahadashas', []) if md['startDate'] <= today < md['endDate']), None)
        if cur_md:
            cur_ad = next((ad for ad in cur_md.get('antardasha', []) if ad['startDate'] <= today < ad['endDate']), None)
            cur_pd = None
            if cur_ad:
                cur_pd = next((pd for pd in cur_ad.get('pratyantar', []) if pd['startDate'] <= today < pd['endDate']), None)
        else:
            cur_ad, cur_pd = None, None
        if cur_md:
            cur_sook = None
            if cur_pd:
                try:
                    cur_sook = next((sd for sd in cur_pd.get('sookshma', []) if sd['startDate'] <= today < sd['endDate']), None)
                except Exception:
                    cur_sook = None
            current_now = {
                'mahadasha': {'planet': cur_md['planet'], 'startDate': cur_md['startDate'], 'endDate': cur_md['endDate']},
                'antardasha': ({'planet': cur_ad['planet'], 'startDate': cur_ad['startDate'], 'endDate': cur_ad['endDate']} if cur_ad else None),
                'pratyantar': ({'planet': cur_pd['planet'], 'startDate': cur_pd['startDate'], 'endDate': cur_pd['endDate']} if cur_pd else None),
                'sookshma': ({'planet': cur_sook['planet'], 'startDate': cur_sook['startDate'], 'endDate': cur_sook['endDate']} if cur_sook else None)
            }

            # Build prediction
            md_pred = DASHA_PREDICTIONS.get(cur_md['planet'], {})
            ad_pred = DASHA_PREDICTIONS.get(cur_ad['planet'], {}) if cur_ad else {}
            pd_pred = DASHA_PREDICTIONS.get(cur_pd['planet'], {}) if cur_pd else {}

            current_prediction = {
                'period': f"{cur_md['planet']} Mahadasha > {cur_ad['planet'] if cur_ad else 'N/A'} Antardasha > {cur_pd['planet'] if cur_pd else 'N/A'} Pratyantar",
                'general': md_pred.get('general', ''),
                'mahadashaEffect': md_pred.get('general', ''),
                'antardashaEffect': ad_pred.get('general', ''),
                'pratyantarEffect': pd_pred.get('general', ''),
                'subPeriodNote': SUB_PERIOD_MODIFIERS.get(cur_ad['planet'], '') if cur_ad else '',
                'positive': md_pred.get('positive', ''),
                'challenges': md_pred.get('challenges', ''),
                'remedies': md_pred.get('remedies', []),
                'adPositive': ad_pred.get('positive', ''),
                'adChallenges': ad_pred.get('challenges', ''),
            }
    except Exception:
        current_now = None
        current_prediction = None

    context = {}
    if body.latitude is not None and body.longitude is not None:
        try:
            planets = calc_planets(jd, None, 'mean')
            hs_code = body.houseSystem or 'W'
            houses = calc_houses(jd, float(body.latitude), float(body.longitude), planets, hs_code)
            sr, ss, sr_jd, ss_jd = sunrise_sunset(body.dateOfBirth, body.timezone, float(body.latitude), float(body.longitude))
            context = {
                'ascendant': houses.get('ascendant'),
                'houses': houses.get('houses'),
                'sunrise': sr,
                'sunset': ss,
                'houseSystem': hs_code
            }
        except Exception as e:
            context = {'warning': f'Location context unavailable: {e}'}

    return {
        'status': 200,
        'system': 'Vimshottari',
        'data': res,
        'currentNow': current_now,
        'currentPrediction': current_prediction,
        'context': context,
        'validation': validation
    }
