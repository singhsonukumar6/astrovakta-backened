from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import swisseph as swe

from ..utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ZODIAC_SIGNS, SIGN_LORDS, PLANET_PROPS, planet_status,
)

router = APIRouter()


class BhavaChalitRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field("W", example="W")
    nodeMode: Optional[str] = Field("mean", example="mean")


def _compute_both_systems(body: BhavaChalitRequest) -> Dict[str, Any]:
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    lat, lon = body.latitude, body.longitude

    ws_planets = calc_planets(jd, None, body.nodeMode or "mean")
    ws_result = calc_houses(jd, lat, lon, ws_planets, "W")
    ws_houses = ws_result["houses"]
    ws_asc = ws_result["ascendant"]
    ws_cusps = ws_result["cusps"]

    pl_planets = calc_planets(jd, None, body.nodeMode or "mean")
    pl_result = calc_houses(jd, lat, lon, pl_planets, "P")
    pl_houses = pl_result["houses"]
    pl_asc = pl_result["ascendant"]
    pl_cusps_raw = pl_result["cusps"]

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    raw_cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
    cusp_list = list(raw_cusps)
    if len(cusp_list) >= 13:
        cusp_degrees = cusp_list[1:13]
    else:
        cusp_degrees = cusp_list[0:12]

    asc_cusp = ascmc[0]
    mc_cusp = ascmc[1]
    armc_cusp = ascmc[2]
    vertex_cusp = ascmc[3]

    cusp_details = []
    for i, deg in enumerate(cusp_degrees):
        sign_name = get_sign(deg)
        nk = get_nakshatra(deg)
        cusp_details.append({
            "house": i + 1,
            "degree": round(deg, 4),
            "degreeDMS": _to_dms(deg),
            "sign": sign_name,
            "signLord": SIGN_LORDS[sign_name],
            "nakshatra": nk["name"],
            "nakshatraLord": nk["lord"],
            "nakshatraPada": nk["pada"],
        })

    ws_map = {}
    for h in ws_houses:
        ws_map[h["number"]] = h["planets"]

    pl_map = {}
    for h in pl_houses:
        pl_map[h["number"]] = h["planets"]

    differences = []
    for pname in [p["name"] for p in ws_planets]:
        ws_house = next((p["house"] for p in ws_planets if p["name"] == pname), 0)
        pl_house = next((p["house"] for p in pl_planets if p["name"] == pname), 0)
        if ws_house != pl_house:
            differences.append({
                "planet": pname,
                "wholeSignHouse": ws_house,
                "cuspBasedHouse": pl_house,
                "difference": pl_house - ws_house,
                "significance": _significance_text(ws_house, pl_house),
            })

    ws_planets_enriched = []
    for p in ws_planets:
        ws_planets_enriched.append({
            "name": p["name"],
            "longitude": round(p["longitude"], 4),
            "sign": p["sign"],
            "signLord": p["signLord"],
            "degree": round(p["degree"], 4),
            "degreeDMS": p["degreeDMS"],
            "nakshatra": p["nakshatra"],
            "nakshatraLord": p["nakshatraLord"],
            "nakshatraPada": p["nakshatraPada"],
            "house": p["house"],
            "isRetrograde": p["isRetrograde"],
            "avastha": p["avastha"],
        })

    pl_planets_enriched = []
    for p in pl_planets:
        pl_planets_enriched.append({
            "name": p["name"],
            "longitude": round(p["longitude"], 4),
            "sign": p["sign"],
            "signLord": p["signLord"],
            "degree": round(p["degree"], 4),
            "degreeDMS": p["degreeDMS"],
            "nakshatra": p["nakshatra"],
            "nakshatraLord": p["nakshatraLord"],
            "nakshatraPada": p["nakshatraPada"],
            "house": p["house"],
            "isRetrograde": p["isRetrograde"],
            "avastha": p["avastha"],
        })

    return {
        "wholeSign": {
            "houses": ws_houses,
            "planets": ws_planets_enriched,
            "ascendant": ws_asc,
        },
        "cuspBased": {
            "houses": pl_houses,
            "planets": pl_planets_enriched,
            "ascendant": pl_asc,
            "cusps": cusp_details,
            "specialPoints": {
                "ascendant": {"degree": round(asc_cusp, 4), "sign": get_sign(asc_cusp), "signLord": SIGN_LORDS[get_sign(asc_cusp)]},
                "midheaven": {"degree": round(mc_cusp, 4), "sign": get_sign(mc_cusp), "signLord": SIGN_LORDS[get_sign(mc_cusp)]},
                "armc": {"degree": round(armc_cusp, 4), "sign": get_sign(armc_cusp)},
                "vertex": {"degree": round(vertex_cusp, 4), "sign": get_sign(vertex_cusp)},
            },
        },
        "differences": differences,
        "hasDifferences": len(differences) > 0,
        "summary": _build_summary(differences, ws_planets, pl_planets),
    }


def _to_dms(x: float) -> str:
    s = -1 if x < 0 else 1
    x = abs(x)
    d = int(x)
    m = int((x - d) * 60)
    sec = int(round(((x - d) * 60 - m) * 60))
    sign = "-" if s < 0 else ""
    return f"{sign}{d}°{m}'{sec}\""


def _significance_text(ws: int, pl: int) -> str:
    diff = pl - ws
    if abs(diff) == 1:
        return "Adjacent house shift — marginal cusp boundary effect. Interpretation mostly preserved."
    if abs(diff) == 2:
        return "Two-house shift — notable difference. Key significations may change. Review carefully."
    return f"Significant {abs(diff)}-house shift. Core house meaning changes materially between systems."


def _build_summary(diffs: list, ws_planets: list, pl_planets: list) -> str:
    if not diffs:
        return "All planets occupy the same house in both whole-sign and cusp-based systems. No interpretive conflict."
    changed = [d["planet"] for d in diffs]
    return (
        f"{len(diffs)} planet(s) differ between systems: {', '.join(changed)}. "
        f"Cross-reference both house placements for accurate interpretation."
    )


@router.post("/horoscope/bhava-chalit")
def bhava_chalit(body: BhavaChalitRequest):
    result = _compute_both_systems(body)
    return {
        "status": "success",
        "meta": {
            "dateOfBirth": body.dateOfBirth,
            "timeOfBirth": body.timeOfBirth,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "timezone": body.timezone,
            "houseSystem": body.houseSystem,
            "nodeMode": body.nodeMode,
        },
        "data": result,
    }


@router.post("/horoscope/bhava-chalit/compare")
def bhava_chalit_compare(body: BhavaChalitRequest):
    result = _compute_both_systems(body)

    ws_planets = result["wholeSign"]["planets"]
    pl_planets = result["cuspBased"]["planets"]

    comparison_rows = []
    for wp in ws_planets:
        pp = next((p for p in pl_planets if p["name"] == wp["name"]), None)
        cusp_house = pp["house"] if pp else wp["house"]
        same = wp["house"] == cusp_house
        comparison_rows.append({
            "planet": wp["name"],
            "sign": wp["sign"],
            "signLord": wp["signLord"],
            "degree": wp["degree"],
            "degreeDMS": wp["degreeDMS"],
            "isRetrograde": wp["isRetrograde"],
            "wholeSignHouse": wp["house"],
            "cuspBasedHouse": cusp_house,
            "same": same,
            "shift": cusp_house - wp["house"],
        })

    ws_asc = result["wholeSign"]["ascendant"]
    pl_asc = result["cuspBased"]["ascendant"]

    return {
        "status": "success",
        "meta": {
            "dateOfBirth": body.dateOfBirth,
            "timeOfBirth": body.timeOfBirth,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "timezone": body.timezone,
        },
        "data": {
            "comparisonTable": comparison_rows,
            "ascendant": {
                "wholeSign": ws_asc,
                "cuspBased": pl_asc,
                "sameSign": ws_asc["sign"] == pl_asc["sign"],
            },
            "differences": result["differences"],
            "hasDifferences": result["hasDifferences"],
            "summary": result["summary"],
            "totalPlanets": len(comparison_rows),
            "planetsWithShift": sum(1 for r in comparison_rows if not r["same"]),
            "planetsSame": sum(1 for r in comparison_rows if r["same"]),
        },
    }


@router.post("/horoscope/bhava-chalit/cusps")
def bhava_chalit_cusps(body: BhavaChalitRequest):
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    lat, lon = body.latitude, body.longitude

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    raw_cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
    cusp_list = list(raw_cusps)
    if len(cusp_list) >= 13:
        cusp_degrees = cusp_list[1:13]
    else:
        cusp_degrees = cusp_list[0:12]

    asc_cusp = ascmc[0]
    mc_cusp = ascmc[1]
    armc_cusp = ascmc[2]
    vertex_cusp = ascmc[3]

    cusps = []
    for i, deg in enumerate(cusp_degrees):
        sign_name = get_sign(deg)
        nk = get_nakshatra(deg)
        cusps.append({
            "house": i + 1,
            "degree": round(deg, 4),
            "degreeDMS": _to_dms(deg),
            "sign": sign_name,
            "signLord": SIGN_LORDS[sign_name],
            "nakshatra": nk["name"],
            "nakshatraLord": nk["lord"],
            "nakshatraPada": nk["pada"],
        })

    asc_sign = get_sign(asc_cusp)
    mc_sign = get_sign(mc_cusp)

    return {
        "status": "success",
        "meta": {
            "dateOfBirth": body.dateOfBirth,
            "timeOfBirth": body.timeOfBirth,
            "latitude": body.latitude,
            "longitude": body.longitude,
            "timezone": body.timezone,
        },
        "data": {
            "cusps": cusps,
            "specialPoints": {
                "ascendant": {
                    "degree": round(asc_cusp, 4),
                    "degreeDMS": _to_dms(asc_cusp),
                    "sign": asc_sign,
                    "signLord": SIGN_LORDS[asc_sign],
                },
                "midheaven": {
                    "degree": round(mc_cusp, 4),
                    "degreeDMS": _to_dms(mc_cusp),
                    "sign": mc_sign,
                    "signLord": SIGN_LORDS[mc_sign],
                },
                "armc": {
                    "degree": round(armc_cusp, 4),
                    "degreeDMS": _to_dms(armc_cusp),
                    "sign": get_sign(armc_cusp),
                    "signLord": SIGN_LORDS[get_sign(armc_cusp)],
                },
                "vertex": {
                    "degree": round(vertex_cusp, 4),
                    "degreeDMS": _to_dms(vertex_cusp),
                    "sign": get_sign(vertex_cusp),
                    "signLord": SIGN_LORDS[get_sign(vertex_cusp)],
                },
            },
        },
    }
