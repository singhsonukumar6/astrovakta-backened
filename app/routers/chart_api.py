from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(tags=["Charts"])

class ChartRequest(BaseModel):
    dateOfBirth: str
    timeOfBirth: str
    latitude: float
    longitude: float
    timezone: str
    chartType: str = Field('north_indian', description="north_indian, south_indian, navamsa, ashtakavarga")
    houseSystem: Optional[str] = 'W'
    nodeMode: Optional[str] = 'mean'
    width: int = 600
    height: int = 450

@router.post('/chart/generate')
def generate_chart(body: ChartRequest):
    """Generate a chart SVG for given birth data and chart type."""
    from ..main import to_julian, calc_planets, calc_houses
    from ..utils import ayanamsa_value

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    house_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    asc = house_data['ascendant']

    if body.chartType == 'navamsa':
        from ..main import varga_sign
        from ..utils import ZODIAC_SIGNS
        nav_planets = []
        for p in planets:
            vsign = varga_sign(p['longitude'], 9)
            if vsign:
                nav_planets.append({'name': p['name'], 'sign': vsign, 'degree': p['degree'],
                                    'isRetrograde': p.get('isRetrograde', False), 'isCombust': p.get('isCombust', False), 'house': 0})
        asc_nav = {'sign': varga_sign(asc['degree'], 9) or asc['sign'], 'degree': 0}
        from .chart_svg import render_svg
        svg_str = render_svg(body.width, body.height, asc_nav, nav_planets, theme='light', show_degrees=False)
    elif body.chartType == 'ashtakavarga':
        from ..main import compute_ashtakavarga
        av = compute_ashtakavarga(planets)
        from .chart_svg import render_all_ashtakavarga_svgs
        svgs = render_all_ashtakavarga_svgs(body.width, body.height, av)
        from fastapi.responses import JSONResponse
        return JSONResponse({'charts': svgs})
    else:
        asc_dict = {'sign': asc['sign'], 'degree': 0, 'nakshatra': '', 'nakshatraLord': '', 'nakshatraPada': 1}
        from .chart_svg import render_svg
        svg_str = render_svg(body.width, body.height, asc_dict, planets, theme='light', show_degrees=False)

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=svg_str, media_type='image/svg+xml')
