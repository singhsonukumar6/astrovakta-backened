from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime, timedelta
import swisseph as swe
import pytz
from dateutil import parser
import json
import os
import math
import logging

app = FastAPI(title="Vedic Astrology API (Python)", version="1.0.0")

# Routers
try:
    from .routers.chart_svg import router as chart_svg_router
    app.include_router(chart_svg_router, prefix="/chart")
except Exception as e:
    import logging as _logging
    _logging.error(f"Failed to include chart SVG router: {e}")

# Grid-style chart router (South-Indian-like example grid)
try:
    from .routers.chart_grid import router as chart_grid_router
    app.include_router(chart_grid_router, prefix="/chart")
except Exception as e:
    import logging as _logging2
    _logging2.error(f"Failed to include chart GRID router: {e}")

# Dasha router
try:
    from .routers.dasha import router as dasha_router
    app.include_router(dasha_router, prefix="/horoscope")
except Exception as e:
    import logging as _logging3
    _logging3.error(f"Failed to include DASHA router: {e}")

# Chara Dasha router
try:
    from .routers.dasha_chara import router as dasha_chara_router
    app.include_router(dasha_chara_router, prefix="/horoscope")
except Exception as e:
    import logging as _logging3b
    _logging3b.error(f"Failed to include CHARA DASHA router: {e}")

# Dosha router
try:
    from .routers.dosha import router as dosha_router
    app.include_router(dosha_router, prefix="/horoscope")
except Exception as e:
    import logging as _logging4
    _logging4.error(f"Failed to include DOSHA router: {e}")

# Panchang router
try:
    from .routers.panchang import router as panchang_router
    app.include_router(panchang_router, prefix="/horoscope")
except Exception as e:
    import logging as _logging5
    _logging5.error(f"Failed to include PANCHANG router: {e}")

ZODIAC_SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]

SIGN_LORDS = {
    'Aries': 'Mars','Taurus': 'Venus','Gemini': 'Mercury','Cancer': 'Moon',
    'Leo': 'Sun','Virgo': 'Mercury','Libra': 'Venus','Scorpio': 'Mars',
    'Sagittarius': 'Jupiter','Capricorn': 'Saturn','Aquarius': 'Saturn','Pisces': 'Jupiter'
}

NAKSHATRAS = [
    ('Ashwini','Ketu',0,13.333333),('Bharani','Venus',13.333333,26.666667),('Krittika','Sun',26.666667,40),
    ('Rohini','Moon',40,53.333333),('Mrigashira','Mars',53.333333,66.666667),('Ardra','Rahu',66.666667,80),
    ('Punarvasu','Jupiter',80,93.333333),('Pushya','Saturn',93.333333,106.666667),('Ashlesha','Mercury',106.666667,120),
    ('Magha','Ketu',120,133.333333),('Purva Phalguni','Venus',133.333333,146.666667),('Uttara Phalguni','Sun',146.666667,160),
    ('Hasta','Moon',160,173.333333),('Chitra','Mars',173.333333,186.666667),('Swati','Rahu',186.666667,200),
    ('Vishakha','Jupiter',200,213.333333),('Anuradha','Saturn',213.333333,226.666667),('Jyeshtha','Mercury',226.666667,240),
    ('Mula','Ketu',240,253.333333),('Purva Ashadha','Venus',253.333333,266.666667),('Uttara Ashadha','Sun',266.666667,280),
    ('Shravana','Moon',280,293.333333),('Dhanishta','Mars',293.333333,306.666667),('Shatabhisha','Rahu',306.666667,320),
    ('Purva Bhadrapada','Jupiter',320,333.333333),('Uttara Bhadrapada','Saturn',333.333333,346.666667),('Revati','Mercury',346.666667,360)
]

# Load Vedic properties (nakshatra table) from JSON
def load_vedic_properties() -> Dict[str, Any]:
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'vedic_properties.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load vedic_properties.json: {e}")
        return {}

NAKSHATRA_PROPERTIES = load_vedic_properties()

PLANET_IDS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
    'Rahu': swe.MEAN_NODE,
    'Ketu': swe.MEAN_NODE,
}

COMBUSTION_DIST = {'Moon':12,'Mars':17,'Mercury':14,'Jupiter':11,'Venus':10,'Saturn':15}

PLANET_PROPS = {
    'Sun':     {'exalted':'Aries','exDeg':10,'debil':'Libra','debilDeg':10,'own':['Leo'],'mool':'Leo','friends':['Moon','Mars','Jupiter'],'enemies':['Venus','Saturn'],'neutral':['Mercury']},
    'Moon':    {'exalted':'Taurus','exDeg':3,'debil':'Scorpio','debilDeg':3,'own':['Cancer'],'mool':'Taurus','friends':['Sun','Mercury'],'enemies':[],'neutral':['Mars','Jupiter','Venus','Saturn']},
    'Mars':    {'exalted':'Capricorn','exDeg':28,'debil':'Cancer','debilDeg':28,'own':['Aries','Scorpio'],'mool':'Aries','friends':['Sun','Moon','Jupiter'],'enemies':['Mercury'],'neutral':['Venus','Saturn']},
    'Mercury': {'exalted':'Virgo','exDeg':15,'debil':'Pisces','debilDeg':15,'own':['Gemini','Virgo'],'mool':'Virgo','friends':['Sun','Venus'],'enemies':['Moon','Mars'],'neutral':['Jupiter','Saturn']},
    'Jupiter': {'exalted':'Cancer','exDeg':5,'debil':'Capricorn','debilDeg':5,'own':['Sagittarius','Pisces'],'mool':'Sagittarius','friends':['Sun','Moon','Mars'],'enemies':['Mercury','Venus'],'neutral':['Saturn']},
    'Venus':   {'exalted':'Pisces','exDeg':27,'debil':'Virgo','debilDeg':27,'own':['Taurus','Libra'],'mool':'Libra','friends':['Mercury','Saturn'],'enemies':['Sun','Moon'],'neutral':['Mars','Jupiter']},
    'Saturn':  {'exalted':'Libra','exDeg':20,'debil':'Aries','debilDeg':20,'own':['Capricorn','Aquarius'],'mool':'Aquarius','friends':['Mercury','Venus'],'enemies':['Sun','Moon','Mars'],'neutral':['Jupiter']},
}

DASHA_YEARS = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}
DASHA_SEQUENCE = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']

TITHI_NAMES = [
    'Pratipada','Dwitiya','Tritiya','Chaturthi','Panchami','Shashthi','Saptami','Ashtami','Navami','Dashami',
    'Ekadashi','Dwadashi','Trayodashi','Chaturdashi','Purnima','Pratipada','Dwitiya','Tritiya','Chaturthi','Panchami',
    'Shashthi','Saptami','Ashtami','Navami','Dashami','Ekadashi','Dwadashi','Trayodashi','Chaturdashi','Amavasya'
]
YOGA_NAMES = [
    'Vishkambha','Priti','Ayushman','Saubhagya','Shobhana','Atiganda','Sukarma','Dhriti','Shoola','Ganda','Vriddhi','Dhruva','Vyaghata','Harshana','Vajra','Siddhi','Vyatipata','Variyan','Parigha','Shiva','Siddhartha','Sadhya','Shubha','Shukla','Brahma','Indra','Vaidhriti'
]
KARANA_SEQUENCE = ['Bava','Balava','Kaulava','Taitila','Garaja','Vanija','Vishti','Shakuni','Chatushpada','Naga','Kimstughna']

class BirthDetails(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    propertyProfile: Optional[str] = Field(None, example=None)
    propertySource: Optional[Literal['moon','ascendant','sunriseMoon']] = Field('moon', example='moon')
    houseSystem: Optional[Literal['P','W']] = Field('W', example='W')
    nodeMode: Optional[Literal['mean','true']] = Field('mean', example='mean')
    debug: Optional[bool] = Field(False, example=False)


def to_julian(date_str: str, time_str: str, tz_name: str) -> float:
    dt_local = parser.parse(f"{date_str} {time_str}")
    tz = pytz.timezone(tz_name)
    dt_local = tz.localize(dt_local)
    dt_utc = dt_local.astimezone(pytz.utc)
    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
    hour = dt_utc.hour + dt_utc.minute/60
    return swe.julday(year, month, day, hour)


def get_sign(lon: float) -> str:
    return ZODIAC_SIGNS[int(lon // 30) % 12]


def get_nakshatra(lon: float):
    for name, lord, start, end in NAKSHATRAS:
        if start <= lon < end:
            span = end - start
            pos = lon - start
            pada = int((pos / span) * 4) + 1
            return {'name': name, 'lord': lord, 'pada': pada}
    return {'name':'Unknown','lord':'Unknown','pada':1}


def ayanamsa_value(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return swe.get_ayanamsa(jd)


def to_dms(x: float) -> str:
    s = -1 if x < 0 else 1
    x = abs(x)
    d = int(x)
    m = int((x - d)*60)
    sec = int(round(((x - d)*60 - m)*60))
    sign = '-' if s < 0 else ''
    return f"{sign}{d}°{m}′{sec}″"


def get_avastha(deg_in_sign: float, sign: str) -> str:
    idx = max(0, min(4, int(deg_in_sign // 6)))
    odd = sign in ['Aries','Gemini','Leo','Libra','Sagittarius','Aquarius']
    odd_order = ['Infant (Bala)','Young (Kumara)','Youth (Yuva)','Old (Vriddha)','Dead (Mrita)']
    even_order = list(reversed(odd_order))
    return (odd_order if odd else even_order)[idx]


def is_combust(name: str, lon: float, sun_lon: float, retro: bool) -> bool:
    if name in ['Sun','Rahu','Ketu','Uranus','Neptune','Pluto']:
        return False
    dist = abs(lon - sun_lon)
    dist = min(dist, 360 - dist)
    c = COMBUSTION_DIST.get(name)
    if not c:
        return False
    if name == 'Mercury' and retro:
        c = 12
    if name == 'Venus' and retro:
        c = 8
    return dist < c


def calc_planets(jd: float, profile: Optional[str], node_mode: str):
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    planets = []
    sun_lon = None
    for pname, pid in PLANET_IDS.items():
        if pname in ['Rahu','Ketu']:
            pid = swe.TRUE_NODE if node_mode == 'true' else swe.MEAN_NODE
        xx, rf = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
        lon, lat, dist, lon_spd, lat_spd, dist_spd = xx[0], xx[1], xx[2], xx[3], xx[4], xx[5]
        if pname == 'Ketu':
            lon = (lon + 180) % 360
        if pname == 'Sun' and sun_lon is None:
            sun_lon = lon
        sign = get_sign(lon)
        deg_in_sign = lon % 30
        nk = get_nakshatra(lon)
        retro = lon_spd < 0
        avastha = get_avastha(deg_in_sign, sign)
        planets.append({
            'name': pname,
            'longitude': lon,
            'latitude': lat,
            'speed': lon_spd,
            'degree': deg_in_sign,
            'degreeDMS': to_dms(deg_in_sign),
            'longitudeDMS': to_dms(lon),
            'sign': sign,
            'signLord': SIGN_LORDS[sign],
            'nakshatra': nk['name'],
            'nakshatraLord': nk['lord'],
            'nakshatraPada': nk['pada'],
            'house': 0,
            'isRetrograde': retro and pname not in ['Sun','Moon'],
            'isCombust': False,
            'avastha': avastha,
            'houseStatus': None,
        })
    # combustion
    if sun_lon is not None:
        for p in planets:
            if p['name'] != 'Sun':
                p['isCombust'] = is_combust(p['name'], p['longitude'], sun_lon, p['isRetrograde'])
    return planets


def calc_houses(jd: float, lat: float, lon: float, planets: list, house_system: str):
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    hsys = (house_system or 'P').encode('ascii')
    cusps, ascmc = swe.houses_ex(jd, lat, lon, hsys, swe.FLG_SIDEREAL)
    asc_deg = ascmc[0]
    asc_sign = get_sign(asc_deg)
    asc_nk = get_nakshatra(asc_deg)

    if house_system == 'W':
        asc_idx = ZODIAC_SIGNS.index(asc_sign)
        hs = []
        for i in range(12):
            sidx = (asc_idx + i) % 12
            sname = ZODIAC_SIGNS[sidx]
            hs.append({'number': i+1, 'sign': sname, 'signLord': SIGN_LORDS[sname], 'degree': sidx*30, 'planets': []})
        for p in planets:
            psidx = ZODIAC_SIGNS.index(p['sign'])
            hnum = ((psidx - asc_idx + 12) % 12) + 1
            p['house'] = hnum
            hs[hnum-1]['planets'].append(p['name'])
    else:
        # Normalize cusps to a 0-based 12-length list for safe indexing
        cusps_list = list(cusps)
        if len(cusps_list) >= 13:
            cusps12 = cusps_list[1:13]
        else:
            cusps12 = cusps_list[0:12]

        hs = []
        for i in range(12):
            cusp = cusps12[i]
            sname = get_sign(cusp)
            plist = []
            nxt = cusps12[(i + 1) % 12]
            for p in planets:
                inside = (p['longitude'] >= cusp and p['longitude'] < nxt) if nxt > cusp else (p['longitude'] >= cusp or p['longitude'] < nxt)
                if inside:
                    plist.append(p['name'])
                    p['house'] = i+1
            hs.append({'number': i+1, 'sign': sname, 'signLord': SIGN_LORDS[sname], 'degree': cusp, 'planets': plist})

    asc = {'sign': asc_sign, 'degree': asc_deg, 'nakshatra': asc_nk['name'], 'nakshatraLord': asc_nk['lord']}
    # Also return cusps for debugging/verification
    # Return cusps normalized to 12-length list
    cusps_out = list(cusps)[1:13] if len(list(cusps)) >= 13 else list(cusps)[0:12]
    return {'houses': hs, 'ascendant': asc, 'cusps': cusps_out}


def planet_status(name: str, sign: str) -> str:
    props = PLANET_PROPS.get(name)
    if not props:
        return 'Neutral'
    if props['exalted'] == sign:
        return 'Exalted'
    if props['debil'] == sign:
        return 'Debilitated'
    if sign in props['own']:
        return 'Own Sign'
    if props['mool'] == sign:
        return 'Mooltrikona'
    lord = SIGN_LORDS[sign]
    if lord in props['friends']:
        return 'Friendly'
    if lord in props['enemies']:
        return 'Enemy'
    return 'Neutral'


def sunrise_sunset(date_str: str, tz_name: str, lat: float, lon: float):
    # Validate coordinates
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        logging.error(f"Invalid coordinates provided: lat={lat}, lon={lon}")
        return None, None, None, None
    
    try:
        tz = pytz.timezone(tz_name)
        dt_local = tz.localize(parser.parse(f"{date_str} 00:00"))
        dt_utc = dt_local.astimezone(pytz.utc)
        jd0 = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60)

        rsmi_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
        rsmi_set = swe.CALC_SET | swe.BIT_DISC_CENTER
        press = 1013.25
        temp = 15
        geopos = (lon, lat, 0.0)

        # Per installed swisseph doc: res, tret = rise_trans(tjdut, body, rsmi, geopos, atpress, attemp, flags)
        res_rise, tret_rise = swe.rise_trans(jd0, swe.SUN, rsmi_rise, geopos, press, temp, swe.FLG_SWIEPH)
        res_set, tret_set = swe.rise_trans(jd0, swe.SUN, rsmi_set, geopos, press, temp, swe.FLG_SWIEPH)

        # res == 0 means success, -2 circumpolar (no event)
        if res_rise != 0 or res_set != 0:
            logging.warning(f"swe.rise_trans no event: rise_res={res_rise}, set_res={res_set}")
            return None, None, None, None

        sr_jdut = tret_rise[0]
        ss_jdut = tret_set[0]

        def to_local_str(jdut):
            if not jdut:
                return None
            y, m, d, ut = swe.revjul(jdut)
            hh = int(ut)
            mm = int(round((ut - hh) * 60))
            dt = datetime(y, m, d, hh, mm, tzinfo=pytz.utc).astimezone(tz)
            return dt.strftime('%H:%M')

        return to_local_str(sr_jdut), to_local_str(ss_jdut), sr_jdut, ss_jdut
    except Exception as e:
        logging.error(f"Error in sunrise_sunset calculation: {e}", exc_info=True)
        return None, None, None, None


def panchang_at_jd(jd: float) -> Dict[str, Any]:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xs, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    xm, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    s_lon = xs[0]
    m_lon = xm[0]
    diff = (m_lon - s_lon) % 360.0
    tithi_num = int(diff // 12) + 1
    tithi_name = TITHI_NAMES[tithi_num - 1]
    paksha = 'Shukla' if tithi_num <= 15 else 'Krishna'
    nk = get_nakshatra(m_lon)
    nk_num = next((i+1 for i, (n, *_rest) in enumerate(NAKSHATRAS) if n == nk['name']), None)
    yoga_sum = (s_lon + m_lon) % 360.0
    yoga_num = int(yoga_sum // 13.333333) + 1
    yoga_name = YOGA_NAMES[(yoga_num - 1) % 27]
    kar_index = int((diff % 12) // 6)
    kar_name = KARANA_SEQUENCE[min(kar_index, len(KARANA_SEQUENCE)-1)]
    moon_phase = 'Full Moon' if tithi_num == 15 else ('New Moon' if tithi_num == 30 else ('Waxing' if tithi_num < 15 else 'Waning'))
    return {
        'tithi': tithi_name,
        'tithiNumber': tithi_num,
        'nakshatra': nk['name'],
        'nakshatraNumber': nk_num,
        'yoga': yoga_name,
        'karana': kar_name,
        'paksha': paksha,
        'moonPhase': moon_phase
    }


def compute_panchang(date_str: str, time_str: str, tz: str, lat: float, lon: float) -> Dict[str, Any]:
    """Compute Panchang using sunrise JD when available and include sunrise/sunset local strings."""
    jd = to_julian(date_str, time_str, tz)
    sr, ss, sr_jd, _ = sunrise_sunset(date_str, tz, lat, lon)
    core = panchang_at_jd(sr_jd if sr_jd else jd)
    core.update({'sunrise': sr, 'sunset': ss})
    return core


def pd_years(years: float) -> timedelta:
    return timedelta(days=int(round(years * 365.25)))


def parse_local_datetime(date_str: str, time_str: str, tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    dt_local = parser.parse(f"{date_str} {time_str}")
    return tz.localize(dt_local)


def vimshottari_full(jd: float, birth_dt_local: datetime) -> Dict[str, Any]:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xm, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    m_lon = xm[0]
    nk_idx = int(m_lon // 13.333333) % 27
    start_lord = [n[1] for n in NAKSHATRAS][nk_idx]
    pos_in_nk = (m_lon % 13.333333) / 13.333333
    md_years_total = DASHA_YEARS[start_lord]
    first_md_years = (1 - pos_in_nk) * md_years_total
    start_index = DASHA_SEQUENCE.index(start_lord)
    mahadashas = []
    cursor = birth_dt_local
    md_years_list = []
    md_years_list.append((start_lord, first_md_years))
    total_years = first_md_years
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

    def build_antardasha(md_start: datetime, md_years: float):
        antars = []
        cursor_a = md_start
        for ad_lord in DASHA_SEQUENCE:
            ad_years = md_years * (DASHA_YEARS[ad_lord] / 120.0)
            ad_start = cursor_a
            ad_end = ad_start + pd_years(ad_years)
            pratis = []
            cursor_p = ad_start
            for pd_lord in DASHA_SEQUENCE:
                pr_years = (ad_years) * (DASHA_YEARS[pd_lord] / 120.0)
                p_start = cursor_p
                p_end = p_start + pd_years(pr_years)
                pratis.append({
                    'planet': pd_lord,
                    'startDate': p_start.date().isoformat(),
                    'endDate': p_end.date().isoformat()
                })
                cursor_p = p_end
            antars.append({
                'planet': ad_lord,
                'startDate': ad_start.date().isoformat(),
                'endDate': ad_end.date().isoformat(),
                'pratyantar': pratis
            })
            cursor_a = ad_end
        return antars

    for lord, years in md_years_list:
        md_start = cursor
        md_end = md_start + pd_years(years)
        mahadashas.append({
            'planet': lord,
            'startDate': md_start.date().isoformat(),
            'endDate': md_end.date().isoformat(),
            'antardasha': build_antardasha(md_start, years)
        })
        cursor = md_end

    current = {
        'planet': start_lord,
        'startDate': mahadashas[0]['startDate'],
        'endDate': mahadashas[0]['endDate']
    }
    return {'current': current, 'mahadashas': mahadashas}


def modality_of(sign_index: int) -> str:
    if sign_index % 3 == 0:
        return 'Movable'
    if sign_index % 3 == 1:
        return 'Fixed'
    return 'Dual'


def varga_sign(lon: float, varga: int) -> Optional[str]:
    si = int(lon // 30)
    deg = lon % 30
    if varga == 2:
        odd = si % 2 == 0
        first = 'Leo' if odd else 'Cancer'
        second = 'Cancer' if odd else 'Leo'
        return first if deg < 15 else second
    if varga == 3:
        part = int(deg // 10)
        offsets = [0, 4, 8]
        return ZODIAC_SIGNS[(si + offsets[part]) % 12]
    if varga == 4:
        part = int(deg // 7.5)
        mod = modality_of(si)
        base = 0 if mod == 'Movable' else (3 if mod == 'Fixed' else 6)
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 7:
        part = int(deg // (30/7))
        base = 0 if (si % 2 == 0) else 6
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 9:
        part = int(deg // (30/9))
        mod = modality_of(si)
        base = 0 if mod == 'Movable' else (8 if mod == 'Fixed' else 4)
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 10:
        part = int(deg // 3)
        base = 0 if (si % 2 == 0) else 8
        return ZODIAC_SIGNS[(si + base + part) % 12]
    if varga == 12:
        part = int(deg // (30/12))
        return ZODIAC_SIGNS[(si + part) % 12]
    # Generic fallback for any varga: split sign into 'varga' equal parts and advance signs sequentially
    # Note: This is a simplified/generalized mapping to support additional Varga charts when a classical rule isn't implemented.
    try:
        if varga > 1:
            step = 30.0 / float(varga)
            part = int(deg // step)
            return ZODIAC_SIGNS[(si + part) % 12]
    except Exception:
        return None
    return ZODIAC_SIGNS[si]


def varga_mode(varga: int) -> str:
    """Return mapping mode used: 'classical' for explicitly implemented charts, else 'generic'."""
    return 'classical' if varga in {1, 2, 3, 4, 7, 9, 10, 12} else 'generic'


VARGA_META = {
    'D1': {'name': 'Rasi', 'focus': 'General life'} , 'D2': {'name': 'Hora', 'focus': 'Wealth'},
    'D3': {'name': 'Drekkana', 'focus': 'Siblings/Co-borns'}, 'D4': {'name': 'Chaturthamsa', 'focus': 'Home/Property'},
    'D5': {'name': 'Panchamsa', 'focus': 'Power/Authority'}, 'D6': {'name': 'Shashtamsa', 'focus': 'Health/Illness'},
    'D7': {'name': 'Saptamsa', 'focus': 'Children/Progeny'}, 'D9': {'name': 'Navamsa', 'focus': 'Marriage/Dharma'},
    'D10': {'name': 'Dashamamsa', 'focus': 'Career/Profession'}, 'D12': {'name': 'Dwadasamsa', 'focus': 'Parents/Ancestry'},
    'D16': {'name': 'Shodasamsa', 'focus': 'Vehicles/Comforts'}, 'D20': {'name': 'Vimsamsa', 'focus': 'Spirituality/Upasana'},
    'D24': {'name': 'Siddhamsa', 'focus': 'Education/Learning'}, 'D27': {'name': 'Nakshatramsa', 'focus': 'Strength/Deity'},
    'D30': {'name': 'Trimshamsa', 'focus': 'Mishaps/Defects'}, 'D40': {'name': 'Khavedamsa', 'focus': 'Purva Punya/Sins'},
    'D45': {'name': 'Akshavedamsa', 'focus': 'Character/Spiritual Merit'}, 'D60': {'name': 'Shashtiamsa', 'focus': 'Past Life/Overall'}
}


def charts_divisional_extended(planets: list, ascendant: Dict[str, Any]) -> Dict[str, Any]:
    charts: Dict[str, Any] = {}

    def build_chart(d: int) -> Dict[str, Any]:
        key = f'D{d}'
        name = VARGA_META[key]['name']
        focus = VARGA_META[key]['focus']

        asc_degree = ascendant['degree']
        asc_sign_d1 = ascendant['sign']
        asc_sign = asc_sign_d1 if d == 1 else varga_sign(asc_degree, d)
        asc_sign = asc_sign or asc_sign_d1
        asc = {
            'sign': asc_sign,
            'signLord': SIGN_LORDS[asc_sign],
            'degree': asc_degree % 30,
            'longitude': asc_degree
        }

        asc_idx = ZODIAC_SIGNS.index(asc_sign)
        plist = []
        for p in planets:
            vs = p['sign'] if d == 1 else varga_sign(p['longitude'], d)
            if vs is None:
                continue
            if d == 1:
                house = p.get('house') or 0
            else:
                sidx = ZODIAC_SIGNS.index(vs)
                house = ((sidx - asc_idx + 12) % 12) + 1
            plist.append({
                'name': p['name'],
                'sign': vs,
                'house': house,
                'degree': p['degree'],
                'dignity': planet_status(p['name'], vs),
                'isRetrograde': p['isRetrograde'],
                'isCombust': p['isCombust']
            })

        return {'name': name, 'focus': focus, 'ascendant': asc, 'planets': plist}

    # Build main vargas with full details
    for d in [1,2,3,4,7,9,10,12]:
        charts[f'D{d}'] = build_chart(d)

    # Placeholders for other vargas
    for key in ['D16','D20','D24','D27','D30']:
        charts[key] = {'name': VARGA_META[key]['name'], 'focus': VARGA_META[key]['focus'], 'ascendant': None, 'planets': [], 'note': 'Not implemented yet'}

    return charts


def kp_sub_lord_for(lon: float) -> str:
    nk_start = (int(lon // 13.333333)) * 13.333333
    pos = lon - nk_start
    total = 13.333333
    accum = 0.0
    for lord in DASHA_SEQUENCE:
        portion = total * (DASHA_YEARS[lord] / 120.0)
        if pos < accum + portion:
            return lord
        accum += portion
    return DASHA_SEQUENCE[-1]


def kp_details(houses: list, planets: list) -> Dict[str, Any]:
    bhav = []
    for h in houses:
        mid = (h['degree'] + 15) % 360 if isinstance(h['degree'], (int, float)) else 0
        bhav.append({'bhav': h['number'], 'sign': h['sign'], 'midPoint': mid, 'planets': h['planets']})
    pdetails = []
    for p in planets:
        pdetails.append({
            'planet': p['name'], 'cusp': p['house'], 'sign': p['sign'],
            'cuspalLord': SIGN_LORDS[houses[p['house']-1]['sign']] if p['house'] else None,
            'starLord': p['nakshatraLord'], 'subLord': kp_sub_lord_for(p['longitude']), 'degree': p['degree'],
        })
    return {'bhavChalitChart': bhav, 'planetDetails': pdetails}


def detect_yogas(planets: list, houses: list, asc_sign: str) -> list:
    res = []
    moon = next((p for p in planets if p['name']=='Moon'), None)
    jup = next((p for p in planets if p['name']=='Jupiter'), None)
    if moon and jup and moon['house'] in [1,4,7,10] and jup['house'] in [1,4,7,10]:
        res.append({'name':'Gajakesari Yoga','description':'Moon and Jupiter in kendras from ascendant','strength':'Strong'})
    for p in planets:
        if planet_status(p['name'], p['sign']) == 'Debilitated':
            lord = SIGN_LORDS[p['sign']]
            lord_planet = next((q for q in planets if q['name']==lord), None)
            if lord_planet and planet_status(lord, lord_planet['sign']) == 'Exalted':
                res.append({'name':'Neecha Bhanga (simplified)','description':f"{p['name']} debilitation cancelled by exalted {lord}", 'strength':'Medium'})
    return res


def detect_doshas(planets: list) -> list:
    res = []
    mars = next((p for p in planets if p['name']=='Mars'), None)
    present = mars and mars['house'] in [1,4,7,8,12]
    res.append({'name':'Mangal Dosha','description':'Mars in 1/4/7/8/12 (simplified)','present': bool(present), 'remedies':['Hanuman Chalisa','Kumbh Vivah']})
    rahu = next((p for p in planets if p['name']=='Rahu'), None)
    ketu = next((p for p in planets if p['name']=='Ketu'), None)
    classical = [p for p in planets if p['name'] in ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn']]
    if rahu and ketu and classical:
        a = rahu['longitude']; b = ketu['longitude']
        lo = min(a,b); hi = max(a,b)
        inside = all((lo <= p['longitude'] <= hi) for p in classical)
        present2 = inside or all(not (lo <= p['longitude'] <= hi) for p in classical)
    else:
        present2 = False
    res.append({'name':'Kaal Sarp Dosha','description':'All planets confined between Rahu and Ketu (simplified)','present': bool(present2), 'remedies':['Rahu-Ketu Shanti']})
    sun = next((p for p in planets if p['name']=='Sun'), None)
    present3 = sun and (sun['sign'] == (rahu['sign'] if rahu else '') or sun['sign'] == (ketu['sign'] if ketu else ''))
    res.append({'name':'Pitra Dosha','description':'Sun afflicted by nodes (sign-conjunction)','present': bool(present3), 'remedies':['Pitru Tarpan','Rahu/Ketu Shanti']})
    return res


# NEW: Function to get dynamic Vedic properties based on Moon's position
def get_vedic_properties(sign: str, nakshatra: str, pada: int) -> Dict[str, str]:
    props = NAKSHATRA_PROPERTIES.get(nakshatra, {})
    if not props:
        return {'error': 'Nakshatra properties not found'}

    # Determine Tatva (Element) from Moon's sign
    if sign in ['Aries', 'Leo', 'Sagittarius']:
        tatva = 'Fire'
    elif sign in ['Taurus', 'Virgo', 'Capricorn']:
        tatva = 'Earth'
    elif sign in ['Gemini', 'Libra', 'Aquarius']:
        tatva = 'Air'
    else: # Cancer, Scorpio, Pisces
        tatva = 'Water'

    # Determine Paya (Foot/Pillar) from Moon's sign
    if sign in ['Aries', 'Virgo', 'Aquarius']:
        paya = 'Gold'
    elif sign in ['Taurus', 'Libra', 'Sagittarius']:
        paya = 'Silver'
    elif sign in ['Gemini', 'Leo', 'Capricorn']:
        paya = 'Copper'
    else: # Cancer, Scorpio, Pisces
        paya = 'Iron'

    return {
        'varna': props.get('varna', 'Unknown'),
        'vashya': props.get('vashya', 'Unknown'),
        'yoni': props.get('yoni', 'Unknown'),
        'gan': props.get('gan', 'Unknown'),
        'nadi': props.get('nadi', 'Unknown'),
        'nameAlphabet': props.get('padas', ['?'])[max(1, min(4, pada)) - 1],
        'yunja': 'Harmonious', # Placeholder
        'tatva': tatva,
        'paya': paya
    }


@app.post('/api/kundli')
def generate_kundli(body: BirthDetails) -> Dict[str, Any]:
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    ayan = ayanamsa_value(jd)

    planets = calc_planets(jd, body.propertyProfile, body.nodeMode)
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    # Default to Whole Sign if not provided; North-Indian style charts usually expect whole sign houses
    hs_code = body.houseSystem or 'W'
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, hs_code)

    # Panchang via shared helper
    panch = compute_panchang(body.dateOfBirth, body.timeOfBirth, body.timezone, body.latitude, body.longitude)
    
    # Use propertySource to choose source for Vedic properties: 'moon' | 'ascendant' | 'sunriseMoon'
    source = (body.propertySource or 'moon').lower()
    chosen = None
    if source == 'ascendant':
        asc = house_data['ascendant']
        chosen = {'sign': asc['sign'], 'nakshatra': asc['nakshatra'], 'pada': 1}
    elif source == 'sunrisemoon':
        # Recompute Moon at sunrise JD if available; else fallback to current jd
        _sr, _ss, _sr_jd, _ = sunrise_sunset(body.dateOfBirth, body.timezone, body.latitude, body.longitude)
        sr_jd_effective = _sr_jd if _sr_jd else jd
        xm, _ = swe.calc_ut(sr_jd_effective, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        m_lon = xm[0]
        chosen = {
            'sign': get_sign(m_lon),
            'nakshatra': get_nakshatra(m_lon)['name'],
            'pada': get_nakshatra(m_lon)['pada']
        }
    else:  # default to 'moon'
        moon_details = next((p for p in planets if p['name'] == 'Moon'), None)
        if moon_details:
            chosen = {'sign': moon_details['sign'], 'nakshatra': moon_details['nakshatra'], 'pada': moon_details['nakshatraPada']}

    if chosen:
        vedic_props = get_vedic_properties(chosen['sign'], chosen['nakshatra'], chosen['pada'])
        vedic_source_nk = {'name': chosen['nakshatra'], 'pada': chosen['pada']}
    else:
        vedic_props = {'error': 'Source details could not be calculated'}
        vedic_source_nk = {}

    basic = {
        'birthDate': body.dateOfBirth,
        'birthTime': body.timeOfBirth,
        'birthPlace': f"{body.latitude}, {body.longitude}",
        'latitude': body.latitude,
        'longitude': body.longitude,
        'timezone': body.timezone,
        'ayanamsa': 'Lahiri',
        'ayanamsaValue': ayan,
        'sunSign': next(p['sign'] for p in planets if p['name']=='Sun'),
        'moonSign': next(p['sign'] for p in planets if p['name']=='Moon'),
        'ascendant': house_data['ascendant'],
        'houseSystem': hs_code
    }

    return {
        'success': True,
        'data': {
            'basicDetails': basic,
            'vedicProperties': {
                'source': body.propertySource,
                'sourceNakshatra': vedic_source_nk,
                'values': vedic_props
            },
            'panchang': panch,
        }
    }

# --------------------- New endpoint: /horoscope/planet-details ---------------------

NAME_ABBR = {
    'Ascendant': 'As', 'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
    'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke'
}

NAKSHATRA_NAME_NORMALIZE = {
    'Ashwini': 'Ashvini', 'Dhanishta': 'Dhanista', 'Shravana': 'Sravana'
}

def normalize_nk(name: str) -> str:
    return NAKSHATRA_NAME_NORMALIZE.get(name, name)

def sign_index(sign: str) -> int:
    return ZODIAC_SIGNS.index(sign)

def rasi_no_from_sign(sign: str) -> int:
    return sign_index(sign) + 1

def nakshatra_number(name: str) -> Optional[int]:
    for i, (n, *_rest) in enumerate(NAKSHATRAS):
        if n == name:
            return i + 1
    return None

def avastha_compact(label: str) -> str:
    # Map 'Infant (Bala)' -> 'Bala', 'Young (Kumara)' -> 'Kumara', 'Dead (Mrita)' -> 'Mritya'
    if 'Bala' in label and 'Infant' in label: return 'Bala'
    if 'Kumara' in label: return 'Kumara'
    if 'Yuva' in label: return 'Yuva'
    if 'Vriddha' in label: return 'Vriddha'
    if 'Mrita' in label or 'Mrity' in label: return 'Mritya'
    return label

def lord_status_from_dignity(d: str) -> str:
    if d == 'Exalted':
        return 'Highly Benefic'
    if d in ['Own Sign', 'Mooltrikona', 'Friendly']:
        return 'Benefic'
    if d in ['Enemy', 'Debilitated']:
        return 'Malefic'
    return 'Neutral'

def planet_full_name(name: str) -> str:
    return 'Ascendant' if name == 'Ascendant' else name

PLANET_DEFS = {
    'Sun': {
        'definitions': 'The radiant Sun is the significator (Karaka) of health, vitality, energy, and strength. It embodies qualities of leadership, courage, and personal power. Revered as a royal and aristocratic planet, the Sun represents the conscious ego and the soul, guiding the path of self-realization.',
        'gayatri': 'Om Bhaskaraya Vidmahe Mahadyutikaraya Dheemahi Tanno Adityah Prachodayaat'
    }
}

@app.post('/horoscope/planet-details')
def planet_details(body: BirthDetails):
    import math
    # Compute base data
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, body.propertyProfile, body.nodeMode)
    hs_code = body.houseSystem or 'W'
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, hs_code)

    # Build ascendant record
    asc = house_data['ascendant']
    asc_nk = get_nakshatra(asc['degree'])
    asc_item = {
        'name': NAME_ABBR['Ascendant'],
        'full_name': 'Ascendant',
        'local_degree': asc['degree'] % 30,
        'global_degree': asc['degree'] % 360,
        'progress_in_percentage': (asc['degree'] % 30) / 30 * 100,
        'rasi_no': rasi_no_from_sign(asc['sign']),
        'zodiac': asc['sign'],
        'house': 1,
        'nakshatra': normalize_nk(asc_nk['name']),
        'nakshatra_lord': asc_nk['lord'],
        'nakshatra_pada': asc_nk['pada'],
        'nakshatra_no': nakshatra_number(asc_nk['name']),
        'zodiac_lord': SIGN_LORDS[asc['sign']],
        'is_planet_set': False,
        'lord_status': '-',
        'basic_avastha': '-',
        'is_combust': False
    }

    # Only classical + nodes in this report
    ordered = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']
    plist = [p for p in planets if p['name'] in ordered]
    plist.sort(key=lambda p: ordered.index(p['name']))

    result_indexed: Dict[str, Any] = {'0': asc_item}

    for idx, p in enumerate(plist, start=1):
        nk_num = nakshatra_number(p['nakshatra'])
        dignity = planet_status(p['name'], p['sign'])
        lord_stat = lord_status_from_dignity(dignity)
        set_flag = bool(p.get('house', 0) in [1,2,3,4,5,6])
        item = {
            'name': NAME_ABBR.get(p['name'], p['name'][:2]),
            'full_name': planet_full_name(p['name']),
            'local_degree': p['degree'],
            'global_degree': p['longitude'],
            'progress_in_percentage': p['degree'] / 30.0 * 100.0,
            'rasi_no': rasi_no_from_sign(p['sign']),
            'zodiac': p['sign'],
            'house': p.get('house', 0),
            'speed_radians_per_day': p['speed'] * math.pi / 180.0,
            'retro': bool(p['isRetrograde']),
            'nakshatra': normalize_nk(p['nakshatra']),
            'nakshatra_lord': p['nakshatraLord'],
            'nakshatra_pada': p['nakshatraPada'],
            'nakshatra_no': nk_num,
            'zodiac_lord': p['signLord'],
            'is_planet_set': set_flag,
            'basic_avastha': avastha_compact(p.get('avastha','')),
            'lord_status': lord_stat,
            'is_combust': bool(p['isCombust'])
        }
        result_indexed[str(idx)] = item

    # Personal characteristics per house (simple template-based)
    personal: list[Dict[str, Any]] = []
    asc_sign = asc['sign']
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    house_signs = [ZODIAC_SIGNS[(asc_idx + i) % 12] for i in range(12)]
    pmap = {p['name']: p for p in planets}

    for h in range(1, 13):
        sign = house_signs[h-1]
        lord = SIGN_LORDS[sign]
        lord_p = pmap.get(lord)
        lord_sign = lord_p['sign'] if lord_p else None
        lord_house = lord_p.get('house') if lord_p else None
        strength = planet_status(lord, lord_sign) if lord_sign else 'Neutral'
        verbal = f"{h}st lord is in the {lord_house}th house" if h == 1 else f"{h}th lord is in the {lord_house}th house"
        personal.append({
            'current_house': h,
            'verbal_location': verbal,
            'current_zodiac': sign,
            'lord_of_zodiac': lord,
            'lord_zodiac_location': lord_sign,
            'lord_house_location': lord_house,
            'personalised_prediction': f"Since the  {h} lord, {lord} is in the {lord_house} house, outcomes relate to {sign.lower()} themes.",
            'lord_strength': strength
        })

    # Simple planet report for Sun (example)
    sun = pmap.get('Sun')
    if sun:
        z_lord = SIGN_LORDS[sun['sign']]
        z_lord_p = pmap.get(z_lord)
        report = {
            'planet_considered': 'Sun',
            'planet_location': sun.get('house'),
            'planet_native_location': 5,  # Sun's natural house in Kaal Purusha (Leo)
            'planet_zodiac': sun['sign'],
            'zodiac_lord': z_lord,
            'zodiac_lord_location': z_lord_p['sign'] if z_lord_p else None,
            'zodiac_lord_house_location': z_lord_p.get('house') if z_lord_p else None,
            'general_prediction': 'Your personality, vitality, and leadership themes are highlighted by the Sun\'s placement.',
            'zodiac_lord_strength': planet_status(z_lord, z_lord_p['sign']) if z_lord_p else 'Neutral',
            'planet_strength': planet_status('Sun', sun['sign']),
            'planet_definitions': PLANET_DEFS['Sun']['definitions'],
            'gayatri_mantra': PLANET_DEFS['Sun']['gayatri'],
            'qualities_long': 'This placement fuels ambition and visibility; hard work is needed if afflicted.',
            'qualities_short': 'Seeks recognition through contribution.',
            'affliction': 'Afflictions can bring career hurdles or vitality dips.',
            'personalised_prediction': f"Since the  11th lord, Sun, influences {sun.get('house')}th house matters, career and visibility are emphasized.",
            'verbal_location': 'Lord of the 11th lord in 12th house',
            'planet_zodiac_prediction': f"{sun['sign']} is a {('Movable' if sign_index(sun['sign'])%3==0 else ('Fixed' if sign_index(sun['sign'])%3==1 else 'Dual'))} sign; its lord {z_lord} colors self-expression.",
            'character_keywords_positive': ['principled','Attractive','Virtuous','Creative'],
            'character_keywords_negative': ['indecisive','Doubtful']
        }
    else:
        report = {}

    return {
        'status': 200,
        'response': result_indexed,
        'personal_characteristics': personal,
        'planet_report': report
    }