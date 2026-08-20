"""Shared Pydantic models for panchang and calendar endpoints."""
from pydantic import BaseModel, Field, model_validator


class BaseLocationRequest(BaseModel):
    """Base model with geographic coordinates and timezone."""
    latitude: float = Field(..., example=28.6139, ge=-90, le=90)
    longitude: float = Field(..., example=77.2090, ge=-180, le=180)
    timezone: str = Field(..., example="Asia/Kolkata")


class PanchangRequest(BaseLocationRequest):
    """Request model for single-date panchang endpoints.

    Accepts either 'date' (new) or 'dateOfBirth' (legacy) for the date field.
    'timeOfBirth' / 'time' are accepted but ignored — panchang is always computed at sunrise.
    """
    date: str = Field(None, alias="dateOfBirth", example="2025-06-15")
    time: str = Field(None, alias="timeOfBirth", example="14:30",
                       description="Ignored — panchang is computed at sunrise")

    model_config = {"populate_by_name": True}

    @model_validator(mode='after')
    def ensure_date(self):
        if not self.date:
            raise ValueError("Either 'date' or 'dateOfBirth' is required")
        return self


class CalendarPanchangRequest(BaseLocationRequest):
    """Request model for monthly calendar panchang endpoints."""
    year: int = Field(..., example=2025)
    month: int = Field(..., ge=1, le=12, example=6)
