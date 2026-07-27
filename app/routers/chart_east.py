from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import svgwrite
from io import StringIO


router = APIRouter()


class EastChartRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    width: Optional[int] = Field(800, example=800)
    height: Optional[int] = Field(600, example=600)
    theme: Optional[str] = Field('light', example='light')
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


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

# East Indian chart: 4x3 grid.
# Cells are indexed 0..11 row-major.
# The fixed sign placement in East Indian chart:
# Cell  0: Aries       Cell  1: Taurus      Cell  2: Gemini       Cell  3: Cancer
# Cell  4: Leo         Cell  5: Virgo        Cell  6: Libra        Cell  7: Scorpio
# Cell  8: Sagittarius Cell  9: Capricorn    Cell 10: Aquarius    Cell 11: Pisces
#
# The ascendant sign is placed in its natural cell. Houses are counted
# from the ascendant sign cell going sequentially.

EAST_SIGN_CELLS = {
    'Aries': 0, 'Taurus': 1, 'Gemini': 2, 'Cancer': 3,
    'Leo': 4, 'Virgo': 5, 'Libra': 6, 'Scorpio': 7,
    'Sagittarius': 8, 'Capricorn': 9, 'Aquarius': 10, 'Pisces': 11,
}

CELLS_BY_INDEX = {v: k for k, v in EAST_SIGN_CELLS.items()}


def _east_house_from_asc(asc_sign: str):
    """Return a list of 12 entries mapping house number to sign, starting from ascendant."""
    from ..main import ZODIAC_SIGNS
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    return [(i + 1, ZODIAC_SIGNS[(asc_idx + i) % 12]) for i in range(12)]


def _render_east_svg(width: int, height: int, asc: dict, planets: list, theme: str = 'light') -> str:
    from ..main import ZODIAC_SIGNS, SIGN_LORDS

    dwg = svgwrite.Drawing(size=(width, height), profile='full')
    dwg.attribs['viewBox'] = f'0 0 {width} {height}'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'

    grid_w = width * 0.92
    grid_h = height * 0.82
    ox = (width - grid_w) / 2
    oy = (height - grid_h) / 2 + 20
    cell_w = grid_w / 4
    cell_h = grid_h / 3

    bg_color = '#1a1a2e' if 'dark' in theme else ('#ffffff' if 'opaque' in theme else 'none')
    stroke = '#8B4513' if 'dark' not in theme else '#555555'
    text_fill = '#006666' if 'dark' not in theme else '#66cccc'

    if bg_color != 'none':
        dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill=bg_color))

    asc_sign = asc.get('sign')
    house_map = _east_house_from_asc(asc_sign)

    sign_to_house = {}
    for hnum, sname in house_map:
        sign_to_house[sname] = hnum

    # Draw grid cells
    for row in range(3):
        for col in range(4):
            cell_idx = row * 4 + col
            sign_name = CELLS_BY_INDEX[cell_idx]
            house_num = sign_to_house.get(sign_name, 0)

            x = ox + col * cell_w
            y = oy + row * cell_h

            dwg.add(dwg.rect(insert=(x, y), size=(cell_w, cell_h),
                             fill='none', stroke=stroke, stroke_width=1.5))

            # Sign name top-left
            dwg.add(dwg.text(sign_name, insert=(x + 4, y + 16),
                             font_size='11px', fill=text_fill, font_weight='bold'))

            # House number center
            cx = x + cell_w / 2
            cy = y + cell_h / 2
            dwg.add(dwg.text(f'H{house_num}', insert=(cx - 12, cy - 8),
                             font_size='13px', fill='#8B008B', font_weight='bold'))

    # Place planets
    cell_planets = {i: [] for i in range(12)}
    for p in planets:
        sign = p.get('sign', '')
        cell_idx = EAST_SIGN_CELLS.get(sign)
        if cell_idx is not None:
            cell_planets[cell_idx].append(p)

    for cell_idx, plist in cell_planets.items():
        if not plist:
            continue
        row = cell_idx // 4
        col = cell_idx % 4
        x0 = ox + col * cell_w
        y0 = oy + row * cell_h
        cx = x0 + cell_w / 2
        cy = y0 + cell_h / 2

        n = len(plist)
        step = 16
        start_y = cy - ((n - 1) * step) / 2 + 8
        for j, planet in enumerate(plist):
            py = start_y + j * step
            abbr = PLANET_ABBR.get(planet['name'], planet['name'][:2])
            color = PLANET_COLORS.get(planet['name'], '#000000')
            retro = planet.get('isRetrograde', False)
            label = f"{abbr}{'R' if retro else ''}"
            dwg.add(dwg.text(label, insert=(cx - 8, py),
                             font_size='12px', fill=color, font_weight='bold'))

    # Title
    asc_deg = asc.get('degree', 0)
    asc_deg_local = asc_deg % 30 if isinstance(asc_deg, (int, float)) else 0
    dwg.add(dwg.text(f"East Indian Chart | Asc: {asc_sign} {asc_deg_local:.1f}°",
                     insert=(width / 2, 18), font_size='14px', fill='#8B008B',
                     font_weight='bold', text_anchor='middle'))

    output = StringIO()
    dwg.write(output)
    return output.getvalue()


def _render_moon_svg(width: int, height: int, asc: dict, moon_sign: str, planets: list, theme: str = 'light') -> str:
    """Render a diamond North-Indian style chart but with Moon's sign as house 1."""
    from ..main import ZODIAC_SIGNS

    HOUSE_POLYGONS = {
        1: [(100, 225), (200, 300), (300, 225), (200, 150)],
        2: [(100, 225), (0, 300), (200, 300)],
        3: [(0, 150), (0, 300), (100, 225)],
        4: [(0, 150), (100, 225), (200, 150), (100, 75)],
        5: [(0, 0), (0, 150), (100, 75)],
        6: [(0, 0), (100, 75), (200, 0)],
        7: [(100, 75), (200, 150), (300, 75), (200, 0)],
        8: [(200, 0), (300, 75), (400, 0)],
        9: [(300, 75), (400, 150), (400, 0)],
        10: [(300, 75), (200, 150), (300, 225), (400, 150)],
        11: [(300, 225), (400, 300), (400, 150)],
        12: [(300, 225), (200, 300), (400, 300)],
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

    dwg = svgwrite.Drawing(size=(width, height), profile='full')
    dwg.attribs['viewBox'] = f'0 0 {width} {height}'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'

    scale_x = width / 400
    scale_y = height / 300

    def sp(pt):
        return (pt[0] * scale_x, pt[1] * scale_y)

    g = svgwrite.gradients.LinearGradient(start=(0, 0), end=(0, 1), id="grad")
    if 'dark' in theme:
        g.add_stop_color(0, '#1a1a2e', opacity=0.15)
        g.add_stop_color(1, '#16213e', opacity=0.08)
    else:
        g.add_stop_color(0, 'white', opacity=0.0)
        g.add_stop_color(1, '#f0f3bf', opacity=0.0)
    dwg.defs.add(g)

    moon_idx = ZODIAC_SIGNS.index(moon_sign)
    house_signs = [ZODIAC_SIGNS[(moon_idx + i) % 12] for i in range(12)]

    for h in range(1, 13):
        pts = [sp(p) for p in HOUSE_POLYGONS[h]]
        dwg.add(svgwrite.shapes.Polygon(pts, fill="url(#grad)", stroke='#8B4513', stroke_width=1.5))

    tc = '#006666' if 'dark' not in theme else '#66cccc'
    for h in range(1, 13):
        pos = sp(HOUSE_NO_POS[h])
        dwg.add(dwg.text(str(h), insert=pos, font_size='14px', fill=tc, font_weight='bold'))

    # Group planets by house relative to Moon
    by_house = {i: [] for i in range(1, 13)}
    for p in planets:
        p_sign = p.get('sign', '')
        p_sign_idx = ZODIAC_SIGNS.index(p_sign) if p_sign in ZODIAC_SIGNS else 0
        h = ((p_sign_idx - moon_idx + 12) % 12) + 1
        p['_moon_house'] = h
        by_house[h].append(p)

    import math
    radius = 20 * min(scale_x, scale_y)
    for h in range(1, 13):
        center = sp(HOUSE_CENTERS[h])
        hplanets = by_house[h]
        for j, planet in enumerate(hplanets):
            if len(hplanets) == 1:
                px, py = center
            else:
                angle = 2 * math.pi * j / len(hplanets)
                px = center[0] + radius * math.cos(angle)
                py = center[1] + radius * math.sin(angle)
            abbr = PLANET_ABBR.get(planet['name'], planet['name'][:2])
            color = PLANET_COLORS.get(planet['name'], '#000000')
            retro = planet.get('isRetrograde', False)
            label = f"{abbr}{'®' if retro else ''}"
            dwg.add(dwg.text(label, insert=(px, py), font_size='14px', fill=color, font_weight='bold', text_anchor='middle'))
            deg = f"{planet['degree']:.1f}°"
            dwg.add(dwg.text(deg, insert=(px, py + 14 * scale_y), font_size='11px', fill=color, text_anchor='middle'))

    dwg.add(dwg.text(f"Moon Chart | Moon: {moon_sign}",
                     insert=(width / 2, 20), font_size='15px', fill='#8B008B',
                     font_weight='bold', text_anchor='middle'))

    output = StringIO()
    dwg.write(output)
    return output.getvalue()


@router.post('/east-svg', response_class=Response)
async def east_svg(req: EastChartRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode or 'mean')
    house_data = calc_houses(jd, req.latitude, req.longitude, planets, req.houseSystem or 'W')
    asc = house_data['ascendant']
    w = req.width or 800
    h = req.height or 600
    svg = _render_east_svg(w, h, asc, planets, req.theme or 'light')
    return Response(content=svg, media_type='image/svg+xml')


@router.post('/moon-svg', response_class=Response)
async def moon_svg(req: EastChartRequest):
    from ..main import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode or 'mean')
    house_data = calc_houses(jd, req.latitude, req.longitude, planets, req.houseSystem or 'W')
    moon_p = next((p for p in planets if p['name'] == 'Moon'), None)
    moon_sign = moon_p['sign'] if moon_p else house_data['ascendant']['sign']
    w = req.width or 800
    h = req.height or 600
    svg = _render_moon_svg(w, h, house_data['ascendant'], moon_sign, planets, req.theme or 'light')
    return Response(content=svg, media_type='image/svg+xml')
