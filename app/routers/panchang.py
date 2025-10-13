from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class PanchangRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


@router.post('/panchang')
def compute(body: PanchangRequest):
    # Import lazily to avoid circular dependencies
    from ..main import compute_panchang
    data = compute_panchang(body.dateOfBirth, body.timeOfBirth, body.timezone, body.latitude, body.longitude)
    return {
        'status': 200,
        'data': data
    }
