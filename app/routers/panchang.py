from fastapi import APIRouter, Request

from ..utils import compute_panchang
from ..models import PanchangRequest
from ..i18n import detect_language, translate_response

router = APIRouter()

# Field → translation category mapping for panchang response
PANCHANG_FIELDS = {
    "tithi": "tithi",
    "nakshatra": "nakshatra",
    "yoga": "yoga",
    "karana": "karana",
    "paksha": "paksha",
    "moonPhase": "moon_phase",
}


@router.post('/panchang')
def compute(body: PanchangRequest, request: Request):
    lang = detect_language(query_lang=body.lang, header_lang=request.headers.get("accept-language"))
    time_str = body.time or "12:00"
    data = compute_panchang(body.date, time_str, body.timezone, body.latitude, body.longitude)
    data = translate_response(data, lang, PANCHANG_FIELDS)
    return {
        'status': 200,
        'data': data
    }
