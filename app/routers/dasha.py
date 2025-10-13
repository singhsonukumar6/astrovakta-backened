from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional


router = APIRouter()


class DashaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    timezone: str = Field(..., example="Asia/Kolkata")
    # Optional location to enrich predictions/context (timing does not require it)
    latitude: Optional[float] = Field(None, example=28.6139)
    longitude: Optional[float] = Field(None, example=77.2090)
    houseSystem: Optional[str] = Field(None, example='W')


@router.post('/dasha/vimshottari')
def vimshottari(body: DashaRequest):
    # Import locally to avoid circular imports
    from ..main import to_julian, parse_local_datetime, vimshottari_full, calc_planets, calc_houses, sunrise_sunset
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    res = vimshottari_full(jd, birth_local)

    # Determine current MD/AD/PD at 'now' in the provided timezone
    current_now = None
    try:
        import pytz
        from datetime import datetime
        tz = pytz.timezone(body.timezone)
        today = datetime.now(tz).date().isoformat()
        cur_md = next((md for md in res.get('mahadashas', []) if md['startDate'] <= today < md['endDate']), None)
        if cur_md:
            cur_ad = next((ad for ad in cur_md.get('antardasha', []) if ad['startDate'] <= today < ad['endDate']), None)
            cur_pd = None
            if cur_ad:
                cur_pd = next((pd for pd in cur_ad.get('pratyantar', []) if pd['startDate'] <= today < pd['endDate']), None)
        else:
            cur_ad, cur_pd = None, None
        if cur_md:
            current_now = {
                'mahadasha': {'planet': cur_md['planet'], 'startDate': cur_md['startDate'], 'endDate': cur_md['endDate']},
                'antardasha': ({'planet': cur_ad['planet'], 'startDate': cur_ad['startDate'], 'endDate': cur_ad['endDate']} if cur_ad else None),
                'pratyantar': ({'planet': cur_pd['planet'], 'startDate': cur_pd['startDate'], 'endDate': cur_pd['endDate']} if cur_pd else None)
            }
    except Exception:
        current_now = None

    context = {}
    # If latitude/longitude provided, compute ascendant/houses and sunrise for prediction context
    if body.latitude is not None and body.longitude is not None:
        try:
            planets = calc_planets(jd, None, 'mean')
            hs_code = body.houseSystem or 'W'
            houses = calc_houses(jd, float(body.latitude), float(body.longitude), planets, hs_code)
            sr, ss, sr_jd, ss_jd = sunrise_sunset(body.dateOfBirth, body.timezone, float(body.latitude), float(body.longitude))
            context = {
                'ascendant': houses.get('ascendant'),
                'houses': houses.get('houses'),
                'sunrise': sr,
                'sunset': ss,
                'houseSystem': hs_code
            }
        except Exception as e:
            context = {'warning': f'Location context unavailable: {e}'}

    return {
        'status': 200,
        'system': 'Vimshottari',
        'data': res,
        'currentNow': current_now,
        'context': context
    }
