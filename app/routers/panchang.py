from fastapi import APIRouter

from ..utils import compute_panchang
from ..models import PanchangRequest

router = APIRouter()


@router.post('/panchang')
def compute(body: PanchangRequest):
    time_str = body.time or "12:00"
    data = compute_panchang(body.date, time_str, body.timezone, body.latitude, body.longitude)
    return {
        'status': 200,
        'data': data
    }
