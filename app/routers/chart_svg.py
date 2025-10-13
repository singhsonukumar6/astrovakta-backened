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
    theme: Optional[str] = Field('light', example='light')  # 'light' | 'dark'
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
    'Sun': '#FFD700', 'Moon': '#C0C0C0', 'Mars': '#FF0000', 'Mercury': '#008000',
    'Jupiter': '#0000FF', 'Venus': '#FF1493', 'Saturn': '#000000', 
    'Rahu': '#708090', 'Ketu': '#A52A2A',
    'Uranus': '#00CED1', 'Neptune': '#4169E1', 'Pluto': '#8B008B'
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
    
    # Calculate scaling factors (base chart is 400x300)
    scale_x = width / 400
    scale_y = height / 300
    
    # Add gradient
    if theme == 'light':
        gradient = svgwrite.gradients.LinearGradient(start=(0, 0), end=(0, 1), id="grad")
        gradient.add_stop_color(0, 'white')
        gradient.add_stop_color(1, '#f0f3bf')
    else:
        gradient = svgwrite.gradients.LinearGradient(start=(0, 0), end=(0, 1), id="grad")
        gradient.add_stop_color(0, '#1a1a2e')
        gradient.add_stop_color(1, '#16213e')
    dwg.defs.add(gradient)
    
    # Get ascendant house mapping
    asc_sign = asc.get('sign')
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    
    # House numbers relative to ascendant (ascendant is always in house 1)
    # North Indian style: house numbers are zodiac signs starting from ascendant
    house_sign_nums = [((asc_idx + i) % 12) + 1 for i in range(12)]
    
    # Draw house polygons
    for house_num in range(1, 13):
        points = [scale_point(p, scale_x, scale_y) for p in HOUSE_POLYGONS[house_num]]
        polygon = svgwrite.shapes.Polygon(points, fill="url(#grad)", stroke='#8B4513', stroke_width=1.5)
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
    radius = 20 * min(scale_x, scale_y)
    line_step = 18 * min(scale_x, scale_y)
    for house_num in range(1, 13):
        center = scale_point(HOUSE_CENTERS[house_num], scale_x, scale_y)
        house_planets = by_house[house_num]
        
        if not house_planets:
            continue

        # For divisional or stacked mode, place planets in a vertical column with degree on the side
        if (stack_mode == 'vertical' or len(house_planets) >= max(2, stack_threshold)) and len(house_planets) >= 2:
            n = len(house_planets)
            start_y = center[1] - ((n - 1) * line_step) / 2.0
            for j, planet in enumerate(house_planets):
                y = start_y + j * line_step
                planet_name = planet['name']
                abbr = PLANET_ABBR.get(planet_name, planet_name[:2])
                color = PLANET_COLORS.get(planet_name, '#000000')
                # Retrograde indicator (use the registered symbol "®")
                if show_retrograde and planet.get('isRetrograde'):
                    abbr_label = f"{abbr}®"
                else:
                    abbr_label = abbr
                if show_degrees:
                    deg = f"{planet['degree']:.1f}°"
                    # Abbreviation left of center, degree to the right
                    x_abbr = center[0] - 14 * scale_x
                    x_deg = center[0] + 12 * scale_x
                    dwg.add(dwg.text(abbr_label, insert=(x_abbr, y), font_size='14px', fill=color, font_weight='bold', text_anchor='end'))
                    dwg.add(dwg.text(deg, insert=(x_deg, y), font_size='12px', fill=color, text_anchor='start'))
                else:
                    # Center the abbreviation when degrees are hidden
                    dwg.add(dwg.text(abbr_label, insert=(center[0], y), font_size='14px', fill=color, font_weight='bold', text_anchor='middle'))
        else:
            # Arrange planets in circular pattern if multiple; degree below
            for j, planet in enumerate(house_planets):
                if len(house_planets) == 1:
                    x, y = center
                else:
                    angle = 2 * math.pi * j / len(house_planets)
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                
                planet_name = planet['name']
                abbr = PLANET_ABBR.get(planet_name, planet_name[:2])
                color = PLANET_COLORS.get(planet_name, '#000000')
                # Retrograde indicator (use the registered symbol "®")
                if show_retrograde and planet.get('isRetrograde'):
                    abbr_label = f"{abbr}®"
                else:
                    abbr_label = abbr
                
                # Add planet abbreviation (larger text)
                text = dwg.text(abbr_label, insert=(x, y), font_size='14px', fill=color, font_weight='bold', text_anchor='middle')
                dwg.add(text)
                
                # Add degree below (slightly larger) if enabled
                if show_degrees:
                    deg = f"{planet['degree']:.1f}°"
                    text_deg = dwg.text(deg, insert=(x, y + 14 * scale_y), font_size='12px', fill=color, text_anchor='middle')
                    dwg.add(text_deg)
    
    # Add ascendant marker (use local degree within sign to match grid behavior)
    asc_deg_global = asc.get('degree', 0)
    asc_deg_local = (asc_deg_global % 30) if isinstance(asc_deg_global, (int, float)) else 0
    asc_text = f"Asc: {asc_deg_local:.2f}°"
    asc_pos = scale_point((200, 20), scale_x, scale_y)
    text = dwg.text(asc_text, insert=asc_pos, font_size='16px', fill='#8B008B', font_weight='bold', text_anchor='middle')
    dwg.add(text)
    
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


@router.post('/divisional-svg')
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
