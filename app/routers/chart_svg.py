from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import svgwrite
import math
from io import StringIO

router = APIRouter()

class ChartRequest(BaseModel):
    """Compute planets/houses internally from birth details and render North-Indian chart."""
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    # Rendering options
    width: Optional[int] = Field(800, example=800)
    height: Optional[int] = Field(600, example=600)  # North Indian chart works well in 4:3 ratio
    theme: Optional[str] = Field('light', example='light')  # 'light' (transparent) | 'dark' (transparent) | 'opaque-light' | 'opaque-dark'
    includeOuterPlanets: Optional[bool] = Field(True, example=True)
    stackIfCountAtLeast: Optional[int] = Field(3, example=3, description='If a house has >= this many planets, stack them vertically with degrees to the side')

# North Indian Chart Generator using svgwrite
# Proper polygon-based houses with gradient backgrounds

PLANET_ABBR = {
    'Ascendant': 'Asc', 'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
    'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke',
    'Uranus': 'Ur', 'Neptune': 'Ne', 'Pluto': 'Pl'
}

PLANET_COLORS = {
    'Sun': '#B8860B', 'Moon': '#4682B4', 'Mars': '#B22222', 'Mercury': '#006400',
    'Jupiter': '#8B4513', 'Venus': '#C71585', 'Saturn': '#1a1a1a', 
    'Rahu': '#4a0080', 'Ketu': '#8B4513',
    'Uranus': '#008B8B', 'Neptune': '#4169E1', 'Pluto': '#800080'
}

# House polygon coordinates (scaled to 400x300 base, will be scaled to requested size)
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

# Label centers for each house (scaled coordinates)
HOUSE_CENTERS = {
    1: (190, 75),
    2: (100, 30),
    3: (30, 75),
    4: (90, 150),
    5: (30, 225),
    6: (90, 278),
    7: (190, 225),
    8: (290, 278),
    9: (360, 225),
    10: (290, 150),
    11: (360, 75),
    12: (290, 30),
}

# House number positions
HOUSE_NO_POS = {
    1: (195, 130),
    2: (97, 60),
    3: (75, 78),
    4: (170, 152),
    5: (75, 227),
    6: (95, 245),
    7: (195, 170),
    8: (295, 245),
    9: (320, 227),
    10: (220, 152),
    11: (320, 77),
    12: (295, 60),
}


def scale_point(point, scale_x, scale_y):
    """Scale a point from base 400x300 to target dimensions."""
    return (point[0] * scale_x, point[1] * scale_y)


def render_svg(width: int, height: int, asc: dict, planets: list, theme: str = 'light', include_outer: bool = True, stack_mode: Optional[str] = None, stack_threshold: int = 3, show_degrees: bool = True, show_retrograde: bool = True):
    """Generate North Indian chart using svgwrite with proper polygon houses."""
    from ..main import ZODIAC_SIGNS
    
    # Create drawing
    dwg = svgwrite.Drawing(size=(width, height), profile='full')
    dwg.attribs['viewBox'] = f'0 0 {width} {height}'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'
    
    # Calculate scaling factors (base chart is 400x300)
    scale_x = width / 400
    scale_y = height / 300
    
    # Full background rect to ensure borders are fully visible
    dwg.add(svgwrite.shapes.Rect(
        insert=(0, 0), size=(width, height),
        fill='none', stroke='none'
    ))

    # Add gradient (transparent by default)
    def _add_gradient(dwg, color1, opacity1, color2, opacity2):
        g = svgwrite.gradients.LinearGradient(start=(0, 0), end=(0, 1), id="grad")
        g.add_stop_color(0, color1, opacity=opacity1)
        g.add_stop_color(1, color2, opacity=opacity2)
        dwg.defs.add(g)

    if theme == 'opaque-light':
        _add_gradient(dwg, 'white', 1.0, '#f0f3bf', 1.0)
    elif theme == 'opaque-dark':
        _add_gradient(dwg, '#1a1a2e', 1.0, '#16213e', 1.0)
    elif theme == 'dark':
        _add_gradient(dwg, '#1a1a2e', 0.15, '#16213e', 0.08)
    else:
        _add_gradient(dwg, 'white', 0.0, '#f0f3bf', 0.0)
    
    # Get ascendant house mapping
    asc_sign = asc.get('sign')
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    
    # House numbers relative to ascendant (ascendant is always in house 1)
    # North Indian style: house numbers are zodiac signs starting from ascendant
    house_sign_nums = [((asc_idx + i) % 12) + 1 for i in range(12)]
    
    # Draw house polygons with increased stroke for visibility
    for house_num in range(1, 13):
        points = [scale_point(p, scale_x, scale_y) for p in HOUSE_POLYGONS[house_num]]
        polygon = svgwrite.shapes.Polygon(points, fill="url(#grad)", stroke='#8B4513', stroke_width=2)
        dwg.add(polygon)
    
    # Add house sign numbers
    text_color = '#006666' if theme == 'light' else '#66cccc'
    for house_num in range(1, 13):
        pos = scale_point(HOUSE_NO_POS[house_num], scale_x, scale_y)
        sign_num = house_sign_nums[house_num - 1]
        text = dwg.text(str(sign_num), insert=pos, font_size='14px', fill=text_color, font_weight='bold')
        dwg.add(text)
    
    # Group planets by house
    outer = {'Uranus', 'Neptune', 'Pluto'}
    by_house = {i: [] for i in range(1, 13)}
    for p in planets:
        if not include_outer and p['name'] in outer:
            continue
        h = int(p.get('house', 0))
        if 1 <= h <= 12:
            by_house[h].append(p)
    
    # Add planets to houses
    radius = 18 * min(scale_x, scale_y)
    line_step = 14 * min(scale_x, scale_y)
    for house_num in range(1, 13):
        center = scale_point(HOUSE_CENTERS[house_num], scale_x, scale_y)
        house_planets = by_house[house_num]
        
        if not house_planets:
            continue

        n = len(house_planets)
        # Use vertical stacking for 2+ planets, scaled font for 4+
        font_size = 13
        if n >= 5:
            line_step = 11 * min(scale_x, scale_y)
            font_size = 8
        elif n >= 4:
            line_step = 12 * min(scale_x, scale_y)
            font_size = 9
        elif n >= 3:
            line_step = 14 * min(scale_x, scale_y)
            font_size = 10
        elif n >= 2:
            line_step = 16 * min(scale_x, scale_y)
            font_size = 11

        deg_font_size = max(7, font_size - 2)

        start_y = center[1] - ((n - 1) * line_step) / 2.0
        for j, planet in enumerate(house_planets):
            y = start_y + j * line_step
            planet_name = planet['name']
            abbr = PLANET_ABBR.get(planet_name, planet_name[:2])
            color = PLANET_COLORS.get(planet_name, '#000000')
            if show_retrograde and planet.get('isRetrograde'):
                abbr_label = f"{abbr}®"
            else:
                abbr_label = abbr
            if show_degrees:
                deg = f"{planet['degree']:.1f}°"
                inline_label = f"{abbr_label} {deg}"
                dwg.add(dwg.text(inline_label, insert=(center[0], y), font_size=f'{deg_font_size}px', fill=color, font_weight='bold', text_anchor='middle'))
            else:
                dwg.add(dwg.text(abbr_label, insert=(center[0], y), font_size=f'{font_size}px', fill=color, font_weight='bold', text_anchor='middle'))
    
    # Add ascendant marker (small, only visible on standard charts)
    asc_deg_global = asc.get('degree', 0)
    asc_deg_local = (asc_deg_global % 30) if isinstance(asc_deg_global, (int, float)) else 0
    asc_text = f"Asc {asc_deg_local:.1f}°"
    asc_pos = scale_point((200, 18), scale_x, scale_y)
    dwg.add(dwg.text(asc_text, insert=asc_pos, font_size='9px', fill='#666', font_weight='normal', text_anchor='middle'))
    
    # Convert to string
    output = StringIO()
    dwg.write(output)
    return output.getvalue()

@router.post('/svg', response_class=Response)
async def chart_svg(req: ChartRequest):
    """
    Generate SVG chart by computing planets/houses from birth details (no precomputed data).
    """
    from ..main import to_julian, calc_planets, calc_houses
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode or 'mean')
    house_data = calc_houses(jd, req.latitude, req.longitude, planets, req.houseSystem or 'W')

    width = req.width or 640
    height = req.height or width
    theme = (req.theme or 'light').lower()
    include_outer = bool(req.includeOuterPlanets) if req.includeOuterPlanets is not None else True

    svg = render_svg(width, height, house_data['ascendant'], planets, theme=theme, include_outer=include_outer, stack_threshold=int(req.stackIfCountAtLeast or 3))
    return Response(content=svg, media_type='image/svg+xml')

# ---------------- Divisional Chart (Varga) SVG ----------------

class DivisionalChartRequest(BaseModel):
    name: str = Field(..., example="D9")  # e.g., D1, D2, D3, D4, D7, D9, D10, D12
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    nodeMode: Optional[str] = Field('mean', example='mean')
    width: Optional[int] = Field(800, example=800)
    height: Optional[int] = Field(600, example=600)
    theme: Optional[str] = Field('light', example='light')
    includeOuterPlanets: Optional[bool] = Field(True, example=True)
    stackIfCountAtLeast: Optional[int] = Field(2, example=2)


def _parse_varga_name(name: str) -> Optional[int]:
    if not name:
        return None
    n = name.strip().lower()
    if n.startswith('d') and n[1:].isdigit():
        return int(n[1:])
    if n.isdigit():
        return int(n)
    return None


@router.post('/divisional-svg', tags=["Charts - Divisional"],
             summary="Divisional Chart SVG (D1-D60)",
             description="Generate any of the 60 divisional charts as SVG. Classical vargas: D1 (Rasi), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsa), D7 (Saptamsa), D9 (Navamsa), D10 (Dashamamsa), D12 (Dwadasamsa), D16 (Shodasamsa), D20 (Vimsamsa), D24 (Siddhamsa), D27 (Nakshatramsa), D30 (Trimshamsa), D40 (Khavedamsa), D45 (Akshavedamsa), D60 (Shashtiamsa).")
def divisional_chart_svg(req: DivisionalChartRequest):
    from ..main import to_julian, calc_planets, calc_houses, varga_sign, ZODIAC_SIGNS

    d = _parse_varga_name(req.name)
    # Allow any Dn using generic fallback if not classical
    supported = list(range(1, 61))
    if d not in supported:
        return {'status': 400, 'error': f'Invalid varga {req.name}', 'supported': [f'D{x}' for x in supported]}

    # Compute base planets and natal ascendant
    jd = to_julian(req.dateOfBirth, req.timeOfBirth, req.timezone)
    planets = calc_planets(jd, None, req.nodeMode or 'mean')
    natal = calc_houses(jd, req.latitude, req.longitude, planets, 'W')

    # Ascendant for varga
    asc_degree = natal['ascendant']['degree']
    asc_sign = natal['ascendant']['sign'] if d == 1 else (varga_sign(asc_degree, d) or natal['ascendant']['sign'])
    asc = {
        'sign': asc_sign,
        'degree': asc_degree,
        'nakshatra': natal['ascendant'].get('nakshatra'),
        'nakshatraLord': natal['ascendant'].get('nakshatraLord')
    }

    # Build varga planets with houses relative to varga ascendant (whole-sign)
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    vplanets = []
    for p in planets:
        vsign = p['sign'] if d == 1 else varga_sign(p['longitude'], d)
        if not vsign:
            continue
        sidx = ZODIAC_SIGNS.index(vsign)
        house = ((sidx - asc_idx + 12) % 12) + 1
        vplanets.append({
            'name': p['name'],
            'longitude': p['longitude'],
            'degree': p['degree'],  # keep natal local degree for label (simple)
            'sign': vsign,
            'house': house,
            'isRetrograde': p['isRetrograde'],
            'isCombust': p['isCombust']
        })

    width = req.width or 640
    height = req.height or width
    theme = (req.theme or 'light').lower()
    include_outer = bool(req.includeOuterPlanets) if req.includeOuterPlanets is not None else True

    svg = render_svg(width, height, asc, vplanets, theme=theme, include_outer=include_outer, stack_mode='vertical', stack_threshold=int(req.stackIfCountAtLeast or 2), show_degrees=False, show_retrograde=True)

    # Chart name
    try:
        from ..main import VARGA_META, varga_mode
        meta = VARGA_META.get(f'D{d}', {})
        chart_name = meta.get('name', f'D{d}')
        focus = meta.get('focus')
        mode = varga_mode(d)
    except Exception:
        chart_name, focus, mode = f'D{d}', None, 'generic'

    # Planet details to return
    pdetails = [
        {
            'name': p['name'],
            'sign': p['sign'],
            'house': p['house'],
            'degree': p['degree'],
            'isRetrograde': bool(p.get('isRetrograde'))
        } for p in vplanets
    ]

    return {
        'status': 200,
        'chart': {
            'name': f'{chart_name} (D{d})',
            'varga': d,
            'focus': focus,
            'mappingMode': mode,
            'ascendant': {
                'sign': asc['sign'],
                'degreeLocal': float(asc['degree']) % 30.0 if isinstance(asc['degree'], (int, float)) else 0.0,
                'degreeGlobal': asc['degree']
            }
        },
        'planets': pdetails,
        'svg': svg
    }

# (Template-based endpoint removed per instruction to keep a single /chart/svg endpoint.)


def render_ashtakavarga_svg(width: int, height: int, bindu_data: dict, planet_name: str = 'SAV', theme: str = 'light') -> str:
    """Render a single Ashtakavarga chart in North Indian diamond style.
    Simple transparent background, black text points, no house numbers.
    bindu_data: dict of {house_num: bindu_count}."""
    dwg = svgwrite.Drawing(size=(width, height), profile='full')
    dwg.attribs['viewBox'] = f'0 0 {width} {height}'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'

    scale_x = width / 400
    scale_y = height / 300

    # Title
    dwg.add(dwg.text(
        planet_name,
        insert=(width / 2, 20),
        font_size='16px', font_weight='bold',
        fill='#333', text_anchor='middle'
    ))

    def sp(point):
        return (point[0] * scale_x, 30 + point[1] * (height - 60) / 270)

    # Draw house polygons - transparent fill, thin grey stroke
    for h_num in range(1, 13):
        pts_poly = [sp(p) for p in HOUSE_POLYGONS[h_num]]
        polygon = svgwrite.shapes.Polygon(
            pts_poly,
            fill='none',
            stroke='#999', stroke_width=0.8
        )
        dwg.add(polygon)

    # Bindu counts only at house centers (no house numbers)
    for h_num in range(1, 13):
        center = sp(HOUSE_CENTERS[h_num])
        pts = bindu_data.get(h_num, 0)
        dwg.add(dwg.text(
            str(pts),
            insert=(center[0], center[1] + 2),
            font_size='16px', font_weight='bold',
            fill='#000', text_anchor='middle'
        ))

    output = StringIO()
    dwg.write(output)
    return output.getvalue()


def render_all_ashtakavarga_svgs(width: int, height: int, ashtakavarga_data: dict, theme: str = 'light') -> list:
    """Render all 8 Ashtakavarga charts as individual SVG strings."""
    planets_order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    svgs = []
    for pname in planets_order:
        contrib = ashtakavarga_data.get('planetContributions', {}).get(pname, {})
        pts = {h: contrib.get(h, 0) for h in range(1, 13)}
        svg = render_ashtakavarga_svg(width, height, pts, planet_name=pname, theme=theme)
        svgs.append({'planet': pname, 'svg': svg})

    sav = ashtakavarga_data.get('sarvashtakavarga', {})
    sav_pts = {int(h): sav.get('housePoints', {}).get(str(h), 0) for h in range(1, 13)}
    svg = render_ashtakavarga_svg(width, height, sav_pts, planet_name='SAV', theme=theme)
    svgs.append({'planet': 'SAV', 'svg': svg})
    return svgs
