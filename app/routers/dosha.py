from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional

from ..i18n import detect_language, translate_response, translate_paragraphs, t as _t

router = APIRouter()

# Field → translation category mapping for dosha response
_DOSHA_FIELDS = {
    "name": "dosha",
    "severity": "dosha_severity",
    "description": "dosha_description",
    "remedies": "dosha_remedy",
}


class DoshaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    lang: str = Field("en", example="hi", description="Response language: en, hi, ta, te, kn, ml, bn, mr, gu, pa")


@router.post('/dosha/compute')
def compute_dosha(body: DoshaRequest, request: Request):
    lang = detect_language(query_lang=body.lang, header_lang=request.headers.get("accept-language"))
    # Import locally to avoid circular imports
    from ..main import to_julian, calc_planets, calc_houses, detect_doshas
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    # Ensure houses are set so Mangal dosha etc can be evaluated
    calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    doshas = detect_doshas(planets)
    data = translate_response(doshas, lang, _DOSHA_FIELDS)
    data = translate_paragraphs(data, lang, request)
    return {
        'status': 200,
        'data': data
    }
