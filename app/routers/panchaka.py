"""
Panchaka Analysis + Gulika Position + Roga Nidana router.
Traditional Vedic astrology calculations for panchaka, gulika, and disease prediction.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from ..utils import (
    to_julian,
    calc_planets,
    calc_houses,
    get_sign,
    get_nakshatra,
    ZODIAC_SIGNS,
    SIGN_LORDS,
    planet_status,
    panchang_at_jd,
    sunrise_sunset,
)
import swisseph as swe
import pytz
from dateutil import parser as dtparser
from typing import Optional

router = APIRouter()


# ─── PanchakaRequest model ───

class PanchakaRequest(BaseModel):
    dateOfBirth: str
    timeOfBirth: str
    latitude: float
    longitude: float
    timezone: str


# ──────────────────────────── Constants ────────────────────────────

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

# Panchaka classification by nakshatra
# Rogaka – disease; Mrityu – death-like obstacles; Agni – fire/accidents;
# Soola – trident/strife; Rajapujya – royal honour
PANCHAKA_MAP = {
    # Rogaka (disease)
    "Ashwini": "Rogaka",
    "Pushya": "Rogaka",
    "Anuradha": "Rogaka",
    "Revati": "Rogaka",
    # Mrityu (death-like obstacles)
    "Mrigashira": "Mrityu",
    "Chitra": "Mrityu",
    "Vishakha": "Mrityu",
    "Dhanishta": "Mrityu",
    # Agni (fire / accidents)
    "Krittika": "Agni",
    "Magha": "Agni",
    "Swati": "Agni",
    "Purva Ashadha": "Agni",
    # Soola (trident / strife)
    "Rohini": "Soola",
    "Punarvasu": "Soola",
    "Mula": "Soola",
    "Uttara Bhadrapada": "Soola",
    # Rajapujya (royal honour)
    "Ardra": "Rajapujya",
    "Ashlesha": "Rajapujya",
    "Purva Phalguni": "Rajapujya",
    "Shravana": "Rajapujya",
    "Hasta": "Rajapujya",
    "Jyeshtha": "Rajapujya",
    "Uttara Ashadha": "Rajapujya",
    "Purva Bhadrapada": "Rajapujya",
    "Bharani": "Rajapujya",
    "Abhijit": "Rajapujya",
}

PANCHAKA_DETAILS = {
    "Rogaka": {
        "severity": "Medium",
        "description": "The native is prone to chronic ailments and health-related struggles.",
        "affected_areas": [
            "Physical health",
            "Chronic diseases",
            "Immune system",
            "Mental wellbeing",
        ],
        "remedies": [
            "Worship Lord Dhanvantari (physician of the gods).",
            "Donate medicine or medical equipment on Wednesdays.",
            "Recite Mrityunjaya Mantra 108 times daily.",
            "Maintain a sattvic diet and avoid stale food.",
        ],
    },
    "Mrityu": {
        "severity": "High",
        "description": (
            "Life-threatening obstacles or near-death experiences are possible; "
            "extra caution required during panchaka periods."
        ),
        "affected_areas": [
            "Life span",
            "Major accidents",
            "Sudden calamities",
            "Surgery risk",
        ],
        "remedies": [
            "Perform Mrityunjaya Homa or Rudra Abhishekam.",
            "Donate a black cow or brass vessel on Tuesdays.",
            "Chant Mahamrityunjaya Mantra 1,008 times.",
            "Avoid new ventures during Mrityu panchaka days.",
        ],
    },
    "Agni": {
        "severity": "High",
        "description": (
            "Risk of fire-related incidents, burns, accidents, "
            "explosions, and electrical hazards."
        ),
        "affected_areas": [
            "Fire accidents",
            "Burns",
            "Electrical hazards",
            "Government punishment",
        ],
        "remedies": [
            "Offer water to the Sun at sunrise (Arghya).",
            "Donate red lentils (masoor dal) on Tuesdays.",
            "Light a sesame oil lamp in a temple on Saturdays.",
            "Avoid lighting fires or handling explosives on Agni panchaka days.",
        ],
    },
    "Soola": {
        "severity": "Medium-High",
        "description": (
            "Trident of strife – brings conflicts, rivalries, "
            "sharp-weapon injuries, and mental anguish."
        ),
        "affected_areas": [
            "Relationships",
            "Legal disputes",
            "Sharp injuries",
            "Mental peace",
        ],
        "remedies": [
            "Worship Lord Shiva with bilva leaves.",
            "Donate milk and sugar on Mondays.",
            "Recite Shiva Panchakshari Stotram daily.",
            "Avoid travel in the direction of the Soola during this period.",
        ],
    },
    "Rajapujya": {
        "severity": "Favourable",
        "description": (
            "Highly auspicious – the native receives royal honours, "
            "respect, authority, and success."
        ),
        "affected_areas": [
            "Career advancement",
            "Social status",
            "Government favour",
            "Authority and power",
        ],
        "remedies": [
            "Begin important tasks and sign contracts.",
            "Worship the ruling deity of the nakshatra.",
            "Donate sweets and clothes to the needy.",
            "Seek blessings from elders and authority figures.",
        ],
    },
}

# ─── Gulika (Mandi) weekday offsets ───
# Gulika's daily arc = (arc_in_minutes / 60) degrees per sunrise-to-sunrise.
# Traditional: Mon=45m Tue=30m Wed=37.5m Thu=25m Fri=33.75m Sat=40m Sun=41.25m
GULIKA_ARC_MINUTES = {
    0: 41.25,  # Sunday
    1: 45.0,   # Monday
    2: 30.0,   # Tuesday
    3: 37.5,   # Wednesday
    4: 25.0,   # Thursday
    5: 33.75,  # Friday
    6: 40.0,   # Saturday
}

SIGN_EFFECTS_GULIKA = {
    1: {"house": "1st", "effect": "Health issues, low vitality, quarrelsome nature."},
    2: {"house": "2nd", "effect": "Financial loss, harsh speech, family discord."},
    3: {"house": "3rd", "effect": "Courage but excessive risk-taking; disputes with siblings."},
    4: {"house": "4th", "effect": "Mental unrest, property loss, strained mother relations."},
    5: {"house": "5th", "effect": "Obstacles in progeny, poor education, speculative losses."},
    6: {"house": "6th", "effect": "Victory over enemies, but chronic health problems."},
    7: {"house": "7th", "effect": "Marital discord, business partnerships fail, STDs."},
    8: {"house": "8th", "effect": "Major obstacles, accidents, longevity threatened."},
    9: {"house": "9th", "effect": "Bad luck, strained father relations, spiritual obstacles."},
    10: {"house": "10th", "effect": "Career setbacks, reputation damage, job loss."},
    11: {"house": "11th", "effect": "Delayed gains, trouble with elders, unstable income."},
    12: {"house": "12th", "effect": "Heavy expenditure, hospitalisation, foreign exile."},
}

# ─── Roga Nidana (disease prediction) constants ───
SIGNS_BODY_PARTS = {
    "Aries": "Head, brain, face",
    "Taurus": "Throat, neck, voice, thyroid",
    "Gemini": "Shoulders, arms, lungs, nervous system",
    "Cancer": "Chest, stomach, breasts, left eye",
    "Leo": "Heart, spine, upper back, right eye",
    "Virgo": "Abdomen, intestines, spleen, pancreas",
    "Libra": "Kidneys, lumbar region, skin, endocrine",
    "Scorpio": "Reproductive organs, excretory system, nose",
    "Sagittarius": "Hips, thighs, liver, sciatic nerve",
    "Capricorn": "Knees, bones, joints, gallbladder",
    "Aquarius": "Ankles, calves, circulatory system",
    "Pisces": "Feet, lymphatic system, pineal gland",
}

MARS_DISEASE_AFFLICTIONS = {
    "Aries": "Fevers, headaches, inflammations, baldness, burns.",
    "Taurus": "Throat infections, tonsillitis, neck injuries.",
    "Gemini": "Nervous disorders, respiratory issues, shoulder injuries.",
    "Cancer": "Digestive disorders, acid reflux, chest ailments.",
    "Leo": "Heart disease, spinal problems, back pain.",
    "Virgo": "Bowel disorders, food poisoning, skin infections.",
    "Libra": "Kidney stones, lower-back pain, urinary infections.",
    "Scorpio": "Reproductive diseases, blood disorders, surgeries.",
    "Sagittarius": "Liver disease, hip fracture, sciatica.",
    "Capricorn": "Bone fractures, dental problems, joint pain.",
    "Aquarius": "Circulatory issues, varicose veins, ankle injuries.",
    "Pisces": "Foot ailments, lymphoedema, sleep disorders.",
}

SIXTH_LORD_DISEASES = {
    "Aries": "Headaches, tumours, skull injuries, mental fever.",
    "Taurus": "Throat cancer, goitre, vocal cord issues, eating disorders.",
    "Gemini": "Lung cancer, bronchitis, arm fractures, nerve damage.",
    "Cancer": "Stomach ulcers, breast cancer, gastritis, melancholia.",
    "Leo": "Cardiac arrest, spinal cord injury, spinal stenosis.",
    "Virgo": "Intestinal cancer, ulcerative colitis, hernia.",
    "Libra": "Kidney failure, diabetes, backache, skin diseases.",
    "Scorpio": "Prostate issues, colon cancer, reproductive disorders.",
    "Sagittarius": "Hip replacement, liver cirrhosis, thigh abscess.",
    "Capricorn": "Knee replacement, bone cancer, rheumatism, gout.",
    "Aquarius": "Heart rhythm disorders, blood cancer, anemia.",
    "Pisces": "Foot cancer, lymphoma, oedema, tuberculosis.",
}

GULIKA_HEALTH_EFFECTS = {
    1: "Chronic illness from birth, low immunity, constitutional weakness.",
    2: "Mouth/throat diseases, speech defects, dental decay.",
    3: "Arm injuries, shoulder pain, ear infections.",
    4: "Chest diseases, pneumonia, maternal health issues.",
    5: "Mental illness, learning disabilities, fever-related diseases.",
    6: "Victory over disease – but lingering chronic conditions.",
    7: "Sexual diseases, partner's health issues, hernia.",
    8: "Accidents, surgeries, life-threatening illnesses, chronic pain.",
    9: "Liver problems, thigh injuries, hip diseases.",
    10: "Career-ending illnesses, nervous breakdown, burnout.",
    11: "Delayed recovery, slow-healing diseases, recurrent illness.",
    12: "Hospitalisation, hidden diseases, sleep disorders, phobias.",
}


# ──────────────────────────── Helpers ────────────────────────────


def _parse_local_dt(date_of_birth: str, time_of_birth: str, tz_str: str):
    """Parse date/time strings into a timezone-aware datetime in the given zone."""
    tz = pytz.timezone(tz_str)
    naive = dtparser.parse(f"{date_of_birth} {time_of_birth}")
    return tz.localize(naive)


def _calc_gulika_longitude(jd: float, latitude: float, longitude: float, weekday: int) -> float:
    """
    Calculate Gulika's sidereal longitude.

    Method: Gulika advances from the Sun's longiude by its daily arc proportional
    to elapsed time since sunrise.  At sunrise Gulika is at the Ascendant; by next
    sunrise it has advanced by (arc_minutes / 60) degrees.

    We use the ratio of (time since sunrise) / (day-length) × (arc / 60)° added
    to the Sun's longitude.

    For a birth-time calculation we approximate:
      offset_degrees = (arc_minutes / 60) × (time_since_sunrise / day_length)  [in degrees, max = arc_minutes/60]
    But since we need the natal Gulika position (not transit), we use the
    standard approach: Gulika at birth = Sun's longitude + (arc_in_minutes / 60)°.
    """
    arc_minutes = GULIKA_ARC_MINUTES.get(weekday, 30.0)
    arc_degrees = arc_minutes / 60.0  # max offset in degrees
    # Sun longitude (sidereal)
    sun_list = calc_planets(jd, None, 'mean')
    sun_pmap = {p['name']: p for p in sun_list}
    sun_long = sun_pmap.get('Sun', {}).get('longitude', 0.0)

    # Get ascendant to determine day-length context
    hd = calc_houses(jd, latitude, longitude, sun_list, 'P')
    cusps = hd.get('cusps', [])
    asc_long = cusps[0] if cusps else 0.0

    # Gulika longitude = Sun longitude + its daily arc offset (sidereal)
    gulika_long = (sun_long + arc_degrees) % 360.0
    return gulika_long


def _sign_from_long(lon: float) -> str:
    """Return zodiac sign name from sidereal longitude."""
    idx = int(lon / 30) % 12
    return ZODIAC_SIGNS[idx]


def _house_from_long(lon: float, cusps: list) -> int:
    """Determine house number from longitude and house cusps (Placidus)."""
    if not cusps or len(cusps) < 12:
        return 0
    for i in range(12):
        cusp_start = cusps[i]
        cusp_end = cusps[(i + 1) % 12]
        if cusp_start < cusp_end:
            if cusp_start <= lon < cusp_end:
                return i + 1
        else:
            # Cusp wraps around 360°
            if lon >= cusp_start or lon < cusp_end:
                return i + 1
    return 1


def _get_dasha_lord(nakshatra_index: int) -> str:
    """
    Simple Vimshottari dasha lord for a nakshatra (for severity context).
    Returns the planet ruling the mahadasha starting at that nakshatra.
    """
    # Ashwini = Ketu, Bharani = Venus, Krittika = Sun, ...
    order = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
        "Jupiter", "Saturn", "Mercury",
    ]
    return order[nakshatra_index % 9]


# ──────────────────────────── Endpoints ────────────────────────────


@router.post("/horoscope/panchang/panchaka")
def panchaka_analysis(body: PanchakaRequest):
    """
    Panchaka analysis for a given date/time/place.
    Determines the panchaka type from the Moon's nakshatra at birth
    and returns effects, severity, remedies, and day favourability.
    """
    local_dt = _parse_local_dt(body.dateOfBirth, body.timeOfBirth, body.timezone)
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)

    # Calculate planets and Moon's nakshatra
    planets_list = calc_planets(jd, None, 'mean')
    pmap = {p['name']: p for p in planets_list}
    moon_long = pmap.get('Moon', {}).get('longitude', 0.0)
    moon_nk = get_nakshatra(moon_long)
    moon_nak = moon_nk['name']
    moon_nak_pada = moon_nk['pada']

    # Determine panchaka type
    panchaka_type = PANCHAKA_MAP.get(moon_nak, "Rajapujya")  # fallback
    details = PANCHAKA_DETAILS[panchaka_type]

    # Ascendant & houses for additional context
    house_data = calc_houses(jd, body.latitude, body.longitude, planets_list, 'P')
    cusps = house_data.get('cusps', [])
    asc_sign = _sign_from_long(cusps[0] if cusps else 0.0)

    # Moon sign for day-lord context
    moon_sign = _sign_from_long(moon_long)

    # Sun & weekday
    sun_long = pmap.get('Sun', {}).get('longitude', 0.0)
    weekday = local_dt.weekday()  # 0=Mon … 6=Sun

    # Panchang elements
    panchang = panchang_at_jd(jd)

    # Gulika for supplementary info
    gulika_long = _calc_gulika_longitude(jd, body.latitude, body.longitude, weekday)
    gulika_sign = _sign_from_long(gulika_long)

    # Day favourability
    favourable = panchaka_type == "Rajapujya"
    if panchaka_type in ("Rogaka", "Agni", "Soola"):
        favourable = False
    elif panchaka_type == "Mrityu":
        favourable = False

    # Calculate dasha lord for timing context
    moon_nak_idx = next((i for i, n in enumerate(NAKSHATRAS) if n == moon_nak), 0)
    dasha_lord = _get_dasha_lord(moon_nak_idx)

    return {
        "status": "success",
        "input": {
            "dateOfBirth": body.dateOfBirth,
            "timeOfBirth": body.timeOfBirth,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "timezone": body.timezone,
        },
        "panchaka": {
            "type": panchaka_type,
            "severity": details["severity"],
            "description": details["description"],
            "affected_areas": details["affected_areas"],
            "remedies": details["remedies"],
            "favourable": favourable,
        },
        "moon": {
            "longitude": round(moon_long, 4),
            "sign": moon_sign,
            "nakshatra": moon_nak,
            "nakshatra_index": moon_nak_idx,
            "pada": moon_nak_pada,
            "dasha_lord": dasha_lord,
        },
        "ascendant": {
            "sign": asc_sign,
        },
        "sun": {
            "longitude": round(sun_long, 4),
            "weekday": weekday,
        },
        "gulika": {
            "longitude": round(gulika_long, 4),
            "sign": gulika_sign,
        },
        "panchang": panchang,
    }


# ──────────────────────────── Gulika Position ────────────────────────────


@router.post("/horoscope/panchang/gulika-position")
def gulika_position(body: PanchakaRequest):
    """
    Calculate Gulika (Mandi) position in the natal chart and its effects.
    """
    local_dt = _parse_local_dt(body.dateOfBirth, body.timeOfBirth, body.timezone)
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    weekday = local_dt.weekday()

    # House cusps
    planets = calc_planets(jd, None, 'mean')
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, 'P')
    cusps = house_data.get('cusps', [])
    asc_long = cusps[0] if cusps else 0.0

    # Gulika longitude
    gulika_long = _calc_gulika_longitude(jd, body.latitude, body.longitude, weekday)
    gulika_sign = _sign_from_long(gulika_long)
    gulika_house = _house_from_long(gulika_long, cusps)

    # Sign lord of the sign Gulika occupies
    gulika_sign_lord = SIGN_LORDS.get(gulika_sign, "Unknown")

    # Effects
    house_effect = SIGN_EFFECTS_GULIKA.get(gulika_house, {"house": str(gulika_house), "effect": "Mild negative influence."})

    # Gulika in which nakshatra
    gulika_nk = get_nakshatra(gulika_long)
    gulika_nak = gulika_nk['name']
    gulika_nak_pada = gulika_nk['pada']

    # Sun and other planets for context
    planets_list = calc_planets(jd, None, 'mean')
    pmap2 = {p['name']: p for p in planets_list}
    sun_long = pmap2.get('Sun', {}).get('longitude', 0.0)
    moon_long = pmap2.get('Moon', {}).get('longitude', 0.0)
    saturn_long = pmap2.get('Saturn', {}).get('longitude', 0.0)

    # Aspects on Gulika (Saturn's aspect especially malefic)
    aspects = []
    for pname, pdata in pmap2.items():
        plon = pdata.get("longitude", 0.0)
        diff = abs((gulika_long - plon + 180) % 360 - 180)
        if diff < 10:  # conjunction
            aspects.append({"planet": pname, "aspect": "conjunction", "orb": round(diff, 2)})
        elif abs(diff - 120) < 10:
            aspects.append({"planet": pname, "aspect": "trine", "orb": round(abs(diff - 120), 2)})
        elif abs(diff - 180) < 10:
            aspects.append({"planet": pname, "aspect": "opposition", "orb": round(abs(diff - 180), 2)})
        elif abs(diff - 90) < 10:
            aspects.append({"planet": pname, "aspect": "square", "orb": round(abs(diff - 90), 2)})

    # Overall assessment
    severity = "Low"
    if gulika_house in (1, 7, 8, 10):
        severity = "High"
    elif gulika_house in (2, 4, 5, 9, 11):
        severity = "Medium"
    elif gulika_house == 6:
        severity = "Medium (mixed – gives victory over enemies)"
    elif gulika_house == 12:
        severity = "Medium (expenditure and hospitalisation)"

    return {
        "status": "success",
        "input": {
            "dateOfBirth": body.dateOfBirth,
            "timeOfBirth": body.timeOfBirth,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "timezone": body.timezone,
        },
        "gulika": {
            "longitude": round(gulika_long, 4),
            "sign": gulika_sign,
            "sign_lord": gulika_sign_lord,
            "house": gulika_house,
            "nakshatra": gulika_nak,
            "nakshatra_pada": gulika_nak_pada,
            "effect": house_effect["effect"],
            "severity": severity,
            "aspects": aspects,
        },
        "weekday": weekday,
        "arc_minutes": GULIKA_ARC_MINUTES.get(weekday, 30.0),
        "context": {
            "sun_longitude": round(sun_long, 4),
            "moon_longitude": round(moon_long, 4),
            "saturn_longitude": round(saturn_long, 4),
            "ascendant_longitude": round(asc_long, 4),
        },
    }


# ──────────────────────────── Roga Nidana ────────────────────────────


@router.post("/horoscope/panchang/roga-nidana")
def roga_nidana(body: PanchakaRequest):
    """
    Disease prediction (Roga Nidana) based on:
    - 6th house and 6th lord
    - Mars and its position
    - Gulika position
    - Ascendant lord and ascendant sign
    """
    local_dt = _parse_local_dt(body.dateOfBirth, body.timeOfBirth, body.timezone)
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    weekday = local_dt.weekday()

    # Planets and houses
    planets_list = calc_planets(jd, None, 'mean')
    pmap = {p['name']: p for p in planets_list}
    house_data = calc_houses(jd, body.latitude, body.longitude, planets_list, 'P')
    cusps = house_data.get('cusps', [])
    asc_long = cusps[0] if cusps else 0.0
    asc_sign = _sign_from_long(asc_long)

    # 6th house cusp and sign
    sixth_cusp_long = cusps[5] if len(cusps) > 5 else (asc_long + 150) % 360
    sixth_sign = _sign_from_long(sixth_cusp_long)

    # 6th lord
    sixth_lord = SIGN_LORDS.get(sixth_sign, "Unknown")

    # Mars position
    mars_long = pmap.get('Mars', {}).get('longitude', 0.0)
    mars_sign = _sign_from_long(mars_long)
    mars_house = _house_from_long(mars_long, cusps)

    # Gulika position
    gulika_long = _calc_gulika_longitude(jd, body.latitude, body.longitude, weekday)
    gulika_sign = _sign_from_long(gulika_long)
    gulika_house = _house_from_long(gulika_long, cusps)

    # Saturn position (natural malefic)
    saturn_long = pmap.get('Saturn', {}).get('longitude', 0.0)
    saturn_sign = _sign_from_long(saturn_long)
    saturn_house = _house_from_long(saturn_long, cusps)

    # Rahu position
    rahu_long = pmap.get('Rahu', {}).get('longitude', 0.0)
    rahu_sign = _sign_from_long(rahu_long)
    rahu_house = _house_from_long(rahu_long, cusps)

    # 6th lord's house position
    sixth_lord_planet = None
    sixth_lord_house = 0
    for pname, pdata in pmap.items():
        if pname.lower() in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"):
            if pname.lower() == sixth_lord.lower():
                sixth_lord_planet = pname
                sixth_lord_house = _house_from_long(pdata.get("longitude", 0.0), cusps)
                break

    # ── Disease indications ──

    # 1. Mars afflictions
    mars_afflictions = []
    mars_body = SIGNS_BODY_PARTS.get(mars_sign, "")
    mars_disease = MARS_DISEASE_AFFLICTIONS.get(mars_sign, "General heat and inflammation related disorders.")
    mars_afflictions.append({
        "planet": "Mars",
        "sign": mars_sign,
        "house": mars_house,
        "body_part_at_risk": mars_body,
        "likely_diseases": mars_disease,
    })

    if mars_house in (1, 4, 7, 8, 12):
        mars_afflictions.append({
            "warning": "Mars in a Kendra or 8th/12th house amplifies disease potential.",
            "severity": "Elevated",
        })

    # Mars-Saturn conjunction or opposition
    mars_sat_diff = abs((mars_long - saturn_long + 180) % 360 - 180)
    if mars_sat_diff < 10:
        mars_afflictions.append({
            "warning": "Mars-Saturn conjunction: severe chronic illness, surgeries, accidents.",
            "severity": "Very High",
        })
    elif abs(mars_sat_diff - 180) < 10:
        mars_afflictions.append({
            "warning": "Mars-Saturn opposition: recurring illness, painful conditions.",
            "severity": "High",
        })

    # 2. 6th house indications
    sixth_house_diseases = SIXTH_LORD_DISEASES.get(sixth_sign, "General health issues related to the 6th house sign.")

    sixth_house_analysis = {
        "sixth_house_sign": sixth_sign,
        "sixth_lord": sixth_lord,
        "sixth_lord_in_house": sixth_lord_house,
        "sign_ruled": SIGNS_BODY_PARTS.get(sixth_sign, ""),
        "diseases_indicated": sixth_house_diseases,
    }

    # If 6th lord is in 6th, 8th, or 12th – strengthens disease potential
    if sixth_lord_house in (6, 8, 12):
        sixth_house_analysis["strength"] = "Strong disease potential – 6th lord in dusthana."
    elif sixth_lord_house in (1, 4, 7, 10):
        sixth_house_analysis["strength"] = "Moderate – 6th lord in Kendra."
    elif sixth_lord_house in (3, 6, 11):
        sixth_house_analysis["strength"] = "Reduced – 6th lord in Upachaya houses."

    # 3. Gulika health effects
    gulika_health = GULIKA_HEALTH_EFFECTS.get(gulika_house, "Minor health disturbances.")
    gulika_analysis = {
        "gulika_sign": gulika_sign,
        "gulika_house": gulika_house,
        "body_part_affected": SIGNS_BODY_PARTS.get(gulika_sign, ""),
        "disease_tendency": gulika_health,
    }

    # 4. 6th lord conjunct or aspected by malefics
    sixth_lord_vulnerability = []
    if sixth_lord_planet:
        s6_long = pmap.get(sixth_lord_planet, {}).get("longitude", 0.0)
        for pname, pdata in pmap.items():
            if pname == sixth_lord_planet:
                continue
            plon = pdata.get("longitude", 0.0)
            diff = abs((s6_long - plon + 180) % 360 - 180)
            if diff < 10 and pname in ("Mars", "Saturn", "Rahu", "Ketu"):
                sixth_lord_vulnerability.append({
                    "malefic": pname,
                    "aspect": "conjunction",
                    "orb": round(diff, 2),
                    "note": f"{sixth_lord} conjunct {pname} increases disease risk.",
                })
            elif abs(diff - 180) < 10 and pname in ("Mars", "Saturn", "Rahu", "Ketu"):
                sixth_lord_vulnerability.append({
                    "malefic": pname,
                    "aspect": "opposition",
                    "orb": round(abs(diff - 180), 2),
                    "note": f"{sixth_lord} opposed by {pname} increases disease risk.",
                })

    # 5. Ketu in 6th or 8th – hidden diseases
    ketu_long = (rahu_long + 180) % 360
    ketu_house = _house_from_long(ketu_long, cusps)
    hidden_disease_note = None
    if ketu_house in (6, 8, 12):
        hidden_disease_note = (
            f"Ketu in the {ketu_house}th house indicates hidden, undiagnosed, "
            "or psychosomatic diseases that are difficult to detect."
        )

    # ── Overall risk assessment ──
    risk_score = 0

    # Mars in 1/4/7/8/12
    if mars_house in (1, 4, 7, 8, 12):
        risk_score += 2
    # Mars-Saturn aspect
    if mars_sat_diff < 10 or abs(mars_sat_diff - 180) < 10:
        risk_score += 3
    # Gulika in 1/8
    if gulika_house in (1, 8):
        risk_score += 3
    elif gulika_house in (6, 12):
        risk_score += 2
    # 6th lord in dusthana
    if sixth_lord_house in (6, 8, 12):
        risk_score += 2
    # Rahu in 6/8/12
    if rahu_house in (6, 8, 12):
        risk_score += 2
    # Malefics conjunct 6th lord
    risk_score += len(sixth_lord_vulnerability)

    if risk_score >= 6:
        overall_risk = "Very High"
    elif risk_score >= 4:
        overall_risk = "High"
    elif risk_score >= 2:
        overall_risk = "Moderate"
    else:
        overall_risk = "Low"

    # ── Remedies ──
    remedies = [
        "Donate medicines to hospitals or patients on Tuesdays (for Mars).",
        "Feed stray dogs on Saturdays (for Saturn).",
        "Perform Rudra Abhishekam monthly for overall health protection.",
        "Chant Mrityunjaya Mantra 108 times daily.",
        "Worship Lord Dhanvantari on Ekadashi (11th lunar day).",
    ]
    if mars_house in (1, 8):
        remedies.append("Wear a copper bracelet or donate copper items on Tuesdays.")
    if gulika_house in (1, 8):
        remedies.append("Light a mustard oil lamp in a Shani temple on Saturdays.")
    if sixth_lord_house in (6, 8, 12):
        remedies.append("Perform Saturn remedies: donate black sesame, iron, and blue cloth on Saturdays.")
    if rahu_house in (6, 8, 12):
        remedies.append("Donate copper items or feed crows on Saturdays to pacify Rahu.")

    # Planet strengths for context
    planet_positions = {}
    for pname, pdata in pmap.items():
        plon = pdata.get("longitude", 0.0)
        planet_positions[pname] = {
            "longitude": round(plon, 4),
            "sign": _sign_from_long(plon),
            "house": _house_from_long(plon, cusps),
        }

    return {
        "status": "success",
        "input": {
            "dateOfBirth": body.dateOfBirth,
            "timeOfBirth": body.timeOfBirth,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "timezone": body.timezone,
        },
        "overall_risk": overall_risk,
        "risk_score": risk_score,
        "ascendant": {
            "sign": asc_sign,
            "lord": SIGN_LORDS.get(asc_sign, "Unknown"),
        },
        "mars_analysis": mars_afflictions,
        "sixth_house_analysis": sixth_house_analysis,
        "sixth_lord_vulnerability": sixth_lord_vulnerability,
        "gulika_analysis": gulika_analysis,
        "hidden_disease_note": hidden_disease_note,
        "planet_positions": planet_positions,
        "remedies": remedies,
    }
