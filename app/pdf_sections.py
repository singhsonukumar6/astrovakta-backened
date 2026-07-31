"""
PDF Sections — All report section builders for the Kundli PDF.
Each function returns a list of ReportLab flowables.
"""
from reportlab.platypus import Spacer, Paragraph, KeepTogether, PageBreak
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
import logging
from .pdf_engine import (
    get_styles, make_table, make_left_table, make_modern_table,
    colored_heading, section_divider, make_section_box, make_chart_container,
    make_page_break_if_needed,
    svg_to_image_flowable, make_dual_chart_table,
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
def build_kundli_chart_section(planets: list, asc_sign: str, asc_degree: float = 0) -> list:
    elements = []
    elements.append(colored_heading('2. Kundli Chart (Rasi - North Indian Diamond)', PRIMARY, 14))
    elements.append(section_divider())

    # Build asc dict for render_svg
    asc = {'sign': asc_sign, 'degree': asc_degree, 'nakshatra': '', 'nakshatraLord': '', 'nakshatraPada': 1}

    # Render North Indian Diamond SVG
    try:
        from .routers.chart_svg import render_svg
        svg_str = render_svg(400, 300, asc, planets, theme='light', include_outer=True, stack_threshold=3, show_degrees=True)
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=300, height=225)
            elements.extend(make_chart_container(img, 'Lagna Kundli (D1 - Rasi)', page_break_before=False))
    except Exception as e:
        logger.warning(f"North Indian SVG render failed for D1 chart: {e}")

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
def build_navamsa_chart_section(planets: list, ascendant: dict = None) -> list:
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

    # Compute Navamsa ascendant from D1 ascendant degree
    asc_degree = (ascendant or {}).get('degree', 0)
    asc_nav_sign = varga_sign(asc_degree, 9) or navamsa_map.get('Sun', ZODIAC_SIGNS[0])

    nav_asc_idx = ZODIAC_SIGNS.index(asc_nav_sign) if asc_nav_sign in ZODIAC_SIGNS else 0
    for p in planets:
        if p['name'] not in navamsa_map:
            continue
        vsign = navamsa_map[p['name']]
        sign_idx = ZODIAC_SIGNS.index(vsign) if vsign in ZODIAC_SIGNS else 0
        house = ((sign_idx - nav_asc_idx + 12) % 12) + 1
        nav_planets.append({
            'name': p['name'],
            'sign': vsign,
            'degree': p['degree'],
            'isRetrograde': p.get('isRetrograde', False),
            'isCombust': p.get('isCombust', False),
            'house': house,
        })

    # Render North Indian Diamond SVG for Navamsa
    try:
        from .routers.chart_svg import render_svg
        asc_deg = (ascendant or {}).get('degree', 0)
        asc_nav = {'sign': asc_nav_sign, 'degree': asc_deg}
        svg_str = render_svg(400, 300, asc_nav, nav_planets, theme='light', include_outer=False, stack_threshold=3, show_degrees=True)
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=300, height=225)
            elements.extend(make_chart_container(img, 'Navamsa (D9)', page_break_before=False))
    except Exception as e:
        logger.warning(f"Navamsa North Indian SVG render failed: {e}")

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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)
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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)

    retro_planets = [p['name'] for p in planets if p.get('isRetrograde')]
    combust_planets = [p['name'] for p in planets if p.get('isCombust')]
    if retro_planets:
        content.append(Paragraph(
            f'<b>Retrograde:</b> {", ".join(retro_planets)}', styles['BodyText2']))
    if combust_planets:
        content.append(Paragraph(
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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)
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

    current_planet = dasha.get('current', {}).get('planet', '')

    for md in mahadashas[:9]:
        planet = md.get('planet', '')
        is_current = planet == current_planet
        pcolor = PLANET_COLORS.get(planet, PRIMARY)
        md_title = f"{planet} Mahadasha"
        if is_current:
            md_title = f"{md_title} (CURRENT)"

        elements.append(Paragraph(
            f'<font color="{pcolor.hexval()}"><b>{md_title}</b></font>  '
            f'<font size="8">{md.get("startDate", "")} \u2013 {md.get("endDate", "")}</font>',
            ParagraphStyle('md_head', parent=styles['SubSection'], fontSize=11, spaceBefore=10, spaceAfter=4)
        ))

        ad_list = md.get('antardasha', [])
        if ad_list:
            ad_headers = ['Antardasha', 'Start', 'End']
            ad_rows = []
            for ad in ad_list:
                ad_rows.append([ad.get('planet', ''), ad.get('startDate', ''), ad.get('endDate', '')])
            elements.append(make_modern_table(ad_headers, ad_rows, [100, 80, 80]))
        else:
            elements.append(Paragraph('No antardasha data.', styles['SmallText']))
        elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 12))
    return elements


def build_extended_dasha_section(dasha: dict, timezone: str) -> list:
    """Extended dasha view showing MD, AD, PD, and Sookshma Dasha as nested tables."""
    elements = []
    elements.append(colored_heading('Extended Dasha Analysis', PRIMARY, 14))
    elements.append(section_divider())

    mahadashas = dasha.get('mahadashas', [])
    if not mahadashas:
        elements.append(Paragraph('Extended dasha data not available.', styles['BodyText2']))
        elements.append(Spacer(1, 12))
        return elements

    current_planet = dasha.get('current', {}).get('planet', '')

    for md in mahadashas[:5]:
        planet = md.get('planet', '')
        is_current = planet == current_planet
        pcolor = PLANET_COLORS.get(planet, PRIMARY)
        md_title = f"{planet}   Mahadasha"
        if is_current:
            md_title = f"\u2605 {md_title} (CURRENT)"

        md_content = []
        md_content.append(Paragraph(
            f'<b>Period:</b> {md.get("startDate", "")} \u2013 {md.get("endDate", "")}',
            styles['BodyText2']
        ))
        md_content.append(Spacer(1, 4))

        ad_list = md.get('antardasha', [])
        if not ad_list:
            md_content.append(Paragraph('No antardasha data.', styles['SmallText']))
        else:
            ad_rows = []
            for ad in ad_list:
                ad_name = ad.get('planet', '')
                ad_start = ad.get('startDate', '')
                ad_end = ad.get('endDate', '')
                pratyantar = ad.get('pratyantar', [])

                pd_text = ''
                if pratyantar:
                    pd_parts = []
                    for pd in pratyantar:
                        pd_name = pd.get('planet', '')
                        pd_start = pd.get('startDate', '')[:7]
                        pd_end = pd.get('endDate', '')[:7]
                        sookshma = pd.get('pratyantar', [])
                        if sookshma:
                            sd_text = ', '.join([
                                f"{sd['planet']} ({sd.get('startDate', '')[:7]}\u2013{sd.get('endDate', '')[:7]})"
                                for sd in sookshma[:3]
                            ])
                            pd_parts.append(f"{pd_name}  ({pd_start}\u2013{pd_end})  [SD: {sd_text}]")
                        else:
                            pd_parts.append(f"{pd_name}  ({pd_start}\u2013{pd_end})")
                    pd_text = ', '.join(pd_parts)

                ad_rows.append([
                    ad_name,
                    ad_start,
                    ad_end,
                    Paragraph(pd_text, styles['SmallText']) if pd_text else '-'
                ])

            md_content.append(make_modern_table(
                ['Antardasha', 'Start', 'End', 'Pratyantar (PD) / Sookshma (SD)'],
                ad_rows,
                [70, 60, 60, 200]
            ))

        elements.extend(md_content)
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 9: YOGAS ────────────────
def build_yogas_section(yogas: list) -> list:
    elements = []
    elements.append(colored_heading('9. Yogas in Birth Chart', PRIMARY, 14))
    elements.append(section_divider())

    if not yogas:
        content = [Paragraph('No significant yogas detected.', styles['BodyText2'])]
        elements.extend(content)
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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 10: DOSHAS ────────────────
def build_doshas_section(doshas: list) -> list:
    elements = []
    elements.append(colored_heading('10. Doshas & Afflictions', PRIMARY, 14))
    elements.append(section_divider())

    if not doshas:
        content = [Paragraph('No significant doshas detected.', styles['BodyText2'])]
        elements.extend(content)
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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)
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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)
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
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
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
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
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
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
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
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
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
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
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
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Summary:</b> {result['summary']}", styles['BodyText2']))
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

    asc = {'sign': asc_sign, 'nakshatra': '', 'degree': asc_degree, 'nakshatraLord': '', 'nakshatraPada': 1}

    # 1. Rasi (D1) - North Indian Diamond
    try:
        from .routers.chart_svg import render_svg
        svg_str = render_svg(400, 300, asc, planets, theme='light', include_outer=True, show_degrees=False)
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=400, height=300)
            elements.extend(make_chart_container(img, 'Rasi (D1) - General Life', page_break_before=False))
    except Exception as e:
        logger.warning(f"Rasi SVG render failed: {e}")

    # 2. Moon Chart
    try:
        from .routers.chart_east import _render_moon_svg
        svg_str = _render_moon_svg(400, 300, asc, moon_sign or asc_sign, planets, theme='light')
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=400, height=300)
            elements.extend(make_chart_container(img, 'Moon Chart', page_break_before=True))
    except Exception as e:
        logger.warning(f"Moon SVG render failed: {e}")

    # 3. East Indian Chart
    try:
        from .routers.chart_east import _render_east_svg
        svg_str = _render_east_svg(400, 300, asc, planets, theme='light')
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=400, height=300)
            elements.extend(make_chart_container(img, 'East Indian Chart', page_break_before=True))
    except Exception as e:
        logger.warning(f"East Indian SVG render failed: {e}")

    # 4. All Divisional Charts (D3 through D60)
    divisional_vargas = [3, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

    for d in divisional_vargas:
        try:
            meta = VARGA_META.get(f'D{d}', {})
            chart_name = meta.get('name', f'D{d}')
            focus = meta.get('focus', '')

            asc_sign_d = varga_sign(asc_degree, d) if d > 1 else asc_sign
            asc_sign_d = asc_sign_d or asc_sign

            vplanets = []
            asc_idx = ZODIAC_SIGNS.index(asc_sign_d)
            for p in planets:
                if d == 1:
                    vsign = p.get('sign', '')
                else:
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
                img = svg_to_image_flowable(svg_str, width=350, height=260)
                label = f'{chart_name} (D{d})'
                if focus:
                    label += f' - {focus}'
                elements.extend(make_chart_container(img, label, page_break_before=True))
        except Exception as e:
            logger.warning(f"D{d} SVG render failed: {e}")

    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 19c: ASHTAKAVARGA CHART ────────────────
def build_ashtakavarga_chart_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('Ashtakavarga (Eight-fold Strength)', PRIMARY, 14))
    elements.append(section_divider())
    elements.append(Paragraph(
        'Ashtakavarga shows the benefic bindu count in each house from each planet\'s aspect pattern. '
        'Higher counts (8+) indicate strong houses; lower counts (0-4) indicate weak houses.',
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8))

    try:
        from .main import compute_ashtakavarga
        from .routers.chart_svg import render_ashtakavarga_svg

        av = compute_ashtakavarga(planets)
        planets_order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

        for pname in planets_order:
            contrib = av.get('planetContributions', {}).get(pname, {})
            pts = {h: contrib.get(h, 0) for h in range(1, 13)}
            svg_str = render_ashtakavarga_svg(300, 240, pts, planet_name=pname)
            if svg_str:
                img = svg_to_image_flowable(svg_str, width=260, height=210)
                elements.extend(make_chart_container(img, f'{pname} Ashtakavarga', page_break_before=False))

        # SAV chart
        sav = av.get('sarvashtakavarga', {})
        sav_pts = {int(h): sav.get('housePoints', {}).get(str(h), 0) for h in range(1, 13)}
        svg_str = render_ashtakavarga_svg(300, 240, sav_pts, planet_name='SAV')
        if svg_str:
            img = svg_to_image_flowable(svg_str, width=260, height=210)
            elements.extend(make_chart_container(img, 'Sarvashtakavarga (Total)', page_break_before=False))

        # Tables for each planet + SAV
        elements.append(PageBreak())
        elements.append(colored_heading('Ashtakavarga Tables', PRIMARY, 14))
        elements.append(section_divider())

        headers = ['Planet'] + [str(h) for h in range(1, 13)] + ['Total']
        rows = []
        for pname in planets_order:
            contrib = av.get('planetContributions', {}).get(pname, {})
            row = [pname] + [str(contrib.get(h, 0)) for h in range(1, 13)] + [str(sum(contrib.values()))]
            rows.append(row)
        sav_row = ['SAV'] + [str(sav.get('housePoints', {}).get(str(h), 0)) for h in range(1, 13)] + [str(sum(sav.get('housePoints', {}).values()))]
        rows.append(sav_row)
        elements.append(make_modern_table(headers, rows, [45] + [25]*12 + [35]))
        elements.append(Spacer(1, 8))

        strong_houses = ', '.join([f"H{h.get('house')}({h.get('points')})" for h in sav.get('strongestHouses', [])])
        weak_houses = ', '.join([f"H{h.get('house')}({h.get('points')})" for h in sav.get('weakestHouses', [])])
        elements.append(Paragraph(
            f"<b>Sarvashtakavarga Average:</b> {sav.get('average', 0)} | "
            f"<b>Strongest Houses:</b> {strong_houses} | "
            f"<b>Weakest Houses:</b> {weak_houses}",
            styles['BodyText2']
        ))

    except Exception as e:
        logger.warning(f"Ashtakavarga chart section failed: {e}")
        elements.append(Paragraph('Ashtakavarga data could not be generated.', styles['BodyText2']))

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
    content = [make_modern_table(headers, rows, col_widths)]
    elements.extend(content)
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
        1:  {'color': 'Gold, Yellow', 'number': '1, 3, 5, 9', 'day': 'Sunday', 'metal': 'Gold', 'direction': 'North'},
        2:  {'color': 'White, Silver', 'number': '2, 4, 7, 9', 'day': 'Monday', 'metal': 'Silver', 'direction': 'North-West'},
        3:  {'color': 'Yellow, Orange', 'number': '1, 3, 5, 9', 'day': 'Thursday', 'metal': 'Gold', 'direction': 'East'},
        4:  {'color': 'Blue, Grey', 'number': '2, 4, 7, 8', 'day': 'Saturday', 'metal': 'Iron', 'direction': 'West'},
        5:  {'color': 'Green, Aqua', 'number': '2, 3, 5, 6', 'day': 'Wednesday', 'metal': 'Bronze', 'direction': 'North-East'},
        6:  {'color': 'Pink, White', 'number': '3, 5, 6, 9', 'day': 'Friday', 'metal': 'Copper', 'direction': 'South-East'},
        7:  {'color': 'White, Grey', 'number': '1, 2, 4, 7', 'day': 'Monday', 'metal': 'Silver', 'direction': 'North-East'},
        8:  {'color': 'Blue, Black', 'number': '1, 4, 5, 8', 'day': 'Saturday', 'metal': 'Iron', 'direction': 'South-West'},
        9:  {'color': 'Red, Orange', 'number': '1, 3, 5, 9', 'day': 'Tuesday', 'metal': 'Copper', 'direction': 'South'},
        11: {'color': 'Silver, White', 'number': '2, 4, 7, 11', 'day': 'Monday', 'metal': 'Silver', 'direction': 'North'},
        22: {'color': 'Blue, Navy', 'number': '4, 6, 7, 22', 'day': 'Saturday', 'metal': 'Steel', 'direction': 'West'},
        33: {'color': 'Gold, Rose', 'number': '3, 6, 9, 33', 'day': 'Thursday', 'metal': 'Gold', 'direction': 'East'},
    }
    luck = LUCKY.get(life_path, LUCKY[1])

    data = {
        'Life Path Number': life_path,
        'Lucky Colors': luck['color'],
        'Lucky Numbers': luck['number'],
        'Lucky Day': luck['day'],
        'Lucky Metal': luck['metal'],
        'Lucky Direction': luck['direction'],
    }
    elements.extend(_kv_block(data, f'Life Path {life_path}'))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 23: PANCHANG ────────────────
def build_panchang_section(jd: float, latitude: float, longitude: float, timezone: str, birth_date: str = None) -> list:
    elements = []
    elements.append(colored_heading('23. Birth Panchang', PRIMARY, 14))
    elements.append(section_divider())
    elements.append(Paragraph(
        'The Panchang (five limbs) describes the cosmic time at birth - Tithi (lunar day), '
        'Nakshatra (constellation), Yoga (auspiciousness), Karana (half-day), and Vaar (weekday).',
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8))

    from .utils import sunrise_sunset, compute_panchang
    try:
        sr, ss, _, _ = sunrise_sunset(
            birth_date or '1990-01-01', timezone, latitude, longitude
        )
    except Exception:
        sr, ss = None, None
    panchang_data = compute_panchang(birth_date or '1990-01-01', '00:00', timezone, latitude, longitude)

    data = {
        'Tithi': panchang_data.get('tithi', '') + f" ({panchang_data.get('tithiNumber', '')})",
        'Nakshatra': panchang_data.get('nakshatra', '') + f" ({panchang_data.get('nakshatraNumber', '')})",
        'Yoga': panchang_data.get('yoga', ''),
        'Karana': panchang_data.get('karana', ''),
        'Paksha': panchang_data.get('paksha', ''),
        'Moon Phase': panchang_data.get('moonPhase', ''),
        'Sunrise': sr or 'N/A',
        'Sunset': ss or 'N/A',
    }
    elements.extend(_kv_block(data, 'Birth Panchang'))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 24: AVAKHADA DETAILS ────────────────
def build_avakhada_section(planet: dict) -> list:
    elements = []
    elements.append(colored_heading('24. Avakhada Details (Vedic Attributes)', PRIMARY, 14))
    elements.append(section_divider())
    elements.append(Paragraph(
        'Avakhada details reveal the subtle qualities of the birth chart based on Nakshatra and planetary positions.',
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8))

    from .utils import ZODIAC_SIGNS, NAKSHATRAS

    nak_name = planet.get('nakshatra', '')
    nak_idx = next((i for i, n in enumerate(NAKSHATRAS) if n[0] == nak_name), 0)

    VARNA_MAP = ['Brahmin', 'Kshatriya', 'Vaishya', 'Shudra', 'Brahmin', 'Kshatriya', 'Vaishya', 'Shudra',
                 'Shudra', 'Vaishya', 'Kshatriya', 'Brahmin', 'Brahmin', 'Kshatriya', 'Vaishya', 'Shudra',
                 'Brahmin', 'Kshatriya', 'Shudra', 'Vaishya', 'Kshatriya', 'Brahmin', 'Vaishya', 'Shudra',
                 'Brahmin', 'Kshatriya', 'Vaishya']
    GANA_MAP = ['Deva', 'Manushya', 'Rakshasa', 'Deva', 'Manushya', 'Rakshasa', 'Deva', 'Manushya', 'Rakshasa',
                'Rakshasa', 'Manushya', 'Deva', 'Deva', 'Rakshasa', 'Manushya', 'Rakshasa', 'Deva', 'Manushya',
                'Rakshasa', 'Manushya', 'Deva', 'Deva', 'Rakshasa', 'Manushya', 'Manushya', 'Rakshasa', 'Deva']
    NADI_MAP = ['Adi', 'Madhya', 'Antya'] * 9
    VASHYA_MAP = ['Chatushpad', 'Manav', 'Vanchar', 'Jalachar', 'Chatushpad', 'Vanchar',
                  'Manav', 'Jalachar', 'Jalachar', 'Vanchar', 'Manav', 'Chatushpad',
                  'Manav', 'Vanchar', 'Manav', 'Vanchar', 'Jalachar', 'Manav',
                  'Chatushpad', 'Vanchar', 'Manav', 'Chatushpad', 'Vanchar', 'Jalachar',
                  'Manav', 'Chatushpad', 'Manav']
    YONI_MAP = ['Ashwa', 'Gaja', 'Mesha', 'Sarpa', 'Shwana', 'Bidala', 'Mushika', 'Gomayu', 'Simha',
                'Shwana', 'Vrishabha', 'Gomayu', 'Mahish', 'Vyaghra', 'Mahish', 'Shwana', 'Mriga', 'Sarp',
                'Shwana', 'Vrishabha', 'Gomayu', 'Gaja', 'Simha', 'Ashwa', 'Vrishabha', 'Gomayu', 'Gaja']

    varna = VARNA_MAP[nak_idx] if nak_idx < len(VARNA_MAP) else 'N/A'
    gana = GANA_MAP[nak_idx] if nak_idx < len(GANA_MAP) else 'N/A'
    nadi = NADI_MAP[nak_idx] if nak_idx < len(NADI_MAP) else 'N/A'
    vashya = VASHYA_MAP[nak_idx] if nak_idx < len(VASHYA_MAP) else 'N/A'
    yoni = YONI_MAP[nak_idx] if nak_idx < len(YONI_MAP) else 'N/A'

    data = {
        'Nakshatra': nak_name,
        'Nakshatra Lord': planet.get('nakshatraLord', ''),
        'Pada': planet.get('nakshatraPada', 1),
        'Varna': varna,
        'Vashya': vashya,
        'Gana': gana,
        'Nadi': nadi,
        'Yoni': yoni,
        'Sign': planet.get('sign', ''),
        'Sign Lord': planet.get('signLord', ''),
    }
    elements.extend(_kv_block(data, 'Avakhada Attributes'))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 25: BHAVA CHALIT ────────────────
def build_bhava_chalit_section(house_data: dict) -> list:
    elements = []
    elements.append(colored_heading('25. Bhava Chalit (House Cusp Analysis)', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    houses = house_data.get('houses', [])
    cusps = house_data.get('cusps', [])

    elements.append(Paragraph(
        'Bhava Chalit shows the cusp-based house system where each house starts at a specific degree '
        'rather than being a whole sign. Planets near house cusps show stronger influence.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    if cusps:
        cusp_data = []
        for i, cusp_deg in enumerate(cusps[:12]):
            from .utils import ZODIAC_SIGNS, SIGN_LORDS, get_nakshatra
            sign_idx = int(cusp_deg // 30) % 12
            sign = ZODIAC_SIGNS[sign_idx]
            degree_in_sign = cusp_deg % 30
            nak = get_nakshatra(cusp_deg)
            cusp_data.append({
                'house': i + 1,
                'sign': sign,
                'lord': SIGN_LORDS.get(sign, ''),
                'degree': f"{degree_in_sign:.2f}°",
                'nakshatra': nak.get('name', ''),
            })
        headers = ['Cusp', 'Sign', 'Lord', 'Degree', 'Nakshatra']
        rows = [[f"H{c['house']}", c['sign'], c['lord'], c['degree'], c['nakshatra']] for c in cusp_data]
        col_widths = [40, 70, 70, 60, 80]
        content.append(make_modern_table(headers, rows, col_widths))
    else:
        content.append(Paragraph(
            'Cusp data not available for the selected house system. Showing whole-sign houses.',
            styles['BodyText2']
        ))
        headers = ['House', 'Sign', 'Lord', 'Planets']
        rows = []
        for h in houses:
            planets_str = ', '.join(h.get('planets', [])) or '—'
            rows.append([str(h['number']), h.get('sign', ''), h.get('signLord', ''), planets_str])
        col_widths = [40, 70, 70, 140]
        content.append(make_modern_table(headers, rows, col_widths))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 26: KP SYSTEM ────────────────
def build_kp_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('26. KP Astrology (Star & Sub Lord)', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    from .main import kp_sub_lord_for, kp_details
    from .utils import SIGN_LORDS, ZODIAC_SIGNS

    pmap = {p['name']: p for p in planets}
    houses = []
    for i in range(12):
        house_planets = [p['name'] for p in planets if p.get('house', 0) == i + 1]
        houses.append({
            'number': i + 1,
            'sign': ZODIAC_SIGNS[i],
            'signLord': SIGN_LORDS.get(ZODIAC_SIGNS[i], ''),
            'degree': 0,
            'planets': house_planets,
        })

    elements.append(Paragraph(
        'KP (Krishnamurti Paddhati) system divides each nakshatra into 9 unequal sub-lords '
        'based on the Vimshottari Dasha year proportions for precise event prediction.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    try:
        kp = kp_details(houses, planets)
    except Exception:
        kp = None

    if kp and kp.get('planetDetails'):
        headers = ['Planet', 'Cusp', 'Sign', 'Sign Lord', 'Star Lord', 'Sub Lord', 'Sub Sub Lord']
        rows = []
        for pd in kp['planetDetails']:
            sign = pd.get('sign', '')
            sign_lord = SIGN_LORDS.get(sign, '')
            star_lord = pd.get('starLord', '') or ''
            sub_lord = pd.get('subLord', '') or ''
            sub_sub_lord = kp_sub_lord_for(
                next((p['longitude'] for p in planets if p['name'] == pd['planet']), 0)
            )
            rows.append([
                pd['planet'], str(pd.get('cusp', '')), sign, sign_lord,
                star_lord, sub_lord, sub_sub_lord
            ])
    else:
        headers = ['Planet', 'Cusp', 'Sign', 'Sign Lord', 'Star Lord', 'Sub Lord', 'Sub Sub Lord']
        rows = []
        for p in planets:
            if p['name'] not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                continue
            sign = p.get('sign', '')
            sign_lord = p.get('signLord', SIGN_LORDS.get(sign, ''))
            star_lord = p.get('nakshatraLord', '') or ''
            sub_lord = kp_sub_lord_for(p['longitude'])
            sub_sub_lord = kp_sub_lord_for(p['longitude'])
            rows.append([
                p['name'], str(p.get('house', '')), sign, sign_lord,
                star_lord, sub_lord, sub_sub_lord
            ])

    col_widths = [45, 35, 55, 55, 65, 65, 65]
    content.append(make_modern_table(headers, rows, col_widths))

    content.append(Spacer(1, 8))
    content.append(colored_heading('Ruling Planets', ACCENT, 11))

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    first_house_planets = [p for p in planets if p.get('house', 0) == 1]
    asc_sign = first_house_planets[0].get('sign', '') if first_house_planets else ''
    asc_lord = SIGN_LORDS.get(asc_sign, '') if asc_sign else ''
    moon_nak_lord = ''
    moon_sub_lord = ''

    if moon:
        moon_nak_lord = moon.get('nakshatraLord', '')
        moon_sub_lord = kp_sub_lord_for(moon['longitude'])

    rp_headers = ['Ruling Factor', 'Lord']
    rp_rows = [
        ['Ascendant Lord', asc_lord or '-'],
        ['Moon Star Lord', moon_nak_lord or '-'],
        ['Moon Sub Lord', moon_sub_lord or '-'],
        ['Day Lord', 'Sun'],
    ]
    content.append(make_modern_table(rp_headers, rp_rows, [120, 100]))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 27: SHADBALA ────────────────
def build_shadbala_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('27. Shadbala (Six-fold Planetary Strength)', PRIMARY, 14))
    elements.append(section_divider())

    from .utils import planet_status, ZODIAC_SIGNS, PLANET_PROPS

    pmap = {p['name']: p for p in planets}
    planet_order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

    required_rupas = {
        'Sun': 5, 'Moon': 6, 'Mars': 5, 'Mercury': 7,
        'Jupiter': 6.5, 'Venus': 5.5, 'Saturn': 5,
    }
    directional_houses = {
        'Sun': 10, 'Moon': 4, 'Mars': 10, 'Mercury': 1,
        'Jupiter': 1, 'Venus': 4, 'Saturn': 7,
    }

    benefic_planets = {'Jupiter', 'Venus', 'Mercury', 'Moon'}
    malefic_planets = {'Sun', 'Mars', 'Saturn'}
    diurnal_planets = {'Sun', 'Jupiter', 'Venus'}
    nocturnal_planets = {'Moon', 'Mars', 'Saturn'}

    # Exaltation degrees for Uchcha Bala
    EXALTATION_DEG = {
        'Sun': 10, 'Moon': 3, 'Mars': 28, 'Mercury': 15,
        'Jupiter': 5, 'Venus': 27, 'Saturn': 20,
    }

    def _uchcha_bala(p):
        name = p['name']
        deg = p.get('longitude', 0)
        ex_deg = EXALTATION_DEG.get(name, 0)
        ex_long = (ZODIAC_SIGNS.index(PLANET_PROPS[name]['exalted']) * 30 + ex_deg) if PLANET_PROPS.get(name, {}).get('exalted', '') in ZODIAC_SIGNS else deg
        return max(0, 60 * (1 - abs(deg - ex_long) / 180))

    def _sthaana_bala(p):
        name = p['name']
        sign = p.get('sign', '')
        status = planet_status(name, sign)
        uchcha = _uchcha_bala(p)
        house = p.get('house', 1) or 1
        kendra_bala = 60 if house in (1, 4, 7, 10) else (30 if house in (2, 5, 8, 11) else 15)
        ojha = 15 if ZODIAC_SIGNS.index(sign) % 2 == 0 else 0 if sign else 7
        saptavargaja = sum([60, 45, 30, 15, 0, 0, 0][:1])  # simplified
        drekkana = 15 if house in (1, 5, 9) else (10 if house in (2, 6, 10) else 5)
        return round((uchcha + kendra_bala + ojha + drekkana) * 1.85, 2)

    def _kaala_bala(p):
        name = p['name']
        house = p.get('house', 1) or 1
        nathonnata = 60 if (name in diurnal_planets and house in (1, 10, 11, 12)) or (name in nocturnal_planets and house in (4, 5, 6, 7)) else 30
        paksha = 30
        tribhaga = 20 if house in (1, 5, 9) else 15
        ayana = 30
        return round((nathonnata + tribhaga + ayana) * 1.95, 2)

    def _diga_bala(p):
        name = p['name']
        dh = directional_houses.get(name, 1)
        ph = p.get('house', 1) or 1
        diff = abs(ph - dh)
        if diff > 6:
            diff = 12 - diff
        return round(max(0, 60 * (1 - diff / 6)) * 2.2, 2)

    def _cheshta_bala(p):
        speed = abs(p.get('speed', 1))
        retro = p.get('isRetrograde', False)
        is_combust = p.get('isCombust', False)
        bala = 0
        if retro:
            bala = 60 + min(50, int(abs(p.get('speed', 0)) * 100))
        elif is_combust:
            bala = 10
        else:
            if speed < 1:
                bala = 30 + int(speed * 20)
            else:
                bala = max(0, 50 - int(speed * 3))
        return min(110, bala)

    def _naisargika_bala(pname):
        vals = {'Sun': 60, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71,
                'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 85.71}
        return vals.get(pname, 40)

    def _drik_bala(p):
        total = 0
        for other in planets:
            if other['name'] == p['name'] or other['name'] not in planet_order + ['Rahu', 'Ketu']:
                continue
            diff = abs(p.get('longitude', 0) - other.get('longitude', 0))
            diff = min(diff, 360 - diff)
            aspect_val = 0
            if abs(diff - 180) < 10:
                aspect_val = -12
            elif abs(diff - 120) < 8:
                aspect_val = 8
            elif abs(diff - 90) < 8:
                aspect_val = 6
            elif diff < 8:
                aspect_val = 4
            if aspect_val:
                if other['name'] in benefic_planets:
                    total += aspect_val * 1.5
                elif other['name'] in malefic_planets:
                    total -= abs(aspect_val) * 1.2
                elif other['name'] in ('Rahu', 'Ketu'):
                    total -= abs(aspect_val) * 0.8
        return round(max(-20, total), 2)

    headers = [
        'Planet', 'Sthaana Bala', 'Kaala Bala', 'Diga Bala', 'Cheshta Bala',
        'Naisargika Bala', 'Drik Bala', 'Total Shad Bala', 'Shad Bala Rupas',
        'Required', 'Ratio', 'Ranking', 'Ishta Phala'
    ]
    rows = []
    totals = []
    for pname in planet_order:
        p = pmap.get(pname)
        if not p:
            continue
        sb = _sthaana_bala(p)
        kb = _kaala_bala(p)
        db = _diga_bala(p)
        cb = _cheshta_bala(p)
        nb = _naisargika_bala(pname)
        drik = _drik_bala(p)
        total = sb + kb + db + cb + nb + drik
        rupas = total / 60.0
        req = required_rupas.get(pname, 5)
        ratio = total / (req * 60)
        ishta = (sb + kb + db + cb) / 4.0
        ishta = max(0, min(60, ishta))
        totals.append((pname, ratio, total))

    totals.sort(key=lambda x: -x[1])
    ranking_map = {t[0]: i + 1 for i, t in enumerate(totals)}

    for pname in planet_order:
        p = pmap.get(pname)
        if not p:
            continue
        sb = _sthaana_bala(p)
        kb = _kaala_bala(p)
        db = _diga_bala(p)
        cb = _cheshta_bala(p)
        nb = _naisargika_bala(pname)
        drik = _drik_bala(p)
        total = sb + kb + db + cb + nb + drik
        rupas = total / 60.0
        req = required_rupas.get(pname, 5)
        ratio = total / (req * 60)
        rank = ranking_map.get(pname, '-')
        ishta = (sb + kb + db + cb) / 4.0
        ishta = max(0, min(60, ishta))
        rows.append([
            pname, f'{sb:.1f}', f'{kb:.1f}', f'{db:.1f}', f'{cb:.1f}',
            f'{nb:.1f}', f'{drik:.1f}', f'{total:.1f}', f'{rupas:.2f}',
            str(req), f'{ratio:.3f}', str(rank), f'{ishta:.1f}'
        ])

    col_widths = [40, 55, 50, 45, 55, 60, 45, 60, 60, 45, 40, 35, 45]
    elements.append(make_modern_table(headers, rows, col_widths))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        '<i>All values in Virupas (0-60 scale per component). 1 Rupa = 60 Virupas. '
        'Ranking = 1 (highest ratio) to 7 (lowest). Ishta Phala = avg(Sthaana, Kaala, Diga, Cheshta).</i>',
        styles['SmallText']
    ))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 28: CHAR DASHA ────────────────
def build_char_dasha_section(planets: list, ascendant: dict) -> list:
    elements = []
    elements.append(colored_heading('28. Chara Dasha (Jaimini System)', PRIMARY, 14))
    elements.append(section_divider())
    elements.append(Paragraph(
        'Chara Dasha (Moving Dasha) is a Jaimini system where Mahadasha periods are calculated '
        'based on the number of signs from a sign to its lord. It complements Vimshottari Dasha.',
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8))

    from .utils import ZODIAC_SIGNS, SIGN_LORDS

    asc_sign = ascendant.get('sign', '')
    asc_idx = ZODIAC_SIGNS.index(asc_sign) if asc_sign in ZODIAC_SIGNS else 0

    chara_years = {}
    pmap = {p['name']: p for p in planets}
    for i, sign in enumerate(ZODIAC_SIGNS):
        lord = SIGN_LORDS[sign]
        lord_p = pmap.get(lord, {})
        lord_house = lord_p.get('house', ((i - asc_idx + 12) % 12) + 1)
        # MD duration = number of signs from this sign to its lord's position
        lord_sign_idx = ZODIAC_SIGNS.index(lord_p.get('sign', sign)) if lord_p.get('sign', '') in ZODIAC_SIGNS else i
        distance = (lord_sign_idx - i + 12) % 12
        if distance == 0:
            distance = 12
        chara_years[sign] = distance

    headers = ['Sign', 'Lord', 'Duration (yrs)', 'Start Age']
    rows = []
    age = 0
    ordered = ZODIAC_SIGNS[asc_idx:] + ZODIAC_SIGNS[:asc_idx]
    for sign in ordered:
        lord = SIGN_LORDS[sign]
        yrs = chara_years.get(sign, 12)
        rows.append([sign, lord, str(yrs), f"{age:.1f}"])
        age += yrs

    col_widths = [80, 60, 80, 80]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        '<i>Chara Dasha periods repeat in 120-year cycles. The current MD is determined by the sign '
        'whose age range includes the native\'s current age.</i>',
        styles['SmallText']
    ))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 29: SADE SATI ────────────────
def build_sade_sati_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('29. Sade Sati (Saturn Transit Analysis)', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    sat = next((p for p in planets if p['name'] == 'Saturn'), None)

    elements.append(Paragraph(
        'Sade Sati is the 7.5-year period when Saturn transits the 12th, 1st, and 2nd houses '
        'from the natal Moon. It is a significant period of karmic testing and transformation.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    from .utils import ZODIAC_SIGNS

    if moon and sat:
        moon_sign = moon.get('sign', '')
        sat_sign = sat.get('sign', '')
        moon_idx = ZODIAC_SIGNS.index(moon_sign) if moon_sign in ZODIAC_SIGNS else 0
        sat_idx = ZODIAC_SIGNS.index(sat_sign) if sat_sign in ZODIAC_SIGNS else 0
        diff = (sat_idx - moon_idx) % 12

        phase = ''
        if diff == 0:
            phase = 'Peak Phase (Saturn in same sign as Moon) - Intense karmic testing, health challenges, major life transformations'
        elif diff == 11:
            phase = 'Rising Phase (Saturn in 12th from Moon) - Beginning of Sade Sati, financial strain, preparatory challenges'
        elif diff == 1:
            phase = 'Settling Phase (Saturn in 2nd from Moon) - Waning of Sade Sati, gradual relief, lesson integration'
        else:
            phase = 'Not Active - Saturn is not transiting Moon\'s adjacent signs'

        sat_house = sat.get('house', 0)
        moon_house = moon.get('house', 0)
        house_diff = (sat_house - moon_house) % 12

        data = {
            'Moon Sign': moon_sign,
            'Saturn Sign': sat_sign,
            'Phase': phase,
            'House Relation': f"Moon house {moon_house}, Saturn house {sat_house} (diff {house_diff})",
        }
        content.extend(_kv_block(data, 'Sade Sati Status'))
    else:
        content.append(Paragraph('Moon or Saturn data not available.', styles['BodyText2']))

    content.append(Spacer(1, 6))
    sat_remedies = [
        'Recite Shani Mantra 108 times daily: "Om Sham Shanaishcharaya Namah"',
        'Visit Hanuman temple every Saturday',
        'Donate black sesame, urad dal, and iron items on Saturdays',
        'Offer mustard oil to Shani Dev at a Shani temple',
        'Serve the elderly and underprivileged with humility',
    ]
    content.append(colored_heading('Sade Sati Remedies', ACCENT, 11))
    for r in sat_remedies:
        content.append(_bullet(r))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 30: VARSHAPHAL ────────────────
def build_varshaphal_section(planets: list, ascendant: dict) -> list:
    elements = []
    elements.append(colored_heading('30. Varshaphal (Annual Solar Return)', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'Varshaphal is the annual horoscope based on the exact moment the Sun returns to its natal '
        'position each year. It provides year-ahead predictions for key life areas.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    sun = next((p for p in planets if p['name'] == 'Sun'), None)
    asc_sign = ascendant.get('sign', '')
    from .utils import ZODIAC_SIGNS, SIGN_LORDS
    asc_idx = ZODIAC_SIGNS.index(asc_sign) if asc_sign in ZODIAC_SIGNS else 0

    if sun:
        sun_sign = sun.get('sign', '')
        sun_sign_idx = ZODIAC_SIGNS.index(sun_sign) if sun_sign in ZODIAC_SIGNS else 0
        muntha_house = ((sun_sign_idx - asc_idx + 12) % 12) + 1

        data = {
            'Return Sign': sun_sign,
            'Muntha House': str(muntha_house),
            'Year Theme': ['New Beginnings', 'Finance & Values', 'Communication', 'Home & Family',
                          'Creativity', 'Health & Service', 'Relationships', 'Transformation',
                          'Philosophy', 'Career', 'Community', 'Spirituality'][muntha_house - 1],
        }
        content.extend(_kv_block(data, f'Solar Return in {sun_sign}'))
    else:
        content.append(Paragraph('Sun data not available.', styles['BodyText2']))

    content.append(Spacer(1, 6))

    domain_predictions = {
        'Career': ['Focus on career growth', 'Seek mentorship', 'Take calculated risks'][:1],
        'Finance': ['Review investments', 'Avoid major debts', 'Plan savings'][:1],
        'Health': ['Prioritize wellness', 'Regular check-ups', 'Stress management'][:1],
        'Relationships': ['Strengthen bonds', 'Communicate openly', 'Quality time'][:1],
        'Travel': ['Short trips favorable', 'Plan ahead', 'Document readiness'][:1],
    }
    content.append(colored_heading('Yearly Domain Forecast', ACCENT, 11))
    for domain, pts in domain_predictions.items():
        content.append(Paragraph(f"<b>{domain}:</b> {pts[0]}", styles['BodyText2']))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 31: RUDRAKSHA ────────────────
def build_rudraksha_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('31. Rudraksha Recommendations', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'Rudraksha beads are sacred seeds worn for their spiritual and astrological benefits. '
        'Each Mukhi (face) corresponds to a specific planetary energy and deity.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    sun = next((p for p in planets if p['name'] == 'Sun'), None)
    from .utils import ZODIAC_SIGNS

    MOON_SIGN_RUDRAK = {
        'Aries': '4 Mukhi', 'Taurus': '5 Mukhi', 'Gemini': '6 Mukhi',
        'Cancer': '7 Mukhi', 'Leo': '8 Mukhi', 'Virgo': '9 Mukhi',
        'Libra': '10 Mukhi', 'Scorpio': '11 Mukhi', 'Sagittarius': '12 Mukhi',
        'Capricorn': '13 Mukhi', 'Aquarius': '14 Mukhi', 'Pisces': '1 Mukhi',
    }
    PLANET_RUDRAK = {
        'Sun': '1 Mukhi', 'Moon': '2 Mukhi', 'Mars': '3 Mukhi',
        'Mercury': '4 Mukhi', 'Jupiter': '5 Mukhi', 'Venus': '6 Mukhi',
        'Saturn': '7 Mukhi', 'Rahu': '8 Mukhi', 'Ketu': '9 Mukhi',
    }
    RUDRAKSHA_DETAILS = {
        '1 Mukhi': {'deity': 'Shiva', 'planet': 'Sun', 'benefits': 'Liberation, enlightenment, self-realization'},
        '2 Mukhi': {'deity': 'Ardhanarishwara', 'planet': 'Moon', 'benefits': 'Harmony in relationships, emotional balance'},
        '3 Mukhi': {'deity': 'Agni', 'planet': 'Mars', 'benefits': 'Courage, confidence, overcoming fear'},
        '4 Mukhi': {'deity': 'Brahma', 'planet': 'Mercury', 'benefits': 'Knowledge, wit, communication skills'},
        '5 Mukhi': {'deity': 'Kalagni Rudra', 'planet': 'Jupiter', 'benefits': 'Wisdom, prosperity, spiritual growth'},
        '6 Mukhi': {'deity': 'Kartikeya', 'planet': 'Venus', 'benefits': 'Creativity, luxury, relationship harmony'},
        '7 Mukhi': {'deity': 'Ananta', 'planet': 'Saturn', 'benefits': 'Career success, longevity, overcoming obstacles'},
        '8 Mukhi': {'deity': 'Vasuki', 'planet': 'Rahu', 'benefits': 'Removes confusion, ancestral blessing'},
        '9 Mukhi': {'deity': 'Bhairava', 'planet': 'Ketu', 'benefits': 'Spiritual awakening, moksha, karmic release'},
        '10 Mukhi': {'deity': 'Vishnu', 'planet': 'Jupiter', 'benefits': 'Protection, success in endeavors'},
        '11 Mukhi': {'deity': 'Rudra', 'planet': 'Sun', 'benefits': 'Victory, leadership, authority'},
        '12 Mukhi': {'deity': 'Aditya', 'planet': 'Sun', 'benefits': 'Radiant health, vitality, spiritual light'},
        '13 Mukhi': {'deity': 'Vishwakarma', 'planet': 'Venus', 'benefits': 'Creativity, career fulfillment, wish fulfillment'},
        '14 Mukhi': {'deity': 'Shiva', 'planet': 'Saturn', 'benefits': 'Protection from evil, longevity, peace'},
    }

    recommended = []
    if moon:
        moon_sign = moon.get('sign', '')
        primary = MOON_SIGN_RUDRAK.get(moon_sign, '5 Mukhi')
        recommended.append(('Primary (Moon Sign)', primary))

    weak_planets = [p for p in planets if p.get('houseStatus') in ['Debilitated', 'Enemy']]
    for p in weak_planets[:3]:
        if p['name'] in PLANET_RUDRAK:
            recommended.append((f'{p['name']} (Weak)', PLANET_RUDRAK[p['name']]))

    if not recommended:
        recommended.append(('General Wellness', '5 Mukhi (Kalagni Rudra)'))

    headers = ['Recommendation', 'Mukhi', 'Deity', 'Benefits']
    rows = []
    for reason, mukhi in recommended:
        det = RUDRAKSHA_DETAILS.get(mukhi, {})
        deity = det.get('deity', '')
        benefits = det.get('benefits', '')
        rows.append([reason, mukhi, deity, benefits])

    col_widths = [80, 60, 70, 170]
    content.append(make_modern_table(headers, rows, col_widths))
    content.append(Spacer(1, 6))

    content.append(colored_heading('Wearing Instructions', ACCENT, 11))
    instructions = [
        'Purchase from a trusted source; soak in raw milk and Ganga jal overnight before wearing',
        'String in a silk or red thread; wear on Tuesday or Sunday morning after purification',
        'Apply sandalwood paste and chant the corresponding Beej Mantra 108 times',
        'Keep the Rudraksha clean; oil occasionally with sesame or sandalwood oil',
        'Remove during sleep and intimate activities; store in a clean, sacred space',
    ]
    for instr in instructions:
        content.append(_bullet(instr))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 32: LAL KITAB ────────────────
def build_lal_kitab_section(planets: list, houses: list) -> list:
    elements = []
    elements.append(colored_heading('32. Lal Kitab Remedies', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'Lal Kitab is a unique system of Vedic astrology that focuses on simple, practical remedies '
        'for planetary afflictions. Remedies often involve donations, daily habits, and charitable acts.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    LAL_KITAB_REMEDIES = {
        'Sun': ['Offer water to Sun at sunrise from a copper vessel', 'Donate wheat or jaggery on Sunday',
                'Avoid consuming non-vegetarian food on Sunday', 'Plant a Peepal tree'],
        'Moon': ['Offer white rice and curd to the poor on Monday', 'Keep fast on Mondays',
                 'Wear pearl or moonstone (if favorable)', 'Pour water on Peepal tree roots on Mondays'],
        'Mars': ['Donate red lentils or red cloth on Tuesday', 'Recite Hanuman Chalisa on Tuesday',
                 'Avoid arguments and conflicts', 'Offer coconut at Hanuman temple'],
        'Mercury': ['Donate green vegetables or moong dal on Wednesday', 'Chant Vishnu Sahasranama',
                    'Serve cows with green fodder', 'Keep a small green marble in your pocket'],
        'Jupiter': ['Donate turmeric or yellow cloth on Thursday', 'Chant Guru Mantra daily',
                    'Respect and serve your teachers/guru', 'Feed Brahmins or priests on Thursday'],
        'Venus': ['Donate white items (rice, milk, sugar) on Friday', 'Apply sandalwood paste daily',
                  'Keep flowers in the home', 'Worship Goddess Lakshmi on Friday evening'],
        'Saturn': ['Donate black items (sesame, urad dal, iron) on Saturday', 'Feed crows or black dogs',
                   'Offer mustard oil at Shani temple', 'Recite Shani Stotra or Hanuman Chalisa'],
        'Rahu': ['Donate blue/black items or coconut', 'Feed fish daily if possible',
                 'Perform Nag Puja or Rahu Shanti', 'Chant Rahu Beej Mantra 108 times'],
        'Ketu': ['Donate blankets or mustard oil', 'Feed dogs and stray animals',
                 'Perform Ketu Shanti Homa', 'Chant Ketu Beej Mantra'],
    }

    pmap = {p['name']: p for p in planets}
    headers = ['Planet', 'House', 'Status', 'Suggested Remedy']
    rows = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        p = pmap.get(pname)
        if not p:
            continue
        status = p.get('houseStatus', '')
        if status in ['Debilitated', 'Enemy'] or (status in ['Neutral'] and p.get('house') in [6, 8, 12]):
            remedies = LAL_KITAB_REMEDIES.get(pname, [])
            remedy_text = remedies[0] if remedies else 'General charity recommended'
            rows.append([pname, str(p.get('house', '')), status, remedy_text])

    if rows:
        col_widths = [45, 40, 60, 235]
        content.append(make_modern_table(headers, rows, col_widths))
    else:
        content.append(Paragraph('No specific Lal Kitab remedies needed - all planets are well-placed.',
                                  styles['BodyText2']))

    content.append(Spacer(1, 6))
    content.append(colored_heading('General Lal Kitab Practices', ACCENT, 11))
    general = [
        'Feed the hungry and stray animals regularly',
        'Keep a clean water bowl for birds in the balcony/garden',
        'Plant a Tulsi (holy basil) plant at home and water it daily',
        'Donate to charity on your birth star (Nakshatra) day',
        'Practice forgiveness and avoid holding grudges',
    ]
    for g in general:
        content.append(_bullet(g))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 33: MANTRAS & YANTRAS ────────────────
def build_mantras_yantras_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('33. Mantras & Yantras', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'Mantras are sound vibrations that align planetary energies. Yantras are geometric diagrams '
        'that focus cosmic energy. Regular chanting and worship brings peace, success, and spiritual growth.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    BEEJ_MANTRAS = {
        'Sun': 'Om Hram Hreem Hraum Sah Suryaya Namah',
        'Moon': 'Om Shram Shreem Shraum Sah Chandraya Namah',
        'Mars': 'Om Kram Krim Kroum Sah Bhaumaya Namah',
        'Mercury': 'Om Bram Brim Broom Sah Budhaya Namah',
        'Jupiter': 'Om Gram Greem Graum Sah Gurave Namah',
        'Venus': 'Om Dram Dreem Droum Sah Shukraya Namah',
        'Saturn': 'Om Pram Preem Proum Sah Shanaishcharaya Namah',
        'Rahu': 'Om Bhram Bhreem Bhroum Sah Rahave Namah',
        'Ketu': 'Om Sram Sreem Sroum Sah Ketave Namah',
    }
    GAYATRI_MANTRAS = {
        'Sun': 'Om Bhur Bhavah Svah, Tat Savitur Varenyam, Bhargo Devasya Dhimahi, Dhiyo Yo Nah Prachodayat',
        'Moon': 'Om Aam Aam Aam, Chandramase Namah, Kshirarnave Namah, Shankhachakradharaya Namah',
        'Mars': 'Om Angarakaya Vidmahe, Shaktihastaya Dhimahi, Tanno Bhaumah Prachodayat',
        'Mercury': 'Om Budhaya Vidmahe, Shashthibhushanaya Dhimahi, Tanno Budhah Prachodayat',
        'Jupiter': 'Om Devaguru Vidmahe, Dharmagnaya Dhimahi, Tanno Guru Prachodayat',
        'Venus': 'Om Shukraya Vidmahe, Devanjanaya Dhimahi, Tanno Shukrah Prachodayat',
        'Saturn': 'Om Shanaishcharaya Vidmahe, Mandaya Karmathaya Dhimahi, Tanno Mandah Prachodayat',
        'Rahu': 'Om Rahave Vidmahe, Simhashanaya Dhimahi, Tanno Rahuh Prachodayat',
        'Ketu': 'Om Ketave Vidmahe, Dhumraketave Dhimahi, Tanno Ketuh Prachodayat',
    }
    YANTRAS = {
        'Sun': 'Surya Yantra - Copper, square design with a circle at center',
        'Moon': 'Chandra Yantra - Silver, crescent moon on lotus',
        'Mars': 'Mangal Yantra - Red, triangular with six-pointed star',
        'Mercury': 'Budh Yantra - Green, hexagonal design',
        'Jupiter': 'Guru Yantra - Yellow, square within octagon',
        'Venus': 'Shukra Yantra - White, diamond/pentagram design',
        'Saturn': 'Shani Yantra - Black/Blue, iron or steel with square pattern',
        'Rahu': 'Rahu Yantra - Blue/Black, serpentine design',
        'Ketu': 'Ketu Yantra - Multicolor, flag/tassel motif',
    }

    headers = ['Planet', 'Beej Mantra', 'Yantra']
    rows = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        p = next((p for p in planets if p['name'] == pname), None)
        if p:
            beej = BEEJ_MANTRAS.get(pname, '')
            yantra = YANTRAS.get(pname, '')
            rows.append([pname, beej, yantra])

    col_widths = [40, 220, 180]
    content.append(make_modern_table(headers, rows, col_widths))
    content.append(Spacer(1, 6))

    content.append(colored_heading('Chanting Guidelines', ACCENT, 11))
    guidelines = [
        'Chant mantras 108 times daily, preferably at sunrise facing East',
        'Use a rudraksha or sandalwood mala (rosary) for counting',
        'Sit on a clean mat facing the appropriate direction for the planet',
        'Light a ghee lamp and incense before chanting',
        'Maintain purity of thought and diet for best results',
    ]
    for g in guidelines:
        content.append(_bullet(g))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 34: ASHTAKAVARGA ────────────────
def build_ashtakavarga_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('34. Ashtakavarga (Eight-fold Strength)', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'Ashtakavarga is a unique system that evaluates the strength of each house through benefic '
        'aspects from all seven primary planets. Higher bindu count indicates stronger results.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    from .main import compute_ashtakavarga
    av = compute_ashtakavarga(planets)

    planets_order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

    headers = ['Planet'] + [str(h) for h in range(1, 13)] + ['Total']
    rows = []
    for pname in planets_order:
        contrib = av.get('planetContributions', {}).get(pname, {})
        row = [pname] + [str(contrib.get(h, 0)) for h in range(1, 13)] + [str(sum(contrib.values()))]
        rows.append(row)

    sav = av.get('sarvashtakavarga', {})
    house_points = sav.get('housePoints', {})
    sav_row = ['SAV'] + [str(house_points.get(str(h), 0)) for h in range(1, 13)] + [str(sum(house_points.values()))]
    rows.append(sav_row)

    col_widths = [45] + [25] * 12 + [35]
    content.append(make_modern_table(headers, rows, col_widths))
    content.append(Spacer(1, 8))

    strong_houses = ', '.join([f"H{h.get('house')}({h.get('points')})" for h in sav.get('strongestHouses', [])])
    weak_houses = ', '.join([f"H{h.get('house')}({h.get('points')})" for h in sav.get('weakestHouses', [])])
    content.append(Paragraph(
        f"<b>Sarvashtakavarga Average:</b> {sav.get('average', 0)} | "
        f"<b>Strongest Houses:</b> {strong_houses} | "
        f"<b>Weakest Houses:</b> {weak_houses}",
        styles['BodyText2']
    ))
    content.append(Paragraph(
        '<i>House strength guide: 8+ Excellent, 6-7 Good, 4-5 Average, 0-3 Weak. '
        'Higher bindu count = stronger results from the house.</i>',
        styles['SmallText']
    ))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── SECTION 35: GANDMOOL & PUNARPHOO DOSHA ────────────────
def build_gandmool_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('35. Gandmool & Punarphoo Dosha', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'Gandmool Dosha occurs when planets are at the junction (Gandanta) between water and fire '
        'nakshatras. Punarphoo Dosha arises from Saturn-Moon affliction causing delays in marriage.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    from .main import detect_gandmool_dosha
    doshas = detect_gandmool_dosha(planets)

    for d in doshas:
        content.append(colored_heading(d['name'], ACCENT, 11))
        content.append(Paragraph(d.get('description', ''), styles['BodyText2']))
        if d.get('present'):
            severity = d.get('severity', 'Medium')
            color = colors.red if severity == 'High' else (colors.orange if severity == 'Medium' else colors.green)
            content.append(Paragraph(
                f"<b>Severity:</b> <font color='{color.hexval()}'>{severity}</font>",
                styles['BodyText2']
            ))
            remedies = d.get('remedies', [])
            if remedies:
                content.append(Paragraph('<b>Remedies:</b>', styles['BodyText2']))
                for r in remedies:
                    content.append(_bullet(r))
        content.append(Spacer(1, 6))

    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements


# ──────────────── EXTRA: BHAVABALA (HOUSE STRENGTH) ────────────────
def build_bhavabala_section(planets: list, houses: list) -> list:
    elements = []
    elements.append(colored_heading('Bhavabala (House Strength)', ACCENT, 11))
    from .utils import ZODIAC_SIGNS, SIGN_LORDS, planet_status

    pmap = {p['name']: p for p in planets}
    hp_map = {}
    for h in houses:
        for pname in h.get('planets', []):
            hp_map.setdefault(h['number'], []).append(pname)

    benefic_planets = {'Jupiter', 'Venus', 'Mercury', 'Moon'}
    malefic_planets = {'Sun', 'Mars', 'Saturn'}

    def _aspects_to_house(house_num):
        score = 0
        for other in planets:
            if other['name'] not in benefic_planets | malefic_planets | {'Rahu', 'Ketu'}:
                continue
            diff = abs(other.get('longitude', 0) - (house_num - 1) * 30)
            diff = min(diff, 360 - diff)
            if abs(diff - 180) < 10:
                score += 15 if other['name'] in benefic_planets else 8
            elif abs(diff - 120) < 8:
                score += 10 if other['name'] in benefic_planets else 5
            elif abs(diff - 90) < 8:
                score += 8 if other['name'] in benefic_planets else 4
        return score

    headers = ['House', 'Total Bhava Bala', 'Bhava Bala (Rupas)', 'Strength Ratio', 'Ranking']
    rows = []
    house_balances = []

    for h in houses:
        hnum = h['number']
        sign = h.get('sign', '')
        lord = h.get('signLord', '')
        lord_p = pmap.get(lord, {})
        lord_status = planet_status(lord, lord_p.get('sign', '')) if lord_p else 'Neutral'

        total = 180

        if lord_status in ('Exalted', 'Own Sign', 'Mooltrikona'):
            total += 90
        elif lord_status in ('Friendly',):
            total += 45
        elif lord_status == 'Debilitated':
            total -= 60

        if lord_p and lord_p.get('house', 0) == hnum:
            total += 60

        occupants = hp_map.get(hnum, [])
        for occ in occupants:
            p = pmap.get(occ, {})
            dignity = planet_status(occ, p.get('sign', '')) if p else 'Neutral'
            if dignity in ('Exalted', 'Own Sign'):
                total += 45
            elif dignity == 'Debilitated':
                total -= 30
            else:
                total += 20

        total += _aspects_to_house(hnum)

        if hnum in (1, 4, 7, 10):
            total += 60
        if hnum in (1, 5, 9):
            total += 45
        if hnum in (6, 8, 12):
            total -= 30

        total = max(0, total)
        house_balances.append((hnum, total))

    house_balances.sort(key=lambda x: -x[1])
    rank_map = {hb[0]: i + 1 for i, hb in enumerate(house_balances)}

    house_order = [hb[0] for hb in sorted(house_balances)]  # H1-H12 natural order

    for hnum in range(1, 13):
        total = dict(house_balances).get(hnum, 0)
        rupas = total / 60.0
        strength_ratio = total / (60.0 * 1.5)
        rank = rank_map.get(hnum, '-')
        rows.append([
            f'H{hnum}', f'{total:.1f}', f'{rupas:.2f}', f'{strength_ratio:.3f}', str(rank)
        ])

    col_widths = [40, 70, 70, 60, 40]
    elements.append(make_modern_table(headers, rows, col_widths))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        '<i>Bhava Bala based on lord strength, occupants, aspects, and house type. '
        '1 Rupa = 60 units. Strength Ratio = Total / 90.</i>',
        styles['SmallText']
    ))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── EXTRA: KP RULING PLANETS ────────────────
def build_kp_ruling_planets_section(planets: list, ascendant: dict) -> list:
    elements = []
    elements.append(colored_heading('KP Ruling Planets', ACCENT, 11))
    from .utils import ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS
    from .main import kp_sub_lord_for
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    asc_sign = ascendant.get('sign', '')
    asc_lord = SIGN_LORDS.get(asc_sign, '')
    data = {
        'Ascendant Lord': asc_lord,
    }
    if moon:
        moon_nak = moon.get('nakshatra', '')
        moon_nak_lord = moon.get('nakshatraLord', '')
        moon_sub = kp_sub_lord_for(moon['longitude'])
        data['Moon Star Lord'] = moon_nak_lord
        data['Moon Sub Lord'] = moon_sub
    data['Day Lord'] = 'Sun'
    data['Significator'] = 'Strongest among Asc, Moon, and Day lords'
    elements.extend(_kv_block(data, 'Ruling Planets'))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── EXTRA: KP CUSPS ────────────────
def build_kp_cusps_section(planets: list) -> list:
    elements = []
    elements.append(colored_heading('KP Cuspal Lords', ACCENT, 11))
    from .utils import ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS
    from .main import kp_sub_lord_for
    pmap = {p['name']: p for p in planets}
    headers = ['Cusp', 'Sign', 'Sign Lord', 'Star Lord', 'Sub Lord']
    rows = []
    for i in range(12):
        house_num = i + 1
        house_planets = [p for p in planets if p.get('house', 0) == house_num]
        if house_planets:
            p = house_planets[0]
            sign = p.get('sign', ZODIAC_SIGNS[i])
            sign_lord = p.get('signLord', SIGN_LORDS.get(sign, ''))
            star_lord = p.get('nakshatraLord', '')
            sub_lord = kp_sub_lord_for(p['longitude'])
        else:
            sign = ZODIAC_SIGNS[i]
            sign_lord = SIGN_LORDS.get(sign, '')
            star_lord = ''
            sub_lord = ''
        rows.append([str(house_num), sign, sign_lord, star_lord, sub_lord])
    col_widths = [40, 60, 60, 60, 60]
    elements.append(make_table(headers, rows, col_widths))
    elements.append(Spacer(1, 12))
    return elements


# ──────────────── EXTRA: PER-PLANET DEEP ANALYSIS ────────────────
def build_planet_analysis_section(planets: list, houses: list, ascendant: dict) -> list:
    elements = []
    elements.append(colored_heading('Planets Deep Analysis', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    from .utils import ZODIAC_SIGNS, SIGN_LORDS, planet_status, PLANET_PROPS

    PLANET_DOMAIN = {
        'Sun': 'Authority, vitality, ego, father, leadership',
        'Moon': 'Mind, emotions, mother, nurturing, public',
        'Mars': 'Energy, courage, siblings, action, conflict',
        'Mercury': 'Intellect, communication, commerce, education',
        'Jupiter': 'Wisdom, wealth, knowledge, spirituality, children',
        'Venus': 'Love, beauty, luxury, marriage, arts, relationships',
        'Saturn': 'Discipline, delays, karma, longevity, service',
        'Rahu': 'Material desires, obsession, foreign, innovation',
        'Ketu': 'Spirituality, detachment, past life, liberation',
    }
    HOUSE_MEANINGS = {
        1: 'Self, body, personality, beginnings',
        2: 'Wealth, family, speech, food',
        3: 'Courage, siblings, communication, short travel',
        4: 'Home, mother, comfort, education',
        5: 'Creativity, children, romance, intelligence',
        6: 'Health, enemies, service, debt',
        7: 'Marriage, partner, business, public',
        8: 'Transformation, secrets, longevity, occult',
        9: 'Fortune, dharma, higher learning, travel',
        10: 'Career, status, father, authority',
        11: 'Gains, friends, aspirations, income',
        12: 'Expenditure, spirituality, isolation, foreign',
    }

    asc_sign = ascendant.get('sign', '')
    asc_idx = ZODIAC_SIGNS.index(asc_sign) if asc_sign in ZODIAC_SIGNS else 0

    for p in planets:
        if p['name'] in ['Uranus', 'Neptune', 'Pluto']:
            continue
        pcolor = PLANET_COLORS.get(p['name'], ACCENT)
        block_content = []
        h = p.get('house', 0)
        sign = p.get('sign', '')
        status = planet_status(p['name'], sign)
        domain = PLANET_DOMAIN.get(p['name'], 'General')
        house_meaning = HOUSE_MEANINGS.get(h, '')
        is_retro = p.get('isRetrograde', False)
        is_combust = p.get('isCombust', False)

        data = {
            'Placement': f"{sign} (House {h})",
            'Dignity': status,
            'Domain': domain,
            'House Meaning': house_meaning,
            'Retrograde': 'Yes' if is_retro else 'No',
            'Combust': 'Yes' if is_combust else 'No',
            'Nakshatra': f"{p.get('nakshatra', '')} (Lord: {p.get('nakshatraLord', '')})",
            'Degree': f"{p.get('degree', 0):.2f}°",
        }
        block_content.extend(_kv_block(data))
        block_content.append(Spacer(1, 4))

        positives = []
        if status in ['Exalted', 'Own Sign', 'Mooltrikona']:
            positives.append(f"{p['name']} is strong in {status} — gives excellent results")
        if h in [1, 4, 5, 7, 9, 10]:
            positives.append(f"Placed in a favorable house (House {h})")
        if not is_retro and not is_combust:
            positives.append("Direct motion and not combust — unobstructed expression")
        if positives:
            block_content.append(Paragraph('<b>Positive Effects:</b>', styles['BodyText2']))
            for pos in positives:
                block_content.append(_bullet(pos))

        challenges = []
        if status in ['Debilitated', 'Enemy']:
            challenges.append(f"{p['name']} is {status} — requires remedial measures")
        if h in [6, 8, 12]:
            challenges.append(f"Placed in a challenging house (House {h})")
        if is_retro:
            challenges.append("Retrograde motion — internalized energy, delayed results")
        if is_combust:
            challenges.append("Combust — weakened by proximity to Sun")
        if challenges:
            block_content.append(Paragraph('<b>Challenges:</b>', styles['BodyText2']))
            for ch in challenges:
                block_content.append(_bullet(ch))

        elements.extend(block_content)
        elements.append(Spacer(1, 8))
    elements.extend(content)
    return elements


# ──────────────── EXTRA: OVERALL SUMMARY ────────────────
def build_overall_summary_section(planets: list, yogas: list, doshas: list, dasha: dict, ascendant: dict) -> list:
    elements = []
    elements.append(colored_heading('Overall Summary', PRIMARY, 14))
    elements.append(section_divider())

    from .utils import ZODIAC_SIGNS
    asc_sign = ascendant.get('sign', '')
    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    sun = next((p for p in planets if p['name'] == 'Sun'), None)
    moon_sign = moon.get('sign', '') if moon else ''
    sun_sign = sun.get('sign', '') if sun else ''

    strong_planets = [p['name'] for p in planets if p.get('houseStatus') in ['Exalted', 'Own Sign', 'Mooltrikona'] and p['name'] not in ['Uranus', 'Neptune', 'Pluto']]
    weak_planets = [p['name'] for p in planets if p.get('houseStatus') in ['Debilitated', 'Enemy'] and p['name'] not in ['Uranus', 'Neptune', 'Pluto']]
    active_doshas = [d['name'] for d in doshas if d.get('present')]
    beneficial_yogas = [y['name'] for y in yogas if y.get('strength') in ['Strong', 'Very Strong']]
    current_md = dasha.get('current', {}).get('planet', '')

    highlights = []
    highlights.append(f"<b>Birth Chart:</b> {asc_sign} Ascendant, {sun_sign} Sun, {moon_sign} Moon")
    if strong_planets:
        highlights.append(f"<b>Strong Planets:</b> {', '.join(strong_planets)} — favorable placements")
    if weak_planets:
        highlights.append(f"<b>Planets Needing Attention:</b> {', '.join(weak_planets)} — remedial measures recommended")
    if beneficial_yogas:
        highlights.append(f"<b>Beneficial Yogas:</b> {', '.join(beneficial_yogas[:5])}")
    if active_doshas:
        highlights.append(f"<b>Active Doshas:</b> {', '.join(active_doshas)} — appropriate remedies suggested in this report")
    if current_md:
        highlights.append(f"<b>Current Mahadasha:</b> {current_md} — this period shapes current life themes")

    elements.append(Paragraph('Your birth chart reveals a unique cosmic blueprint. Below are the key highlights:', styles['BodyText2']))
    elements.append(Spacer(1, 4))
    for h in highlights:
        elements.append(_bullet(h))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        'This report provides a comprehensive Vedic astrology analysis. For personalized guidance, '
        'consult a qualified Vedic astrologer who can synthesize these factors with current transits.',
        styles['BodyText2']
    ))

    elements.append(Spacer(1, 12))
    return elements


# ──────────────── SECTION 36: ASCENDANT & PLANETARY PREDICTIONS ────────────────
def build_ascendant_predictions_section(ascendant: dict) -> list:
    elements = []
    elements.append(colored_heading('36. Ascendant & Personality', PRIMARY, 14))
    elements.append(section_divider())
    content = []

    elements.append(Paragraph(
        'The Ascendant (Lagna) is the most important factor in the birth chart. It represents your '
        'outer personality, physical body, and the lens through which you experience life.',
        styles['BodyText2']
    ))
    content.append(Spacer(1, 6))

    ASCENDANT_TRAITS = {
        'Aries': {'traits': 'Courageous, impulsive, competitive, pioneering', 'personality': 'Natural leader with boundless energy. Quick to act but must learn patience.', 'career': 'Military, sports, surgery, entrepreneurship'},
        'Taurus': {'traits': 'Patient, reliable, sensual, stubborn', 'personality': 'Grounded and practical. Values security, comfort, and consistency.', 'career': 'Banking, agriculture, art, culinary arts'},
        'Gemini': {'traits': 'Adaptable, curious, communicative, restless', 'personality': 'Intellectual and versatile. Thrives on variety and mental stimulation.', 'career': 'Writing, teaching, sales, media, technology'},
        'Cancer': {'traits': 'Nurturing, emotional, intuitive, protective', 'personality': 'Deeply caring and family-oriented. Strong intuition and emotional intelligence.', 'career': 'Healthcare, real estate, counseling, food industry'},
        'Leo': {'traits': 'Confident, generous, dramatic, proud', 'personality': 'Natural performer with a warm heart. Seeks recognition and creative expression.', 'career': 'Entertainment, management, politics, luxury goods'},
        'Virgo': {'traits': 'Analytical, practical, modest, perfectionist', 'personality': 'Detail-oriented and service-minded. Seeks order and continuous improvement.', 'career': 'Healthcare, research, accounting, teaching, editing'},
        'Libra': {'traits': 'Diplomatic, charming, indecisive, peace-loving', 'personality': 'Balanced and artistic. Values harmony, relationships, and beauty.', 'career': 'Law, diplomacy, design, consulting, fashion'},
        'Scorpio': {'traits': 'Intense, determined, secretive, transformative', 'personality': 'Deeply passionate and resourceful. Seeks truth and emotional depth.', 'career': 'Research, detective work, psychology, surgery, finance'},
        'Sagittarius': {'traits': 'Optimistic, adventurous, philosophical, blunt', 'personality': 'Free-spirited explorer. Seeks meaning through travel, learning, and experiences.', 'career': 'Travel, education, publishing, law, spirituality'},
        'Capricorn': {'traits': 'Ambitious, disciplined, responsible, cautious', 'personality': 'Hardworking and achievement-oriented. Builds success through persistence.', 'career': 'Business, engineering, administration, banking, politics'},
        'Aquarius': {'traits': 'Innovative, humanitarian, eccentric, detached', 'personality': 'Forward-thinking and independent. Values freedom and social progress.', 'career': 'Technology, science, social work, aviation, astrology'},
        'Pisces': {'traits': 'Compassionate, artistic, dreamy, escapist', 'personality': 'Deeply spiritual and creative. Intuitive connection to the collective unconscious.', 'career': 'Arts, music, healing, spirituality, film, charity'},
    }

    asc_sign = ascendant.get('sign', '')
    traits = ASCENDANT_TRAITS.get(asc_sign, {})

    data = {
        'Ascendant Sign': asc_sign,
        'Degree': f"{ascendant.get('degree', 0) % 30:.2f}°",
        'Nakshatra': ascendant.get('nakshatra', ''),
        'Nakshatra Lord': ascendant.get('nakshatraLord', ''),
        'Key Traits': traits.get('traits', ''),
        'Suitable Careers': traits.get('career', ''),
    }
    content.extend(_kv_block(data, f'{asc_sign} Ascendant Profile'))
    content.append(Spacer(1, 4))
    content.append(Paragraph(f"<b>Personality:</b> {traits.get('personality', '')}", styles['BodyText2']))
    elements.append(Spacer(1, 12))
    elements.extend(content)
    return elements
