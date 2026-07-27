"""
PDF Sections — All report section builders for the Kundli PDF.
Each function returns a list of ReportLab flowables.
"""
from reportlab.platypus import Spacer, Paragraph, KeepTogether, PageBreak
from reportlab.lib.units import mm
from reportlab.lib import colors
import logging
from .pdf_engine import (
    get_styles, make_table, make_left_table, colored_heading, section_divider,
    draw_south_indian_kundli, svg_to_image_flowable, make_dual_chart_table,
    PRIMARY, SECONDARY, ACCENT, CREAM, LIGHT_BG,
    PLANET_COLORS, SIGN_COLORS, SIGN_ELEMENT, ELEMENT_COLORS, ZODIAC_SIGNS,
    DARK_TEXT, MID_TEXT, LIGHT_TEXT, FIRE_COLOR, EARTH_COLOR, AIR_COLOR, WATER_COLOR,
)

logger = logging.getLogger(__name__)

styles = get_styles()


def _kv_block(data_dict, title=None):
    """Convert a dict to a key-value table."""
    rows = [(str(k).replace('_', ' ').title(), str(v)) for k, v in data_dict.items() if v is not None]
    if title:
        return [colored_heading(title, ACCENT, 11), Spacer(1, 4), make_left_table(rows)]
    return [make_left_table(rows)]


def _bullet(text):
    return Paragraph(f"\u2022 {text}", styles['BodyText2'])


def _sub_heading(text):
    return colored_heading(text, ACCENT, 11)


# ──────────────── SECTION 1: BIRTH DETAILS ────────────────
def build_birth_details_section(birth_info: dict, ascendant: dict, ayanamsa: str = 'Lahiri') -> list:
    elements = []
    elements.append(colored_heading('1. Birth Details', PRIMARY, 14))
    elements.append(section_divider())

    bio = {
        'Date of Birth': birth_info.get('dateOfBirth', ''),
        'Time of Birth': birth_info.get('timeOfBirth', ''),
        'Place': f"{birth_info.get('latitude', '')}, {birth_info.get('longitude', '')}",
        'Timezone': birth_info.get('timezone', ''),
        'Ayanamsa': ayanamsa,
    }
    elements.extend(_kv_block(bio, 'Birth Information'))

    if ascendant:
        elements.append(Spacer(1, 8))
        asc_data = {
            'Ascendant Sign': ascendant.get('sign', ''),
            'Ascendant Degree': f"{ascendant.get('degree', 0):.2f}\u00b0",
            'Nakshatra': ascendant.get('nakshatra', ''),
            'Nakshatra Lord': ascendant.get('nakshatraLord', ''),
        }
        elements.extend(_kv_block(asc_data, 'Ascendant (Lagna)'))

    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 2: KUNDLI CHART (RASI) ────────────────
def build_kundli_chart_section(planets: list, asc_sign: str) -> list:
    elements = []
    elements.append(colored_heading('2. Kundli Chart (Rasi - North Indian Diamond)', PRIMARY, 14))
    elements.append(section_divider())

    # Build asc dict for render_svg
    asc = {'sign': asc_sign, 'degree': 0, 'nakshatra': '', 'nakshatraLord': '', 'nakshatraPada': 1}

    # Render North Indian Diamond SVG
    try:
        from .routers.chart_svg import render_svg
        svg_str = render_svg(400, 300, asc, planets, theme='light', include_outer=True, stack_threshold=3)
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=300, height=225)
            elements.append(img)
    except Exception as e:
        logger.warning(f"North Indian SVG render failed: {e}, falling back to text table")
        # Fallback: simple table
        planets_by_sign = {}
        for p in planets:
            sign = p.get('sign', '')
            if sign:
                planets_by_sign.setdefault(sign, []).append(p['name'])
        chart = draw_south_indian_kundli(planets_by_sign, asc_sign, size=220)
        elements.append(chart)

    elements.append(Spacer(1, 8))

    legend_text = ' | '.join([
        f'<font color="{PLANET_COLORS[p].hexval()}"><b>{p}</b></font>'
        for p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        if p in PLANET_COLORS
    ])
    elements.append(Paragraph(f'Legend: {legend_text}', styles['SmallText']))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 3: NAVAMSA CHART ────────────────
def build_navamsa_chart_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('3. Navamsa Chart (D9 - North Indian Diamond)', PRIMARY, 14))
    elements.append(section_divider())
    elements.append(Paragraph(
        'The Navamsa chart reveals the inner strength of planets and is crucial for marriage, '
        'partnerships, and spiritual growth. A planet strong in both Rasi and Navamsa is very powerful.',
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8))

    # Compute navamsa positions using varga_sign from main
    from .main import varga_sign
    from .utils import ZODIAC_SIGNS
    nav_planets = []
    navamsa_map = {}
    for p in planets:
        if p['name'] not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            continue
        vsign = varga_sign(p['longitude'], 9)
        if vsign:
            navamsa_map[p['name']] = vsign
            nav_planets.append({
                'name': p['name'],
                'sign': vsign,
                'degree': p['degree'],
                'isRetrograde': p.get('isRetrograde', False),
                'isCombust': p.get('isCombust', False),
                'house': 0,
            })

    # Find Navamsa ascendant from planet longitudes
    asc_nav_sign = navamsa_map.get('Sun', ZODIAC_SIGNS[0])

    # Render North Indian Diamond SVG for Navamsa
    try:
        from .routers.chart_svg import render_svg
        asc_nav = {'sign': asc_nav_sign, 'degree': 0}
        svg_str = render_svg(400, 300, asc_nav, nav_planets, theme='light', include_outer=False, stack_threshold=3)
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=300, height=225)
            elements.append(img)
    except Exception as e:
        logger.warning(f"Navamsa North Indian SVG render failed: {e}, falling back to text table")
        nav_planets_by_sign = {}
        for pname, nsign in navamsa_map.items():
            nav_planets_by_sign.setdefault(nsign, []).append(pname)
        chart = draw_south_indian_kundli(nav_planets_by_sign, asc_nav_sign, size=200)
        elements.append(chart)

    elements.append(Spacer(1, 8))

    # Navamsa table
    headers = ['Planet', 'Rasi Sign', 'Navamsa Sign', 'Navamsa Lord']
    rows = []
    sign_lords = {
        'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
        'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
        'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
    }
    for p in planets:
        if p['name'] not in navamsa_map:
            continue
        nav_sign = navamsa_map[p['name']]
        rows.append([p['name'], p.get('sign', ''), nav_sign, sign_lords.get(nav_sign, '')])

    col_widths = [60, 90, 90, 80]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 4: HORA CHART ────────────────
def build_hora_chart_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('4. Hora Chart (D2)', PRIMARY, 14))
    elements.append(section_divider())
    elements.append(Paragraph(
        'The Hora chart reveals financial prospects and wealth potential. '
        'Sun Hora (Leo/Aries/Sagittarius) natives are self-made earners. '
        'Moon Hora (Cancer/Taurus/Scorpio) natives inherit wealth or earn through partnerships.',
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8))

    # Hora calculation: odd signs -> Sun Hora (Leo), even signs -> Moon Hora (Cancer)
    hora_map = {}
    for p in planets:
        if p['name'] not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            continue
        sign = p.get('sign', '')
        sign_idx = ZODIAC_SIGNS.index(sign) if sign in ZODIAC_SIGNS else 0
        is_odd = (sign_idx % 2 == 0)  # Aries=0 is odd sign (1-indexed: 1=odd)
        hora_map[p['name']] = 'Sun (Leo)' if is_odd else 'Moon (Cancer)'

    headers = ['Planet', 'Sign', 'Hora', 'Wealth Indicator']
    rows = []
    for p in planets:
        if p['name'] not in hora_map:
            continue
        hora = hora_map[p['name']]
        indicator = 'Self-earned' if 'Sun' in hora else 'Partnership/Inheritance'
        rows.append([p['name'], p.get('sign', ''), hora, indicator])

    col_widths = [60, 80, 100, 160]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 5: PLANET POSITIONS ────────────────
def build_planet_positions_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('5. Planet Positions', PRIMARY, 14))
    elements.append(section_divider())

    headers = ['Planet', 'Sign', 'Degree', 'House', 'Nakshatra', 'Pada', 'Retro', 'Combust', 'Status']
    rows = []
    for p in planets:
        if p['name'] not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            continue
        retro = 'Yes' if p.get('isRetrograde') else 'No'
        combust = 'Yes' if p.get('isCombust') else 'No'
        status = p.get('houseStatus', '') or ''
        rows.append([
            p['name'], p['sign'], p.get('degreeDMS', ''),
            p.get('house', ''), p.get('nakshatra', ''),
            p.get('nakshatraPada', ''), retro, combust, status
        ])

    col_widths = [50, 55, 55, 35, 75, 30, 35, 40, 55]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 6))

    retro_planets = [p['name'] for p in planets if p.get('isRetrograde')]
    combust_planets = [p['name'] for p in planets if p.get('isCombust')]
    if retro_planets:
        elements.append(Paragraph(
            f'<b>Retrograde:</b> {", ".join(retro_planets)}', styles['BodyText2']))
    if combust_planets:
        elements.append(Paragraph(
            f'<b>Combust:</b> {", ".join(combust_planets)}', styles['BodyText2']))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 6: HOUSE ANALYSIS ────────────────
def build_houses_section(houses: list, pmap: dict) -> list:
    elements = []
    elements.append(colored_heading('6. House Analysis (Bhava)', PRIMARY, 14))
    elements.append(section_divider())

    headers = ['House', 'Sign', 'Lord', 'Planets', 'Analysis']
    rows = []
    house_meanings = {
        1: 'Self, Personality', 2: 'Wealth, Family', 3: 'Courage, Siblings',
        4: 'Home, Comfort', 5: 'Children, Intellect', 6: 'Enemies, Disease',
        7: 'Marriage, Partnership', 8: 'Longevity, Transformation', 9: 'Fortune, Dharma',
        10: 'Career, Status', 11: 'Gains, Aspirations', 12: 'Losses, Liberation',
    }
    for h in houses:
        num = h.get('number', 0)
        planets_in = ', '.join(h.get('planets', [])) or '-'
        meaning = house_meanings.get(num, '')
        lord = h.get('lord', h.get('signLord', ''))
        lord_p = pmap.get(lord, {})
        lord_status = lord_p.get('houseStatus', '') if lord_p else ''
        analysis = f"Lord {lord} in {lord_p.get('house', '?')} ({lord_status})" if lord_p else meaning
        rows.append([num, h.get('sign', ''), lord, planets_in, analysis])

    col_widths = [35, 60, 50, 100, 200]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 7: NAKSHATRA ANALYSIS ────────────────
def build_nakshatra_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('7. Nakshatra Analysis', PRIMARY, 14))
    elements.append(section_divider())

    headers = ['Planet', 'Nakshatra', 'Lord', 'Pada', 'Sign', 'Degree']
    rows = []
    for p in planets:
        if p['name'] not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            continue
        rows.append([
            p['name'], p.get('nakshatra', ''),
            p.get('nakshatraLord', ''), p.get('nakshatraPada', ''),
            p['sign'], p.get('degreeDMS', ''),
        ])

    col_widths = [50, 90, 60, 40, 70, 60]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 8: DASHA ────────────────
def build_dasha_section(dasha: dict, timezone: str) -> list:
    elements = []
    elements.append(colored_heading('8. Vimshottari Dasha Periods', PRIMARY, 14))
    elements.append(section_divider())

    mahadashas = dasha.get('mahadashas', [])
    if not mahadashas:
        elements.append(Paragraph('Dasha data not available.', styles['BodyText2']))
        elements.append(Spacer(1, 12))
        return elements

    headers = ['Mahadasha', 'Start', 'End', 'Antardasha (Sub-periods)']
    rows = []
    for md in mahadashas[:9]:
        ad_list = md.get('antardasha', [])
        ad_summary = ', '.join([
            f"{ad['planet'][:3]} ({ad['startDate'][:7]}\u2013{ad['endDate'][:7]})"
            for ad in ad_list[:5]
        ])
        if len(ad_list) > 5:
            ad_summary += f' ... +{len(ad_list)-5} more'
        rows.append([
            md.get('planet', ''),
            md.get('startDate', ''),
            md.get('endDate', ''),
            ad_summary or '-'
        ])

    col_widths = [80, 70, 70, 220]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 9: YOGAS ────────────────
def build_yogas_section(yogas: list) -> list:
    elements = []
    elements.append(colored_heading('9. Yogas in Birth Chart', PRIMARY, 14))
    elements.append(section_divider())

    if not yogas:
        elements.append(Paragraph('No significant yogas detected.', styles['BodyText2']))
        elements.append(Spacer(1, 12))
        return elements

    headers = ['Yoga', 'Type', 'Planets', 'Effect']
    rows = []
    for y in yogas:
        rows.append([
            y.get('name', ''),
            y.get('type', ''),
            ', '.join(y.get('planets', [])) if isinstance(y.get('planets'), list) else str(y.get('planets', '')),
            y.get('effect', y.get('description', ''))[:80],
        ])

    col_widths = [100, 70, 100, 170]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 10: DOSHAS ────────────────
def build_doshas_section(doshas: list) -> list:
    elements = []
    elements.append(colored_heading('10. Doshas & Afflictions', PRIMARY, 14))
    elements.append(section_divider())

    if not doshas:
        elements.append(Paragraph('No significant doshas detected.', styles['BodyText2']))
        elements.append(Spacer(1, 12))
        return elements

    headers = ['Dosha', 'Present', 'Severity', 'Planets', 'Remedies']
    rows = []
    for d in doshas:
        present = 'Yes' if d.get('present') else 'No'
        severity = d.get('severity', '-')
        remedies = ', '.join(d.get('remedies', [])[:3]) if d.get('remedies') else '-'
        rows.append([
            d.get('name', ''), present, severity,
            ', '.join(d.get('planets', [])) if isinstance(d.get('planets'), list) else str(d.get('planets', '-')),
            remedies[:60],
        ])

    col_widths = [90, 45, 50, 90, 160]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 11: PLANET STRENGTHS ────────────────
def build_planet_strengths_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('11. Planet Strengths & Avastha', PRIMARY, 14))
    elements.append(section_divider())

    headers = ['Planet', 'Sign', 'Status', 'Avastha', 'Element']
    rows = []
    for p in planets:
        if p['name'] not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            continue
        element = SIGN_ELEMENT.get(p['sign'], '')
        status = p.get('houseStatus', '') or ''
        rows.append([
            p['name'], p['sign'], status,
            p.get('avastha', ''), element,
        ])

    col_widths = [60, 70, 80, 120, 80]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 12: CAREER PREDICTIONS ────────────────
def _predict_career(planets, houses, pmap, yogas, doshas, dasha):
    tenth_house = houses[9] if len(houses) > 9 else {}
    tenth_lord = pmap.get(tenth_house.get('signLord', ''), {})
    saturn = pmap.get('Saturn', {})
    mercury = pmap.get('Mercury', {})
    sun = pmap.get('Sun', {})

    points = []
    points.append(f"10th house sign: {tenth_house.get('sign', 'N/A')}")
    points.append(f"10th lord {tenth_house.get('signLord', '')} in house {tenth_lord.get('house', '?')} ({tenth_lord.get('houseStatus', '')})")
    if saturn:
        points.append(f"Saturn (karmakaraka) in {saturn['sign']} house {saturn.get('house', '?')} ({saturn.get('houseStatus', '')})")
    if mercury:
        points.append(f"Mercury (intelligence) in {mercury['sign']} house {mercury.get('house', '?')}")
    if sun:
        points.append(f"Sun (authority) in {sun['sign']} house {sun.get('house', '?')} ({sun.get('houseStatus', '')})")

    career_yogas = [y['name'] for y in yogas if any(k in y.get('name', '').lower() for k in ['raja', 'dhana', 'mahapurusha', 'amala', 'bhadra', 'saraswati'])]
    if career_yogas:
        points.append(f"Favorable yogas: {', '.join(career_yogas)}")

    # Suggested professions based on 10th house and its lord
    prof_map = {
        'Aries': 'Military, Sports, Engineering, Surgery, Entrepreneurship',
        'Taurus': 'Banking, Music, Food Industry, Real Estate, Luxury Goods',
        'Gemini': 'Communication, Writing, Teaching, Sales, IT, Media',
        'Cancer': 'Healthcare, Nursing, Real Estate, Food, Hospitality',
        'Leo': 'Government, Politics, Entertainment, Leadership Roles',
        'Virgo': 'Accounting, Healthcare, Analysis, Service Industry',
        'Libra': 'Law, Design, Fashion, Diplomacy, Partnership Businesses',
        'Scorpio': 'Research, Investigation, Insurance, Occult Sciences',
        'Sagittarius': 'Teaching, Philosophy, International Business, Travel',
        'Capricorn': 'Management, Mining, Agriculture, Government Administration',
        'Aquarius': 'Technology, Innovation, Social Work, Space Research',
        'Pisces': 'Spirituality, Art, Film, Healing, Marine Industry',
    }
    suggested = prof_map.get(tenth_house.get('sign', ''), 'Versatile career options')
    points.append(f"Suggested professions: {suggested}")

    # Dasha timing
    current_md = ''
    if dasha.get('mahadashas'):
        current_md = dasha['mahadashas'][0].get('planet', '')
    if current_md:
        points.append(f"Current Mahadasha: {current_md} — focus on career growth during this period")

    return {'points': points, 'summary': f"Career oriented toward {tenth_house.get('sign', 'N/A')} themes. {suggested}."}


def build_career_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('12. Career & Profession Predictions', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_career(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 13: FINANCE PREDICTIONS ────────────────
def _predict_finance(planets, houses, pmap, yogas, doshas, dasha):
    second_house = houses[1] if len(houses) > 1 else {}
    eleventh_house = houses[10] if len(houses) > 10 else {}
    jupiter = pmap.get('Jupiter', {})
    venus = pmap.get('Venus', {})

    points = []
    points.append(f"2nd house (savings): {second_house.get('sign', 'N/A')}, lord {second_house.get('signLord', '')}")
    points.append(f"11th house (gains): {eleventh_house.get('sign', 'N/A')}, lord {eleventh_house.get('signLord', '')}")
    if jupiter:
        points.append(f"Jupiter (wealth karaka) in {jupiter['sign']} house {jupiter.get('house', '?')} ({jupiter.get('houseStatus', '')})")
    if venus:
        points.append(f"Venus (luxury) in {venus['sign']} house {venus.get('house', '?')}")
    wealth_yogas = [y['name'] for y in yogas if any(k in y.get('name', '').lower() for k in ['dhana', 'lakshmi', 'vasumad', 'gajakesari'])]
    if wealth_yogas:
        points.append(f"Wealth yogas: {', '.join(wealth_yogas)}")
    points.append("Income sources: salary, business, investments, or inheritance based on planetary periods")

    return {'points': points, 'summary': 'Financial prospects analyzed through 2nd, 6th, 10th, and 11th houses.'}


def build_finance_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('13. Finance & Wealth Predictions', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_finance(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 14: HEALTH PREDICTIONS ────────────────
def _predict_health(planets, houses, pmap, yogas, doshas, dasha):
    first_house = houses[0] if houses else {}
    sixth_house = houses[5] if len(houses) > 5 else {}
    eighth_house = houses[7] if len(houses) > 7 else {}
    mars = pmap.get('Mars', {})
    saturn = pmap.get('Saturn', {})

    points = []
    points.append(f"1st house (body constitution): {first_house.get('sign', 'N/A')}")
    points.append(f"6th house (disease): {sixth_house.get('sign', 'N/A')}")
    points.append(f"8th house (chronic illness): {eighth_house.get('sign', 'N/A')}")
    if mars:
        points.append(f"Mars (accident karaka) in {mars['sign']} house {mars.get('house', '?')} ({mars.get('houseStatus', '')})")
    if saturn:
        points.append(f"Saturn (chronic ailments) in {saturn['sign']} house {saturn.get('house', '?')} ({saturn.get('houseStatus', '')})")
    health_doshas = [d['name'] for d in doshas if d.get('present') and d['name'] in ['Shani Dosha', 'Mangal Dosha', 'Kaal Sarp Dosha']]
    if health_doshas:
        points.append(f"Health doshas: {', '.join(health_doshas)}")

    # Vulnerable areas based on sign
    vulnerable_map = {
        'Aries': 'Head, migraines', 'Taurus': 'Throat, thyroid', 'Gemini': 'Lungs, nervous system',
        'Cancer': 'Chest, stomach', 'Leo': 'Heart, spine', 'Virgo': 'Digestive system, intestines',
        'Libra': 'Kidneys, lower back', 'Scorpio': 'Reproductive organs', 'Sagittarius': 'Hips, thighs, liver',
        'Capricorn': 'Knees, bones, skin', 'Aquarius': 'Ankles, circulation', 'Pisces': 'Feet, lymph system',
    }
    asc_sign = first_house.get('sign', '')
    if asc_sign in vulnerable_map:
        points.append(f"Constitutional vulnerability ({asc_sign} ascendant): {vulnerable_map[asc_sign]}")

    return {'points': points, 'summary': f"Health outlook based on {asc_sign} constitution. Regular check-ups recommended."}


def build_health_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('14. Health & Wellbeing Predictions', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_health(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 15: LOVE & MARRIAGE PREDICTIONS ────────────────
def _predict_love_marriage(planets, houses, pmap, yogas, doshas, dasha):
    seventh_house = houses[6] if len(houses) > 6 else {}
    venus = pmap.get('Venus', {})
    jupiter = pmap.get('Jupiter', {})
    mars = pmap.get('Mars', {})

    points = []
    points.append(f"7th house (marriage): {seventh_house.get('sign', 'N/A')}, lord {seventh_house.get('signLord', '')}")
    if venus:
        points.append(f"Venus (love karaka) in {venus['sign']} house {venus.get('house', '?')} ({venus.get('houseStatus', '')})")
    if jupiter:
        points.append(f"Jupiter (dharmakaraka) in {jupiter['sign']} house {jupiter.get('house', '?')}")
    marriage_yogas = [y['name'] for y in yogas if any(k in y.get('name', '').lower() for k in ['marriage', 'venus', 'seventh'])]
    if marriage_yogas:
        points.append(f"Marriage yogas: {', '.join(marriage_yogas)}")
    love_doshas = [d['name'] for d in doshas if d.get('present') and d['name'] in ['Mangal Dosha', 'Kaal Sarp Dosha']]
    if love_doshas:
        points.append(f"Doshas to note: {', '.join(love_doshas)}")
    if mars and mars.get('house') in [7, 1, 4, 8, 12]:
        points.append("Mars in a Mangal Dosha position — consider matching with compatible charts")

    # Partner characteristics based on 7th lord
    partner_traits = {
        'Sun': 'Authoritative, confident partner', 'Moon': 'Nurturing, emotional partner',
        'Mars': 'Energetic, assertive partner', 'Mercury': 'Intellectual, communicative partner',
        'Jupiter': 'Wise, spiritual partner', 'Venus': 'Charming, artistic partner',
        'Saturn': 'Mature, disciplined partner', 'Rahu': 'Unconventional, ambitious partner',
        'Ketu': 'Spiritual, detached partner',
    }
    lord = seventh_house.get('signLord', '')
    if lord in partner_traits:
        points.append(f"Partner traits (7th lord {lord}): {partner_traits[lord]}")

    return {'points': points, 'summary': f"Marriage prospects through {seventh_house.get('sign', 'N/A')} 7th house. Venus placement favorable."}


def build_love_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('15. Love & Marriage Predictions', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_love_marriage(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 16: EDUCATION PREDICTIONS ────────────────
def _predict_education(planets, houses, pmap, yogas, doshas, dasha):
    fourth_house = houses[3] if len(houses) > 3 else {}
    fifth_house = houses[4] if len(houses) > 4 else {}
    ninth_house = houses[8] if len(houses) > 8 else {}
    mercury = pmap.get('Mercury', {})
    jupiter = pmap.get('Jupiter', {})

    points = []
    points.append(f"4th house (basic education): {fourth_house.get('sign', 'N/A')}, lord {fourth_house.get('signLord', '')}")
    points.append(f"5th house (intellect, higher learning): {fifth_house.get('sign', 'N/A')}, lord {fifth_house.get('signLord', '')}")
    points.append(f"9th house (higher education, wisdom): {ninth_house.get('sign', 'N/A')}, lord {ninth_house.get('signLord', '')}")
    if mercury:
        points.append(f"Mercury (intellect) in {mercury['sign']} house {mercury.get('house', '?')}")
    if jupiter:
        points.append(f"Jupiter (wisdom, teaching) in {jupiter['sign']} house {jupiter.get('house', '?')}")

    edu_yogas = [y['name'] for y in yogas if any(k in y.get('name', '').lower() for k in ['saraswati', 'bhadra', 'gajakesari'])]
    if edu_yogas:
        points.append(f"Education yogas: {', '.join(edu_yogas)}")

    # Suggested fields
    fields_map = {
        'Aries': 'Engineering, Sports Management, Military Science',
        'Taurus': 'Finance, Music, Art, Architecture',
        'Gemini': 'Literature, Communication, Computer Science, Languages',
        'Cancer': 'Psychology, Nursing, History, Public Administration',
        'Leo': 'Political Science, Performing Arts, Law',
        'Virgo': 'Medicine, Data Science, Statistics, Environmental Science',
        'Libra': 'Law, Design, International Relations',
        'Scorpio': 'Research, Psychology, Investigation, Medical Science',
        'Sagittarius': 'Philosophy, Theology, International Business, Travel',
        'Capricorn': 'Management, Engineering, Mining, Government Services',
        'Aquarius': 'Technology, Innovation, Social Sciences, Space Research',
        'Pisces': 'Spiritual Studies, Film, Healing Arts, Marine Biology',
    }
    fifth_lord = fifth_house.get('signLord', '')
    suggested = fields_map.get(fifth_house.get('sign', ''), 'Diverse academic interests')
    points.append(f"Suggested fields of study: {suggested}")

    return {'points': points, 'summary': f"Strong intellectual potential through {fifth_house.get('sign', 'N/A')} 5th house influence."}


def build_education_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('16. Education & Knowledge Predictions', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_education(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 17: FAMILY PREDICTIONS ────────────────
def _predict_family(planets, houses, pmap, yogas, doshas, dasha):
    second_house = houses[1] if len(houses) > 1 else {}
    fourth_house = houses[3] if len(houses) > 3 else {}
    fifth_house = houses[4] if len(houses) > 4 else {}
    moon = pmap.get('Moon', {})

    points = []
    points.append(f"2nd house (family, speech): {second_house.get('sign', 'N/A')}, lord {second_house.get('signLord', '')}")
    points.append(f"4th house (home, mother): {fourth_house.get('sign', 'N/A')}, lord {fourth_house.get('signLord', '')}")
    points.append(f"5th house (children): {fifth_house.get('sign', 'N/A')}, lord {fifth_house.get('signLord', '')}")
    if moon:
        points.append(f"Moon (mind, mother karaka) in {moon['sign']} house {moon.get('house', '?')} ({moon.get('houseStatus', '')})")

    # Children prospects
    fifth_lord = pmap.get(fifth_house.get('signLord', ''), {})
    if fifth_lord:
        points.append(f"5th lord {fifth_house.get('signLord', '')} in house {fifth_lord.get('house', '?')} ({fifth_lord.get('houseStatus', '')})")
    points.append("Timing of children: check Jupiter and 5th house dasha periods")

    return {'points': points, 'summary': 'Family dynamics analyzed through 2nd, 4th, and 5th house configurations.'}


def build_family_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('17. Family Life Predictions', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_family(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 18: TRAVEL PREDICTIONS ────────────────
def _predict_travel(planets, houses, pmap, yogas, doshas, dasha):
    ninth_house = houses[8] if len(houses) > 8 else {}
    twelfth_house = houses[11] if len(houses) > 11 else {}
    jupiter = pmap.get('Jupiter', {})
    rahu = pmap.get('Rahu', {})

    points = []
    points.append(f"9th house (long travel, foreign): {ninth_house.get('sign', 'N/A')}, lord {ninth_house.get('signLord', '')}")
    points.append(f"12th house (foreign settlement): {twelfth_house.get('sign', 'N/A')}, lord {twelfth_house.get('signLord', '')}")
    if jupiter:
        points.append(f"Jupiter (fortune, long travel) in {jupiter['sign']} house {jupiter.get('house', '?')}")
    if rahu:
        points.append(f"Rahu (foreign connection) in {rahu['sign']} house {rahu.get('house', '?')} ({rahu.get('houseStatus', '')})")
    points.append("Foreign settlement strong if 12th lord or Rahu is connected to 9th/12th houses")
    points.append("Travel during Jupiter/Mercury/Rahu dasha periods is especially fruitful")

    return {'points': points, 'summary': 'Travel and foreign connections analyzed through 9th and 12th house dynamics.'}


def build_travel_predictions_section(planets, houses, pmap, yogas, doshas, dasha):
    elements = []
    elements.append(colored_heading('18. Travel & Foreign Settlement', PRIMARY, 14))
    elements.append(section_divider())

    result = _predict_travel(planets, houses, pmap, yogas, doshas, dasha)
    for pt in result['points']:
        elements.append(_bullet(pt))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 19: AI LIFE PREDICTIONS ────────────────
AI_LIFE_PROMPT = (
    "You are an expert Vedic astrologer. Based on this birth chart, provide detailed "
    "life predictions organized into these 9 categories. For each category, write 2-4 "
    "sentences of specific, insightful analysis. Use the planetary data provided.\n\n"
    "Categories:\n"
    "1. Personality & Character\n"
    "2. Career & Professional Life\n"
    "3. Wealth & Financial Growth\n"
    "4. Health & Wellness\n"
    "5. Relationships & Marriage\n"
    "6. Family & Children\n"
    "7. Education & Learning\n"
    "8. Spiritual Growth\n"
    "9. Annual Forecasts (next 5 years)\n\n"
    "Format each category as:\n"
    "CATEGORY: [Category Name]\n"
    "[Your analysis]\n\n"
)


def build_ai_life_predictions_section(planets, houses, pmap, yogas, doshas, dasha, ascendant,
                                     user_id=None) -> list:
    elements = []
    elements.append(colored_heading('19. AI-Powered Life Predictions', PRIMARY, 14))
    elements.append(section_divider())

    ai_text = None
    if user_id:
        try:
            from .routers.ai_astro import _call_ai_provider, _build_chart_context, _dasha, AI_SYSTEM_PROMPT
            from .routers.ai_astro import BirthRequest as _BR

            cur = None
            try:
                cur = _dasha(_BR(
                    dateOfBirth=planets[0].get('dateOfBirth', '1990-01-01') if planets else '1990-01-01',
                    timeOfBirth=planets[0].get('timeOfBirth', '12:00') if planets else '12:00',
                    latitude=planets[0].get('latitude', 28.6139) if planets else 28.6139,
                    longitude=planets[0].get('longitude', 77.2090) if planets else 77.2090,
                    timezone=planets[0].get('timezone', 'Asia/Kolkata') if planets else 'Asia/Kolkata',
                ))
            except Exception:
                pass

            # Build a minimal hd-like dict for context
            hd = {'ascendant': ascendant, 'houses': houses}
            ctx = _build_chart_context(planets, hd, yogas, doshas, cur, pmap)
            full_prompt = AI_SYSTEM_PROMPT + "\n\n" + AI_LIFE_PROMPT
            user_prompt = f"Birth Chart Data:\n{ctx}\n\nProvide the 9 life predictions."
            ai_text, err = _call_ai_provider(user_id, full_prompt, user_prompt)
        except Exception as e:
            logger.warning(f"AI call for PDF life predictions failed: {e}")

    if ai_text:
        # Parse AI response into categories
        categories = {}
        current_cat = None
        current_text = []
        for line in ai_text.split('\n'):
            line = line.strip()
            if line.upper().startswith('CATEGORY:') or (line.startswith('#') and ':' in line):
                if current_cat:
                    categories[current_cat] = ' '.join(current_text)
                cat_line = line.replace('CATEGORY:', '').replace('#', '').strip().rstrip(':').strip()
                current_cat = cat_line
                current_text = []
            elif line:
                current_text.append(line)
        if current_cat:
            categories[current_cat] = ' '.join(current_text)

        if not categories:
            # Fallback: split by paragraphs
            paras = [p.strip() for p in ai_text.split('\n\n') if p.strip()]
            cat_names = [
                'Personality & Character', 'Career & Professional Life',
                'Wealth & Financial Growth', 'Health & Wellness',
                'Relationships & Marriage', 'Family & Children',
                'Education & Learning', 'Spiritual Growth', 'Annual Forecasts',
            ]
            for i, name in enumerate(cat_names):
                if i < len(paras):
                    categories[name] = paras[i]

        headers = ['Life Area', 'AI Analysis']
        rows = []
        for cat_name, cat_text in categories.items():
            display = cat_text[:300] + '...' if len(cat_text) > 300 else cat_text
            rows.append([cat_name, display])

        if rows:
            col_widths = [120, 360]
            elements.append(make_table(headers, rows, col_widths))
            elements.append(Spacer(1, 6))

        # Full AI text below
        elements.append(Paragraph(
            '<b>Full AI Analysis:</b>',
            styles['BodyText2']
        ))
        elements.append(Spacer(1, 4))
        for para in ai_text.split('\n\n'):
            para = para.strip()
            if para:
                elements.append(Paragraph(para, styles['BodyText2']))
                elements.append(Spacer(1, 4))
    else:
        # Fallback placeholder
        elements.append(Paragraph(
            '<i>AI-powered detailed predictions will be available here. '
            'Connect to an AI service for personalized, in-depth analysis of your birth chart '
            'covering all life aspects with natural language interpretations.</i>',
            styles['Disclaimer']
        ))
        elements.append(Spacer(1, 10))

        categories = [
            ('Personality & Character', 'Deep analysis of ascendant, Moon, and Sun placements revealing core personality traits, strengths, weaknesses, and behavioral patterns.'),
            ('Career & Professional Life', 'AI analysis of 10th house, its lord, and relevant yogas for career trajectory, leadership potential, and professional fulfillment.'),
            ('Wealth & Financial Growth', 'Comprehensive financial outlook based on 2nd, 6th, 11th houses and Jupiter/Venus placements across all dasha periods.'),
            ('Health & Wellness', 'Detailed health forecast identifying vulnerable periods, constitutional tendencies, and preventive recommendations.'),
            ('Relationships & Marriage', 'In-depth compatibility analysis, timing of significant relationships, and partner characteristics based on 7th house and Venus.'),
            ('Family & Children', 'Analysis of family dynamics, parent-child relationships, and timing of significant family events.'),
            ('Education & Learning', 'Optimal fields of study, timing of academic achievements, and intellectual growth patterns.'),
            ('Spiritual Growth', 'Karmic lessons, spiritual inclinations, and guidance for inner development based on Ketu, 12th house, and Jupiter.'),
            ('Annual Forecasts', 'Year-by-year predictions aligned with planetary transits and dasha periods for the next 10 years.'),
        ]
        headers = ['Category', 'AI Analysis Preview']
        rows = [[cat, desc[:100] + '...' if len(desc) > 100 else desc] for cat, desc in categories]
        col_widths = [120, 360]
        elements.append(make_table(headers, rows, col_widths))
        elements.append(Spacer(1, 8))

        elements.append(Paragraph(
            '<b>Note:</b> To enable full AI predictions, integrate with an AI provider (OpenAI, Anthropic, etc.) '
            'and call the <b>/ai/interpret</b> endpoint with the birth chart data.',
            styles['BodyText2']
        ))

    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 19b: MAJOR CHART SVGs ────────────────
def build_major_charts_svg_section(planets: list, asc_sign: str, asc_degree: float = 0, user_id=None) -> list:
    """Render all major charts as North Indian Diamond SVG images in PDF."""
    elements = []
    elements.append(colored_heading('19b. Major Charts (North Indian Diamond)', PRIMARY, 14))
    elements.append(section_divider())

    from .main import varga_sign, VARGA_META
    from .utils import ZODIAC_SIGNS

    moon_sign = ''
    for p in planets:
        if p['name'] == 'Moon':
            moon_sign = p.get('sign', '')
            break

    # Build asc dict for render_svg
    asc = {'sign': asc_sign, 'nakshatra': '', 'degree': 0, 'nakshatraLord': '', 'nakshatraPada': 1}

    charts_rendered = []

    # 1. Rasi (D1) - North Indian Diamond
    try:
        from .routers.chart_svg import render_svg
        svg_str = render_svg(400, 300, asc, planets, theme='light', include_outer=True)
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=220, height=165)
            charts_rendered.append(('Rasi (D1) - General Life', img))
    except Exception as e:
        logger.warning(f"Rasi SVG render failed: {e}")

    # 2. Moon Chart
    try:
        from .routers.chart_east import _render_moon_svg
        svg_str = _render_moon_svg(400, 300, asc, moon_sign or asc_sign, planets, theme='light')
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=220, height=165)
            charts_rendered.append(('Moon Chart', img))
    except Exception as e:
        logger.warning(f"Moon SVG render failed: {e}")

    # 3. East Indian Chart
    try:
        from .routers.chart_east import _render_east_svg
        svg_str = _render_east_svg(400, 300, asc, planets, theme='light')
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=220, height=165)
            charts_rendered.append(('East Indian', img))
    except Exception as e:
        logger.warning(f"East Indian SVG render failed: {e}")

    # 4. All Divisional Charts (D3 through D60)
    divisional_vargas = [3, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

    for d in divisional_vargas:
        try:
            meta = VARGA_META.get(f'D{d}', {})
            chart_name = meta.get('name', f'D{d}')
            focus = meta.get('focus', '')

            # Compute divisional ascendant
            asc_sign_d = varga_sign(asc_degree, d) if d > 1 else asc_sign
            asc_sign_d = asc_sign_d or asc_sign

            # Compute divisional planets
            vplanets = []
            asc_idx = ZODIAC_SIGNS.index(asc_sign_d)
            for p in planets:
                if d == 1:
                    vsign = p.get('sign', '')
                else:
                    # Use full sidereal longitude for varga_sign
                    lon = p.get('longitude', 0)
                    vsign = varga_sign(lon, d) if lon else p.get('sign', '')
                if not vsign:
                    continue
                sidx = ZODIAC_SIGNS.index(vsign)
                house = ((sidx - asc_idx + 12) % 12) + 1
                vplanets.append({
                    'name': p['name'],
                    'sign': vsign,
                    'house': house,
                    'degree': p.get('degree', 0),
                    'isRetrograde': p.get('isRetrograde', False),
                    'isCombust': p.get('isCombust', False),
                })

            if not vplanets:
                continue

            vasc = {'sign': asc_sign_d, 'degree': 0}
            svg_str = render_svg(400, 300, vasc, vplanets, theme='light',
                                 include_outer=False, stack_threshold=2,
                                 show_degrees=False, show_retrograde=True)
            if svg_str:
                img = svg_to_image_flowable(svg_str, width=220, height=165)
                label = f'{chart_name} (D{d})'
                if focus:
                    label += f' - {focus}'
                charts_rendered.append((label, img))
        except Exception as e:
            logger.warning(f"D{d} SVG render failed: {e}")

    if not charts_rendered:
        elements.append(Paragraph(
            '<i>Charts will appear here when SVG rendering is available.</i>',
            styles['Disclaimer']
        ))
        elements.append(Spacer(1, 12))
        return elements

    # Render charts in pairs (2 per row)
    for i in range(0, len(charts_rendered), 2):
        pair = charts_rendered[i:i+2]
        if len(pair) == 2:
            table = make_dual_chart_table(
                pair[0][1], pair[1][1],
                label1=pair[0][0], label2=pair[1][0],
            )
            elements.append(table)
        elif len(pair) == 1:
            elements.append(Paragraph(f'<b>{pair[0][0]}:</b>', styles['SubSection']))
            elements.append(pair[0][1])
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 20: GEMSTONES ────────────────
def build_gemstone_section(planets: list, pmap: dict, asc_sign: str) -> list:
    elements = []
    elements.append(colored_heading('20. Gemstone Recommendations', PRIMARY, 14))
    elements.append(section_divider())

    GEMSTONE_MAP = {
        'Sun': {'gem': 'Ruby', 'metal': 'Gold', 'finger': 'Ring', 'weight': '3-5 ct', 'day': 'Sunday'},
        'Moon': {'gem': 'Pearl', 'metal': 'Silver', 'finger': 'Little', 'weight': '2-4 ct', 'day': 'Monday'},
        'Mars': {'gem': 'Red Coral', 'metal': 'Gold', 'finger': 'Ring', 'weight': '3-6 ct', 'day': 'Tuesday'},
        'Mercury': {'gem': 'Emerald', 'metal': 'Gold', 'finger': 'Little', 'weight': '1-3 ct', 'day': 'Wednesday'},
        'Jupiter': {'gem': 'Yellow Sapphire', 'metal': 'Gold', 'finger': 'Index', 'weight': '2-4 ct', 'day': 'Thursday'},
        'Venus': {'gem': 'Diamond', 'metal': 'Platinum', 'finger': 'Middle', 'weight': '0.5-1 ct', 'day': 'Friday'},
        'Saturn': {'gem': 'Blue Sapphire', 'metal': 'Silver', 'finger': 'Middle', 'weight': '2-4 ct', 'day': 'Saturday'},
        'Rahu': {'gem': 'Hessonite', 'metal': 'Silver', 'finger': 'Middle', 'weight': '4-6 ct', 'day': 'Saturday'},
        'Ketu': {'gem': "Cat's Eye", 'metal': 'Silver', 'finger': 'Middle', 'weight': '2-3 ct', 'day': 'Tuesday'},
    }

    from .pdf_engine import SIGN_LORDS
    recs = []
    asc_lord = SIGN_LORDS.get(asc_sign, '')
    if asc_lord in GEMSTONE_MAP:
        r = GEMSTONE_MAP[asc_lord].copy()
        r['planet'] = asc_lord
        r['reason'] = 'Ascendant lord'
        recs.append(r)

    moon_p = pmap.get('Moon')
    if moon_p:
        ml = SIGN_LORDS.get(moon_p['sign'], '')
        if ml in GEMSTONE_MAP and ml != asc_lord:
            r = GEMSTONE_MAP[ml].copy()
            r['planet'] = ml
            r['reason'] = 'Moon sign lord'
            recs.append(r)

    for pname in ['Sun', 'Jupiter', 'Venus', 'Saturn']:
        p = pmap.get(pname)
        if p and pname in GEMSTONE_MAP and pname not in [x['planet'] for x in recs]:
            from .pdf_engine import planet_status as _ps
            st = _ps(pname, p['sign'])
            if st in ['Exalted', 'Debilitated', 'Own Sign']:
                r = GEMSTONE_MAP[pname].copy()
                r['planet'] = pname
                r['reason'] = f'{pname} is {st}'
                recs.append(r)

    headers = ['Planet', 'Gemstone', 'Metal', 'Finger', 'Weight', 'Day', 'Reason']
    rows = [[r['planet'], r['gem'], r['metal'], r['finger'], r['weight'], r['day'], r['reason']] for r in recs]
    col_widths = [45, 80, 55, 45, 50, 55, 110]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 21: REMEDIES ────────────────
def build_remedies_section(doshas: list, yogas: list) -> list:
    elements = []
    elements.append(colored_heading('21. Remedies & Spiritual Guidance', PRIMARY, 14))
    elements.append(section_divider())

    active_doshas = [d for d in doshas if d.get('present') and d.get('remedies')]
    if active_doshas:
        elements.append(colored_heading('Dosha Remedies', ACCENT, 11))
        for d in active_doshas:
            elements.append(Paragraph(
                f'<b>{d["name"]}</b> ({d.get("severity", "N/A")}): {", ".join(d["remedies"][:4])}',
                styles['BodyText2']))
            elements.append(Spacer(1, 4))
    else:
        elements.append(Paragraph('No active dosha remedies needed.', styles['BodyText2']))

    elements.append(Spacer(1, 8))
    elements.append(colored_heading('General Spiritual Practices', ACCENT, 11))
    general = [
        'Chant your Ishta Devata mantra daily (108 times)',
        'Practice meditation for 15 minutes each morning',
        'Offer water to Sun at sunrise from a copper vessel',
        'Visit temple on your ruling planet day',
        'Donate to charity on auspicious tithis',
        'Keep north-east corner of home clean and clutter-free',
        'Read or listen to Vishnu Sahasranama weekly',
    ]
    for g in general:
        elements.append(_bullet(g))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 22: LUCKY ATTRIBUTES ────────────────
def build_lucky_section(date_of_birth: str) -> list:
    elements = []
    elements.append(colored_heading('22. Lucky Attributes', PRIMARY, 14))
    elements.append(section_divider())

    parts = date_of_birth.split('-')
    day = int(parts[2])
    total = int(parts[0]) + int(parts[1]) + day
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    life_path = total

    LUCKY = {
        1:  {'color': 'Gold, Yellow', 'number': '1, 3, 5, 9', 'day': 'Sunday', 'metal': 'Gold'},
        2:  {'color': 'White, Silver', 'number': '2, 4, 7, 9', 'day': 'Monday', 'metal': 'Silver'},
        3:  {'color': 'Yellow, Orange', 'number': '1, 3, 5, 9', 'day': 'Thursday', 'metal': 'Gold'},
        4:  {'color': 'Blue, Grey', 'number': '2, 4, 7, 8', 'day': 'Saturday', 'metal': 'Iron'},
        5:  {'color': 'Green, Aqua', 'number': '2, 3, 5, 6', 'day': 'Wednesday', 'metal': 'Bronze'},
        6:  {'color': 'Pink, White', 'number': '3, 5, 6, 9', 'day': 'Friday', 'metal': 'Copper'},
        7:  {'color': 'White, Grey', 'number': '1, 2, 4, 7', 'day': 'Monday', 'metal': 'Silver'},
        8:  {'color': 'Blue, Black', 'number': '1, 4, 5, 8', 'day': 'Saturday', 'metal': 'Iron'},
        9:  {'color': 'Red, Orange', 'number': '1, 3, 5, 9', 'day': 'Tuesday', 'metal': 'Copper'},
        11: {'color': 'Silver, White', 'number': '2, 4, 7, 11', 'day': 'Monday', 'metal': 'Silver'},
        22: {'color': 'Blue, Navy', 'number': '4, 6, 7, 22', 'day': 'Saturday', 'metal': 'Steel'},
        33: {'color': 'Gold, Rose', 'number': '3, 6, 9, 33', 'day': 'Thursday', 'metal': 'Gold'},
    }
    luck = LUCKY.get(life_path, LUCKY[1])

    data = {
        'Life Path Number': life_path,
        'Lucky Colors': luck['color'],
        'Lucky Numbers': luck['number'],
        'Lucky Day': luck['day'],
        'Lucky Metal': luck['metal'],
    }
    elements.extend(_kv_block(data, f'Life Path {life_path}'))
    elements.append(Spacer(1, 12))
    return elements
