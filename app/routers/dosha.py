from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional


router = APIRouter()


class DoshaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


@router.post('/dosha/compute')
def compute_dosha(body: DoshaRequest):
    # Import locally to avoid circular imports
    from ..main import to_julian, calc_planets, calc_houses, detect_doshas
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    # Ensure houses are set so Mangal dosha etc can be evaluated
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    doshas = detect_doshas(planets)
    return {
        'status': 200,
        'data': doshas
    }
