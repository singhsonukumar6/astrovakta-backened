from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pytz
from dateutil import parser

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, DASHA_YEARS, DASHA_SEQUENCE,
    planet_status, NAKSHATRAS,
)

router = APIRouter()


class DashaDetailRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    nodeMode: Optional[str] = Field('mean', example='mean')
    startYear: Optional[int] = Field(None, example=2020)
    endYear: Optional[int] = Field(None, example=2040)


class DashaPlanetRequest(DashaDetailRequest):
    planet: str = Field(..., example="Jupiter", description="Planet name for detailed effects")


PLANET_DASHA_EFFECTS: Dict[str, Dict[str, Any]] = {
    'Sun': {
        'career': 'Rise in authority, government favor, leadership roles. Opportunities in administration and public life. Good period for promotions and recognition from superiors.',
        'health': 'Vitality increases but watch for heart, eye, and bone issues. Overexertion and fevers possible. Stay hydrated and avoid excessive sun exposure.',
        'relationships': 'Relationship with father improves. Ego clashes with partner possible. Social status rises, attracting respect but also envy.',
        'finance': 'Income from government or authority figures. Property gains possible. Speculative gains moderate. Good for investments in gold and government bonds.',
        'general': 'Period of authority, recognition, and self-expression. Strong solar influence brings leadership opportunities and public standing.',
        'favorable': ['Government work', 'Leadership roles', 'Gold investments', 'Public life', 'Authority positions'],
        'unfavorable': ['Ego confrontations', 'Overconfidence', 'Ignoring advice', 'Overexertion'],
        'remedies': ['Worship Sun with water at sunrise', 'Chant Aditya Hridayam', 'Donate wheat on Sundays', 'Wear Ruby gemstone after consultation'],
    },
    'Moon': {
        'career': 'Creative fields flourish. Public-facing roles shine. Travel and relocation opportunities. Good for hospitality, dairy, shipping, and import-export.',
        'health': 'Mental health focus. Vulnerability to stress, anxiety, and sleep disorders. Emotional fluctuations affect physical well-being. Protect from cold and water-related ailments.',
        'relationships': 'Strong bond with mother. Emotional sensitivity deepens. Romantic relationships may fluctuate. Domestic peace generally good with occasional mood-driven disputes.',
        'finance': 'Gains through liquids, dairy, shipping, travel, and feminine products. Investments in silver beneficial. Fluctuating income pattern but overall positive.',
        'general': 'Period of emotional growth, mental peace, and mother-related matters. Strong lunar influence enhances intuition and creativity.',
        'favorable': ['Travel', 'Creative work', 'Silver investments', 'Public interactions', 'Emotional bonding'],
        'unfavorable': ['Emotional decisions', 'Water travel', 'Substance dependency', 'Overthinking'],
        'remedies': ['Worship Lord Shiva', 'Chant Om Namah Shivaya', 'Donate rice on Mondays', 'Wear Pearl gemstone after consultation'],
    },
    'Mars': {
        'career': 'Engineering, military, sports, and real estate thrive. Competitive exams successful. Surgery-related careers advance. Strong period for entrepreneurs and athletes.',
        'health': 'High energy but accident-prone. Surgery, blood disorders, inflammations, and fevers possible. Head injuries and muscle strains need attention.',
        'relationships': 'Conflicts with siblings and neighbors possible. Hot temper causes friction in marriage. Courage and initiative in relationships but impulsiveness damages bonds.',
        'finance': 'Gains through real estate, vehicles, surgery-related fields, and engineering. Property disputes may arise. Good for litigation but avoid impulsive investments.',
        'general': 'Period of energy, courage, and competition. Strong Martian influence drives action and initiative.',
        'favorable': ['Real estate', 'Engineering', 'Sports', 'Surgery', 'Military service', 'Litigation'],
        'unfavorable': ['Impulsiveness', 'Anger', 'Risky ventures', 'Hot-blooded decisions'],
        'remedies': ['Worship Hanuman', 'Chant Hanuman Chalisa', 'Donate red lentils on Tuesdays', 'Wear Red Coral after consultation'],
    },
    'Rahu': {
        'career': 'Foreign connections bring success. Technology, aviation, unconventional fields flourish. Political or投机 gains. Breakthroughs through unorthodox methods.',
        'health': 'Mysterious ailments, allergies, skin problems. Psychological disturbances, phobias, and addiction vulnerability. Unexplained health issues.',
        'relationships': 'Unconventional relationships. Obsessive tendencies. Foreign spouse possible. Secret affairs or unconventional partnerships. Detachment from tradition.',
        'finance': 'Sudden unexpected gains or losses. Speculation can be highly rewarding or devastating. Foreign income likely. Lottery-like gains possible but unreliable.',
        'general': 'Period of unconventional growth, foreign connections, and karmic lessons. Rahu creates desire and illusion.',
        'favorable': ['Foreign travel', 'Technology', 'Innovation', 'Unconventional paths', 'Political gains'],
        'unfavorable': ['Addiction', 'Deception', 'Obsession', 'Confusion', 'Over-ambition'],
        'remedies': ['Worship Lord Ganesha', 'Chant Om Gam Ganapataye Namaha', 'Donate blue/black items on Saturdays', 'Wear Hessonite garnet after consultation'],
    },
    'Jupiter': {
        'career': 'Teaching, banking, law, consulting, and advisory roles thrive. Spiritual and educational ventures prosper. Good for writers, judges, and religious leaders.',
        'health': 'Generally positive. Watch for weight gain, liver, and pancreatic issues. Diabetes risk increases. Overall vitality remains strong.',
        'relationships': "Marriage blessed. Children fortunate. Family harmony. Elders' blessings received. Mentorship relationships form. Spiritual partnerships develop.",
        'finance': 'Steady wealth accumulation. Property and gold investments profitable. Benefits through inheritance and paternal assets. Good for long-term financial planning.',
        'general': 'Period of wisdom, expansion, children, and spiritual growth. Jupiter brings blessings and abundance.',
        'favorable': ['Education', 'Spirituality', 'Banking', 'Law', 'Consulting', 'Long-term investments'],
        'unfavorable': ['Overconfidence', 'Weight gain', 'Laziness', 'Excessive optimism'],
        'remedies': ['Worship Lord Vishnu', 'Chant Vishnu Sahasranama', 'Donate yellow items on Thursdays', 'Wear Yellow Sapphire after consultation'],
    },
    'Saturn': {
        'career': 'Hard work pays slowly but surely. Industrial, agricultural, and labor-intensive work succeeds. Service-oriented roles bring long-term gains. Delayed but permanent success.',
        'health': 'Bone, joint, and dental issues. Chronic ailments surface. Rheumatism, arthritis, and depression possible. Requires disciplined health routine.',
        'relationships': 'Separation or distance from loved ones. Hardships in marriage test bonds. Service to elders and underprivileged brings relief. Karmic lessons through relationships.',
        'finance': 'Slow wealth building. Losses through property or land initially. Steady income through hard work. Avoid shortcuts. Real estate gains in later part of period.',
        'general': 'Period of discipline, karmic lessons, and maturity through challenges. Saturn demands patience and responsibility.',
        'favorable': ['Service work', 'Discipline', 'Long-term planning', 'Industrial work', 'Charity'],
        'unfavorable': ['Depression', 'Laziness', 'Shortcuts', 'Isolation', 'Fear'],
        'remedies': ['Worship Lord Shani', 'Chant Shani Mantra', 'Donate iron/black items on Saturdays', 'Wear Blue Sapphire after consultation only'],
    },
    'Mercury': {
        'career': 'Commerce, writing, communication, education, and analytics excel. Good for traders, teachers, accountants, and IT professionals. Intellectual pursuits rewarded.',
        'health': 'Nervous system, skin, and speech-related issues. Anxiety and overthinking common. Auditory and respiratory sensitivity. Good for overall mental sharpness.',
        'relationships': 'Communication strengthens bonds. Intellectual connection with partner. Youthful energy in relationships. Social circle expands through wit and charm.',
        'finance': 'Gains through trade, communication, writing, and education. Good for stock market and business ventures. Investments in green items and educational institutions profitable.',
        'general': 'Period of communication, intelligence, business, and education. Mercury enhances analytical and communicative abilities.',
        'favorable': ['Trade', 'Writing', 'Education', 'Analytics', 'IT', 'Communication'],
        'unfavorable': ['Nervousness', 'Overthinking', 'Deception in trade', 'Indecisiveness'],
        'remedies': ['Worship Lord Vishnu', 'Chant Vishnu Sahasranama', 'Donate green items on Wednesdays', 'Wear Emerald after consultation'],
    },
    'Ketu': {
        'career': 'Spiritual and research-oriented work thrives. Detachment from material career ambitions. Success in occult, healing, and liberation-focused pursuits.',
        'health': 'Nervous system vulnerabilities. Unexplained ailments. Surgical procedures possible. Psychic disturbances and isolation-related health issues.',
        'relationships': 'Detachment from relationships. Spiritual partnerships preferred. Past life connections surface. Loss or separation possible, leading to spiritual growth.',
        'finance': 'Losses through detachment or confusion. Unexpected financial events. Liberation from material attachments. Gains through spiritual or healing practices.',
        'general': 'Period of spiritual detachment, intuition, and karmic release. Ketu dissolves material attachments.',
        'favorable': ['Spirituality', 'Meditation', 'Research', 'Healing', 'Liberation'],
        'unfavorable': ['Confusion', 'Isolation', 'Material loss', 'Detachment from reality'],
        'remedies': ['Worship Lord Ganesha', 'Chant Om Gan Ganapataye Namaha', 'Donate brown/grey items on Tuesdays', "Wear Cat's Eye after consultation"],
    },
    'Venus': {
        'career': 'Arts, entertainment, luxury, fashion, and beauty industries flourish. Good for designers, artists, musicians, and hospitality professionals.',
        'health': 'Reproductive health attention needed. Kidney and urinary issues possible. Overall vitality good but overindulgence harmful. Skin and beauty concerns.',
        'relationships': 'Romance and marriage peak. Luxurious social life. Strong attraction and chemistry. Artistic and creative partnerships. Sometimes excessive indulgence.',
        'finance': 'Gains through arts, luxury goods, vehicles, and beauty products. Investments in diamonds and white items beneficial. Property gains through female connections.',
        'general': 'Period of love, beauty, luxury, and creative fulfillment. Venus brings romance and artistic inspiration.',
        'favorable': ['Arts', 'Luxury', 'Romance', 'Beauty', 'Fashion', 'Hospitality'],
        'unfavorable': ['Indulgence', 'Over-spending', 'Laziness', 'Infidelity', 'Vanity'],
        'remedies': ['Worship Goddess Lakshmi', 'Chant Lakshmi Mantra', 'Donate white items on Fridays', 'Wear Diamond after consultation'],
    },
}

SUB_PERIOD_MODIFIERS: Dict[str, str] = {
    'Sun': 'Authority and ego themes intensify. Solar energy colors the sub-period.',
    'Moon': 'Emotions and mental state are highlighted. Lunar sensitivity increases.',
    'Mars': 'Energy and conflict themes are amplified. Martian drive pushes forward.',
    'Rahu': 'Unconventional and karmic themes intensify. Rahu creates desire and illusion.',
    'Jupiter': 'Expansion and wisdom themes are highlighted. Jupiterian blessings flow.',
    'Saturn': 'Discipline and restriction themes intensify. Saturn demands responsibility.',
    'Mercury': 'Communication and business themes are highlighted. Mercuryian intellect sharpens.',
    'Ketu': 'Spiritual and detachment themes intensify. Ketu dissolves attachments.',
    'Venus': 'Love and luxury themes are highlighted. Venusian charm and beauty dominate.',
}


def _pd_years(years: float) -> timedelta:
    return timedelta(days=int(round(years * 365.25)))


def _parse_local_dt(date_str: str, time_str: str, tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    dt_local = parser.parse(f"{date_str} {time_str}")
    return tz.localize(dt_local)


def _rotate_seq(start: str) -> List[str]:
    i = DASHA_SEQUENCE.index(start)
    return DASHA_SEQUENCE[i:] + DASHA_SEQUENCE[:i]


def _compute_vimshottari_full(jd: float, birth_dt_local: datetime) -> Dict[str, Any]:
    import swisseph as swe

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xm, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    m_lon = xm[0]
    nk_idx = int(m_lon // 13.333333) % 27
    start_lord = NAKSHATRAS[nk_idx][1]
    pos_in_nk = (m_lon % 13.333333) / 13.333333
    md_years_total = DASHA_YEARS[start_lord]
    first_md_years = (1 - pos_in_nk) * md_years_total

    md_years_list: List[tuple] = [(start_lord, first_md_years)]
    total_years = first_md_years
    start_index = DASHA_SEQUENCE.index(start_lord)
    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(start_index + i) % 9]
        y = DASHA_YEARS[lord]
        md_years_list.append((lord, y))
        total_years += y
    while total_years < 120 - 0.01:
        for lord in DASHA_SEQUENCE:
            y = DASHA_YEARS[lord]
            md_years_list.append((lord, y))
            total_years += y
            if total_years >= 120 - 0.01:
                break

    def build_antardasha(md_start: datetime, md_years: float, md_lord: str):
        antars = []
        cursor_a = md_start
        for ad_lord in _rotate_seq(md_lord):
            ad_years = md_years * (DASHA_YEARS[ad_lord] / 120.0)
            ad_start = cursor_a
            ad_end = ad_start + _pd_years(ad_years)
            pratis = []
            cursor_p = ad_start
            for pd_lord in _rotate_seq(ad_lord):
                pr_years = ad_years * (DASHA_YEARS[pd_lord] / 120.0)
                p_start = cursor_p
                p_end = p_start + _pd_years(pr_years)
                pratis.append({
                    'planet': pd_lord,
                    'startDate': p_start.date().isoformat(),
                    'endDate': p_end.date().isoformat(),
                })
                cursor_p = p_end
            antars.append({
                'planet': ad_lord,
                'startDate': ad_start.date().isoformat(),
                'endDate': ad_end.date().isoformat(),
                'pratyantar': pratis,
            })
            cursor_a = ad_end
        return antars

    mahadashas = []
    cursor = birth_dt_local
    for lord, years in md_years_list:
        md_start = cursor
        md_end = md_start + _pd_years(years)
        mahadashas.append({
            'planet': lord,
            'years': round(years, 4),
            'startDate': md_start.date().isoformat(),
            'endDate': md_end.date().isoformat(),
            'antardasha': build_antardasha(md_start, years, lord),
        })
        cursor = md_end

    return {
        'moonNakshatraIdx': nk_idx,
        'startLord': start_lord,
        'firstMdYears': round(first_md_years, 4),
        'mahadashas': mahadashas,
    }


def _build_period_entry(md_lord: str, ad_lord: str, pd_lord: str,
                        house: int, is_current: bool,
                        start_date: str, end_date: str) -> Dict[str, Any]:
    effects = PLANET_DASHA_EFFECTS.get(md_lord, PLANET_DASHA_EFFECTS.get(ad_lord, {}))
    md_effect = PLANET_DASHA_EFFECTS.get(md_lord, {})
    ad_effect = PLANET_DASHA_EFFECTS.get(ad_lord, {})

    favorable = md_effect.get('favorable', []) + ad_effect.get('favorable', [])
    unfavorable = md_effect.get('unfavorable', []) + ad_effect.get('unfavorable', [])

    return {
        'period': f"{md_lord} > {ad_lord} > {pd_lord}" if pd_lord else f"{md_lord} > {ad_lord}",
        'mahadasha': md_lord,
        'antardasha': ad_lord,
        'pratyantardasha': pd_lord,
        'startDate': start_date,
        'endDate': end_date,
        'isCurrent': is_current,
        'relevantHouse': house,
        'effects': {
            'career': md_effect.get('career', ''),
            'health': md_effect.get('health', ''),
            'relationships': md_effect.get('relationships', ''),
            'finance': md_effect.get('finance', ''),
        },
        'subPeriodNote': SUB_PERIOD_MODIFIERS.get(ad_lord, ''),
        'favorable': favorable,
        'unfavorable': unfavorable,
        'remedies': md_effect.get('remedies', []),
    }


def _find_current_periods(data: Dict[str, Any], today_str: str) -> Dict[str, Any]:
    cur_md = cur_ad = cur_pd = None
    for md in data['mahadashas']:
        if md['startDate'] <= today_str < md['endDate']:
            cur_md = md
            break
    if not cur_md:
        return {'mahadasha': None, 'antardasha': None, 'pratyantardasha': None}
    for ad in cur_md['antardasha']:
        if ad['startDate'] <= today_str < ad['endDate']:
            cur_ad = ad
            break
    if cur_ad:
        for pd in cur_ad['pratyantar']:
            if pd['startDate'] <= today_str < pd['endDate']:
                cur_pd = pd
                break
    return {'mahadasha': cur_md, 'antardasha': cur_ad, 'pratyantardasha': cur_pd}


def _get_house_for_planet(planet: str, houses: List[Dict[str, Any]]) -> int:
    for h in houses:
        if planet in h.get('planets', []):
            return h['number']
    return 0


@router.post('/horoscope/dasha/timeline')
def dasha_timeline(body: DashaDetailRequest) -> Dict[str, Any]:
    from ..utils import to_julian as _to_julian, calc_planets as _calc_planets, calc_houses as _calc_houses

    jd = _to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_dt_local = _parse_local_dt(body.dateOfBirth, body.timeOfBirth, body.timezone)

    data = _compute_vimshottari_full(jd, birth_dt_local)

    tz = pytz.timezone(body.timezone)
    today_str = datetime.now(tz).date().isoformat()

    planets = _calc_planets(jd, None, body.nodeMode or 'mean')
    houses_data = _calc_houses(jd, body.latitude, body.longitude, planets, 'W')
    house_list = houses_data.get('houses', [])

    full_timeline = []
    for md in data['mahadashas']:
        md_lord = md['planet']
        md_house = _get_house_for_planet(md_lord, house_list)

        antardashas = []
        for ad in md['antardasha']:
            ad_lord = ad['planet']
            ad_house = _get_house_for_planet(ad_lord, house_list)

            pratyantardashas = []
            is_md_current = (md['startDate'] <= today_str < md['endDate'])
            is_ad_current = is_md_current and (ad['startDate'] <= today_str < ad['endDate'])
            for pd in ad['pratyantar']:
                pd_lord = pd['planet']
                pd_house = _get_house_for_planet(pd_lord, house_list)
                is_pd_current = is_ad_current and (pd['startDate'] <= today_str < pd['endDate'])
                pratyantardashas.append({
                    'planet': pd_lord,
                    'startDate': pd['startDate'],
                    'endDate': pd['endDate'],
                    'isCurrent': is_pd_current,
                    'relevantHouse': pd_house,
                    'effects': PLANET_DASHA_EFFECTS.get(pd_lord, {}).get('general', ''),
                    'subPeriodNote': SUB_PERIOD_MODIFIERS.get(pd_lord, ''),
                })

            antardashas.append({
                'planet': ad_lord,
                'startDate': ad['startDate'],
                'endDate': ad['endDate'],
                'isCurrent': is_ad_current,
                'relevantHouse': ad_house,
                'effects': {
                    'career': PLANET_DASHA_EFFECTS.get(ad_lord, {}).get('career', ''),
                    'health': PLANET_DASHA_EFFECTS.get(ad_lord, {}).get('health', ''),
                    'relationships': PLANET_DASHA_EFFECTS.get(ad_lord, {}).get('relationships', ''),
                    'finance': PLANET_DASHA_EFFECTS.get(ad_lord, {}).get('finance', ''),
                },
                'subPeriodNote': SUB_PERIOD_MODIFIERS.get(ad_lord, ''),
                'pratyantardashas': pratyantardashas,
            })

        is_md_current = (md['startDate'] <= today_str < md['endDate'])
        full_timeline.append({
            'planet': md_lord,
            'years': md['years'],
            'startDate': md['startDate'],
            'endDate': md['endDate'],
            'isCurrent': is_md_current,
            'relevantHouse': md_house,
            'effects': {
                'career': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('career', ''),
                'health': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('health', ''),
                'relationships': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('relationships', ''),
                'finance': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('finance', ''),
            },
            'favorable': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('favorable', []),
            'unfavorable': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('unfavorable', []),
            'remedies': PLANET_DASHA_EFFECTS.get(md_lord, {}).get('remedies', []),
            'antardashas': antardashas,
        })

    current_periods = _find_current_periods(data, today_str)
    current = None
    if current_periods['mahadasha']:
        cur_md = current_periods['mahadasha']
        cur_ad = current_periods['antardasha']
        cur_pd = current_periods['pratyantardasha']
        cur_md_house = _get_house_for_planet(cur_md['planet'], house_list)
        cur_ad_house = _get_house_for_planet(cur_ad['planet'], house_list) if cur_ad else 0
        cur_pd_house = _get_house_for_planet(cur_pd['planet'], house_list) if cur_pd else 0
        current = _build_period_entry(
            cur_md['planet'],
            cur_ad['planet'] if cur_ad else cur_md['planet'],
            cur_pd['planet'] if cur_pd else '',
            cur_pd_house if cur_pd else cur_ad_house if cur_ad else cur_md_house,
            True,
            cur_pd['startDate'] if cur_pd else cur_ad['startDate'] if cur_ad else cur_md['startDate'],
            cur_pd['endDate'] if cur_pd else cur_ad['endDate'] if cur_ad else cur_md['endDate'],
        )

    return {
        'status': 200,
        'system': 'Vimshottari',
        'birthDetails': {
            'date': body.dateOfBirth,
            'time': body.timeOfBirth,
            'latitude': body.latitude,
            'longitude': body.longitude,
            'timezone': body.timezone,
        },
        'moonNakshatra': data.get('startLord', ''),
        'firstMahadashaLord': data.get('startLord', ''),
        'firstMahadashaYears': data.get('firstMdYears', 0),
        'currentDate': today_str,
        'current': current,
        'timeline': full_timeline,
        'summary': {
            'totalMahadashas': len(full_timeline),
            'dateRange': f"{full_timeline[0]['startDate']} to {full_timeline[-1]['endDate']}" if full_timeline else '',
            'totalSpanYears': sum(md['years'] for md in full_timeline),
        },
    }


@router.post('/horoscope/dasha/details')
def dasha_planet_details(body: DashaPlanetRequest) -> Dict[str, Any]:
    from ..utils import to_julian as _to_julian, calc_planets as _calc_planets, calc_houses as _calc_houses

    valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    planet_name = body.planet.capitalize()
    if planet_name not in valid_planets:
        return {'status': 400, 'error': f"Invalid planet. Must be one of: {', '.join(valid_planets)}"}

    jd = _to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_dt_local = _parse_local_dt(body.dateOfBirth, body.timeOfBirth, body.timezone)

    data = _compute_vimshottari_full(jd, birth_dt_local)

    tz = pytz.timezone(body.timezone)
    today_str = datetime.now(tz).date().isoformat()

    planets = _calc_planets(jd, None, body.nodeMode or 'mean')
    houses_data = _calc_houses(jd, body.latitude, body.longitude, planets, 'W')
    house_list = houses_data.get('houses', [])
    ascendant = houses_data.get('ascendant', {})

    effects = PLANET_DASHA_EFFECTS.get(planet_name, {})

    planet_natal = next((p for p in planets if p['name'] == planet_name), None)
    natal_info = {}
    if planet_natal:
        natal_info = {
            'sign': planet_natal['sign'],
            'signLord': planet_natal['signLord'],
            'house': planet_natal['house'],
            'degree': planet_natal['degree'],
            'degreeDMS': planet_natal['degreeDMS'],
            'nakshatra': planet_natal['nakshatra'],
            'nakshatraLord': planet_natal['nakshatraLord'],
            'dignity': planet_status(planet_name, planet_natal['sign']),
            'isRetrograde': planet_natal['isRetrograde'],
        }

    planet_md_entries = []
    for md in data['mahadashas']:
        if md['planet'] != planet_name:
            continue
        ad_details = []
        for ad in md['antardasha']:
            is_current = (ad['startDate'] <= today_str < ad['endDate'])
            ad_effect = PLANET_DASHA_EFFECTS.get(ad['planet'], {})
            pratyantar_details = []
            for pd in ad['pratyantar']:
                pd_is_current = is_current and (pd['startDate'] <= today_str < pd['endDate'])
                pd_effect = PLANET_DASHA_EFFECTS.get(pd['planet'], {})
                pratyantar_details.append({
                    'planet': pd['planet'],
                    'startDate': pd['startDate'],
                    'endDate': pd['endDate'],
                    'isCurrent': pd_is_current,
                    'effects': {
                        'career': pd_effect.get('career', ''),
                        'health': pd_effect.get('health', ''),
                        'relationships': pd_effect.get('relationships', ''),
                        'finance': pd_effect.get('finance', ''),
                    },
                    'subPeriodNote': SUB_PERIOD_MODIFIERS.get(pd['planet'], ''),
                })
            ad_details.append({
                'planet': ad['planet'],
                'startDate': ad['startDate'],
                'endDate': ad['endDate'],
                'isCurrent': is_current,
                'effects': {
                    'career': ad_effect.get('career', ''),
                    'health': ad_effect.get('health', ''),
                    'relationships': ad_effect.get('relationships', ''),
                    'finance': ad_effect.get('finance', ''),
                },
                'subPeriodNote': SUB_PERIOD_MODIFIERS.get(ad['planet'], ''),
                'pratyantardashas': pratyantar_details,
            })
        is_md_current = (md['startDate'] <= today_str < md['endDate'])
        planet_md_entries.append({
            'years': md['years'],
            'startDate': md['startDate'],
            'endDate': md['endDate'],
            'isCurrent': is_md_current,
            'antardashas': ad_details,
        })

    current_md = next(
        (md for md in planet_md_entries if md['isCurrent']),
        planet_md_entries[0] if planet_md_entries else None
    )

    current_period = None
    if current_md:
        cur_ad = next((ad for ad in current_md['antardashas'] if ad['isCurrent']), None)
        cur_pd = None
        if cur_ad:
            cur_pd = next((pd for pd in cur_ad['pratyantardashas'] if pd['isCurrent']), None)
        current_period = {
            'mahadasha': {
                'startDate': current_md['startDate'],
                'endDate': current_md['endDate'],
            },
            'antardasha': {
                'planet': cur_ad['planet'],
                'startDate': cur_ad['startDate'],
                'endDate': cur_ad['endDate'],
            } if cur_ad else None,
            'pratyantardasha': {
                'planet': cur_pd['planet'],
                'startDate': cur_pd['startDate'],
                'endDate': cur_pd['endDate'],
            } if cur_pd else None,
        }

    return {
        'status': 200,
        'system': 'Vimshottari',
        'planet': planet_name,
        'currentDate': today_str,
        'natalPosition': natal_info,
        'ascendant': ascendant,
        'effects': {
            'career': effects.get('career', ''),
            'health': effects.get('health', ''),
            'relationships': effects.get('relationships', ''),
            'finance': effects.get('finance', ''),
            'general': effects.get('general', ''),
        },
        'favorable': effects.get('favorable', []),
        'unfavorable': effects.get('unfavorable', []),
        'remedies': effects.get('remedies', []),
        'mahadashas': planet_md_entries,
        'currentPeriod': current_period,
        'totalOccurrences': len(planet_md_entries),
        'note': f"This shows all {planet_name} Mahadasha periods in the full 120-year Vimshottari cycle. Each Mahadasha contains proportional Antardasha and Pratyantardasha sub-periods.",
    }


@router.post('/horoscope/dasha/current')
def current_dasha(body: DashaDetailRequest) -> Dict[str, Any]:
    from ..utils import to_julian as _to_julian, calc_planets as _calc_planets, calc_houses as _calc_houses

    jd = _to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_dt_local = _parse_local_dt(body.dateOfBirth, body.timeOfBirth, body.timezone)

    data = _compute_vimshottari_full(jd, birth_dt_local)

    tz = pytz.timezone(body.timezone)
    today_str = datetime.now(tz).date().isoformat()

    planets = _calc_planets(jd, None, body.nodeMode or 'mean')
    houses_data = _calc_houses(jd, body.latitude, body.longitude, planets, 'W')
    house_list = houses_data.get('houses', [])

    current_periods = _find_current_periods(data, today_str)
    cur_md = current_periods['mahadasha']
    cur_ad = current_periods['antardasha']
    cur_pd = current_periods['pratyantardasha']

    if not cur_md:
        return {
            'status': 404,
            'error': 'Could not determine current dasha. Birth date may be too far in the future or past the 120-year cycle.',
        }

    cur_md_house = _get_house_for_planet(cur_md['planet'], house_list)
    cur_ad_house = _get_house_for_planet(cur_ad['planet'], house_list) if cur_ad else 0
    cur_pd_house = _get_house_for_planet(cur_pd['planet'], house_list) if cur_pd else 0

    current = _build_period_entry(
        cur_md['planet'],
        cur_ad['planet'] if cur_ad else cur_md['planet'],
        cur_pd['planet'] if cur_pd else '',
        cur_pd_house if cur_pd else cur_ad_house if cur_ad else cur_md_house,
        True,
        cur_pd['startDate'] if cur_pd else cur_ad['startDate'] if cur_ad else cur_md['startDate'],
        cur_pd['endDate'] if cur_pd else cur_ad['endDate'] if cur_ad else cur_md['endDate'],
    )

    next_transitions = []
    transition_count = 0
    if cur_ad:
        ad_list = cur_md['antardasha']
        current_ad_idx = None
        for idx, ad in enumerate(ad_list):
            if ad['planet'] == cur_ad['planet'] and ad['startDate'] == cur_ad['startDate']:
                current_ad_idx = idx
                break
        if current_ad_idx is not None:
            remaining_ad = ad_list[current_ad_idx + 1:]
            for ad in remaining_ad:
                if transition_count >= 3:
                    break
                ad_house = _get_house_for_planet(ad['planet'], house_list)
                ad_effect = PLANET_DASHA_EFFECTS.get(ad['planet'], {})
                ad_md_effect = PLANET_DASHA_EFFECTS.get(cur_md['planet'], {})
                transition_count += 1
                next_transitions.append({
                    'transitionNumber': transition_count,
                    'type': 'Antardasha',
                    'fromPlanet': cur_ad['planet'] if transition_count == 1 else ad_list[current_ad_idx + transition_count - 2]['planet'],
                    'toPlanet': ad['planet'],
                    'date': ad['startDate'],
                    'relevantHouse': ad_house,
                    'effects': {
                        'career': ad_effect.get('career', ''),
                        'health': ad_effect.get('health', ''),
                        'relationships': ad_effect.get('relationships', ''),
                        'finance': ad_effect.get('finance', ''),
                    },
                    'subPeriodNote': SUB_PERIOD_MODIFIERS.get(ad['planet'], ''),
                    'expectation': f"Transition from {cur_ad['planet'] if transition_count == 1 else ad_list[current_ad_idx + transition_count - 2]['planet']} to {ad['planet']} sub-period. {SUB_PERIOD_MODIFIERS.get(ad['planet'], '')}",
                })

            if transition_count < 3 and cur_md['planet'] != data['mahadashas'][-1]['planet']:
                next_md_idx = None
                for idx, md in enumerate(data['mahadashas']):
                    if md['planet'] == cur_md['planet'] and md['startDate'] == cur_md['startDate']:
                        next_md_idx = idx
                        break
                if next_md_idx is not None and next_md_idx + 1 < len(data['mahadashas']):
                    next_md = data['mahadashas'][next_md_idx + 1]
                    next_md_house = _get_house_for_planet(next_md['planet'], house_list)
                    transition_count += 1
                    next_transitions.append({
                        'transitionNumber': transition_count,
                        'type': 'Mahadasha',
                        'fromPlanet': cur_md['planet'],
                        'toPlanet': next_md['planet'],
                        'date': next_md['startDate'],
                        'relevantHouse': next_md_house,
                        'effects': {
                            'career': PLANET_DASHA_EFFECTS.get(next_md['planet'], {}).get('career', ''),
                            'health': PLANET_DASHA_EFFECTS.get(next_md['planet'], {}).get('health', ''),
                            'relationships': PLANET_DASHA_EFFECTS.get(next_md['planet'], {}).get('relationships', ''),
                            'finance': PLANET_DASHA_EFFECTS.get(next_md['planet'], {}).get('finance', ''),
                        },
                        'subPeriodNote': '',
                        'expectation': f"Major life shift from {cur_md['planet']} to {next_md['planet']} Mahadasha. Theme changes significantly.",
                    })

    md_effect = PLANET_DASHA_EFFECTS.get(cur_md['planet'], {})
    ad_effect = PLANET_DASHA_EFFECTS.get(cur_ad['planet'], {}) if cur_ad else {}
    pd_effect = PLANET_DASHA_EFFECTS.get(cur_pd['planet'], {}) if cur_pd else {}

    return {
        'status': 200,
        'system': 'Vimshottari',
        'currentDate': today_str,
        'currentDasha': {
            'mahadasha': {
                'planet': cur_md['planet'],
                'startDate': cur_md['startDate'],
                'endDate': cur_md['endDate'],
                'relevantHouse': cur_md_house,
                'effects': {
                    'career': md_effect.get('career', ''),
                    'health': md_effect.get('health', ''),
                    'relationships': md_effect.get('relationships', ''),
                    'finance': md_effect.get('finance', ''),
                },
                'favorable': md_effect.get('favorable', []),
                'unfavorable': md_effect.get('unfavorable', []),
                'remedies': md_effect.get('remedies', []),
            },
            'antardasha': {
                'planet': cur_ad['planet'],
                'startDate': cur_ad['startDate'],
                'endDate': cur_ad['endDate'],
                'relevantHouse': cur_ad_house,
                'effects': {
                    'career': ad_effect.get('career', ''),
                    'health': ad_effect.get('health', ''),
                    'relationships': ad_effect.get('relationships', ''),
                    'finance': ad_effect.get('finance', ''),
                },
                'subPeriodNote': SUB_PERIOD_MODIFIERS.get(cur_ad['planet'], ''),
            } if cur_ad else None,
            'pratyantardasha': {
                'planet': cur_pd['planet'],
                'startDate': cur_pd['startDate'],
                'endDate': cur_pd['endDate'],
                'relevantHouse': cur_pd_house,
                'effects': {
                    'career': pd_effect.get('career', ''),
                    'health': pd_effect.get('health', ''),
                    'relationships': pd_effect.get('relationships', ''),
                    'finance': pd_effect.get('finance', ''),
                },
                'subPeriodNote': SUB_PERIOD_MODIFIERS.get(cur_pd['planet'], ''),
            } if cur_pd else None,
        },
        'nextTransitions': next_transitions,
        'overallPrediction': {
            'theme': f"{cur_md['planet']} Mahadasha with {cur_ad['planet'] if cur_ad else cur_md['planet']} Antardasha is active.",
            'positive': md_effect.get('general', '') + ' ' + ad_effect.get('general', ''),
            'challenges': f"Watch for {', '.join(md_effect.get('unfavorable', [])[:3])} during this period.",
            'keyAdvice': f"Focus on {', '.join(md_effect.get('favorable', [])[:3])}. Perform remedies for {cur_md['planet']} to maximize benefits.",
        },
    }
