from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from typing import Optional


router = APIRouter()


class GridChartRequest(BaseModel):
    # Reuse BirthDetails shape, but we avoid importing Pydantic model to prevent circulars
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    width: Optional[int] = Field(500, example=500)
    height: Optional[int] = Field(500, example=500)
    theme: Optional[str] = Field('light', example='light')  # currently used only for colors


def _line(x1, y1, x2, y2, color="#ff3366", w=3):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color};stroke-width:{w}" />'


def _text(x, y, content, fill, size, opacity=None):
    style = "font-family: '','Lucida Sans', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;display:flex;justify-content:center;align-items:center;"
    if opacity is not None:
        style += f"opacity:{opacity};"
    return f'<text x="{x}" y= "{y}" style = "{style}fill:{fill};font-size:{size}px; ">{content}</text>'


def render_grid_svg(width: int, height: int, cell_lines: list[list[str]]) -> str:
    # Based on the provided example, draw a 500x500 grid scaled to dimensions
    W, H = 500, 500
    sx, sy = width / W, height / H

    def scx(x):
        return round(x * sx, 2)

    def scy(y):
        return round(y * sy, 2)

    orange = '#ff3366'
    svg = [f'<svg height="{height}" width="{width}" xmlns="http://www.w3.org/2000/svg">']
    # Border/grid lines (scaled)
    svg.append(_line(scx(1.5), scy(0), scx(1.5), scy(500), orange))
    svg.append(_line(scx(125), scy(0), scx(125), scy(500), orange))
    svg.append(_line(scx(0), scy(498), scx(500), scy(498), orange))
    svg.append(_line(scx(375), scy(500), scx(375), scy(0), orange))
    svg.append(_line(scx(498), scy(500), scx(498), scy(0), orange))
    svg.append(_line(scx(0), scy(1.5), scx(500), scy(1.5), orange))
    svg.append(_line(scx(0), scy(125), scx(500), scy(125), orange))
    svg.append(_line(scx(0), scy(375), scx(500), scy(375), orange))
    svg.append(_line(scx(0), scy(250), scx(125), scy(250), orange))
    svg.append(_line(scx(375), scy(250), scx(500), scy(250), orange))
    svg.append(_line(scx(250), scy(0), scx(250), scy(125), orange))
    svg.append(_line(scx(250), scy(375), scx(250), scy(500), orange))

    # Positions for 12 signs (clockwise as per example). We'll show degree and sign name similar to sample.
    # Order in the sample appears as 1st row (between x=125..375): Aries, Taurus, Gemini
    # We'll compute sign labels from ascendant and fill degrees from sign_degrees[1..12]
    def positions():
        return [
            (177.5, 62.5, 172.5, 115),   # Aries (row1,col2)
            (302.5, 62.5, 294.5, 115),   # Taurus (row1,col3)
            (427.5, 62.5, 419.5, 115),   # Gemini (row1,col4)
            (427.5, 187.5, 419.5, 240),  # Cancer
            (427.5, 312.5, 428.5, 365),  # Leo
            (427.5, 437.5, 422.5, 490),  # Virgo
            (302.5, 437.5, 297.5, 490),  # Libra
            (177.5, 437.5, 166.5, 490),  # Scorpio
            (55.5, 437.5, 32.5, 490),    # Sagittarius
            (55.5, 312.5, 38.5, 365),    # Capricorn
            (55.5, 187.5, 41.5, 240),    # Aquarius
            (55.5, 65.5, 47.5, 118),     # Pisces
        ]

    # Text color styles
    text_fill = '#222222'
    # Draw planet lines per cell (e.g., "Su 10.2°", "Mo 23.4°")
    line_gap = 18  # base gap in px at 500x500; will scale with sy
    for i, (dx, dy, _sx, _sy) in enumerate(positions(), start=0):
        lines = cell_lines[i] if i < len(cell_lines) else []
        for j, content in enumerate(lines):
            y = dy + j * line_gap
            svg.append(_text(scx(dx), scy(y), content, text_fill, 16))

    svg.append('</svg>')
    return ''.join(svg)


@router.post('/grid-svg', response_class=Response)
def chart_grid_svg(body: GridChartRequest):
    # Import locally to avoid circulars at module import time
    from ..main import to_julian, calc_planets, calc_houses

    SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    ABR = {
        'Ascendant':'As','Sun':'Su','Moon':'Mo','Mars':'Ma','Mercury':'Me','Jupiter':'Ju','Venus':'Ve','Saturn':'Sa','Rahu':'Ra','Ketu':'Ke','Uranus':'Ur','Neptune':'Ne','Pluto':'Pl'
    }

    # Compute planets and ascendant
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    asc_sign = house_data['ascendant']['sign']
    asc_deg_local = float(house_data['ascendant']['degree']) % 30.0

    # Group planets by sign with degrees
    sign_map = {s: [] for s in SIGNS}
    for p in planets:
        sign = p.get('sign')
        deg = p.get('degree')
        name = p.get('name')
        if sign in sign_map and isinstance(deg, (int, float)) and name:
            sign_map[sign].append(f"{ABR.get(name, name[:2])} {deg:.1f}°")

    # Add Ascendant to its sign at the top
    sign_map[asc_sign].insert(0, f"{ABR['Ascendant']} {asc_deg_local:.1f}°")

    # Maintain South-Indian fixed sign placement order (Aries..Pisces)
    cell_lines = [sign_map[s] for s in SIGNS]

    svg = render_grid_svg(body.width or 500, body.height or 500, cell_lines)
    return Response(content=svg, media_type='image/svg+xml')
