from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import random
import swisseph as swe

from ..utils import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS, planet_status, get_nakshatra, ayanamsa_value

router = APIRouter()

class BirthRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")

class MonthlyTransitRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000, le=2100)


def _get_chart(body):
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, "mean")
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, "W")
    moon_sign = next((p['sign'] for p in planets if p['name'] == 'Moon'), 'Aries')
    sun_sign = next((p['sign'] for p in planets if p['name'] == 'Sun'), 'Aries')
    asc_sign = house_data['ascendant']['sign']
    pmap = {p['name']: p for p in planets}
    house_map = {h['number']: h for h in house_data['houses']}
    return jd, planets, house_data, moon_sign, sun_sign, asc_sign, pmap, house_map


# ══════════════════════════════════════════════
# BUSINESS PREDICTION
# ══════════════════════════════════════════════

_BUSINESS = {
    'Aries': {"overview": "Your entrepreneurial spirit thrives when leading from the front. Mars energy favors competitive industries, engineering, defense, sports, and ventures requiring bold initiative.", "strengths": "Leadership, decisiveness, courage to pioneer new markets, crisis handling", "challenges": "Impatience with slow growth, starting multiple ventures without completing", "sectors": "Manufacturing, sports equipment, defense, fire-related industries, restaurants, iron/steel, automotive"},
    'Taurus': {"overview": "Venus blesses you with an eye for beauty, luxury, and value creation. You build businesses that last through patient accumulation of wealth and assets.", "strengths": "Patience, financial acumen, lasting value creation, quality sense", "challenges": "Resistance to pivoting when markets change, slow to innovate", "sectors": "Banking, jewelry, luxury goods, agriculture, food processing, interior design, fashion, textiles"},
    'Gemini': {"overview": "Mercury makes you a natural communicator. Media, publishing, trading, and technology businesses thrive under your versatile mind.", "strengths": "Adaptability, networking, multitasking, quick learning, trend-spotting", "challenges": "Scattered focus, starting too many projects, difficulty with routine", "sectors": "Media, publishing, digital marketing, stock trading, e-commerce, consulting, telecom"},
    'Cancer': {"overview": "The Moon-ruled entrepreneur builds businesses centered on care, nurturing, and emotional connection. Food, hospitality, real estate, and healthcare align with your nature.", "strengths": "Emotional intelligence, loyalty building, intuitive understanding of needs", "challenges": "Taking business setbacks personally, mood-driven decisions", "sectors": "Food/restaurant, real estate, healthcare, childcare, hotel, antiques, dairy, Ayurveda"},
    'Leo': {"overview": "The Sun-ruled entrepreneur shines in entertainment, leadership roles, and creative industries. Luxury and premium services suit your generous personality.", "strengths": "Charisma, creative vision, natural authority, brand building", "challenges": "Ego-driven decisions, overspending on image, difficulty accepting failure", "sectors": "Entertainment, fashion, luxury brands, events, politics, gold/jewelry, education"},
    'Virgo': {"overview": "Mercury's analytical side excels in precision-based businesses. Healthcare, accounting, IT, quality consulting benefit from your meticulous approach.", "strengths": "Quality control, process optimization, analytical thinking, reliability", "challenges": "Perfectionism causing delays, over-thinking, inability to delegate", "sectors": "Healthcare, pharmacy, accounting, IT services, food safety, agriculture research, auditing"},
    'Libra': {"overview": "Venus-ruled Libra thrives in partnership-based businesses. Art, beauty, law, diplomacy, and design are your natural domains.", "strengths": "Partnership building, aesthetic sense, negotiation, social connections", "challenges": "Indecisiveness, conflict avoidance, dependency on partners", "sectors": "Art/decor, fashion, legal services, wedding planning, cosmetics, architecture, PR"},
    'Scorpio': {"overview": "Pluto and Mars give investigative depth and transformative power. Businesses involving research, finance, psychology, and hidden resources thrive.", "strengths": "Strategic thinking, research ability, complexity handling, resilience", "challenges": "Trust issues in partnerships, secrecy causing communication breakdowns", "sectors": "Finance, psychology, investigations, mining, insurance, pharmaceuticals, occult sciences"},
    'Sagittarius': {"overview": "Jupiter blesses expansive ventures. Education, publishing, international trade, philosophy, and advisory roles align with your truth-seeking nature.", "strengths": "Vision, optimism, international perspective, teaching ability, ethical approach", "challenges": "Overexpansion, unrealistic optimism, difficulty with details", "sectors": "Education, publishing, import/export, travel, consulting, religious/spiritual services, law"},
    'Capricorn': {"overview": "Saturn's disciplined child builds empires through patience and hard work. Corporate roles, government contracts, and structured businesses yield lasting rewards.", "strengths": "Discipline, long-term planning, organizational skills, perseverance", "challenges": "Over-caution, reluctance to take calculated risks, workaholic tendencies", "sectors": "Real estate, mining, infrastructure, government contracts, manufacturing, agriculture, steel"},
    'Aquarius': {"overview": "Saturn and Uranus create innovative entrepreneurs. Technology, social enterprises, and unconventional ventures that break traditional molds suit you.", "strengths": "Innovation, humanitarian vision, tech-savvy, unconventional thinking", "challenges": "Detachment from team, alienating conventional partners, stubborn individualism", "sectors": "Technology, AI, renewable energy, social enterprises, aviation, telecommunications, research"},
    'Pisces': {"overview": "Jupiter and Neptune give visionary intuition. Creative businesses, healing arts, spirituality, and film/media industries align with your compassionate, imaginative nature.", "strengths": "Intuition, compassion, creative vision, spiritual insight, empathy", "challenges": "Unrealistic expectations, difficulty with business boundaries, escapism", "sectors": "Film, photography, healing arts, spirituality, marine industries, charity, music, dance"},
}


@router.post("/horoscope/business")
def business_prediction(body: BirthRequest) -> Dict[str, Any]:
    jd, planets, house_data, moon_sign, sun_sign, asc_sign, pmap, house_map = _get_chart(body)
    templates = _BUSINESS.get(sun_sign, _BUSINESS['Aries'])

    jup_house = pmap.get('Jupiter', {}).get('house', 0)
    ven_house = pmap.get('Venus', {}).get('house', 0)
    sat_house = pmap.get('Saturn', {}).get('house', 0)
    mer_house = pmap.get('Mercury', {}).get('house', 0)

    wealth_analysis = "2nd and 11th house lords are well-placed for steady income." if house_map.get(2, {}).get('signLord') in ['Jupiter', 'Venus', 'Mercury'] else "Financial growth requires patience and strategic planning."
    career_note = ""
    if jup_house in [1, 5, 9, 10, 11]:
        career_note = "Jupiter in a favorable house strongly supports business expansion and advisory roles."
    if sat_house in [10, 11]:
        career_note += " Saturn in career houses brings steady, structured growth through discipline."

    return {
        "success": True,
        "data": {
            "sunSign": sun_sign, "moonSign": moon_sign, "ascendant": asc_sign,
            "overview": templates["overview"],
            "strengths": templates["strengths"],
            "challenges": templates["challenges"],
            "bestSectors": templates["sectors"],
            "wealthAnalysis": wealth_analysis.strip(),
            "careerNote": career_note.strip() or "Focus on consistent effort and skill development for business success.",
            "planetaryInfluences": {
                "jupiterHouse": jup_house, "venusHouse": ven_house,
                "saturnHouse": sat_house, "mercuryHouse": mer_house,
            },
            "businessTiming": "Transits of Jupiter through your 2nd, 7th, 10th, and 11th houses mark periods of business growth."
        }
    }


# ══════════════════════════════════════════════
# EDUCATION PREDICTION
# ══════════════════════════════════════════════

_EDUCATION = {
    'Aries': {"overview": "Your competitive nature drives academic excellence in science, engineering, sports, and leadership programs. You thrive in hands-on, challenging environments.", "learning_style": "Kinesthetic learner — learn by doing, competing, and leading projects", "best_fields": "Engineering, sports science, military studies, emergency medicine, entrepreneurship", "exam_luck": "Strong during Mars transits — time important exams during Mars in Aries or Scorpio"},
    'Taurus': {"overview": "Patient and methodical, you excel in arts, commerce, finance, and music. Your steady approach ensures deep learning and excellent retention.", "learning_style": "Visual and sensory learner — need comfortable environment and aesthetic surroundings", "best_fields": "Commerce, finance, arts, music, architecture, agriculture science, culinary arts", "exam_luck": "Venus transits favor creative and financial subjects — plan accordingly"},
    'Gemini': {"overview": "Mercury makes you a versatile scholar. Communication, media, languages, and technology are natural strengths. You pick up new subjects quickly.", "learning_style": "Auditory and social learner — discussions, group study, and multimedia resources work best", "best_fields": "Journalism, languages, IT, marketing, research, teaching, content creation", "exam_luck": "Mercury periods favor analytical and communication-based exams"},
    'Cancer': {"overview": "Your emotional intelligence aids learning in psychology, history, hospitality, and care-related fields. You absorb information through emotional connection.", "learning_style": "Emotional and visual learner — need safe, nurturing study environment", "best_fields": "Psychology, history, hospitality, teaching, nursing, social work, real estate", "exam_luck": "Moon periods enhance memory and emotional recall — leverage these for exams"},
    'Leo': {"overview": "Creative and dramatic, you excel in arts, performing arts, politics, and leadership programs. Your confidence helps in presentations and public speaking.", "learning_style": "Visual and performative learner — need recognition and creative outlets", "best_fields": "Performing arts, media, political science, public administration, design, fashion", "exam_luck": "Sun transits boost confidence — present and lead during these periods"},
    'Virgo': {"overview": "Analytical and detail-oriented, you excel in science, medicine, statistics, and research. Your methodical approach ensures thorough understanding.", "learning_style": "Analytical learner — need structured notes, detailed textbooks, and systematic study plans", "best_fields": "Medicine, data science, statistics, pharmacy, environmental science, accounting", "exam_luck": "Mercury and Saturn periods favor analytical and detail-heavy exams"},
    'Libra': {"overview": "Venus-ruled balance helps in law, arts, social sciences, and design. You thrive in collaborative and aesthetically rich learning environments.", "learning_style": "Social and aesthetic learner — study groups and beautiful spaces enhance focus", "best_fields": "Law, interior design, fine arts, political science, fashion, diplomacy, counseling", "exam_luck": "Venus periods favor creative and humanities-based subjects"},
    'Scorpio': {"overview": "Deep research ability makes you suited for investigation, psychology, occult sciences, and medical research. You uncover hidden depths in any subject.", "learning_style": "Deep focus learner — need solitude and intensity, prefer mastering one subject thoroughly", "best_fields": "Psychology, research, forensic science, philosophy, medical research, cybersecurity", "exam_luck": "Pluto and Mars periods favor deep research and investigation-based work"},
    'Sagittarius': {"overview": "Jupiter's blessings make you a natural philosopher. Higher education, foreign studies, philosophy, and advisory fields align with your quest for truth.", "learning_style": "Exploratory learner — travel, real-world experiences, and philosophical discussions enhance learning", "best_fields": "Philosophy, international relations, law, theology, higher education, travel/tourism", "exam_luck": "Jupiter periods strongly favor higher education and competitive exams"},
    'Capricorn': {"overview": "Saturn's discipline ensures you complete what you start. Management, engineering, and structured programs suit your patient, hardworking nature.", "learning_style": "Structured learner — need clear goals, timelines, and practical applications", "best_fields": "Management, engineering, architecture, government services, urban planning", "exam_luck": "Saturn periods reward sustained, disciplined study — avoid shortcuts"},
    'Aquarius': {"overview": "Innovation and technology are your strengths. You excel in STEM fields, especially emerging technologies and unconventional academic paths.", "learning_style": "Independent and tech-savvy learner — online courses, innovative tools, and peer networks", "best_fields": "Computer science, AI/ML, aerospace, renewable energy, social sciences, innovation studies", "exam_luck": "Uranus transits bring sudden breakthroughs — stay open to unconventional approaches"},
    'Pisces': {"overview": "Jupiter and Neptune give strong intuitive and creative abilities. Arts, spirituality, healing, and film studies align with your imaginative mind.", "learning_style": "Intuitive and creative learner — need music, art, or spiritual practice alongside studies", "best_fields": "Fine arts, film, music, psychology, healing arts, marine biology, spirituality", "exam_luck": "Jupiter and Neptune periods enhance creativity — use artistic approaches to study"},
}


@router.post("/horoscope/education")
def education_prediction(body: BirthRequest) -> Dict[str, Any]:
    jd, planets, house_data, moon_sign, sun_sign, asc_sign, pmap, house_map = _get_chart(body)
    templates = _EDUCATION.get(sun_sign, _EDUCATION['Aries'])

    mer = pmap.get('Mercury', {})
    jup = pmap.get('Jupiter', {})
    mercury_house = mer.get('house', 0)
    mercury_sign = mer.get('sign', '')
    jupiter_house = jup.get('house', 0)

    study_tips = []
    if mercury_house in [1, 5, 9]:
        study_tips.append("Mercury in a trine house gives natural intelligence — leverage analytical subjects.")
    if jupiter_house in [1, 5, 9, 11]:
        study_tips.append("Jupiter's favorable placement supports higher education and competitive exams.")
    if mercury_house in [4, 10]:
        study_tips.append("Mercury in kendras gives practical, career-oriented learning ability.")
    if not study_tips:
        study_tips.append("Focus on consistent daily study habits and seek mentorship for best results.")

    return {
        "success": True,
        "data": {
            "sunSign": sun_sign, "moonSign": moon_sign, "ascendant": asc_sign,
            "overview": templates["overview"],
            "learningStyle": templates["learning_style"],
            "bestFields": templates["best_fields"],
            "examLuck": templates["exam_luck"],
            "studyTips": study_tips,
            "mercuryInfluence": {"house": mercury_house, "sign": mercury_sign, "status": planet_status('Mercury', mercury_sign)},
            "jupiterInfluence": {"house": jupiter_house, "sign": jup.get('sign', ''), "status": planet_status('Jupiter', jup.get('sign', ''))},
            "bestPeriodsForStudy": "Jupiter and Mercury transits through your 1st, 5th, and 9th houses are especially favorable for academic progress."
        }
    }


# ══════════════════════════════════════════════
# CHILD PREDICTION
# ══════════════════════════════════════════════

@router.post("/horoscope/child")
def child_prediction(body: BirthRequest) -> Dict[str, Any]:
    jd, planets, house_data, moon_sign, sun_sign, asc_sign, pmap, house_map = _get_chart(body)

    fifth_house = house_map.get(5, {})
    fifth_sign = fifth_house.get('sign', '')
    fifth_lord = fifth_house.get('signLord', '')
    jup = pmap.get('Jupiter', {})
    sun = pmap.get('Sun', {})

    jup_house = jup.get('house', 0)
    jup_sign = jup.get('sign', '')
    jup_status = planet_status('Jupiter', jup_sign)

    fifth_lord_planet = pmap.get(fifth_lord, {})
    fifth_lord_house = fifth_lord_planet.get('house', 0)
    fifth_lord_retro = fifth_lord_planet.get('isRetrograde', False)

    favorable = jup_house in [1, 4, 5, 7, 9, 11] and jup_status in ['Exalted', 'Own Sign', 'Mooltrikona', 'Friendly']
    timing = "Favorable period for progeny" if favorable else "Challenges indicated — remedies recommended"

    child_gender_note = "5th house sign and Jupiter influence suggest the nature of progeny."
    if fifth_sign in ['Aries', 'Leo', 'Sagittarius', 'Gemini', 'Libra', 'Aquarius']:
        child_gender_note = "5th house in masculine sign with Jupiter support indicates strong prospects for children."
    elif fifth_sign in ['Cancer', 'Scorpio', 'Pisces', 'Taurus', 'Virgo', 'Capricorn']:
        child_gender_note = "5th house in feminine sign — progeny matters connected to emotional fulfillment."

    remedies = []
    if not favorable:
        remedies = ["Jupiter beeja mantra (Om Gram Greem Graum Sah Gurave Namaha)", "Worship Lord Vishnu on Thursdays", "Donate yellow items on Thursdays", "Fast on Thursdays for 16 weeks"]

    return {
        "success": True,
        "data": {
            "sunSign": sun_sign, "moonSign": moon_sign, "ascendant": asc_sign,
            "fifthHouse": {"sign": fifth_sign, "lord": fifth_lord, "planets": fifth_house.get('planets', [])},
            "jupiter": {"house": jup_house, "sign": jup_sign, "status": jup_status, "retrograde": jup.get('isRetrograde', False)},
            "prospects": timing,
            "childNature": child_gender_note,
            "fifthLordPlacement": {"house": fifth_lord_house, "retrograde": fifth_lord_retro},
            "timingNote": "Jupiter transiting 5th house or aspecting natal Jupiter marks favorable conception periods.",
            "remedies": remedies,
            "overallAssessment": "Strong" if favorable else "Requires patience and remedies — not impossible, just needs timing"
        }
    }


# ══════════════════════════════════════════════
# FOREIGN SETTLEMENT PREDICTION
# ══════════════════════════════════════════════

@router.post("/horoscope/foreign")
def foreign_settlement(body: BirthRequest) -> Dict[str, Any]:
    jd, planets, house_data, moon_sign, sun_sign, asc_sign, pmap, house_map = _get_chart(body)

    twelfth_house = house_map.get(12, {})
    twelfth_sign = twelfth_house.get('sign', '')
    twelfth_lord = twelfth_house.get('signLord', '')

    rahu = pmap.get('Rahu', {})
    rahu_house = rahu.get('house', 0)
    rahu_sign = rahu.get('sign', '')

    fourth_house = house_map.get(4, {})
    fourth_lord = fourth_house.get('signLord', '')
    fourth_lord_planet = pmap.get(fourth_lord, {})
    fourth_lord_house = fourth_lord_planet.get('house', 0)

    twelfth_lord_planet = pmap.get(twelfth_lord, {})
    twelfth_lord_house = twelfth_lord_planet.get('house', 0)

    foreign_score = 0
    reasons = []

    if rahu_house in [12, 1, 4, 7, 10]:
        foreign_score += 30
        reasons.append(f"Rahu in house {rahu_house} strongly indicates foreign connection")
    if twelfth_lord_house in [1, 4, 7, 10]:
        foreign_score += 25
        reasons.append(f"12th lord in house {twelfth_lord_house} supports foreign residence")
    if fourth_lord_house == 12:
        foreign_score += 20
        reasons.append("4th lord in 12th house — native leaves homeland")
    if rahu_house == 12:
        foreign_score += 15
        reasons.append("Rahu in 12th house — strong foreign settlement indication")
    if twelfth_house.get('planets', []):
        foreign_score += 10
        reasons.append(f"Planets in 12th house ({', '.join(twelfth_house['planets'])}) activate foreign connections")

    if foreign_score >= 60:
        likelihood = "Very Strong"
    elif foreign_score >= 35:
        likelihood = "Moderate to Strong"
    elif foreign_score >= 15:
        likelihood = "Possible with effort"
    else:
        likelihood = "Limited indication — can be enhanced through remedies"

    best_timing = "Jupiter or Rahu transits through 12th house or 4th house indicate favorable periods for foreign travel/settlement."

    return {
        "success": True,
        "data": {
            "sunSign": sun_sign, "moonSign": moon_sign, "ascendant": asc_sign,
            "foreignSettlementScore": foreign_score,
            "likelihood": likelihood,
            "reasons": reasons,
            "twelfthHouse": {"sign": twelfth_sign, "lord": twelfth_lord, "planets": twelfth_house.get('planets', [])},
            "rahu": {"house": rahu_house, "sign": rahu_sign},
            "bestTiming": best_timing,
            "favorableCountries": "Western and far-away directions from birthplace are generally favored when Rahu is strong.",
            "remedies": ["Worship Lord Vishnu", "Donate to charity abroad", "Wear Hessonite (Gomed) if Rahu is strong", "Travel during Jupiter transits"]
        }
    }


# ══════════════════════════════════════════════
# MONTHLY TRANSIT
# ══════════════════════════════════════════════

_TRANSIT_EFFECTS = {
    'Sun': {"positive": "Leadership recognition, government favor, authority increases", "challenging": "Ego clashes with authority, health issues for father figures", "neutral": "Self-identity focus, father-related matters"},
    'Moon': {"positive": "Emotional fulfillment, mother's health improves, public support", "challenging": "Emotional instability, mind restlessness, travel delays", "neutral": "Domestic changes, property matters, inner reflection"},
    'Mars': {"positive": "Energy surge, property gains, sibling support, courage", "challenging": "Accidents, conflicts, surgery, litigation", "neutral": "Physical activity, competitive ventures, renovation"},
    'Mercury': {"positive": "Business gains, communication success, education progress", "challenging": "Miscommunication, skin issues, nervous tension", "neutral": "Trade, writing, analytical work, short trips"},
    'Jupiter': {"positive": "Wisdom, children blessed, wealth increases, spiritual growth", "challenging": "Weight gain, overconfidence, expansion without planning", "neutral": "Education, teaching, religious activities, counsel"},
    'Venus': {"positive": "Romance, luxury, vehicle purchase, artistic success", "challenging": "Indulgence, relationship confusion, expenses on pleasure", "neutral": "Aesthetics, social events, marriage-related matters"},
    'Saturn': {"positive": "Discipline brings results, long-term projects succeed", "challenging": "Delays, health issues, hard work without immediate reward", "neutral": "Service, duty, restructuring, karmic lessons"},
    'Rahu': {"positive": "Unconventional gains, foreign connections, technology breakthroughs", "challenging": "Confusion, deception, sudden upheavals, health anomalies", "neutral": "Obsessions, ambition, breaking traditional patterns"},
    'Ketu': {"positive": "Spiritual detachment, sudden insights, liberation", "challenging": "Losses, isolation, confusion about identity", "neutral": "Meditation, research, letting go, past-life karma resolution"},
}


@router.post("/horoscope/transit/monthly")
def monthly_transit(body: MonthlyTransitRequest) -> Dict[str, Any]:
    from datetime import date as _date, timedelta as _td
    jd, planets, house_data, moon_sign, sun_sign, asc_sign, pmap, house_map = _get_chart(body)

    today = _date.today()
    target_month = body.month or today.month
    target_year = body.year or today.year

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    transit_positions = []
    for pname, pid in [('Sun', swe.SUN), ('Moon', swe.MOON), ('Mars', swe.MARS), ('Mercury', swe.MERCURY),
                        ('Jupiter', swe.JUPITER), ('Venus', swe.VENUS), ('Saturn', swe.SATURN),
                        ('Rahu', swe.TRUE_NODE)]:
        try:
            calc = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
            lon = calc[0][0]
            sign_idx = int(lon // 30)
            sign = ZODIAC_SIGNS[sign_idx]
            degree = lon % 30
            house_num = 0
            for h in house_data['houses']:
                if h['sign'] == sign:
                    house_num = h['number']
                    break
            transit_positions.append({"planet": pname, "sign": sign, "degree": round(degree, 2), "house": house_num})
        except Exception:
            continue

    monthly_readings = []
    for tp in transit_positions:
        pname = tp['planet']
        effects = _TRANSIT_EFFECTS.get(pname, {"positive": "General positive influence", "challenging": "May face minor challenges", "neutral": "Steady period"})
        impact_house = tp['house']

        if impact_house in [1, 5, 9, 11]:
            tone = "positive"
        elif impact_house in [6, 8, 12]:
            tone = "challenging"
        else:
            tone = "neutral"

        monthly_readings.append({
            "planet": pname,
            "transitSign": tp['sign'],
            "houseFromAscendant": impact_house,
            "tone": tone,
            "effects": effects[tone],
            "fullEffects": effects,
        })

    pos_count = sum(1 for r in monthly_readings if r['tone'] == 'positive')
    neg_count = sum(1 for r in monthly_readings if r['tone'] == 'challenging')
    if pos_count >= 3:
        overall = "Favorable"
    elif neg_count >= 3:
        overall = "Challenging"
    else:
        overall = "Mixed"

    return {
        "success": True,
        "data": {
            "month": target_month, "year": target_year,
            "sunSign": sun_sign, "moonSign": moon_sign, "ascendant": asc_sign,
            "overallMonth": overall,
            "planetaryTransits": transit_positions,
            "detailedReadings": monthly_readings,
            "advice": "Focus on planets transiting your 1st, 5th, 9th, and 11th houses for opportunities. Navigate carefully when planets transit 6th, 8th, or 12th houses."
        }
    }
