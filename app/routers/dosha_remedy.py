from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from ..utils import to_julian, calc_planets, calc_houses, get_sign, get_nakshatra, ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status

router = APIRouter()

# Compact remedy database: (causing_planets, life_areas, mantras, gems, charity, pujas, fasting_day, fasting_dur, fasting_notes, ausp_days, ausp_tithis, ausp_naks, temp, perm)
_DB: Dict[str, Dict[str, Any]] = {
    'Mangal Dosha': {
        'causing_planets': ['Mars'],
        'life_areas': ['Marriage', 'Relationships', 'Anger management', 'Property disputes'],
        'mantras': ['Om Ang Angarakaya Namaha – 108x daily', 'Mangal Beej Mantra: Om Kraam Kreem Kraum Sah Bhaumaya Namaha', 'Hanuman Chalisa – every Tuesday', 'Satyanarayan Puja on full moon days'],
        'gems': {'primary': 'Red Coral (Moonga)', 'metal': 'Copper/Gold', 'weight': '3-6 carats', 'finger': 'Ring finger right hand', 'wear_day': 'Tuesday Shukla Paksha'},
        'charity': ['Red lentils (masoor dal) on Tuesdays', 'Sweets to soldiers/policemen', 'Copper utensils to temples', 'Land/property-related items'],
        'pujas': ['Kumbh Vivah – symbolic marriage to Vishnu idol before wedding', 'Mangal Graha Shanti Puja', 'Rudra Abhishek with red flowers', 'Angaraka Homa'],
        'fasting': {'day': 'Tuesday', 'duration': '16 consecutive Tuesdays', 'items': 'One meal before sunset; avoid salt'},
        'auspicious': {'days': ['Tuesday', 'Saturday'], 'tithis': 'Shashthi, Saptami', 'nakshatras': 'Mrigashira, Chitra, Dhanishta', 'muhurta': 'Mars hora Tuesdays'},
        'temporary': ['Chant Hanuman Chalisa daily', 'Red thread on wrist', 'Offer jaggery on Tuesdays'],
        'permanent': ['Kumbh Vivah before first marriage', 'Mangal Graha Shanti Puja', 'Tuesday fasting for life', 'Donation of gold/copper'],
    },
    'Kaal Sarp Dosha': {
        'causing_planets': ['Rahu', 'Ketu'],
        'life_areas': ['Career delays', 'Financial instability', 'Psychological stress', 'Ancestral karma', 'Unexpected obstacles'],
        'mantras': ['Om Namah Shivaya – 108x daily', 'Maha Mrityunjaya Mantra – 108x', 'Rahu Beej: Om Raam Rahave Namaha', 'Ketu Beej: Om Ketave Namaha'],
        'gems': {'primary': "Hessonite (Gomed) for Rahu / Cat's Eye (Lehsunia) for Ketu", 'metal': 'Silver/Panchdhatu', 'weight': '4-7 carats', 'finger': 'Middle finger', 'wear_day': 'Saturday evening Rahu Kaal'},
        'charity': ['Sweets with coconut on Saturdays', 'Silver serpent idols to temples', 'Feed stray dogs', 'Blankets to the needy in winter'],
        'pujas': ['Rahu-Ketu Shanti at Kalahasti/Trayambakeshwar', 'Nag Panchami Puja with milk', 'Rudra Abhishek on Mondays', 'Maha Mrityunjaya Homa'],
        'fasting': {'day': 'Saturday / Nag Panchami', 'duration': '40 days', 'items': 'Fruit diet or single meal; no alcohol/non-veg'},
        'auspicious': {'days': ['Saturday', 'Wednesday'], 'tithis': 'Ekadashi, Chaturdashi', 'nakshatras': 'Ardra, Swati, Shatabhisha', 'muhurta': 'Rahu Kaal Saturdays'},
        'temporary': ['Feed orphans', 'Pour milk on Shiva lingam', 'Keep silver ball in water'],
        'permanent': ['Kaal Sarp Shanti at Trayambakeshwar', "Wear Gomed/Cat's Eye", 'Nag Devta worship on Nag Panchami yearly'],
    },
    'Pitra Dosha': {
        'causing_planets': ['Sun', 'Rahu', 'Ketu'],
        'life_areas': ['Ancestral peace', 'Progeny health', 'Financial losses', 'Legal troubles', 'Unexplained sufferings'],
        'mantras': ['Gayatri Mantra – 108x daily at sunrise', 'Pitru Gayatri: Om Pitrabhyah Pitru Matarubhyo Namaha', 'Mahamrityunjaya Mantra', 'Pitru Stotram during Pitru Paksha'],
        'gems': {'primary': 'Ruby (Manikya) for Sun', 'metal': 'Gold', 'weight': '3-5 carats', 'finger': 'Ring finger right hand', 'wear_day': 'Sunday Shukla Paksha'},
        'charity': ['Feed Brahmins/destitute during Pitru Paksha', 'Sesame seeds (til) on Saturdays', 'Water with milk & sesame to ancestors', 'Sponsor education for underprivileged'],
        'pujas': ['Pind Daan at Gaya/river banks', 'Shraddha during Pitru Paksha', 'Pitru Tarpan with black sesame & barley', 'Narayan Bali Puja for ancestral pacification'],
        'fasting': {'day': 'Amavasya / Pitru Paksha', 'duration': '3 days during Pitru Paksha annually', 'items': 'Avoid salt; Satvik food only'},
        'auspicious': {'days': ['Sunday', 'Amavasya'], 'tithis': 'Amavasya, Purnima, Darsha', 'nakshatras': 'Krittika, Pushya, Revati', 'muhurta': 'Sunrise or sunset'},
        'temporary': ['Water to Peepal tree Saturdays', 'Mustard oil lamp on Amavasya', 'Feed cows green fodder'],
        'permanent': ['Annual Shraddha during Pitru Paksha', 'Pind Daan at sacred rivers', 'Regular Gayatri Mantra', 'Narayan Bali Puja once'],
    },
    'Shani Dosha': {
        'causing_planets': ['Saturn'],
        'life_areas': ['Delays & obstacles', 'Career challenges', 'Bone/joint health', 'Mental depression', 'Karmic debts'],
        'mantras': ['Om Sham Shanaishcharaya Namaha – 108x', 'Shani Beej: Om Kraam Kreem Kraum Sah Shanaishcharaya Namaha', 'Hanuman Chalisa every Saturday', 'Dashrath Krit Shani Stotram'],
        'gems': {'primary': 'Blue Sapphire (Neelam)', 'metal': 'Silver/Panchdhatu', 'weight': '4-7 carats', 'finger': 'Middle finger right hand', 'wear_day': 'Saturday evening Shani Hora', 'caution': 'Test 3 days before permanent wearing'},
        'charity': ['Iron items & black sesame on Saturdays', 'Clothe servants/laborers/disabled', 'Blue/black blankets in winter', 'Food to crows on Saturdays'],
        'pujas': ['Shani Shanti at Shani Shingnapur', 'Dashrath Krit Stotra Path', 'Vrischik Dosha Nivaran', 'Rudra Abhishek with sesame oil lamp'],
        'fasting': {'day': 'Saturday', 'duration': '9 or 16 consecutive Saturdays', 'items': 'Eat after sunset; black lentils or khichdi only'},
        'auspicious': {'days': ['Saturday'], 'tithis': 'Ekadashi, Chaturdashi, Amavasya', 'nakshatras': 'Pushya, Anuradha, Uttara Bhadrapada', 'muhurta': 'Shani Hora Saturdays'},
        'temporary': ['Walk barefoot on grass Saturdays', 'Mustard oil lamp under Peepal', 'Chant Hanuman Chalisa daily'],
        'permanent': ['Wear Blue Sapphire (after testing)', 'Saturday fasting for life', 'Lifetime charity to laborers', 'Shani Shanti at Shani temple'],
    },
    'Guru Chandal Dosha': {
        'causing_planets': ['Jupiter', 'Rahu'],
        'life_areas': ['Wisdom & discernment', 'Education', 'Spiritual guidance', 'Financial fraud risk', 'Trust issues'],
        'mantras': ['Om Gram Greem Graum Sah Guruve Namaha', 'Vishnu Sahasranama weekly', 'Brihaspati Stotram'],
        'gems': {'primary': 'Yellow Sapphire (Pukhraj)', 'metal': 'Gold', 'weight': '4-6 carats', 'finger': 'Index finger right hand', 'wear_day': 'Thursday Shukla Paksha'},
        'charity': ['Yellow gram (chana dal) on Thursdays', 'Books/educational materials', 'Turmeric & yellow cloth to temples', 'Feed Brahmins on Thursdays'],
        'pujas': ['Guru (Brihaspati) Graha Shanti', 'Satyanarayan Katha / Vishnu worship', 'Guruwar Puja with yellow flowers', 'Dakshinamurthy Stotram'],
        'fasting': {'day': 'Thursday', 'duration': '16 consecutive Thursdays', 'items': 'Yellow food only (dal, turmeric rice); no alcohol'},
        'auspicious': {'days': ['Thursday', 'Wednesday'], 'tithis': 'Purnima, Ekadashi', 'nakshatras': 'Punarvasu, Vishakha, Purva Bhadrapada', 'muhurta': 'Guru Hora Thursdays'},
        'temporary': ['Ghee lamp in temple Thursdays', 'Chant Vishnu Sahasranama', 'Wear yellow on Thursdays'],
        'permanent': ['Wear Yellow Sapphire in gold', 'Thursday fasting for life', 'Vishnu Sahasranama weekly', 'Guru Graha Shanti Puja'],
    },
    'Kemadruma Dosha': {
        'causing_planets': ['Moon'],
        'life_areas': ['Mental peace', 'Emotional stability', "Mother's health", 'Financial flow', 'Public support'],
        'mantras': ['Om Chandraya Namaha – 108x', 'Chandra Beej: Om Shram Shreem Shraum Sah Chandraya Namaha', 'Durga Saptashati during Navratri', 'Mahamrityunjaya Mantra Mondays'],
        'gems': {'primary': 'Pearl (Moti)', 'metal': 'Silver', 'weight': '4-8 carats', 'finger': 'Little finger right hand', 'wear_day': 'Monday Shukla Paksha (Purnima)'},
        'charity': ['Rice & milk on Mondays', 'White sweets & clothes', 'Feed young girls', 'Silver items to mothers'],
        'pujas': ['Chandra Graha Shanti', 'Shiva Abhishek with milk Mondays', 'Lakshmi Puja Fridays', 'Durga Puja during Navratri'],
        'fasting': {'day': 'Monday', 'duration': '9 or 16 consecutive Mondays', 'items': 'Fruit & milk only; no salt Mondays'},
        'auspicious': {'days': ['Monday', 'Friday'], 'tithis': 'Purnima, Shukla Paksha', 'nakshatras': 'Rohini, Hasta, Shravana', 'muhurta': 'Moon Hora Mondays'},
        'temporary': ['Water from silver vessel', 'Conch shell at home', 'Wear white Mondays'],
        'permanent': ['Wear Pearl in silver', 'Monday fasting for life', 'Shiva Abhishek Mondays', 'Plant a Peepal tree'],
    },
    'Angarak Dosha': {
        'causing_planets': ['Mars'],
        'life_areas': ['Temper & aggression', 'Surgery risk', 'Conflicts', 'Property disputes', 'Accidents'],
        'mantras': ['Om Ang Angarakaya Namaha – 108x', 'Mars Beej: Om Kraam Kreem Kraum Sah Bhaumaya Namaha', 'Hanuman Chalisa daily', 'Sundarkand Path Tuesdays'],
        'gems': {'primary': 'Red Coral (Moonga)', 'metal': 'Copper/Gold', 'weight': '3-5 carats', 'finger': 'Ring finger right hand', 'wear_day': 'Tuesday Shukla Paksha'},
        'charity': ['Red lentils Tuesdays', 'Copper items to young men', 'Laddoos at Hanuman temples', 'Sweets to siblings'],
        'pujas': ['Hanuman Puja every Tuesday', 'Mangal Homa (fire ritual)', 'Sundarkand Path', 'Shri Ram Raksha Stotra'],
        'fasting': {'day': 'Tuesday', 'duration': '21 or 40 consecutive Tuesdays', 'items': 'One meal only; complete fast if possible'},
        'auspicious': {'days': ['Tuesday', 'Saturday'], 'tithis': 'Saptami, Sashthi', 'nakshatras': 'Mrigashira, Chitra', 'muhurta': 'Mars Hora Tuesdays'},
        'temporary': ['Sindoor at Hanuman temple', 'Offer jaggery Tuesdays', 'Chant Bajrang Baan'],
        'permanent': ['Wear Red Coral (after testing)', 'Tuesday fasting for life', 'Daily Hanuman Chalisa', 'Regular Hanuman Puja at temple'],
    },
    'Sade Sati': {
        'causing_planets': ['Saturn', 'Moon'],
        'life_areas': ['Emotional trials', 'Career setbacks', 'Health concerns', 'Mental pressure', 'Transformation & growth'],
        'mantras': ['Om Sham Shanaishcharaya Namaha – 108x', 'Neel Nandan Bhairav Mantra', 'Shani Chalisa every Saturday', 'Shiva Tandava Stotram'],
        'gems': {'primary': 'Blue Sapphire (Neelam) – test first!', 'alternative': 'Hessonite (Gomed) / Amethyst', 'metal': 'Silver/White Gold', 'weight': '4-6 carats', 'finger': 'Middle finger left hand', 'wear_day': 'Saturday evening Shani Hora'},
        'charity': ['Blue/black blankets Saturdays', 'Feed homeless & laborers', 'Umbrellas & shoes', 'Iron implements/tools'],
        'pujas': ['Shani Shanti at Shani temples', 'Laghu Rudra Abhishek', 'Dashrath Krit Stotra', 'Shiva Puja for Moon strengthening'],
        'fasting': {'day': 'Saturday & Monday', 'duration': 'Throughout Sade Sati (7.5 yrs)', 'items': 'Simple Satvik diet; avoid stimulants'},
        'auspicious': {'days': ['Saturday', 'Monday'], 'tithis': 'Amavasya, Ekadashi', 'nakshatras': 'Pushya, Anuradha, Uttara Bhadrapada, Shravana', 'muhurta': 'Shani Hora Sat / Moon Hora Mon'},
        'temporary': ['Chant Hanuman Chalisa daily', 'Mustard oil lamp under Peepal Saturdays', 'Meditation for Moon (emotional) peace'],
        'permanent': ['Wear Blue Sapphire (test first)', 'Saturday & Monday fasting for life', 'Annual Shani Shanti Puja', 'Lifetime charity to the needy'],
    },
    'Rahu-Ketu Kendra Dosha': {
        'causing_planets': ['Rahu', 'Ketu'],
        'life_areas': ['Unexpected life events', 'Spiritual growth', 'Foreign connections', 'Technology & innovation', 'Unconventional path'],
        'mantras': ['Om Raam Rahave Namaha – 108x', 'Om Ketave Namaha – 108x', 'Durga Kavach Tuesdays', 'Lalita Sahasranama Fridays'],
        'gems': {'primary': 'Hessonite (Gomed) for Rahu', 'secondary': "Cat's Eye (Lehsunia) for Ketu", 'metal': 'Silver/Panchdhatu', 'weight': '4-7 carats', 'finger': 'Middle finger', 'wear_day': 'Saturday evening'},
        'charity': ['Electronics/mechanical items', 'Blankets & clothes', 'Feed street animals', 'Orphanage contributions'],
        'pujas': ['Rahu-Ketu Graha Shanti', 'Nag Panchami Puja', 'Lalita Tripura Sundari Puja', 'Vishnu worship Saturdays'],
        'fasting': {'day': 'Saturday', 'duration': '16 consecutive Saturdays', 'items': 'Fruit diet; no garlic/onion'},
        'auspicious': {'days': ['Saturday', 'Wednesday'], 'tithis': 'Chaturdashi, Purnima', 'nakshatras': 'Ardra, Swati, Shatabhisha, Ashwini', 'muhurta': 'Rahu Kaal Saturdays'},
        'temporary': ['Offer rice to temples', 'Chant Durga Kavach', 'Silver Ganesha at home'],
        'permanent': ["Wear Gomed/Cat's Eye (after testing)", 'Nag Panchami worship yearly', 'Rahu-Ketu Shanti Puja annually', 'Regular spiritual practice'],
    },
}

EXCEPTIONS = {
    'Mangal Dosha': [
        'Mars with benefic aspect (Vedha cancellation)',
        'Mars in own sign (Aries/Scorpio) or exalted (Capricorn) – reduces severity',
        'Retrograde Mars in dosha houses – half intensity',
        'Aries/Scorpio Ascendant (Mars rules Lagna) – Dosha does not apply',
        'Mars conjunct/aspected by Jupiter – protective',
    ],
    'Kaal Sarp Dosha': [
        'Jupiter in kendra from Ascendant or Moon',
        'Ascendant same sign as Rahu/Ketu',
        'Benefic planets outside Rahu-Ketu axis',
        'Mars in kendra with Jupiter – protective yoga',
    ],
    'Pitra Dosha': [
        'Sun exalted (Aries) or own sign (Leo)',
        'Sun conjunct Jupiter (Guru-Aditya Yoga)',
        'Jupiter aspecting Sun',
    ],
    'Shani Dosha': [
        'Saturn exalted in Libra – positive results',
        'Saturn in own signs (Capricorn/Aquarius)',
        'Saturn conjunct Jupiter (Guru-Shani Yoga)',
        'Saturn retrograde – internalises effects',
    ],
    'Guru Chandal Dosha': [
        'Jupiter strong & independent',
        'Jupiter in own sign (Sagittarius/Pisces)',
        'Jupiter aspects Ascendant or Moon',
    ],
    'Kemadruma Dosha': [
        'Jupiter or Venus aspects Moon',
        'Moon exalted (Taurus) or own sign (Cancer)',
        'Full Moon (Purnima) birth',
        'Jupiter conjunction/aspect with Moon',
    ],
    'Angarak Dosha': [
        'Mars in own sign or exalted',
        'Mars retrograde – internalises aggression',
        'Mars conjunct Jupiter',
        'Moon-Mars conjunction (Chandra-Mangala Yoga)',
    ],
    'Sade Sati': [
        'Saturn exalted in Libra – positive transformation',
        'Saturn in own sign – structured growth',
        'Jupiter aspecting Saturn',
        'Moon in Taurus/Cancer or strong nakshatra',
        'Saturn yogakaraka for Cancer/Leo Ascendant',
    ],
    'Rahu-Ketu Kendra Dosha': [
        'Jupiter in kendra from Ascendant',
        'Strong Ascendant lord',
        'Venus conjunction with Rahu – artistic benefits',
    ],
}

SEVERITY_LABELS = {'High': 'Severe', 'Medium': 'Moderate', 'Low': 'Mild', 'None': 'Not Present'}


def _calc(body):
    from ..main import detect_doshas
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    return planets, detect_doshas(planets)


def _enrich(d):
    db = _DB.get(d['name'], {})
    for k in ('causing_planets', 'life_areas', 'mantras', 'gems', 'charity', 'pujas', 'fasting', 'auspicious', 'temporary', 'permanent'):
        d[k] = db.get(k, {})
    d['auspicious_times'] = d.pop('auspicious', {})
    d['temporary_remedies'] = d.pop('temporary', [])
    d['permanent_remedies'] = d.pop('permanent', [])
    return d


# --- Models ---
class DoshaRemedyRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.209)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W')
    nodeMode: Optional[str] = Field('mean')


class DoshaCompatibilityRequest(DoshaRemedyRequest):
    partnerDateOfBirth: str = Field(..., example="1992-08-20")
    partnerTimeOfBirth: str = Field(..., example="09:15")
    partnerLatitude: float = Field(..., example=19.076)
    partnerLongitude: float = Field(..., example=72.877)
    partnerTimezone: str = Field(..., example="Asia/Kolkata")


# --- Endpoint 1: Detailed remedies ---
@router.post('/dosha/remedies')
def dosha_remedies(body: DoshaRemedyRequest):
    _, doshas = _calc(body)
    enriched = [_enrich(d) for d in doshas if d.get('present')]
    return {'status': 200, 'data': {'doshas': enriched, 'total_present': len(enriched)}}


# --- Endpoint 2: Severity analysis ---
@router.post('/dosha/severity')
def dosha_severity(body: DoshaRemedyRequest):
    planets, doshas = _calc(body)
    pmap = {p['name']: p for p in planets}
    analysis = []
    for d in doshas:
        if not d.get('present'):
            continue
        level = SEVERITY_LABELS.get(d.get('severity', 'Medium'), 'Moderate')
        affected = []
        for pname in _DB.get(d['name'], {}).get('causing_planets', []):
            p = pmap.get(pname)
            if p:
                affected.append({'planet': pname, 'house': p.get('house', 0), 'sign': p.get('sign', ''), 'status': planet_status(pname, p.get('sign', ''))})
        exc = EXCEPTIONS.get(d['name'], [])
        analysis.append({'name': d['name'], 'severity': level, 'raw_severity': d.get('severity', 'Medium'), 'description': d.get('description', ''), 'affected_planets': affected, 'exemptions': exc, 'exemption_available': bool(exc)})
    return {'status': 200, 'data': {'analysis': analysis, 'total_active': len(analysis)}}


# --- Endpoint 3: Compatibility impact ---
@router.post('/dosha/compatibility-impact')
def dosha_compatibility(body: DoshaCompatibilityRequest):
    from ..main import detect_doshas
    _, native_doshas = _calc(body)
    native_present = {d['name']: d for d in native_doshas if d.get('present')}

    jd_p = to_julian(body.partnerDateOfBirth, body.partnerTimeOfBirth, body.partnerTimezone)
    pp = calc_planets(jd_p, None, body.nodeMode or 'mean')
    calc_houses(jd_p, body.partnerLatitude, body.partnerLongitude, pp, body.houseSystem or 'W')
    partner_doshas = detect_doshas(pp)
    partner_present = {d['name']: d for d in partner_doshas if d.get('present')}

    # Mangal matching
    nm = native_present.get('Mangal Dosha')
    pm = partner_present.get('Mangal Dosha')
    if nm and pm:
        mangal = {'both_have': True, 'note': 'Both have Mangal Dosha – traditionally cancelled (Dosha Samapti)', 'remedy_needed': False}
    elif nm or pm:
        who = 'Native' if nm else 'Partner'
        mangal = {'both_have': False, 'affected_partner': who, 'note': 'One-sided Mangal Dosha – remedies recommended', 'remedy_needed': True, 'remedy': 'Kumbh Vivah or Mangal Graha Shanti Puja'}
    else:
        mangal = {'both_have': False, 'note': 'No Mangal Dosha in either partner', 'remedy_needed': False}

    # Sade Sati
    sade_sati = None
    ssc = []
    if 'Sade Sati' in native_present: ssc.append('Native')
    if 'Sade Sati' in partner_present: ssc.append('Partner')
    if ssc:
        sade_sati = {'affected': ssc, 'note': 'Sade Sati on one/both – period of testing & growth', 'remedy': 'Shani Shanti Puja & Saturday fasting'}

    # Impact items
    all_names = sorted(set(native_present) | set(partner_present))
    items = []
    for name in all_names:
        in_n = name in native_present
        in_p = name in partner_present
        items.append({
            'dosha': name, 'native_has': in_n, 'partner_has': in_p, 'mutual': in_n and in_p,
            'severity': (native_present.get(name) or partner_present.get(name, {})).get('severity', 'Medium'),
            'note': 'Both affected – shared remedies more effective' if (in_n and in_p) else ('Native only' if in_n else 'Partner only'),
        })

    penalty = 0
    for who, pres in [('n', native_present), ('p', partner_present)]:
        for name, d in pres.items():
            if name == 'Mangal Dosha' and mangal and not mangal.get('remedy_needed'):
                continue
            penalty += {'High': 15, 'Medium': 8, 'Low': 3}.get(d.get('severity', 'Medium'), 5)

    return {
        'status': 200,
        'data': {
            'native_doshas': list(native_present.keys()),
            'partner_doshas': list(partner_present.keys()),
            'mangal_impact': mangal,
            'sade_sati_impact': sade_sati,
            'impact_items': items,
            'compatibility_score': max(0, 100 - penalty),
            'recommendation': 'Consult an experienced astrologer for personalised remedies' if penalty else 'Favourable match with minimal dosha conflicts',
        },
    }
