from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import swisseph as swe
import pytz
from dateutil import parser

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status, sunrise_sunset,
    ayanamsa_value,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class VarshaphalRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    year: int = Field(2026, description="Target year for the annual return chart")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_local(date_str: str, time_str: str, tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    return tz.localize(parser.parse(f"{date_str} {time_str}"))


def _jd(dt_utc: datetime) -> float:
    y, m, d = dt_utc.year, dt_utc.month, dt_utc.day
    h = dt_utc.hour + dt_utc.minute / 60.0
    return swe.julday(y, m, d, h)


def _find_solar_return_jd(
    birth_jd: float,
    target_year: int,
    tz_name: str,
    lat: float,
    lon: float,
    node_mode: str,
) -> float:
    """Find exact JD when Sun returns to natal sidereal longitude in *target_year*.

    Strategy: compute natal Sun longitude, then do a coarse search (hour steps)
    through the target year followed by a bisection to ~1 second precision.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    # Natal Sun longitude (sidereal)
    xs, _ = swe.calc_ut(birth_jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    natal_sun_lon = xs[0]

    # Window: Jan 1 to Dec 31 of target year (UTC)
    tz = pytz.timezone(tz_name)
    jan1_local = tz.localize(datetime(target_year, 1, 1, 0, 0))
    dec31_local = tz.localize(datetime(target_year, 12, 31, 23, 59))
    jd_start = _jd(jan1_local.astimezone(pytz.utc))
    jd_end = _jd(dec31_local.astimezone(pytz.utc))

    def sun_lon(jd):
        xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        return xx[0]

    def ang_diff(a, b):
        d = (a - b) % 360.0
        return d if d <= 180.0 else d - 360.0

    # Coarse scan (6-hour steps)
    step = 6.0 / 24.0  # 6 hours in days
    jd = jd_start
    prev_diff = ang_diff(sun_lon(jd), natal_sun_lon)
    coarse_jd = None
    while jd <= jd_end:
        cur_diff = ang_diff(sun_lon(jd), natal_sun_lon)
        if prev_diff > 0 and cur_diff <= 0:
            # Crossing happened between jd-step and jd
            coarse_jd = jd
            break
        prev_diff = cur_diff
        jd += step

    if coarse_jd is None:
        # Fallback: closest match
        best_jd = jd_start
        best_abs = abs(ang_diff(sun_lon(jd_start), natal_sun_lon))
        jd = jd_start + step
        while jd <= jd_end:
            d = abs(ang_diff(sun_lon(jd), natal_sun_lon))
            if d < best_abs:
                best_abs = d
                best_jd = jd
            jd += step
        return best_jd

    # Bisection to ~1 second
    lo = coarse_jd - step
    hi = coarse_jd
    for _ in range(40):  # ~2^-40 * 86400 s < 1 μs
        mid = (lo + hi) / 2.0
        if ang_diff(sun_lon(mid), natal_sun_lon) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _calc_muntha(asc_sign: str, age_at_return: int) -> Dict[str, Any]:
    """Muntha: the house progressed from the natal ascendant (1 sign per year)."""
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    muntha_idx = (asc_idx + age_at_return) % 12
    muntha_sign = ZODIAC_SIGNS[muntha_idx]
    muntha_house = ((muntha_idx - asc_idx + 12) % 12) + 1
    return {
        'sign': muntha_sign,
        'house': muntha_house,
        'lord': SIGN_LORDS[muntha_sign],
        'yearsProgressed': age_at_return,
    }


def _detect_yogas(planets: list, asc_sign: str) -> list:
    res = []
    pmap = {p['name']: p for p in planets}
    asc_idx = ZODIAC_SIGNS.index(asc_sign)

    def in_kendra(p):
        return p.get('house', 0) in [1, 4, 7, 10]

    def in_trikona(p):
        return p.get('house', 0) in [1, 5, 9]

    def house_of(p):
        return p.get('house', 0)

    def sign_of(p):
        return p.get('sign', '')

    # Pancha Mahapurusha Yogas
    mahapurusha = {
        'Mars': ('Ruchaka', 'Mars in own/exalted sign in kendra'),
        'Mercury': ('Bhadra', 'Mercury in own/exalted sign in kendra'),
        'Jupiter': ('Hamsa', 'Jupiter in own/exalted sign in kendra'),
        'Venus': ('Malavya', 'Venus in own/exalted sign in kendra'),
        'Saturn': ('Shasha', 'Saturn in own/exalted sign in kendra'),
    }
    for pname in ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p and in_kendra(p) and planet_status(pname, sign_of(p)) in ('Exalted', 'Own Sign', 'Mooltrikona'):
            label, desc = mahapurusha[pname]
            res.append({'name': f'{label} Yoga', 'description': desc, 'strength': 'Strong'})

    # Gajakesari
    moon, jup = pmap.get('Moon'), pmap.get('Jupiter')
    if moon and jup and in_kendra(moon) and in_kendra(jup):
        res.append({'name': 'Gajakesari Yoga', 'description': 'Moon and Jupiter in mutual kendras', 'strength': 'Strong'})

    # Budha Aditya
    sun, mer = pmap.get('Sun'), pmap.get('Mercury')
    if sun and mer and sign_of(sun) == sign_of(mer):
        res.append({'name': 'Budha Aditya Yoga', 'description': 'Sun-Mercury conjunction', 'strength': 'Medium'})

    # Chandra Mangala
    mar = pmap.get('Mars')
    if moon and mar and sign_of(moon) == sign_of(mar):
        res.append({'name': 'Chandra Mangala Yoga', 'description': 'Moon-Mars conjunction', 'strength': 'Medium'})

    # Dhan Yoga
    ven = pmap.get('Venus')
    if jup and ven:
        if (in_kendra(jup) or in_trikona(jup)) and (in_kendra(ven) or in_trikona(ven)):
            res.append({'name': 'Dhana Yoga', 'description': 'Jupiter-Venus in kendra/trikona', 'strength': 'Strong'})

    # Amala Yoga
    if jup and in_kendra(jup) and house_of(jup) in [1, 4]:
        res.append({'name': 'Amala Yoga', 'description': 'Jupiter in 1st or 4th house', 'strength': 'Strong'})
    if ven and in_kendra(ven) and house_of(ven) in [1, 4]:
        res.append({'name': 'Amala Yoga', 'description': 'Venus in 1st or 4th house', 'strength': 'Strong'})

    # Saraswati
    if jup and ven and mer:
        all_kt = all(in_kendra(p) or in_trikona(p) for p in [jup, ven, mer])
        if all_kt:
            res.append({'name': 'Saraswati Yoga', 'description': 'Jupiter-Venus-Mercury in kendra/trikona', 'strength': 'Strong'})

    # Guru Chandal
    rahu = pmap.get('Rahu')
    if jup and rahu and sign_of(jup) == sign_of(rahu):
        res.append({'name': 'Guru Chandal Yoga', 'description': 'Jupiter-Rahu conjunction', 'strength': 'Malefic'})

    # Viparita Raja Yoga
    dusthana_lords = [p['name'] for p in planets if house_of(p) in [6, 8, 12]]
    if len(dusthana_lords) >= 2:
        res.append({'name': 'Viparita Raja Yoga', 'description': f"Lords of dusthana ({', '.join(dusthana_lords[:3])})", 'strength': 'Medium'})

    # Daridra Yoga
    second_lord_name = SIGN_LORDS[ZODIAC_SIGNS[(asc_idx + 1) % 12]]
    twelfth_lord_name = SIGN_LORDS[ZODIAC_SIGNS[(asc_idx + 11) % 12]]
    sl = pmap.get(second_lord_name)
    tl = pmap.get(twelfth_lord_name)
    if sl and tl and house_of(sl) in [6, 8, 12] and house_of(tl) in [6, 8, 12]:
        res.append({'name': 'Daridra Yoga', 'description': '2nd and 12th lords in dusthana', 'strength': 'Malefic'})

    # Deduplicate
    seen = set()
    unique = []
    for y in res:
        if y['name'] not in seen:
            seen.add(y['name'])
            unique.append(y)
    return unique


def _house_meaning(h: int) -> str:
    return {
        1: "Self, personality, health, new beginnings",
        2: "Wealth, family, speech, food",
        3: "Courage, siblings, communication, short travels",
        4: "Home, property, mother, comfort, vehicles",
        5: "Children, education, creativity, romance, intelligence",
        6: "Enemies, disease, service, competition, debt",
        7: "Marriage, partnership, business, travel, spouse",
        8: "Longevity, transformation, hidden matters, obstacles",
        9: "Luck, dharma, father, long travel, wisdom, spirituality",
        10: "Career, status, authority, karma, profession",
        11: "Gains, income, fulfillment, friends, elder siblings",
        12: "Losses, expenses, foreign lands, moksha, isolation",
    }.get(h, f"House {h}")


def _planet_house_prediction(planet: str, house: int) -> str:
    effects = {
        'Sun': {1: "Leadership and vitality shine this year. Recognition from authority.", 2: "Speech gains weight; financial growth through personal effort.", 3: "Courage increases; short travels and communication improve.", 4: "Domestic peace; property matters favored; mother's health needs attention.", 5: "Creative success; children prosper; intelligence sharpens.", 6: "Victory over enemies; health recovery; competitive success.", 7: "Marriage or partnership gains; business growth; spouse active.", 8: "Transformation year; hidden matters surface; longevity focus.", 9: "Spiritual growth; long travels; father's health; higher learning.", 10: "Career peak; authority increases; professional recognition.", 11: "Income growth; social network expands; wishes fulfilled.", 12: "Expenses rise; foreign travel possible; spiritual retreat favored."},
        'Moon': {1: "Emotional fulfillment; mind stays peaceful; new beginnings.", 2: "Family harmony; wealth through mother's side; speech becomes sweet.", 3: "Courage from emotions; siblings supportive.", 4: "Domestic happiness; inner peace; property acquisition.", 5: "Romantic fulfillment; children bring joy; creative inspiration.", 6: "Emotional health improves; enemies subdued.", 7: "Marriage harmony; partnership emotionally satisfying.", 8: "Emotional transformation; hidden fears surface and heal.", 9: "Emotional wisdom; spiritual inclinations deepen.", 10: "Public image rises; emotional career satisfaction.", 11: "Social circles expand; emotional fulfillment through friends.", 12: "Emotional withdrawal; spiritual healing; retreat needed."},
        'Mars': {1: "Energy and drive peak; physical vitality strong; assertive year.", 2: "Wealth through courage; speech becomes bold; family disputes possible.", 3: "Excellent for courage and initiative; siblings helpful.", 4: "Property disputes possible; domestic harmony tested; vehicle matters.", 5: "Romantic passion; children active; creative energy high.", 6: "Strong victory over enemies; competitive success; health robust.", 7: "Marriage conflicts possible; business partnerships tested.", 8: "Accidents possible; transformation through action; inheritance matters.", 9: "Courage in spiritual pursuits; long travel adventurous.", 10: "Career drive high; professional conflicts; authority asserted.", 11: "Income through effort; friends active; goals achieved.", 12: "Expenses through impulsiveness; foreign travel; anger management needed."},
        'Mercury': {1: "Communication skills improve; intellectual pursuits favored.", 2: "Financial gains through intellect; speech becomes eloquent.", 3: "Excellent for writing, communication; short travels productive.", 4: "Property through intellect; domestic harmony; vehicle purchase.", 5: "Education success; creative writing; children excel.", 6: "Victory through intelligence; health good; competitive exams.", 7: "Business partnerships thrive; spouse communicative; social gains.", 8: "Research success; hidden knowledge uncovered; transformation through learning.", 9: "Higher education; philosophical inclinations; long travel enriching.", 10: "Career through communication; business expands; professional reputation grows.", 11: "Income through communication; social network grows.", 12: "Expenses on education; foreign studies; intellectual retreat."},
        'Jupiter': {1: "Wisdom expands; spiritual growth; health improves; good fortune.", 2: "Wealth increases; family prosperity; speech becomes authoritative.", 3: "Courage with wisdom; siblings benefit; short travels spiritual.", 4: "Property acquisition; domestic bliss; mother blessed.", 5: "Children prosper; education excellent; creative wisdom.", 6: "Victory over obstacles; health recovers; enemies convert.", 7: "Marriage blessed; partnership harmonious; spouse supportive.", 8: "Spiritual transformation; hidden wisdom; longevity blessed.", 9: "Peak fortune; spiritual growth; father blessed; higher learning.", 10: "Career blessed; authority increases; professional peak.", 11: "Income grows; social status rises; wishes fulfilled.", 12: "Expenses on charity; spiritual retreat; foreign travel blessed."},
        'Venus': {1: "Charm and beauty increase; luxury comes; artistic pursuits.", 2: "Wealth through arts; family harmony; eloquent speech.", 3: "Courage in creative pursuits; siblings supportive of arts.", 4: "Domestic luxury; property beautification; vehicle upgrade.", 5: "Romance peaks; creative success; children artistic.", 6: "Victory through charm; health good; competitive diplomacy.", 7: "Marriage blissful; partnerships harmonious; spouse charming.", 8: "Hidden pleasures; transformation through love; inheritance through spouse.", 9: "Spiritual beauty; artistic wisdom; long travel romantic.", 10: "Career through arts; professional charm; public image beautiful.", 11: "Income through arts; social gains; luxury income.", 12: "Expenses on luxury; romantic retreat; artistic isolation."},
        'Saturn': {1: "Discipline increases; health requires attention; maturity tested.", 2: "Wealth through patience; family responsibilities; speech measured.", 3: "Courage tested; siblings need help; communication delayed.", 4: "Domestic responsibilities; property maintenance; mother's health.", 5: "Children need guidance; creative discipline; education requires patience.", 6: "Victory through perseverance; health recovery slow; competition won.", 7: "Marriage tested; partnership requires patience; spouse disciplined.", 8: "Transformation through hardship; hidden obstacles; longevity focus.", 9: "Spiritual discipline; father's health; wisdom through patience.", 10: "Career through hard work; authority tested; professional discipline.", 11: "Income through persistence; social responsibility; slow gains.", 12: "Expenses controlled; spiritual retreat; isolation for growth."},
        'Rahu': {1: "Unconventional beginnings; identity transformation; ambitious year.", 2: "Unusual wealth gains; speech becomes unconventional; family changes.", 3: "Courage through unconventional means; siblings unusual.", 4: "Property through unconventional means; domestic changes.", 5: "Unconventional romance; children surprising; creative breakthrough.", 6: "Victory through unconventional methods; health unusual.", 7: "Unconventional partnership; spouse unique; business breakthrough.", 8: "Hidden transformation; unconventional obstacles; sudden changes.", 9: "Unconventional spirituality; foreign travel; philosophical breakthrough.", 10: "Unconventional career; professional transformation; authority challenged.", 11: "Unconventional income; social network expands unexpectedly.", 12: "Expenses on foreign matters; unconventional retreat; spiritual awakening."},
        'Ketu': {1: "Spiritual detachment; past-life karma resolved; inner peace.", 2: "Wealth through detachment; family karma; speech spiritual.", 3: "Courage through letting go; siblings spiritual.", 4: "Domestic detachment; property through past karma.", 5: "Spiritual children; creative detachment; past-life talent.", 6: "Victory through surrender; health through letting go.", 7: "Spiritual partnership; spouse detached; karmic marriage.", 8: "Deep transformation; past-life resolution; spiritual liberation.", 9: "Peak spiritual growth; detachment from material; wisdom.", 10: "Career through spiritual service; authority through humility.", 11: "Income through spiritual means; friends spiritual.", 12: "Peak detachment; spiritual liberation; foreign lands."},
    }
    return effects.get(planet, {}).get(house, f"{planet} in house {house} brings mixed results.")


def _muntha_prediction(muntha_house: int) -> str:
    effects = {
        1: "Year of self-focus. New identity, health improvements, personal initiatives thrive.",
        2: "Wealth and family focus. Financial gains increase; speech matters prominent.",
        3: "Communication and courage year. Siblings helpful; short travels frequent.",
        4: "Home and property focus. Domestic peace; vehicle or property acquisition.",
        5: "Creativity and children focus. Education, romance, and progeny matters peak.",
        6: "Victory and competition. Enemies defeated; health improves; service gains.",
        7: "Partnership and marriage focus. Business growth; spouse prominent.",
        8: "Transformation year. Hidden matters surface; inheritance; deep changes.",
        9: "Spiritual and wisdom year. Long travel; father's role; higher learning.",
        10: "Career peak year. Professional success; authority and status rise.",
        11: "Gains and fulfillment. Income grows; social network expands; wishes come true.",
        12: "Expenses and detachment. Foreign travel; spiritual retreat; costs increase.",
    }
    return effects.get(muntha_house, f"Muntha in house {muntha_house} brings mixed results.")


def _tajika_aspect_type(lon1: float, lon2: float) -> Optional[Dict[str, Any]]:
    diff = (lon1 - lon2) % 360.0
    if diff > 180:
        diff = 360 - diff

    aspects = [
        (0, 1, 'Conjunction (0°)', 'Strong influence, fusion of energies', 'Neutral'),
        (6, 2, 'Sextile (60°)', 'Harmonious, opportunities, easy flow', 'Benefic'),
        (8, 2, 'Semi-Square (45°)', 'Minor tension, irritation, adjustment needed', 'Mild Malefic'),
        (12, 2, 'Semi-Sextile (30°)', 'Minor harmony, subtle support', 'Mild Benefic'),
        (15, 2, 'Sesqui-Quadrature (135°)', 'Tension requiring adjustment', 'Mild Malefic'),
        (30, 0, 'Trine (120°)', 'Flowing energy, natural harmony, blessings', 'Benefic'),
        (45, 0, 'Square (90°)', 'Tension, action required, growth through friction', 'Malefic'),
        (60, 0, 'Opposition (180°)', 'Awareness, polarity, confrontation and balance', 'Mixed'),
    ]

    best = None
    best_orb = 999
    for base_orb, default_orb, name, effect, nature in aspects:
        orb = base_orb / 2.0 if base_orb > 0 else default_orb
        if abs(diff - base_orb) <= orb:
            actual_orb = abs(diff - base_orb)
            if actual_orb < best_orb:
                best_orb = actual_orb
                best = {
                    'aspect': name,
                    'exactDegree': round(diff, 4),
                    'orb': round(actual_orb, 4),
                    'nature': nature,
                    'effect': effect,
                }
    return best


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/horoscope/varshaphal')
def varshaphal_chart(body: VarshaphalRequest) -> Dict[str, Any]:
    """Annual Solar Return (Varshaphal) chart for the target year."""

    birth_jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    sr_jd = _find_solar_return_jd(
        birth_jd, body.year, body.timezone,
        body.latitude, body.longitude, body.nodeMode,
    )

    # Age at return (years between birth and solar return)
    birth_dt = _parse_local(body.dateOfBirth, body.timeOfBirth, body.timezone)
    tz = pytz.timezone(body.timezone)
    sr_y, sr_m, sr_d, sr_ut = swe.revjul(sr_jd)
    sr_hours = int(sr_ut)
    sr_mins = int(round((sr_ut - sr_hours) * 60))
    sr_dt_utc = datetime(sr_y, sr_m, sr_d, sr_hours, sr_mins, tzinfo=pytz.utc)
    sr_dt_local = sr_dt_utc.astimezone(tz)
    age_at_return = sr_dt_local.year - birth_dt.year

    # Calculate planets for the solar return moment
    planets = calc_planets(sr_jd, None, body.nodeMode)
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    # Calculate houses at the birth location for the SR moment
    house_data = calc_houses(sr_jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')

    asc_sign = house_data['ascendant']['sign']

    # Muntha
    muntha = _calc_muntha(asc_sign, age_at_return)

    # Yogas
    yogas = _detect_yogas(planets, asc_sign)

    # Natal comparison
    natal_planets = calc_planets(birth_jd, None, body.nodeMode)
    natal_map = {p['name']: p for p in natal_planets}

    # Key predictions based on planet placements
    predictions = []
    for p in planets:
        if p['name'] in ('Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto'):
            continue
        predictions.append({
            'planet': p['name'],
            'house': p['house'],
            'sign': p['sign'],
            'dignity': p['houseStatus'],
            'isRetrograde': p['isRetrograde'],
            'prediction': _planet_house_prediction(p['name'], p['house']),
            'natalHouse': natal_map.get(p['name'], {}).get('house', 0),
        })

    # Muntha effects
    muntha_effect = {
        'position': muntha,
        'prediction': _muntha_prediction(muntha['house']),
    }

    # Muntha lord effects
    muntha_lord = SIGN_LORDS[muntha['sign']]
    muntha_lord_p = next((p for p in planets if p['name'] == muntha_lord), None)
    if muntha_lord_p:
        muntha_effect['lordPosition'] = {
            'house': muntha_lord_p['house'],
            'sign': muntha_lord_p['sign'],
        }
        muntha_effect['lordPrediction'] = (
            f"Muntha lord {muntha_lord} in house {muntha_lord_p['house']} "
            f"({muntha_lord_p['sign']}) — {_planet_house_prediction(muntha_lord, muntha_lord_p['house'])}"
        )

    # Solar return date info
    return_date_info = {
        'date': sr_dt_local.strftime('%Y-%m-%d'),
        'time': sr_dt_local.strftime('%H:%M:%S'),
        'timezone': body.timezone,
        'ageAtReturn': age_at_return,
    }

    # Ascendant info
    asc_info = house_data['ascendant']
    asc_info['signLord'] = SIGN_LORDS[asc_info['sign']]
    asc_info['pada'] = get_nakshatra(asc_info['degree'])['pada']

    return {
        'success': True,
        'data': {
            'returnDate': return_date_info,
            'ascendant': asc_info,
            'planets': planets,
            'houses': house_data['houses'],
            'muntha': muntha_effect,
            'yogas': yogas,
            'predictions': predictions,
            'yearSummary': _generate_year_summary(planets, muntha, yogas, asc_sign),
        }
    }


def _generate_year_summary(planets: list, muntha: dict, yogas: list, asc_sign: str) -> str:
    pmap = {p['name']: p for p in planets}
    jup = pmap.get('Jupiter')
    sat = pmap.get('Saturn')
    sun = pmap.get('Sun')
    moon = pmap.get('Moon')

    parts = []
    parts.append(f"The {asc_sign} Ascendant solar return chart themes around {_house_meaning(1).split('.')[0].lower()}.")

    if jup and jup.get('house') in [1, 5, 9, 11]:
        parts.append("Jupiter blesses key houses — expansion and good fortune are indicated.")
    elif jup and jup.get('house') in [6, 8, 12]:
        parts.append("Jupiter in dusthana — spiritual growth through challenges; avoid overindulgence.")

    if sat and sat.get('house') in [1, 4, 7, 10]:
        parts.append("Saturn in kendra — discipline brings structural stability this year.")
    elif sat and sat.get('house') in [3, 6, 11]:
        parts.append("Saturn in upachaya — gradual gains through persistent effort.")

    strong_yogas = [y for y in yogas if y['strength'] in ('Strong', 'Very Strong')]
    if strong_yogas:
        parts.append(f"Key yogas: {', '.join(y['name'] for y in strong_yogas[:3])} strengthen the year.")

    parts.append(f"Muntha in house {muntha['house']} ({muntha['sign']}) — {_muntha_prediction(muntha['house']).split('.')[0].lower()}.")

    return ' '.join(parts)


# ---------------------------------------------------------------------------
# Monthly prediction endpoint
# ---------------------------------------------------------------------------

def _tajika_monthly_aspects(planets: list, target_year: int, tz_name: str, lat: float, lon: float) -> List[Dict[str, Any]]:
    """Compute Tajika aspects for each month (1st of each month) of the target year."""
    tz = pytz.timezone(tz_name)
    monthly = []

    for month in range(1, 13):
        month_start = tz.localize(datetime(target_year, month, 1, 12, 0))
        jd_month = _jd(month_start.astimezone(pytz.utc))

        month_planets = calc_planets(jd_month, None, 'mean')

        aspects_this_month = []
        for i, p1 in enumerate(month_planets):
            if p1['name'] in ('Uranus', 'Neptune', 'Pluto'):
                continue
            for p2 in month_planets[i + 1:]:
                if p2['name'] in ('Uranus', 'Neptune', 'Pluto'):
                    continue
                asp = _tajika_aspect_type(p1['longitude'], p2['longitude'])
                if asp:
                    aspects_this_month.append({
                        'planet1': p1['name'],
                        'planet2': p2['name'],
                        **asp,
                    })

        monthly.append({
            'month': month,
            'monthName': datetime(target_year, month, 1).strftime('%B'),
            'aspects': sorted(aspects_this_month, key=lambda a: a.get('orb', 99)),
        })

    return monthly


@router.post('/horoscope/varshaphal/prediction')
def varshaphal_prediction(body: VarshaphalRequest) -> Dict[str, Any]:
    """Detailed year prediction with monthly Tajika breakdown."""

    birth_jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    sr_jd = _find_solar_return_jd(
        birth_jd, body.year, body.timezone,
        body.latitude, body.longitude, body.nodeMode,
    )

    birth_dt = _parse_local(body.dateOfBirth, body.timeOfBirth, body.timezone)
    tz = pytz.timezone(body.timezone)
    sr_y, sr_m, sr_d, sr_ut = swe.revjul(sr_jd)
    sr_hours = int(sr_ut)
    sr_mins = int(round((sr_ut - sr_hours) * 60))
    sr_dt_utc = datetime(sr_y, sr_m, sr_d, sr_hours, sr_mins, tzinfo=pytz.utc)
    sr_dt_local = sr_dt_utc.astimezone(tz)
    age_at_return = sr_dt_local.year - birth_dt.year

    planets = calc_planets(sr_jd, None, body.nodeMode)
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    house_data = calc_houses(sr_jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    asc_sign = house_data['ascendant']['sign']
    muntha = _calc_muntha(asc_sign, age_at_return)
    yogas = _detect_yogas(planets, asc_sign)

    # Monthly breakdown
    monthly_data = _tajika_monthly_aspects(planets, body.year, body.timezone, body.latitude, body.longitude)

    # Generate month-by-month predictions
    month_predictions = []
    for md in monthly_data:
        month_num = md['month']
        month_name = md['monthName']

        benefic_aspects = [a for a in md['aspects'] if a['nature'] in ('Benefic', 'Mild Benefic')]
        malefic_aspects = [a for a in md['aspects'] if a['nature'] in ('Malefic', 'Mild Malefic')]

        if len(benefic_aspects) > len(malefic_aspects):
            tone = 'positive'
            outlook = 'Overall favorable — benefic influences outweigh challenges.'
        elif len(malefic_aspects) > len(benefic_aspects):
            tone = 'challenging'
            outlook = 'Caution advised — malefic aspects require careful navigation.'
        else:
            tone = 'mixed'
            outlook = 'Mixed influences — balance between opportunity and challenge.'

        key_themes = []
        for a in md['aspects'][:5]:
            key_themes.append(f"{a['planet1']}-{a['planet2']} {a['aspect'].split('(')[0].strip()}")

        month_predictions.append({
            'month': month_num,
            'monthName': month_name,
            'tone': tone,
            'outlook': outlook,
            'keyAspects': key_themes,
            'beneficCount': len(benefic_aspects),
            'maleficCount': len(malefic_aspects),
            'detailedAspects': md['aspects'],
        })

    # Overall year predictions
    overall = {
        'career': _generate_domain_prediction('career', planets, muntha, house_data),
        'finance': _generate_domain_prediction('finance', planets, muntha, house_data),
        'health': _generate_domain_prediction('health', planets, muntha, house_data),
        'relationship': _generate_domain_prediction('relationship', planets, muntha, house_data),
        'spirituality': _generate_domain_prediction('spirituality', planets, muntha, house_data),
        'travel': _generate_domain_prediction('travel', planets, muntha, house_data),
    }

    return {
        'success': True,
        'data': {
            'returnDate': {
                'date': sr_dt_local.strftime('%Y-%m-%d'),
                'time': sr_dt_local.strftime('%H:%M:%S'),
                'ageAtReturn': age_at_return,
            },
            'ascendant': {**house_data['ascendant'], 'signLord': SIGN_LORDS[asc_sign]},
            'muntha': muntha,
            'overallPredictions': overall,
            'monthlyPredictions': month_predictions,
            'yogas': yogas,
        }
    }


def _generate_domain_prediction(domain: str, planets: list, muntha: dict, house_data: dict) -> Dict[str, str]:
    pmap = {p['name']: p for p in planets}
    asc_sign = house_data['ascendant']['sign']

    domain_houses = {
        'career': {'primary': [10], 'secondary': [2, 6, 11], 'planets': ['Sun', 'Saturn', 'Mercury', 'Jupiter']},
        'finance': {'primary': [2, 11], 'secondary': [1, 5, 9], 'planets': ['Jupiter', 'Venus', 'Mercury', 'Sun']},
        'health': {'primary': [1, 6, 8], 'secondary': [3, 12], 'planets': ['Sun', 'Mars', 'Saturn', 'Moon']},
        'relationship': {'primary': [7, 5], 'secondary': [2, 4, 11], 'planets': ['Venus', 'Moon', 'Jupiter', 'Mars']},
        'spirituality': {'primary': [9, 12], 'secondary': [1, 5, 8], 'planets': ['Jupiter', 'Ketu', 'Saturn', 'Moon']},
        'travel': {'primary': [3, 7, 9, 12], 'secondary': [1, 4], 'planets': ['Jupiter', 'Rahu', 'Moon', 'Mercury']},
    }

    info = domain_houses.get(domain, domain_houses['career'])
    score = 0
    notes = []

    for pname in info['planets']:
        p = pmap.get(pname)
        if not p:
            continue
        h = p.get('house', 0)
        dignity = p.get('houseStatus', 'Neutral')
        if h in info['primary']:
            score += 3
            if dignity in ('Exalted', 'Own Sign', 'Mooltrikona'):
                score += 2
                notes.append(f"{pname} strongly placed in {h}th house ({dignity})")
            elif dignity == 'Friendly':
                score += 1
                notes.append(f"{pname} in {h}th house, friendly disposition")
            else:
                notes.append(f"{pname} in {h}th house ({dignity})")
        elif h in info['secondary']:
            score += 1
            notes.append(f"{pname} in {h}th house supporting {domain}")

    if muntha['house'] in info['primary']:
        score += 2
        notes.append(f"Muntha in {muntha['house']}th house supports {domain}")

    if score >= 10:
        strength = 'Excellent'
        summary = f"Outstanding prospects for {domain} this year. Multiple strong planetary supports."
    elif score >= 6:
        strength = 'Good'
        summary = f"Favorable conditions for {domain}. Steady progress expected with some effort."
    elif score >= 3:
        strength = 'Moderate'
        summary = f"Average outlook for {domain}. Mixed results; focus and patience required."
    elif score >= 1:
        strength = 'Challenging'
        summary = f"Challenging period for {domain}. Careful planning and remedies recommended."
    else:
        strength = 'Difficult'
        summary = f"Difficult period for {domain}. Remedies and persistence essential."

    return {
        'domain': domain.title(),
        'strength': strength,
        'score': score,
        'summary': summary,
        'notes': notes,
    }


# ---------------------------------------------------------------------------
# Tajika aspects endpoint
# ---------------------------------------------------------------------------

@router.post('/horoscope/varshaphal/tajika-aspects')
def varshaphal_tajika_aspects(body: VarshaphalRequest) -> Dict[str, Any]:
    """Return all Tajika (annual) aspects between planets for the solar return chart."""

    birth_jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    sr_jd = _find_solar_return_jd(
        birth_jd, body.year, body.timezone,
        body.latitude, body.longitude, body.nodeMode,
    )

    birth_dt = _parse_local(body.dateOfBirth, body.timeOfBirth, body.timezone)
    tz = pytz.timezone(body.timezone)
    sr_y, sr_m, sr_d, sr_ut = swe.revjul(sr_jd)
    sr_hours = int(sr_ut)
    sr_mins = int(round((sr_ut - sr_hours) * 60))
    sr_dt_utc = datetime(sr_y, sr_m, sr_d, sr_hours, sr_mins, tzinfo=pytz.utc)
    sr_dt_local = sr_dt_utc.astimezone(tz)
    age_at_return = sr_dt_local.year - birth_dt.year

    planets = calc_planets(sr_jd, None, body.nodeMode)
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    house_data = calc_houses(sr_jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    asc_sign = house_data['ascendant']['sign']
    muntha = _calc_muntha(asc_sign, age_at_return)

    # Compute all pairwise Tajika aspects
    all_aspects = []
    classical_planets = [p for p in planets if p['name'] not in ('Uranus', 'Neptune', 'Pluto')]

    for i, p1 in enumerate(classical_planets):
        for p2 in classical_planets[i + 1:]:
            asp = _tajika_aspect_type(p1['longitude'], p2['longitude'])
            if asp:
                all_aspects.append({
                    'planet1': p1['name'],
                    'planet2': p2['name'],
                    'planet1Sign': p1['sign'],
                    'planet2Sign': p2['sign'],
                    'planet1House': p1.get('house', 0),
                    'planet2House': p2.get('house', 0),
                    **asp,
                })

    # Sort by orb (tightest first)
    all_aspects.sort(key=lambda a: a.get('orb', 99))

    # Summary
    benefic = [a for a in all_aspects if a['nature'] == 'Benefic']
    malefic = [a for a in all_aspects if a['nature'] == 'Malefic']
    neutral = [a for a in all_aspects if a['nature'] == 'Neutral']
    mixed = [a for a in all_aspects if a['nature'] == 'Mixed']

    # Tajika Sahams (annual points)
    sahams = {}
    for p in classical_planets:
        sahams[p['name']] = {
            'longitude': p['longitude'],
            'sign': p['sign'],
            'house': p.get('house', 0),
            'dignity': p['houseStatus'],
        }

    # Tajika Ithasala chart (aspect-based predictions)
    ithasala_pairs = []
    for a in all_aspects:
        if a['orb'] < 5:  # Only tight aspects (within 5 degrees)
            ithasala_pairs.append({
                'planets': f"{a['planet1']}-{a['planet2']}",
                'aspect': a['aspect'],
                'nature': a['nature'],
                'effect': a['effect'],
                'house1': a['planet1House'],
                'house2': a['planet2House'],
            })

    return {
        'success': True,
        'data': {
            'returnDate': {
                'date': sr_dt_local.strftime('%Y-%m-%d'),
                'time': sr_dt_local.strftime('%H:%M:%S'),
                'ageAtReturn': age_at_return,
            },
            'ascendant': {**house_data['ascendant'], 'signLord': SIGN_LORDS[asc_sign]},
            'muntha': muntha,
            'aspects': all_aspects,
            'summary': {
                'totalAspects': len(all_aspects),
                'benefic': len(benefic),
                'malefic': len(malefic),
                'neutral': len(neutral),
                'mixed': len(mixed),
            },
            'tajikaSahams': sahams,
            'ithasalaChart': ithasala_pairs,
        }
    }
