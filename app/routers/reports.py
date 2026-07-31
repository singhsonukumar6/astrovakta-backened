"""
Reports & PDF generation endpoints.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..response import success as _success, error as _error

router = APIRouter(tags=["Reports"])


# ──────────────── BIRTH CHART REPORT ────────────────
class BirthChartReportRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


@router.post('/reports/birth-chart')
def birth_chart_report(body: BirthChartReportRequest) -> Dict[str, Any]:
    """Generate comprehensive birth chart report with all planetary positions, houses, and analysis."""
    from ..main import (
        to_julian, calc_planets, calc_houses, detect_yogas, detect_doshas,
        vimshottari_full, parse_local_datetime
    )
    from ..utils import ayanamsa_value, planet_status

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    house_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    pmap = {p['name']: p for p in planets}
    asc = house_data['ascendant']

    yogas = detect_yogas(planets, house_data['houses'], asc['sign'])
    doshas = detect_doshas(planets)

    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    dasha = vimshottari_full(jd, birth_local)

    return {
        'success': True,
        'birthData': {
            'date': body.dateOfBirth,
            'time': body.timeOfBirth,
            'lat': body.latitude,
            'lon': body.longitude,
            'tz': body.timezone,
            'ayanamsa': ayanamsa_value(jd),
            'julianDay': jd,
        },
        'ascendant': asc,
        'planets': planets,
        'houses': house_data['houses'],
        'houseSystem': house_data.get('system', body.houseSystem),
        'yogas': yogas,
        'doshas': doshas,
        'dasha': dasha,
        'summary': {
            'sunSign': pmap.get('Sun', {}).get('sign', ''),
            'moonSign': pmap.get('Moon', {}).get('sign', ''),
            'ascSign': asc.get('sign', ''),
            'retroPlanets': [p['name'] for p in planets if p.get('isRetrograde')],
            'combustPlanets': [p['name'] for p in planets if p.get('isCombust')],
            'activeYogas': len(yogas),
            'activeDoshas': len([d for d in doshas if d.get('present')]),
        }
    }


# ──────────────── PREDICTIONS REPORT ────────────────
class PredictionsReportRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')
    aspects: Optional[List[str]] = Field(
        None,
        example=["career", "finance", "health", "love", "education", "family", "travel"],
        description="Specific aspects to predict. Leave empty for all."
    )


@router.post('/reports/predictions')
def predictions_report(body: PredictionsReportRequest) -> Dict[str, Any]:
    """Generate detailed life predictions across all areas from birth chart data."""
    from ..main import (
        to_julian, calc_planets, calc_houses, detect_yogas, detect_doshas,
        vimshottari_full, parse_local_datetime,
    )
    from ..pdf_sections import (
        _predict_career, _predict_finance, _predict_health,
        _predict_education, _predict_love_marriage, _predict_family, _predict_travel,
    )
    from ..utils import ayanamsa_value, planet_status

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    house_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    pmap = {p['name']: p for p in planets}
    asc = house_data['ascendant']
    houses = house_data['houses']

    yogas = detect_yogas(planets, houses, asc['sign'])
    doshas = detect_doshas(planets)

    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    dasha = vimshottari_full(jd, birth_local)

    all_aspects = body.aspects or ["career", "finance", "health", "education", "love", "family", "travel"]

    predictions = {}
    aspect_map = {
        'career': ('Career & Profession', _predict_career),
        'finance': ('Finance & Wealth', _predict_finance),
        'health': ('Health & Wellbeing', _predict_health),
        'education': ('Education & Knowledge', _predict_education),
        'love': ('Love & Marriage', _predict_love_marriage),
        'family': ('Family Life', _predict_family),
        'travel': ('Travel & Settlement', _predict_travel),
    }

    for aspect in all_aspects:
        if aspect in aspect_map:
            title, func = aspect_map[aspect]
            try:
                result = func(planets, houses, pmap, yogas, doshas, dasha)
                predictions[aspect] = {'title': title, 'data': result}
            except Exception as e:
                predictions[aspect] = {'title': title, 'data': {'summary': str(e), 'points': [], 'score': 5}}

    return {
        'success': True,
        'predictions': predictions,
        'meta': {
            'birthDate': body.dateOfBirth,
            'birthTime': body.timeOfBirth,
            'ascendant': asc.get('sign', ''),
            'moonSign': pmap.get('Moon', {}).get('sign', ''),
            'sunSign': pmap.get('Sun', {}).get('sign', ''),
        }
    }


# ──────────────── CAREER REPORT ────────────────
class CareerReportRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


@router.post('/reports/career')
def career_report(body: CareerReportRequest) -> Dict[str, Any]:
    """Detailed career analysis report with profession suggestions, timing, and growth periods."""
    from ..main import (
        to_julian, calc_planets, calc_houses, detect_yogas, detect_doshas,
        vimshottari_full, parse_local_datetime,
    )
    from ..pdf_sections import _predict_career
    from ..utils import ayanamsa_value, planet_status

    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    house_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    pmap = {p['name']: p for p in planets}
    asc = house_data['ascendant']

    yogas = detect_yogas(planets, house_data['houses'], asc['sign'])
    doshas = detect_doshas(planets)

    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    dasha = vimshottari_full(jd, birth_local)

    career = _predict_career(planets, house_data['houses'], pmap, yogas, doshas, dasha)

    return {
        'success': True,
        'career': career,
        'meta': {
            'birthDate': body.dateOfBirth,
            'ascendant': asc.get('sign', ''),
            'moonSign': pmap.get('Moon', {}).get('sign', ''),
            'sunSign': pmap.get('Sun', {}).get('sign', ''),
        }
    }


# ──────────────── COMPREHENSIVE REPORT ────────────────
class ComprehensiveReportRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')


@router.post('/reports/comprehensive')
def comprehensive_report(body: ComprehensiveReportRequest) -> Dict[str, Any]:
    """Generate a complete life report combining birth chart, predictions, dasha, yogas, doshas, and remedies."""
    from ..main import (
        to_julian, calc_planets, calc_houses, detect_yogas, detect_doshas,
        vimshottari_full, parse_local_datetime,
    )
    from ..pdf_sections import (
        _predict_career, _predict_finance, _predict_health,
        _predict_education, _predict_love_marriage, _predict_family, _predict_travel,
    )
    from ..utils import ayanamsa_value, planet_status
    jd = to_julian(body.dateOfBirth, body.timeOfBirth, body.timezone)
    planets = calc_planets(jd, None, body.nodeMode or 'mean')
    for p in planets:
        p['houseStatus'] = planet_status(p['name'], p['sign'])

    house_data = calc_houses(jd, body.latitude, body.longitude, planets, body.houseSystem or 'W')
    pmap = {p['name']: p for p in planets}
    asc = house_data['ascendant']

    yogas = detect_yogas(planets, house_data['houses'], asc['sign'])
    doshas = detect_doshas(planets)

    birth_local = parse_local_datetime(body.dateOfBirth, body.timeOfBirth, body.timezone)
    dasha = vimshottari_full(jd, birth_local)

    predictions = {
        'career': _predict_career(planets, house_data['houses'], pmap, yogas, doshas, dasha),
        'finance': _predict_finance(planets, house_data['houses'], pmap, yogas, doshas, dasha),
        'health': _predict_health(planets, house_data['houses'], pmap, yogas, doshas, dasha),
        'education': _predict_education(planets, house_data['houses'], pmap, yogas, doshas, dasha),
        'love': _predict_love_marriage(planets, house_data['houses'], pmap, yogas, doshas, dasha),
        'family': _predict_family(planets, house_data['houses'], pmap, yogas, doshas, dasha),
        'travel': _predict_travel(planets, house_data['houses'], pmap, yogas, doshas, dasha),
    }

    active_doshas = [d for d in doshas if d.get('present')]

    return {
        'success': True,
        'report': {
            'birthChart': {
                'dateOfBirth': body.dateOfBirth,
                'timeOfBirth': body.timeOfBirth,
                'latitude': body.latitude,
                'longitude': body.longitude,
                'timezone': body.timezone,
                'ascendant': asc,
                'planets': planets,
                'houses': house_data['houses'],
                'sunSign': pmap.get('Sun', {}).get('sign', ''),
                'moonSign': pmap.get('Moon', {}).get('sign', ''),
                'ayanamsa': ayanamsa_value(jd),
            },
            'predictions': predictions,
            'dasha': dasha,
            'yogas': yogas,
            'doshas': doshas,
            'remedies': {
                'dosha_remedies': [d for d in active_doshas if d.get('remedies')],
                'general': [
                    'Chant your Ishta Devata mantra daily',
                    'Practice meditation for 15 minutes each morning',
                    'Offer water to Sun at sunrise',
                    'Donate to charity on auspicious tithis',
                ]
            },
        },
        'meta': {
            'sections': 7,
            'birthDate': body.dateOfBirth,
            'ascendant': asc.get('sign', ''),
            'moonSign': pmap.get('Moon', {}).get('sign', ''),
            'sunSign': pmap.get('Sun', {}).get('sign', ''),
            'yogasFound': len(yogas),
            'doshasFound': len(active_doshas),
        }
    }


# ──────────────── FULL PDF REPORT ────────────────
class FullPDFRequest(BaseModel):
    dateOfBirth: str = Field(..., example="1990-05-15")
    timeOfBirth: str = Field(..., example="14:30")
    latitude: float = Field(..., example=28.6139)
    longitude: float = Field(..., example=77.2090)
    timezone: str = Field(..., example="Asia/Kolkata")
    houseSystem: Optional[str] = Field('W', example='W')
    nodeMode: Optional[str] = Field('mean', example='mean')

    # ── Branding ──
    clientName: Optional[str] = Field(None, example="Rahul Sharma")
    reportTitle: Optional[str] = Field('Vedic Birth Chart Report', example='Vedic Birth Chart Report')
    brandName: Optional[str] = Field(None, example="AstroVakta", description="Brand/company name for header/footer")
    logoUrl: Optional[str] = Field(None, example=None, description="URL or local path to client logo")
    brandLogo: Optional[str] = Field(None, description="URL/path to brand logo image (PNG/JPG) for cover page — shown at top center")
    brandText: Optional[str] = Field(None, example="Your Trusted Astrology Guide", description="Tagline text shown under logo on cover page")
    astrologerImage: Optional[str] = Field(None, description="URL/path to astrologer photo — shown bottom-left on cover, large magazine style")
    backgroundImage: Optional[str] = Field(None, description="URL/path to background image for cover and back pages (rendered faded)")
    contactMobile: Optional[str] = Field(None, example="+91 98765 43210")
    contactEmail: Optional[str] = Field(None, example="info@astrovakta.com")
    contactWebsite: Optional[str] = Field(None, example="www.astrovakta.com")

    # ── Section Selection ──
    sections: Optional[List[str]] = Field(None,
        description="List of section keys to include. Null = all sections. Available: birth_details, kundli_chart, navamsa_chart, hora_chart, planet_positions, houses, nakshatras, dasha, yogas, doshas, planet_strengths, career, finance, health, love, education, family, travel, ai_predictions, major_charts, gemstones, remedies, lucky",
        example=["birth_details", "kundli_chart", "navamsa_chart", "planet_positions", "houses", "yogas", "doshas", "career", "finance"])

    # ── Watermark ──
    watermarkText: Optional[str] = Field(None, example="CONFIDENTIAL", description="Diagonal text watermark on every page (light/transparent)")
    watermarkImageUrl: Optional[str] = Field(None, description="URL or local path to watermark image (semi-transparent overlay)")
    watermarkOpacity: Optional[float] = Field(0.08, ge=0.0, le=0.3, description="Watermark opacity 0.0-0.3 (default 0.08, very light)")


@router.post('/reports/full-pdf')
def generate_full_pdf(body: FullPDFRequest, request: Request = None) -> Response:
    from ..pdf_generator import KundliPDFGenerator

    user_id = None
    if request:
        key_info = getattr(getattr(request, 'state', None), 'api_key_info', None)
        user_id = key_info.get('user_id') if key_info else None

    try:
        generator = KundliPDFGenerator(
            birth_date=body.dateOfBirth,
            birth_time=body.timeOfBirth,
            latitude=body.latitude,
            longitude=body.longitude,
            timezone=body.timezone,
            house_system=body.houseSystem or 'W',
            node_mode=body.nodeMode or 'mean',
            client_name=body.clientName or 'Birth Chart Report',
            client_logo_path=body.logoUrl,
            report_title=body.reportTitle or 'Vedic Birth Chart Report',
            brand_name=body.brandName,
            brand_logo_path=body.brandLogo,
            brand_tagline=body.brandText,
            astrologer_image_path=body.astrologerImage,
            background_image_path=body.backgroundImage,
            contact_mobile=body.contactMobile,
            contact_email=body.contactEmail,
            contact_website=body.contactWebsite,
            user_id=user_id,
            sections=body.sections,
            watermark_text=body.watermarkText,
            watermark_image_path=body.watermarkImageUrl,
            watermark_opacity=body.watermarkOpacity if body.watermarkOpacity is not None else 0.08,
        )

        pdf_bytes = generator.generate()
        info = generator.generate_info()

        safe_name = (body.clientName or 'Report').replace(' ', '_').replace('/', '_')
        filename = f"{safe_name}_Kundli_Report.pdf"

        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'X-Report-Sections': str(len(info.get('sections', []))),
                'X-Report-Yogas': str(info.get('yogas', 0)),
                'X-Report-Doshas': str(info.get('doshas', 0)),
            }
        )
    except Exception as e:
        import traceback
        return _error(str(e), 500)


@router.post('/reports/pdf-info')
def pdf_report_info(body: FullPDFRequest, request: Request = None) -> Dict[str, Any]:
    """Get info about what the PDF report will contain (without generating it)."""
    from ..pdf_generator import KundliPDFGenerator

    user_id = None
    if request:
        key_info = getattr(getattr(request, 'state', None), 'api_key_info', None)
        user_id = key_info.get('user_id') if key_info else None

    try:
        generator = KundliPDFGenerator(
            birth_date=body.dateOfBirth,
            birth_time=body.timeOfBirth,
            latitude=body.latitude,
            longitude=body.longitude,
            timezone=body.timezone,
            house_system=body.houseSystem or 'W',
            node_mode=body.nodeMode or 'mean',
            client_name=body.clientName or 'Birth Chart Report',
            report_title=body.reportTitle or 'Vedic Birth Chart Report',
            brand_name=body.brandName,
            brand_logo_path=body.brandLogo,
            brand_tagline=body.brandText,
            astrologer_image_path=body.astrologerImage,
            background_image_path=body.backgroundImage,
            contact_mobile=body.contactMobile,
            contact_email=body.contactEmail,
            contact_website=body.contactWebsite,
            user_id=user_id,
            sections=body.sections,
            watermark_text=body.watermarkText,
            watermark_image_path=body.watermarkImageUrl,
            watermark_opacity=body.watermarkOpacity if body.watermarkOpacity is not None else 0.08,
        )
        info = generator.generate_info()
        info['availableSections'] = {
            'birth_details': 'Birth Details (date, time, place, ayanamsa)',
            'panchang': 'Birth Panchang (Tithi, Nakshatra, Yoga, Karana, Sunrise/Sunset)',
            'avakhada': 'Avakhada Details (Varna, Vashya, Gana, Nadi, Yoni)',
            'kundli_chart': 'Kundli Chart - North Indian Diamond (D1 Rasi)',
            'navamsa_chart': 'Navamsa Chart (D9)',
            'hora_chart': 'Hora Chart (D2)',
            'planet_positions': 'Full Planet Positions Table',
            'nakshatras': 'Nakshatra Analysis',
            'dasha': 'Vimshottari Dasha Timeline (MD/AD/PD)',
            'extended_dasha': 'Extended Dasha (MD/AD/PD/Sookshma full detail)',
            'char_dasha': 'Chara Dasha (Jaimini System)',
            'shadbala': 'Shadbala (Six-fold Planetary Strength)',
            'bhavabala': 'Bhavabala (House Strength Analysis)',
            'bhava_chalit': 'Bhava Chalit (House Cusp Analysis)',
            'kp_system': 'KP Astrology (Star Lord, Sub Lord per Planet)',
            'kp_ruling_planets': 'KP Ruling Planets (Asc, Moon, Day Lords)',
            'kp_cusps': 'KP Cuspal Lords (12 Cusps with Star/Sub Lords)',
            'ashtakavarga': 'Ashtakavarga (House Strength Bindus)',
            'ashtakavarga_chart': 'Ashtakavarga (Visual Chart Grid)',
            'major_charts': 'All Divisional Chart SVGs (D1-D60)',
            'planet_analysis': 'Planets Deep Analysis (Per-planet strength, effects, challenges)',
            'houses': 'House (Bhava) Analysis',
            'planet_strengths': 'Planet Strengths & Avastha',
            'yogas': 'Yoga Detection & Analysis',
            'doshas': 'Dosha Detection (Manglik, Kaal Sarp, etc.)',
            'gandmool': 'Gandmool & Punarphoo Dosha',
            'career': 'Career & Profession Predictions',
            'finance': 'Finance & Wealth Predictions',
            'health': 'Health Predictions',
            'love': 'Love & Marriage Predictions',
            'education': 'Education & Knowledge Predictions',
            'family': 'Family Life Predictions',
            'travel': 'Travel & Foreign Settlement Predictions',
            'ai_predictions': 'AI-Generated Life Predictions',
            'sade_sati': 'Sade Sati (Saturn Transit Analysis)',
            'varshaphal': 'Varshaphal (Annual Solar Return)',
            'gemstones': 'Gemstone Recommendations',
            'rudraksha': 'Rudraksha Recommendations',
            'remedies': 'Remedies & Spiritual Guidance',
            'lal_kitab': 'Lal Kitab Remedies',
            'mantras_yantras': 'Mantras & Yantras Guide',
            'lucky': 'Lucky Attributes (Color, Number, Day, Metal, Direction)',
            'ascendant_predictions': 'Ascendant Personality & Traits',
            'overall_summary': 'Overall Summary (Key Highlights)',
        }
        info['brandingOptions'] = {
            'logoUrl': 'Path/URL to logo image (shown on cover page)',
            'brandName': 'Brand name in header/footer on every page',
            'clientName': 'Client name on cover page',
            'reportTitle': 'Report title on cover page',
            'contactMobile': 'Contact info on cover/back page',
            'contactEmail': 'Contact info on cover/back page',
            'contactWebsite': 'Contact info in header/footer',
        }
        info['watermarkOptions'] = {
            'watermarkText': 'Diagonal text overlay on every page (e.g. "CONFIDENTIAL")',
            'watermarkImageUrl': 'Image overlay on every page',
            'watermarkOpacity': 'Opacity 0.0-0.3 (default 0.08, very light)',
        }
        return {'success': True, 'data': info}
    except Exception as e:
        return {'success': False, 'error': str(e)}
