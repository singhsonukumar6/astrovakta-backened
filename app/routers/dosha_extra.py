from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import pytz
import swisseph as swe

from ..utils import to_julian, calc_planets, calc_houses, ZODIAC_SIGNS, SIGN_LORDS, NAKSHATRAS, get_nakshatra

router = APIRouter()

class DhaiyaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")


_SADE_SATI_PHASES = {
    "rising": {"description": "Saturn transiting the 12th house from Moon — financial expenses, losses, foreign connections, sleep issues, spiritual transformation", "severity": "Medium", "remedies": ["Shani Puja", "Hanuman Chalisa", "Saturday fasting", "Donate to beggars/laborers"]},
    "peak": {"description": "Saturn transiting the 1st house (over Moon) — identity crisis, health challenges, emotional upheaval, self-discipline required", "severity": "High", "remedies": ["Shani Abhishek", "Maha Mrityunjaya Mantra", "Regular exercise", "Donate black sesame on Saturdays"]},
    "settling": {"description": "Saturn transiting the 2nd house from Moon — family disputes, speech issues, financial restructuring, dietary changes", "severity": "High", "remedies": ["Shani Shanti Puja", "Vishnu Sahasranama", "Control speech", "Donate food on Saturdays"]},
}


@router.post("/horoscope/dosha/dhaiya")
def dhaiya_dosha(body: DhaiyaRequest) -> Dict[str, Any]:
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, "mean")
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    moon = next((p for p in planets if p['name'] == 'Moon'), None)
    if not moon:
        return {"success": False, "error": "Could not calculate Moon position"}

    moon_lon = moon['longitude']
    moon_sign_idx = int(moon_lon // 30)

    # Calculate current Saturn position
    try:
        now_jd = swe.julday(datetime.now().year, datetime.now().month, datetime.now().day + datetime.now().hour / 24.0)
        sat_calc = swe.calc_ut(now_jd, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        saturn_lon = sat_calc[0][0]
        saturn_sign_idx = int(saturn_lon // 30)
    except Exception:
        saturn_sign_idx = 10  # fallback

    # Sade Sati: Saturn within 3 signs of Moon (12th, 1st, 2nd from Moon)
    diff = (saturn_sign_idx - moon_sign_idx) % 12

    in_sade_sati = diff in [11, 0, 1]  # 12th=11, 1st=0, 2nd=1

    # Dhaiya: Saturn in 4th house from Moon (3 signs after Moon) or 8th house from Moon (7 signs after)
    in_dhaiya_4th = diff == 3  # 4th from Moon
    in_dhaiya_8th = diff == 7  # 8th from Moon
    in_dhaiya = in_dhaiya_4th or in_dhaiya_8th

    # Calculate all Saturn-Moon phase relationships
    all_phases = []
    phase_names = {
        0: "Sade Sati (Peak) - Saturn on Moon",
        1: "Sade Sati (Settling) - Saturn 2nd from Moon",
        2: "Dhaiya - Saturn 3rd from Moon",
        3: "Dhaiya - Saturn 4th from Moon (4th house from Moon)",
        4: "Neutral - Saturn 5th from Moon",
        5: "Favorable - Saturn 6th from Moon (gives victories)",
        6: "Neutral - Saturn 7th from Moon",
        7: "Dhaiya - Saturn 8th from Moon (8th house from Moon)",
        8: "Favorable - Saturn 9th from Moon",
        9: "Favorable - Saturn 10th from Moon",
        10: "Favorable - Saturn 11th from Moon (gains)",
        11: "Sade Sati (Rising) - Saturn 12th from Moon",
    }

    for i in range(12):
        phase_name = phase_names.get(i, f"Phase {i}")
        is_active = i == diff
        impact = "Favorable" if i in [5, 8, 9, 10] else "Neutral" if i in [2, 4, 6] else "Challenging" if i in [0, 1, 3, 7, 11] else "Unknown"
        all_phases.append({
            "signsFromMoon": i,
            "phase": phase_name,
            "impact": impact,
            "active": is_active,
        })

    current_status = None
    if in_sade_sati:
        if diff == 0:
            current_status = _SADE_SATI_PHASES["peak"]
            current_status["phase"] = "Peak Sade Sati"
        elif diff == 1:
            current_status = _SADE_SATI_PHASES["settling"]
            current_status["phase"] = "Settling Sade Sati"
        else:
            current_status = _SADE_SATI_PHASES["rising"]
            current_status["phase"] = "Rising Sade Sati"
    elif in_dhaiya:
        dhaiya_type = "4th House Dhaiya" if in_dhaiya_4th else "8th House Dhaiya"
        current_status = {
            "phase": dhaiya_type,
            "description": f"Saturn transiting the {'4th' if in_dhaiya_4th else '8th'} house from Moon — {'domestic challenges, property issues, emotional unrest' if in_dhaiya_4th else 'transformation, hidden obstacles, health concerns, sudden events'}",
            "severity": "Medium",
            "remedies": ["Shani Mantra 108x daily", "Saturday fasting for 16 weeks", "Donate iron items on Saturdays", "Worship Lord Hanuman on Tuesdays and Saturdays"]
        }
    else:
        current_status = {"phase": "No Sade Sati or Dhaiya active", "description": "Saturn is not in a challenging position relative to your natal Moon.", "severity": "None", "remedies": []}

    # Calculate approximate dates for Sade Sati
    sade_sati_dates = {}
    try:
        for years_back in range(100):
            test_jd = jd + (years_back * 365.25)
            try:
                sat_calc_back = swe.calc_ut(test_jd, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
                sat_lon_back = sat_calc_back[0][0]
                sat_sign_back = int(sat_lon_back // 30)
                diff_back = (sat_sign_back - moon_sign_idx) % 12
                if diff_back == 11 and 'start' not in sade_sati_dates:
                    dt_back = swe.jdet_to_datetime(test_jd)
                    sade_sati_dates['start'] = f"{int(dt_back[0])}-{int(dt_back[1]):02d}"
            except Exception:
                continue
        for years_fwd in range(100):
            test_jd = jd + (years_fwd * 365.25)
            try:
                sat_calc_fwd = swe.calc_ut(test_jd, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
                sat_lon_fwd = sat_calc_fwd[0][0]
                sat_sign_fwd = int(sat_lon_fwd // 30)
                diff_fwd = (sat_sign_fwd - moon_sign_idx) % 12
                if diff_fwd == 2 and 'end' not in sade_sati_dates:  # after 2nd house = end
                    dt_fwd = swe.jdet_to_datetime(test_jd)
                    sade_sati_dates['end'] = f"{int(dt_fwd[0])}-{int(dt_fwd[1]):02d}"
            except Exception:
                continue
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "moonSign": ZODIAC_SIGNS[moon_sign_idx],
            "saturnSign": ZODIAC_SIGNS[saturn_sign_idx],
            "signsFromMoon": diff,
            "currentStatus": current_status,
            "inSadeSati": in_sade_sati,
            "inDhaiya": in_dhaiya,
            "dhaiyaType": "4th House" if in_dhaiya_4th else ("8th House" if in_dhaiya_8th else None),
            "allPhases": all_phases,
            "sadeSatiCycleDates": sade_sati_dates if sade_sati_dates else None,
            "dhaiyaNote": "Dhaiya (2.5-year period) occurs when Saturn transits the 4th or 8th house from natal Moon. Sade Sati (7.5-year period) spans 12th, 1st, and 2nd houses from Moon.",
            "generalAdvice": "Challenging Saturn transits bring growth through hardship. Focus on discipline, service, and spiritual practice during these periods."
        }
    }
