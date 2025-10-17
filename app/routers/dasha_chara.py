from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

router = APIRouter()


class CharaDashaRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    timezone: str = Field(..., example="Asia/Kolkata")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    houseSystem: Optional[str] = Field(None, example='W')


def _sign_index(sign: str) -> int:
    from ..main import ZODIAC_SIGNS
    return ZODIAC_SIGNS.index(sign)


def _sign_distance(start: str, end: str) -> int:
    # Inclusive distance in signs moving forward from start to reach end
    from ..main import ZODIAC_SIGNS
    si = _sign_index(start)
    ei = _sign_index(end)
    if ei >= si:
        return (ei - si) + 1
    return (12 - si) + ei + 1


def _build_chara_sequence(lagna_sign: str) -> List[str]:
    # Sequence starting from Lagna sign and moving forward 12 signs
    from ..main import ZODIAC_SIGNS
    si = _sign_index(lagna_sign)
    return [ZODIAC_SIGNS[(si + i) % 12] for i in range(12)]


@router.post('/dasha/chara')
def chara_dasha(body: CharaDashaRequest) -> Dict[str, Any]:
    """
    Simplified Jaimini Chara Dasha implementation (sign-based):
    - Requires location to compute Lagna (ascendant)
    - MD duration for a sign = number of signs from current sign to its lord's sign (inclusive), in years.
    - AD inside a MD: split MD proportionally by the same rule over the 12-sign sequence starting at MD sign.
    - PD inside an AD: similarly proportional.
    Note: Schools vary (K.N. Rao, Sanjay Rath, etc.). This is a basic, consistent variant for productization.
    """
    from ..main import (
        to_julian, parse_local_datetime, calc_planets, calc_houses, SIGN_LORDS,
    )

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)

    planets = calc_planets(jd, None, 'mean')
    houses = calc_houses(jd, float(body.latitude), float(body.longitude), planets, body.houseSystem or 'W')
    lagna_sign = houses['ascendant']['sign']

    seq = _build_chara_sequence(lagna_sign)

    # Compute MD durations
    md_list = []
    cursor = birth_local
    for sign in seq:
        lord = SIGN_LORDS[sign]
        # In Jaimini, some use sign-based lords (same as Parasara); acceptable here
        lord_planet = next((p for p in planets if p['name'] == lord), None)
        lord_sign = lord_planet['sign'] if lord_planet else sign
        years = _sign_distance(sign, lord_sign)
        md_start = cursor
        md_list.append({'sign': sign, 'lord': lord, 'lordSign': lord_sign, 'years': years, 'start': md_start, 'end': None})

    # Assign MD start/end cumulatively
    cursor = birth_local
    for md in md_list:
        from ..main import pd_years
        md['start'] = cursor
        md_end = cursor + pd_years(md['years'])
        md['end'] = md_end
        cursor = md_end

    # Build AD and PD
    def build_ad(md_sign: str, md_start, md_years: float):
        ad = []
        sub_seq = _build_chara_sequence(md_sign)
        from ..main import pd_years, SIGN_LORDS
        cursor_a = md_start
        # Precompute parts and normalize to md_years
        parts = []
        for s in sub_seq:
            lord = SIGN_LORDS[s]
            lord_planet = next((p for p in planets if p['name'] == lord), None)
            lord_sign = lord_planet['sign'] if lord_planet else s
            parts.append((_sign_distance(s, lord_sign), s))
        total_part = sum(p for p, _ in parts)
        for s in sub_seq:
            lord = SIGN_LORDS[s]
            lord_planet = next((p for p in planets if p['name'] == lord), None)
            lord_sign = lord_planet['sign'] if lord_planet else s
            part = _sign_distance(s, lord_sign)
            # proportional split normalized across sequence
            ad_years = md_years * (part / total_part) if total_part > 0 else (md_years / 12.0)
            ad_start = cursor_a
            ad_end = ad_start + pd_years(ad_years)
            ad.append({'sign': s, 'years': ad_years, 'start': ad_start, 'end': ad_end, 'pratyantar': []})
            cursor_a = ad_end
        return ad

    for md in md_list:
        md['antardasha'] = build_ad(md['sign'], md['start'], md['years'])
        # Build PD within each AD: simple equal split across 12 signs
        for ad in md['antardasha']:
            from ..main import pd_years
            cursor_p = ad['start']
            pd_dur = (ad['years'] / 12.0)
            pd_list = []
            for s in _build_chara_sequence(ad['sign']):
                p_start = cursor_p
                p_end = p_start + pd_years(pd_dur)
                pd_list.append({'sign': s, 'years': pd_dur, 'start': p_start, 'end': p_end})
                cursor_p = p_end
            ad['pratyantar'] = pd_list

    # Identify current MD/AD/PD by birth date (start of the sequence)
    def to_date(d):
        return d.date().isoformat()

    now = birth_local
    current_md = next((m for m in md_list if m['start'] <= now < m['end']), md_list[0])
    current_ad = next((a for a in current_md['antardasha'] if a['start'] <= now < a['end']), current_md['antardasha'][0])
    current_pd = next((p for p in current_ad['pratyantar'] if p['start'] <= now < p['end']), current_ad['pratyantar'][0])

    # Serialize
    def ser_md(m):
        return {
            'sign': m['sign'], 'lord': m['lord'], 'lordSign': m['lordSign'], 'startDate': to_date(m['start']), 'endDate': to_date(m['end']), 'years': m['years'],
            'antardasha': [
                {
                    'sign': a['sign'], 'startDate': to_date(a['start']), 'endDate': to_date(a['end']), 'years': a['years'],
                    'pratyantar': [
                        {'sign': p['sign'], 'startDate': to_date(p['start']), 'endDate': to_date(p['end']), 'years': p['years']}
                        for p in a['pratyantar']
                    ]
                }
                for a in m['antardasha']
            ]
        }

    # Validation helpers
    def days_between(a: str, b: str) -> int:
        from datetime import date
        y1, m1, d1 = [int(x) for x in a.split('-')]
        y2, m2, d2 = [int(x) for x in b.split('-')]
        return (date(y2, m2, d2) - date(y1, m1, d1)).days

    def validate(schedule: Dict[str, Any]) -> Dict[str, Any]:
        md_ok, ad_ok, pd_ok, cont_ok = True, True, True, True
        issues: List[str] = []
        prev_md_end = None
        for md in schedule.get('mahadashas', []):
            if prev_md_end and md['startDate'] != prev_md_end:
                cont_ok = False
                issues.append(f"MD continuity break: {prev_md_end} -> {md['startDate']}")
            prev_md_end = md['endDate']
            ad_years_sum = 0.0
            prev_ad_end = md['startDate']
            for ad in md.get('antardasha', []):
                ad_years_sum += float(ad['years'])
                if ad['startDate'] != prev_ad_end:
                    cont_ok = False
                    issues.append(f"AD continuity break in {md['sign']}: {prev_ad_end} -> {ad['startDate']}")
                prev_ad_end = ad['endDate']
                pd_years_sum = 0.0
                prev_pd_end = ad['startDate']
                for pd in ad.get('pratyantar', []):
                    pd_years_sum += float(pd['years'])
                    if pd['startDate'] != prev_pd_end:
                        cont_ok = False
                        issues.append(f"PD continuity break in {md['sign']}/{ad['sign']}: {prev_pd_end} -> {pd['startDate']}")
                    prev_pd_end = pd['endDate']
                if abs(pd_years_sum - float(ad['years'])) > 1e-6:
                    pd_ok = False
                    issues.append(f"PD sum mismatch in {md['sign']}/{ad['sign']}: {pd_years_sum} vs {ad['years']}")
            if abs(ad_years_sum - float(md['years'])) > 1e-6:
                ad_ok = False
                issues.append(f"AD sum mismatch in {md['sign']}: {ad_years_sum} vs {md['years']}")
        return {'adSum': ad_ok, 'pdSum': pd_ok, 'continuity': cont_ok, 'issues': issues}

    schedule = {
        'current': {
            'mahadasha': {'sign': current_md['sign'], 'startDate': to_date(current_md['start']), 'endDate': to_date(current_md['end'])},
            'antardasha': {'sign': current_ad['sign'], 'startDate': to_date(current_ad['start']), 'endDate': to_date(current_ad['end'])},
            'pratyantar': {'sign': current_pd['sign'], 'startDate': to_date(current_pd['start']), 'endDate': to_date(current_pd['end'])},
        },
        'mahadashas': [ser_md(m) for m in md_list]
    }

    return {
        'status': 200,
        'system': 'Chara Dasha (simplified)',
        'data': schedule,
        'validation': validate(schedule),
        'context': {
            'ascendant': houses.get('ascendant'),
            'houseSystem': (body.houseSystem or 'W')
        }
    }
