"""
Dedicated Chart Endpoints — Navamsa, Hora, and Sudarshana Chakra.
These are the most commonly used specialized charts in Vedic Astrology.
"""
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import svgwrite
import math
from io import StringIO

router = APIRouter()

PLANET_ABBR = {
    'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
    'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa',
    'Rahu': 'Ra', 'Ketu': 'Ke',
}
PLANET_COLORS = {
    'Sun': '#FFD700', 'Moon': '#C0C0C0', 'Mars': '#FF0000', 'Mercury': '#008000',
    'Jupiter': '#0000FF', 'Venus': '#FF1493', 'Saturn': '#000000',
    'Rahu': '#708090', 'Ketu': '#A52A2A',
}

# ──────────────────── SHARED: North Indian Diamond Rendering ────────────────────

HOUSE_POLYGONS = {
    1: [(100,225), (200,300), (300,225), (200,150)],
    2: [(100,225), (0,300), (200,300)],
    3: [(0,150), (0,300), (100,225)],
    4: [(0,150), (100,225), (200,150), (100,75)],
    5: [(0,0), (0,150), (100,75)],
    6: [(0,0), (100,75), (200,0)],
    7: [(100,75), (200,150), (300,75), (200,0)],
    8: [(200,0), (300,75), (400,0)],
    9: [(300,75), (400,150), (400,0)],
    10: [(300,75), (200,150), (300,225), (400,150)],
    11: [(300,225), (400,300), (400,150)],
    12: [(300,225), (200,300), (400,300)],
}
HOUSE_CENTERS = {
    1: (190, 75), 2: (100, 30), 3: (30, 75), 4: (90, 150),
    5: (30, 225), 6: (90, 278), 7: (190, 225), 8: (290, 278),
    9: (360, 225), 10: (290, 150), 11: (360, 75), 12: (290, 30),
}
HOUSE_NO_POS = {
    1: (195, 130), 2: (97, 60), 3: (75, 78), 4: (170, 152),
    5: (75, 227), 6: (95, 245), 7: (195, 170), 8: (295, 245),
    9: (320, 227), 10: (220, 152), 11: (320, 77), 12: (295, 60),
}


def _render_diamond_svg(width, height, asc_sign, planets_by_house, title_text, theme='light'):
    """Render a North Indian diamond chart SVG."""
    dwg = svgwrite.Drawing(size=(width, height), profile='full')
    dwg.attribs['viewBox'] = f'0 0 {width} {height}'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'

    scale_x = width / 400
    scale_y = height / 300

    def sp(pt):
        return (pt[0] * scale_x, pt[1] * scale_y)

    # Background
    if 'dark' in theme:
        dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='#1a1a2e'))

    # Gradient
    g = svgwrite.gradients.LinearGradient(start=(0, 0), end=(0, 1), id="grad")
    if 'opaque-dark' in theme:
        g.add_stop_color(0, '#1a1a2e', opacity=1.0)
        g.add_stop_color(1, '#16213e', opacity=1.0)
    elif 'dark' in theme:
        g.add_stop_color(0, '#1a1a2e', opacity=0.15)
        g.add_stop_color(1, '#16213e', opacity=0.08)
    else:
        g.add_stop_color(0, 'white', opacity=0.0)
        g.add_stop_color(1, '#f0f3bf', opacity=0.0)
    dwg.defs.add(g)

    # Draw houses
    for h in range(1, 13):
        pts = [sp(p) for p in HOUSE_POLYGONS[h]]
        dwg.add(svgwrite.shapes.Polygon(pts, fill="url(#grad)", stroke='#8B4513', stroke_width=1.5))

    # House numbers
    tc = '#006666' if 'dark' not in theme else '#66cccc'
    for h in range(1, 13):
        pos = sp(HOUSE_NO_POS[h])
        dwg.add(dwg.text(str(h), insert=pos, font_size='14px', fill=tc, font_weight='bold'))

    # Planets
    import math as _m
    radius = 20 * min(scale_x, scale_y)
    for h in range(1, 13):
        center = sp(HOUSE_CENTERS[h])
        hplanets = planets_by_house.get(h, [])
        for j, planet in enumerate(hplanets):
            if len(hplanets) == 1:
                px, py = center
            else:
                angle = 2 * _m.pi * j / len(hplanets)
                px = center[0] + radius * _m.cos(angle)
                py = center[1] + radius * _m.sin(angle)
            abbr = PLANET_ABBR.get(planet['name'], planet['name'][:2])
            color = PLANET_COLORS.get(planet['name'], '#000000')
            retro = planet.get('isRetrograde', False)
            label = f"{abbr}{'®' if retro else ''}"
            dwg.add(dwg.text(label, insert=(px, py), font_size='14px', fill=color, font_weight='bold', text_anchor='middle'))
            deg = f"{planet.get('degree', 0):.1f}°"
            dwg.add(dwg.text(deg, insert=(px, py + 14 * scale_y), font_size='11px', fill=color, text_anchor='middle'))

    # Title
    dwg.add(dwg.text(title_text, insert=(width / 2, 20), font_size='15px', fill='#8B008B',
                      font_weight='bold', text_anchor='middle'))

    output = StringIO()
    dwg.write(output)
    return output.getvalue()


class DedicatedChartRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    width: Optional[int] = Field(800, example=800)
    height: Optional[int] = Field(600, example=600)
    theme: Optional[str] = Field('light', example='light')


# ──────────────────── 1. NAVAMSA CHART (D9) ────────────────────
@router.post('/chart/navamsa-svg',
             summary="Navamsa (D9) Chart SVG",
             description="Generate the Navamsa chart — the most important divisional chart, showing marriage, dharma, and spiritual strength. Each sign is divided into 9 equal parts (10° each).")
def navamsa_chart_svg(req: DedicatedChartRequest):
    from ..main import to_julian, calc_planets, calc_houses, varga_sign, ZODIAC_SIGNS

    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode or 'mean')
    natal = calc_houses(jd, req.latitude, req.longitude, planets, 'W')

    # Navamsa ascendant
    asc_degree = natal['ascendant']['degree']
    asc_sign = varga_sign(asc_degree, 9) or natal['ascendant']['sign']
    asc_idx = ZODIAC_SIGNS.index(asc_sign)

    # Build navamsa planets
    by_house = {i: [] for i in range(1, 13)}
    planet_details = []
    for p in planets:
        vsign = varga_sign(p['longitude'], 9)
        if not vsign:
            continue
        sidx = ZODIAC_SIGNS.index(vsign)
        house = ((sidx - asc_idx + 12) % 12) + 1
        entry = {
            'name': p['name'],
            'sign': vsign,
            'house': house,
            'degree': p['degree'],
            'isRetrograde': p['isRetrograde'],
            'isCombust': p['isCombust'],
        }
        by_house[house].append(entry)
        planet_details.append(entry)

    w = req.width or 800
    h = req.height or 600
    svg = _render_diamond_svg(w, h, asc_sign, by_house,
                               f"Navamsa Chart (D9) | Asc: {asc_sign}", req.theme or 'light')

    return {
        'status': 200,
        'chart': {
            'name': 'Navamsa (D9)',
            'focus': 'Marriage, Dharma, Spiritual Strength',
            'varga': 9,
            'ascendant': {'sign': asc_sign, 'degree': asc_degree},
        },
        'planets': planet_details,
        'svg': svg,
    }


# ──────────────────── 2. HORA CHART (D2) ────────────────────
@router.post('/chart/hora-svg',
             summary="Hora (D2) Chart SVG",
             description="Generate the Hora chart — used for analyzing wealth and financial prospects. Each sign is divided into 2 equal parts (15° each): odd signs get Sun's hora (Leo), even signs get Moon's hora (Cancer).")
def hora_chart_svg(req: DedicatedChartRequest):
    from ..main import to_julian, calc_planets, calc_houses, varga_sign, ZODIAC_SIGNS

    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode or 'mean')
    natal = calc_houses(jd, req.latitude, req.longitude, planets, 'W')

    asc_degree = natal['ascendant']['degree']
    asc_sign = varga_sign(asc_degree, 2) or natal['ascendant']['sign']
    asc_idx = ZODIAC_SIGNS.index(asc_sign)

    by_house = {i: [] for i in range(1, 13)}
    planet_details = []
    for p in planets:
        vsign = varga_sign(p['longitude'], 2)
        if not vsign:
            continue
        sidx = ZODIAC_SIGNS.index(vsign)
        house = ((sidx - asc_idx + 12) % 12) + 1
        entry = {
            'name': p['name'],
            'sign': vsign,
            'house': house,
            'degree': p['degree'],
            'isRetrograde': p['isRetrograde'],
            'isCombust': p['isCombust'],
        }
        by_house[house].append(entry)
        planet_details.append(entry)

    w = req.width or 800
    h = req.height or 600
    svg = _render_diamond_svg(w, h, asc_sign, by_house,
                               f"Hora Chart (D2) | Asc: {asc_sign}", req.theme or 'light')

    return {
        'status': 200,
        'chart': {
            'name': 'Hora (D2)',
            'focus': 'Wealth, Financial Prospects',
            'varga': 2,
            'ascendant': {'sign': asc_sign, 'degree': asc_degree},
        },
        'planets': planet_details,
        'svg': svg,
    }


# ──────────────────── 3. SUDARSHANA CHAKRA ────────────────────
class SudarshanaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    transitDate: Optional[str] = Field(None, example="2026-07-27", description="Transit date (default: today)")
    transitTime: Optional[str] = Field(None, example="12:00", description="Transit time (default: 12:00)")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    width: Optional[int] = Field(800, example=800)
    height: Optional[int] = Field(600, example=600)
    theme: Optional[str] = Field('light', example='light')


@router.post('/chart/sudarshana-svg',
             summary="Sudarshana Chakra (Transit Overlay) SVG",
             description="Generate the Sudarshana Chakra — a three-layered wheel showing Rasi, Navamsa, and Transit (current) positions overlaid. Shows how transits affect your natal chart.")
def sudarshana_chakra_svg(req: SudarshanaRequest):
    from ..main import to_julian, calc_planets, calc_houses, varga_sign, ZODIAC_SIGNS
    import pytz
    from datetime import datetime

    # Natal chart
    jd_natal = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets_natal = calc_planets(jd_natal, None, req.nodeMode or 'mean')
    natal = calc_houses(jd_natal, req.latitude, req.longitude, planets_natal, 'W')
    asc_natal = natal['ascendant']

    # Transit chart
    tz = pytz.timezone(req.timezone)
    if req.transitDate:
        transit_date = req.transitDate
        transit_time = req.transitTime or '12:00'
    else:
        now = datetime.now(tz)
        transit_date = now.strftime('%Y-%m-%d')
        transit_time = now.strftime('%H:%M')

    jd_transit = to_julian(transit_date, transit_time, req.timezone)
    planets_transit = calc_planets(jd_transit, None, req.nodeMode or 'mean')
    transit_houses = calc_houses(jd_transit, req.latitude, req.longitude, planets_transit, 'W')

    # Navamsa positions
    asc_navamsa_sign = varga_sign(asc_natal['degree'], 9) or asc_natal['sign']

    # Build three layers for each planet
    layers = []
    asc_idx = ZODIAC_SIGNS.index(asc_natal['sign'])
    for p in planets_natal:
        if p['name'] not in PLANET_ABBR:
            continue
        # Rasi layer
        rasi_sign = p['sign']
        rasi_house = ((ZODIAC_SIGNS.index(rasi_sign) - asc_idx + 12) % 12) + 1

        # Navamsa layer
        nav_sign = varga_sign(p['longitude'], 9) or rasi_sign
        nav_asc_idx = ZODIAC_SIGNS.index(asc_navamsa_sign)
        nav_house = ((ZODIAC_SIGNS.index(nav_sign) - nav_asc_idx + 12) % 12) + 1

        # Transit layer
        transit_p = next((tp for tp in planets_transit if tp['name'] == p['name']), None)
        transit_sign = transit_p['sign'] if transit_p else rasi_sign
        transit_house = transit_p.get('house', 0) if transit_p else 0

        layers.append({
            'name': p['name'],
            'rasi': {'sign': rasi_sign, 'house': rasi_house},
            'navamsa': {'sign': nav_sign, 'house': nav_house},
            'transit': {'sign': transit_sign, 'house': transit_house, 'degree': transit_p.get('degree', 0) if transit_p else 0},
            'isRetrograde': p.get('isRetrograde', False),
        })

    # Build a combined diamond chart showing natal rasi positions with transit overlay
    w = req.width or 800
    h = req.height or 600

    dwg = svgwrite.Drawing(size=(w, h), profile='full')
    dwg.attribs['viewBox'] = f'0 0 {w} {h}'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'

    scale_x = w / 400
    scale_y = h / 300
    def sp(pt):
        return (pt[0] * scale_x, pt[1] * scale_y)

    if 'dark' in req.theme:
        dwg.add(dwg.rect(insert=(0, 0), size=(w, h), fill='#1a1a2e'))

    # Gradient
    g = svgwrite.gradients.LinearGradient(start=(0, 0), end=(0, 1), id="grad")
    if 'dark' in req.theme:
        g.add_stop_color(0, '#1a1a2e', opacity=0.15)
        g.add_stop_color(1, '#16213e', opacity=0.08)
    else:
        g.add_stop_color(0, 'white', opacity=0.0)
        g.add_stop_color(1, '#f0f3bf', opacity=0.0)
    dwg.defs.add(g)

    # Draw houses
    for h_num in range(1, 13):
        pts = [sp(p) for p in HOUSE_POLYGONS[h_num]]
        dwg.add(svgwrite.shapes.Polygon(pts, fill="url(#grad)", stroke='#8B4513', stroke_width=1.5))

    # House numbers
    tc = '#006666' if 'dark' not in req.theme else '#66cccc'
    for h_num in range(1, 13):
        pos = sp(HOUSE_NO_POS[h_num])
        dwg.add(dwg.text(str(h_num), insert=pos, font_size='14px', fill=tc, font_weight='bold'))

    # Place planets with three lines each (Rasi / Navamsa / Transit)
    import math as _m
    radius = 20 * min(scale_x, scale_y)
    for layer in layers:
        h_num = layer['rasi']['house']
        center = sp(HOUSE_CENTERS[h_num])
        abbr = PLANET_ABBR.get(layer['name'], layer['name'][:2])
        color = PLANET_COLORS.get(layer['name'], '#000000')
        retro = '®' if layer['isRetrograde'] else ''

        # Find offset if multiple planets in same house
        same_house = [l for l in layers if l['rasi']['house'] == h_num]
        idx = same_house.index(layer)
        n = len(same_house)
        if n == 1:
            px, py = center
        else:
            angle = 2 * _m.pi * idx / n
            px = center[0] + radius * _m.cos(angle)
            py = center[1] + radius * _m.sin(angle)

        # Three-line display: Rasi sign / Navamsa sign / Transit sign
        rasi_label = f"{abbr}{retro}"
        nav_label = layer['navamsa']['sign'][:3]
        transit_label = layer['transit']['sign'][:3]

        dwg.add(dwg.text(rasi_label, insert=(px, py - 8), font_size='12px', fill=color, font_weight='bold', text_anchor='middle'))
        dwg.add(dwg.text(f"({nav_label})", insert=(px, py + 4), font_size='9px', fill='#8B008B', text_anchor='middle'))
        dwg.add(dwg.text(transit_label, insert=(px, py + 14), font_size='9px', fill='#FF6600', text_anchor='middle'))

    # Title and legend
    dwg.add(dwg.text(f"Sudarshana Chakra | {req.dateOfBirth} → {transit_date}",
                     insert=(w / 2, 20), font_size='14px', fill='#8B008B',
                     font_weight='bold', text_anchor='middle'))

    # Legend at bottom
    legend_y = h - 15
    dwg.add(dwg.text("Rasi (outer) / Navamsa (middle) / Transit (inner)",
                     insert=(w / 2, legend_y), font_size='10px', fill='#666666', text_anchor='middle'))

    output = StringIO()
    dwg.write(output)
    svg = output.getvalue()

    return {
        'status': 200,
        'chart': {
            'name': 'Sudarshana Chakra',
            'description': 'Three-layered wheel: Rasi (natal), Navamsa (D9), and Transit positions',
            'transitDate': transit_date,
            'transitTime': transit_time,
        },
        'natalAscendant': asc_natal['sign'],
        'navamsaAscendant': asc_navamsa_sign,
        'layers': layers,
        'svg': svg,
    }
