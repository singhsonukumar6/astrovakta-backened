from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import swisseph as swe
import pytz
from dateutil import parser
import logging

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, planet_status,
)

router = APIRouter()
logger = logging.getLogger(__name__)

SCAN_STEP_MINUTES = 5
ASC_TRANSIT_DEGREES_PER_MIN = 360.0 / (24.0 * 60)


class LifeEvent(BaseModel):
    date: str
    event: str


class RectifyRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field("W", example="W")
    nodeMode: Optional[str] = Field("mean", example="mean")
    knownAscendant: Optional[str] = Field(
        None,
        example="Leo",
        description="Approximate ascendant sign the user believes is correct",
    )
    lifeEvents: Optional[List[LifeEvent]] = Field(
        None,
        example=[{"date": "2015-06-20", "event": "marriage"}],
        description="Known life events with dates for transit-based verification",
    )


class AscendantScanRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field("W", example="W")
    nodeMode: Optional[str] = Field("mean", example="mean")


class TransitVerifyRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field("W", example="W")
    nodeMode: Optional[str] = Field("mean", example="mean")
    eventDate: str = Field(..., example="2015-06-20")
    eventType: str = Field(..., example="marriage")


EVENT_TRANSIT_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "marriage": {
        "description": "Marriage or committed partnership",
        "key_planets": ["Venus", "Jupiter"],
        "transit_houses": [1, 7],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "career_change": {
        "description": "Career change or promotion",
        "key_planets": ["Sun", "Saturn"],
        "transit_houses": [10, 6],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "relocation": {
        "description": "Change of residence or foreign travel",
        "key_planets": ["Rahu", "Jupiter", "Moon"],
        "transit_houses": [4, 9, 12],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "children": {
        "description": "Birth of children or pregnancy",
        "key_planets": ["Jupiter", "Venus"],
        "transit_houses": [5, 1],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "education": {
        "description": "Education or academic achievement",
        "key_planets": ["Jupiter", "Mercury"],
        "transit_houses": [4, 5, 9],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "health_issue": {
        "description": "Health problem or surgery",
        "key_planets": ["Saturn", "Mars"],
        "transit_houses": [1, 6, 8, 12],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "financial_gain": {
        "description": "Major financial gain or loss",
        "key_planets": ["Jupiter", "Venus", "Rahu"],
        "transit_houses": [2, 6, 10, 11],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "loss": {
        "description": "Loss or separation",
        "key_planets": ["Saturn", "Rahu", "Ketu"],
        "transit_houses": [1, 4, 8, 12],
        "check_aspects": True,
        "significance_threshold": 2,
    },
    "spiritual_event": {
        "description": "Spiritual awakening or religious event",
        "key_planets": ["Jupiter", "Ketu"],
        "transit_houses": [9, 12],
        "check_aspects": True,
        "significance_threshold": 2,
    },
}


def _local_to_jd(date_str: str, time_str: str, tz_name: str) -> float:
    return to_julian(date_str, time_str, tz_name)


def _jd_to_local_str(jd: float, tz_name: str) -> str:
    y, m, d, ut = swe.revjul(jd)
    hh = int(ut)
    mm = int(round((ut - hh) * 60))
    if mm == 60:
        hh += 1
        mm = 0
    tz = pytz.timezone(tz_name)
    dt_utc = datetime(y, m, d, min(hh, 23), min(mm, 59), tzinfo=pytz.utc)
    dt_local = dt_utc.astimezone(tz)
    return dt_local.strftime("%H:%M")


def _get_ascendant_deg(jd: float, lat: float, lon: float, house_system: str) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    hsys = (house_system or "W").encode("ascii")
    _, ascmc = swe.houses_ex(jd, lat, lon, hsys, swe.FLG_SIDEREAL)
    return ascmc[0]


def _scan_ascendant_range(
    date_str: str,
    base_time: str,
    tz_name: str,
    lat: float,
    lon: float,
    house_system: str,
    node_mode: str,
    scan_minutes: int = 180,
    step_minutes: int = SCAN_STEP_MINUTES,
) -> List[Dict[str, Any]]:
    tz = pytz.timezone(tz_name)
    dt_local = tz.localize(parser.parse(f"{date_str} {base_time}"))
    dt_utc = dt_local.astimezone(pytz.utc)

    results: List[Dict[str, Any]] = []
    total_steps = int((scan_minutes * 2) / step_minutes) + 1

    for i in range(total_steps):
        offset_minutes = -scan_minutes + i * step_minutes
        dt_step = dt_utc + timedelta(minutes=offset_minutes)
        jd = swe.julday(
            dt_step.year, dt_step.month, dt_step.day,
            dt_step.hour + dt_step.minute / 60.0 + dt_step.second / 3600.0,
        )

        asc_deg = _get_ascendant_deg(jd, lat, lon, house_system)
        asc_sign = get_sign(asc_deg)
        asc_nk = get_nakshatra(asc_deg)
        deg_in_sign = asc_deg % 30

        local_time_str = _jd_to_local_str(jd, tz_name)

        results.append({
            "time": local_time_str,
            "minutesOffset": offset_minutes,
            "ascendantDegree": round(asc_deg, 4),
            "ascendantSign": asc_sign,
            "degreeInSign": round(deg_in_sign, 2),
            "nakshatra": asc_nk["name"],
            "nakshatraLord": asc_nk["lord"],
        })

    return results


def _find_sign_transitions(
    scan_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    transitions: List[Dict[str, Any]] = []
    for i in range(1, len(scan_results)):
        prev_sign = scan_results[i - 1]["ascendantSign"]
        curr_sign = scan_results[i]["ascendantSign"]
        if prev_sign != curr_sign:
            prev_deg = scan_results[i - 1]["ascendantDegree"]
            curr_deg = scan_results[i]["ascendantDegree"]
            prev_offset = scan_results[i - 1]["minutesOffset"]
            curr_offset = scan_results[i]["minutesOffset"]

            if prev_offset != curr_offset:
                frac = (360 - prev_deg) / (curr_deg - prev_deg + 360 if curr_deg < prev_deg else curr_deg - prev_deg)
            else:
                frac = 0

            exact_offset = prev_offset + frac * (curr_offset - prev_offset)
            transitions.append({
                "fromSign": prev_sign,
                "toSign": curr_sign,
                "approxTime": scan_results[i]["time"],
                "minutesOffset": round(exact_offset, 1),
                "fromDegree": round(prev_deg, 4),
                "toDegree": round(curr_deg, 4),
            })

    return transitions


def _match_known_ascendant(
    scan_results: List[Dict[str, Any]],
    known_sign: str,
) -> Dict[str, Any]:
    matches = [r for r in scan_results if r["ascendantSign"] == known_sign]

    if not matches:
        return {
            "matched": False,
            "message": f"Ascendant '{known_sign}' was not found in the scan range. Try a wider scan or verify the sign.",
            "candidates": [],
        }

    best = min(matches, key=lambda r: abs(r["minutesOffset"]))
    candidates = sorted(matches, key=lambda r: abs(r["minutesOffset"]))[:5]

    total_range = len(scan_results)
    sign_positions = [i for i, r in enumerate(scan_results) if r["ascendantSign"] == known_sign]
    confidence_base = min(95, 50 + (len(sign_positions) / total_range) * 100)
    if len(sign_positions) <= 1:
        confidence_base = min(confidence_base, 75)

    return {
        "matched": True,
        "suggestedTime": best["time"],
        "suggestedMinutesOffset": best["minutesOffset"],
        "confidence": round(min(95, confidence_base), 1),
        "signFound": known_sign,
        "candidates": [
            {
                "time": c["time"],
                "minutesOffset": c["minutesOffset"],
                "degreeInSign": c["degreeInSign"],
            }
            for c in candidates
        ],
    }


def _score_event_transits(
    natal_planets: List[Dict[str, Any]],
    transit_planets: List[Dict[str, Any]],
    event_type: str,
) -> Dict[str, Any]:
    sig = EVENT_TRANSIT_SIGNATURES.get(event_type.lower())
    if not sig:
        return {
            "score": 0,
            "activeTransits": [],
            "message": f"Unknown event type: '{event_type}'. Supported types: {', '.join(sorted(EVENT_TRANSIT_SIGNATURES.keys()))}",
        }

    key_planets = sig["key_planets"]
    target_houses = sig["transit_houses"]
    threshold = sig["significance_threshold"]

    natal_map = {p["name"]: p for p in natal_planets}
    transit_map = {p["name"]: p for p in transit_planets}

    score = 0
    active_transits: List[Dict[str, Any]] = []

    for pname in key_planets:
        t_planet = transit_map.get(pname)
        n_planet = natal_map.get(pname)
        if not t_planet:
            continue

        t_house = t_planet.get("house", 0)
        t_sign = t_planet.get("sign", "")

        in_target = t_house in target_houses
        is_retro = t_planet.get("isRetrograde", False)

        aspects_to_natal: List[Dict[str, Any]] = []
        if sig["check_aspects"] and n_planet:
            n_house = n_planet.get("house", 0)
            diff = abs(t_house - n_house) % 12
            aspect_names = {
                0: ("Conjunction", 0),
                2: ("Trine", 120),
                3: ("Square", 90),
                4: ("Opposition", 180),
                6: ("Sextile", 60),
                10: ("Sextile", 300),
            }
            if diff in aspect_names:
                name, deg = aspect_names[diff]
                aspects_to_natal.append({
                    "aspect": name,
                    "degree": deg,
                    "natalPlanet": pname,
                    "natalHouse": n_house,
                })
                score += 2

        natal_status = planet_status(pname, t_sign) if n_planet else "N/A"

        transit_entry = {
            "planet": pname,
            "transitHouse": t_house,
            "transitSign": t_sign,
            "isRetrograde": is_retro,
            "inTargetHouse": in_target,
            "aspectsToNatal": aspects_to_natal,
            "natalDignity": natal_status,
        }

        if in_target:
            score += 3
            if is_retro:
                score += 1
        if aspects_to_natal:
            score += 1

        active_transits.append(transit_entry)

    rahu = transit_map.get("Rahu")
    ketu = transit_map.get("Ketu")
    if rahu and rahu.get("house", 0) in target_houses:
        score += 1
        active_transits.append({
            "planet": "Rahu",
            "transitHouse": rahu.get("house", 0),
            "transitSign": rahu.get("sign", ""),
            "isRetrograde": True,
            "inTargetHouse": True,
            "aspectsToNatal": [],
            "note": "Rahu transit over key house - karmic trigger",
        })
    if ketu and ketu.get("house", 0) in target_houses:
        score += 1
        active_transits.append({
            "planet": "Ketu",
            "transitHouse": ketu.get("house", 0),
            "transitSign": ketu.get("sign", ""),
            "isRetrograde": True,
            "inTargetHouse": True,
            "aspectsToNatal": [],
            "note": "Ketu transit over key house - spiritual/detachment trigger",
        })

    max_possible = len(key_planets) * 5 + 2
    normalized = min(100, round((score / max(max_possible, 1)) * 100))

    return {
        "score": normalized,
        "rawScore": score,
        "eventDescription": sig["description"],
        "activeTransits": active_transits,
        "verdict": (
            "Strong confirmation"
            if normalized >= 60
            else "Moderate confirmation"
            if normalized >= 30
            else "Weak or no confirmation"
        ),
    }


@router.post("/utility/rectify")
def rectify_birth_time(req: RectifyRequest):
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        jd = _local_to_jd(req.dateOfBirth, req.timeOfBirth, req.timezone)
        planets = calc_planets(jd, None, req.nodeMode or "mean")
        for p in planets:
            p["houseStatus"] = planet_status(p["name"], p["sign"])

        house_data = calc_houses(jd, req.latitude, req.longitude, planets, req.houseSystem or "W")
        ascendant = house_data["ascendant"]

        scan_results = _scan_ascendant_range(
            req.dateOfBirth, req.timeOfBirth, req.timezone,
            req.latitude, req.longitude, req.houseSystem or "W", req.nodeMode or "mean",
            scan_minutes=120, step_minutes=SCAN_STEP_MINUTES,
        )

        transitions = _find_sign_transitions(scan_results)

        ascendant_match = None
        if req.knownAscendant:
            ascendant_match = _match_known_ascendant(scan_results, req.knownAscendant)

        event_analyses: List[Dict[str, Any]] = []
        if req.lifeEvents:
            for ev in req.lifeEvents:
                try:
                    event_jd = _local_to_jd(ev.date, "12:00", req.timezone)
                    event_planets = calc_planets(event_jd, None, req.nodeMode or "mean")
                    event_house_data = calc_houses(
                        event_jd, req.latitude, req.longitude,
                        event_planets, req.houseSystem or "W",
                    )
                    for ep in event_planets:
                        ep["houseStatus"] = planet_status(ep["name"], ep["sign"])

                    event_score = _score_event_transits(planets, event_planets, ev.event)

                    event_analyses.append({
                        "date": ev.date,
                        "eventType": ev.event,
                        "eventTransits": event_score,
                        "transitChart": {
                            "planets": [
                                {
                                    "name": p["name"],
                                    "sign": p["sign"],
                                    "house": p["house"],
                                    "isRetrograde": p["isRetrograde"],
                                    "degree": p["degree"],
                                }
                                for p in event_planets
                            ],
                            "ascendant": event_house_data["ascendant"],
                        },
                    })
                except Exception as e:
                    logger.error(f"Error analyzing event '{ev.event}' on {ev.date}: {e}", exc_info=True)
                    event_analyses.append({
                        "date": ev.date,
                        "eventType": ev.event,
                        "error": str(e),
                    })

        suggested_time = req.timeOfBirth
        confidence = 50.0
        confidence_factors: List[str] = []

        if ascendant_match and ascendant_match["matched"]:
            suggested_time = ascendant_match["suggestedTime"]
            confidence = ascendant_match["confidence"]
            confidence_factors.append(
                f"Known ascendant '{req.knownAscendant}' matched with {confidence}% confidence"
            )

        if event_analyses:
            verified_events = [
                ea for ea in event_analyses
                if "eventTransits" in ea and ea["eventTransits"].get("score", 0) >= 30
            ]
            if verified_events:
                avg_event_score = sum(ea["eventTransits"]["score"] for ea in verified_events) / len(verified_events)
                confidence = min(95, confidence * 0.6 + avg_event_score * 0.4)
                confidence_factors.append(
                    f"{len(verified_events)}/{len(event_analyses)} life events show transit confirmation (avg score: {avg_event_score:.0f})"
                )
            else:
                confidence *= 0.7
                confidence_factors.append("No life events showed strong transit confirmation")

        original_chart = {
            "ascendant": ascendant,
            "planets": [
                {
                    "name": p["name"],
                    "sign": p["sign"],
                    "house": p["house"],
                    "degree": p["degree"],
                    "degreeDMS": p["degreeDMS"],
                    "isRetrograde": p["isRetrograde"],
                }
                for p in planets
            ],
        }

        scan_summary = {
            "totalScanPoints": len(scan_results),
            "signsEncountered": list(dict.fromkeys(r["ascendantSign"] for r in scan_results)),
            "transitions": transitions,
        }

        return {
            "status": 200,
            "data": {
                "originalInput": {
                    "dateOfBirth": req.dateOfBirth,
                    "timeOfBirth": req.timeOfBirth,
                    "latitude": req.latitude,
                    "longitude": req.longitude,
                    "timezone": req.timezone,
                },
                "originalChart": original_chart,
                "rectification": {
                    "suggestedTime": suggested_time,
                    "confidence": round(confidence, 1),
                    "confidenceFactors": confidence_factors,
                    "knownAscendantMatch": ascendant_match,
                },
                "lifeEventAnalyses": event_analyses if event_analyses else None,
                "scanSummary": scan_summary,
                "note": (
                    "Birth time rectification is advisory. Results depend on the accuracy "
                    "of provided life events and known ascendant. For precise rectification, "
                    "consult an experienced astrologer."
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error in birth time rectification: {e}", exc_info=True)
        return {"status": 500, "error": str(e), "message": "Error in birth time rectification"}


@router.post("/utility/ascendant-scan")
def ascendant_scan(req: AscendantScanRequest):
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        jd = _local_to_jd(req.dateOfBirth, req.timeOfBirth, req.timezone)
        planets = calc_planets(jd, None, req.nodeMode or "mean")
        for p in planets:
            p["houseStatus"] = planet_status(p["name"], p["sign"])

        house_data = calc_houses(jd, req.latitude, req.longitude, planets, req.houseSystem or "W")
        original_asc = house_data["ascendant"]

        scan_results = _scan_ascendant_range(
            req.dateOfBirth, req.timeOfBirth, req.timezone,
            req.latitude, req.longitude, req.houseSystem or "W", req.nodeMode or "mean",
            scan_minutes=180, step_minutes=SCAN_STEP_MINUTES,
        )

        transitions = _find_sign_transitions(scan_results)

        sign_timeline: Dict[str, List[Dict[str, Any]]] = {}
        for r in scan_results:
            sign = r["ascendantSign"]
            if sign not in sign_timeline:
                sign_timeline[sign] = []
            sign_timeline[sign].append({
                "time": r["time"],
                "minutesOffset": r["minutesOffset"],
                "degreeInSign": r["degreeInSign"],
            })

        sign_durations: List[Dict[str, Any]] = []
        for sign in ZODIAC_SIGNS:
            if sign in sign_timeline:
                entries = sign_timeline[sign]
                first = entries[0]
                last = entries[-1]
                sign_durations.append({
                    "sign": sign,
                    "firstSeen": first["time"],
                    "lastSeen": last["time"],
                    "firstSeenOffset": first["minutesOffset"],
                    "lastSeenOffset": last["minutesOffset"],
                    "durationMinutes": round(last["minutesOffset"] - first["minutesOffset"], 1),
                    "samplePoints": len(entries),
                })

        return {
            "status": 200,
            "data": {
                "originalInput": {
                    "dateOfBirth": req.dateOfBirth,
                    "timeOfBirth": req.timeOfBirth,
                    "latitude": req.latitude,
                    "longitude": req.longitude,
                    "timezone": req.timezone,
                },
                "originalAscendant": original_asc,
                "scanRange": {
                    "from": f"{'+' if False else ''}{-180} minutes",
                    "to": "+180 minutes",
                    "totalMinutes": 360,
                    "stepMinutes": SCAN_STEP_MINUTES,
                },
                "signTransitions": transitions,
                "signDurations": sign_durations,
                "fullScan": scan_results,
                "note": (
                    "Ascendant changes approximately 1 degree every 4 minutes. "
                    "Each sign occupies 30 degrees, so a sign typically rises for ~2 hours. "
                    "Exact durations vary with latitude and time of year."
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error in ascendant scan: {e}", exc_info=True)
        return {"status": 500, "error": str(e), "message": "Error in ascendant scan"}


@router.post("/utility/transit-verify")
def transit_verify(req: TransitVerifyRequest):
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        jd = _local_to_jd(req.dateOfBirth, req.timeOfBirth, req.timezone)
        natal_planets = calc_planets(jd, None, req.nodeMode or "mean")
        for p in natal_planets:
            p["houseStatus"] = planet_status(p["name"], p["sign"])

        natal_house_data = calc_houses(
            jd, req.latitude, req.longitude,
            natal_planets, req.houseSystem or "W",
        )

        event_jd = _local_to_jd(req.eventDate, "12:00", req.timezone)
        transit_planets = calc_planets(event_jd, None, req.nodeMode or "mean")
        for p in transit_planets:
            p["houseStatus"] = planet_status(p["name"], p["sign"])

        transit_house_data = calc_houses(
            event_jd, req.latitude, req.longitude,
            transit_planets, req.houseSystem or "W",
        )

        event_analysis = _score_event_transits(
            natal_planets, transit_planets, req.eventType,
        )

        natal_significance: List[Dict[str, Any]] = []
        for pname in ["Jupiter", "Saturn", "Rahu", "Ketu", "Mars"]:
            np = next((p for p in natal_planets if p["name"] == pname), None)
            if np:
                natal_significance.append({
                    "planet": pname,
                    "natalSign": np["sign"],
                    "natalHouse": np["house"],
                    "dignity": np.get("houseStatus", "N/A"),
                    "isRetrograde": np["isRetrograde"],
                })

        transit_significance: List[Dict[str, Any]] = []
        for pname in ["Jupiter", "Saturn", "Rahu", "Ketu", "Mars"]:
            tp = next((p for p in transit_planets if p["name"] == pname), None)
            if tp:
                transit_significance.append({
                    "planet": pname,
                    "transitSign": tp["sign"],
                    "transitHouse": tp["house"],
                    "dignity": tp.get("houseStatus", "N/A"),
                    "isRetrograde": tp["isRetrograde"],
                })

        confirms = event_analysis["score"] >= 30

        return {
            "status": 200,
            "data": {
                "input": {
                    "dateOfBirth": req.dateOfBirth,
                    "timeOfBirth": req.timeOfBirth,
                    "eventDate": req.eventDate,
                    "eventType": req.eventType,
                    "latitude": req.latitude,
                    "longitude": req.longitude,
                    "timezone": req.timezone,
                },
                "natalChart": {
                    "ascendant": natal_house_data["ascendant"],
                    "keyPlanets": natal_significance,
                },
                "transitChart": {
                    "eventDate": req.eventDate,
                    "ascendant": transit_house_data["ascendant"],
                    "keyTransits": transit_significance,
                },
                "transitVerification": event_analysis,
                "confirmation": {
                    "birthTimeConfirmed": confirms,
                    "confidence": event_analysis["score"],
                    "verdict": event_analysis["verdict"],
                    "explanation": (
                        f"The transits at the event date ({req.eventDate}) for event type "
                        f"'{req.eventType}' {event_analysis['verdict'].lower()} for the given "
                        f"birth time. Score: {event_analysis['score']}/100."
                    ),
                },
                "note": (
                    "Transit verification checks if key planetary transits at the event date "
                    "align with the expected patterns for the given event type. This is one "
                    "method of birth time verification; multiple events should be checked for "
                    "higher confidence."
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error in transit verification: {e}", exc_info=True)
        return {"status": 500, "error": str(e), "message": "Error in transit verification"}
