"""Shared utilities extracted from main.py to break circular imports."""
from typing import Optional, Dict, Any, List
from datetime import datetime
import swisseph as swe
import pytz
from dateutil import parser
import logging

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

PLANET_IDS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
    'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO, 'Rahu': swe.MEAN_NODE, 'Ketu': swe.MEAN_NODE,
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


def to_julian(date_str: str, time_str: str, tz_name: str) -> float:
    dt_local = parser.parse(f"{date_str} {time_str}")
    tz = pytz.timezone(tz_name)
    dt_local = tz.localize(dt_local)
    dt_utc = dt_local.astimezone(pytz.utc)
    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
    hour = dt_utc.hour + dt_utc.minute / 60
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
    return {'name': 'Unknown', 'lord': 'Unknown', 'pada': 1}


def ayanamsa_value(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return swe.get_ayanamsa(jd)


def to_dms(x: float) -> str:
    s = -1 if x < 0 else 1
    x = abs(x)
    d = int(x)
    m = int((x - d) * 60)
    sec = int(round(((x - d) * 60 - m) * 60))
    sign = '-' if s < 0 else ''
    return f"{sign}{d}°{m}′{sec}″"


def get_avastha(deg_in_sign: float, sign: str) -> str:
    idx = max(0, min(4, int(deg_in_sign // 6)))
    odd = sign in ['Aries', 'Gemini', 'Leo', 'Libra', 'Sagittarius', 'Aquarius']
    odd_order = ['Infant (Bala)', 'Young (Kumara)', 'Youth (Yuva)', 'Old (Vriddha)', 'Dead (Mrita)']
    even_order = list(reversed(odd_order))
    return (odd_order if odd else even_order)[idx]


def is_combust(name: str, lon: float, sun_lon: float, retro: bool) -> bool:
    if name in ['Sun', 'Rahu', 'Ketu', 'Uranus', 'Neptune', 'Pluto']:
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
        if pname in ['Rahu', 'Ketu']:
            pid = swe.TRUE_NODE if node_mode == 'true' else swe.MEAN_NODE
        xx, rf = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
        lon, lat, dist = xx[0], xx[1], xx[2]
        lon_spd = xx[3]
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
            'isRetrograde': retro and pname not in ['Sun', 'Moon'],
            'isCombust': False,
            'avastha': avastha,
            'houseStatus': None,
        })
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
            hs.append({'number': i + 1, 'sign': sname, 'signLord': SIGN_LORDS[sname], 'degree': sidx * 30, 'planets': []})
        for p in planets:
            psidx = ZODIAC_SIGNS.index(p['sign'])
            hnum = ((psidx - asc_idx + 12) % 12) + 1
            p['house'] = hnum
            hs[hnum - 1]['planets'].append(p['name'])
    else:
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
                    p['house'] = i + 1
            hs.append({'number': i + 1, 'sign': sname, 'signLord': SIGN_LORDS[sname], 'degree': cusp, 'planets': plist})

    asc = {'sign': asc_sign, 'degree': asc_deg, 'nakshatra': asc_nk['name'], 'nakshatraLord': asc_nk['lord']}
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
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return None, None, None, None
    try:
        tz = pytz.timezone(tz_name)
        dt_local = tz.localize(parser.parse(f"{date_str} 00:00"))
        dt_utc = dt_local.astimezone(pytz.utc)
        jd0 = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60)

        rsmi_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
        rsmi_set = swe.CALC_SET | swe.BIT_DISC_CENTER
        press = 1013.25
        temp = 15
        geopos = (lon, lat, 0.0)

        res_rise, tret_rise = swe.rise_trans(jd0, swe.SUN, rsmi_rise, geopos, press, temp, swe.FLG_SWIEPH)
        res_set, tret_set = swe.rise_trans(jd0, swe.SUN, rsmi_set, geopos, press, temp, swe.FLG_SWIEPH)

        if res_rise != 0 or res_set != 0:
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
    nk_num = next((i + 1 for i, (n, *_rest) in enumerate(NAKSHATRAS) if n == nk['name']), None)
    yoga_sum = (s_lon + m_lon) % 360.0
    yoga_num = int(yoga_sum // 13.333333) + 1
    yoga_name = YOGA_NAMES[(yoga_num - 1) % 27]
    kar_index = int((diff % 12) // 6)
    kar_name = KARANA_SEQUENCE[min(kar_index, len(KARANA_SEQUENCE) - 1)]
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
    jd = to_julian(date_str, time_str, tz)
    sr, ss, sr_jd, _ = sunrise_sunset(date_str, tz, lat, lon)
    core = panchang_at_jd(sr_jd if sr_jd else jd)
    core.update({'sunrise': sr, 'sunset': ss})
    return core
