"""
PDF Generator — Orchestrates the full Kundli PDF report.
Computes all chart data and assembles sections into a complete PDF.
"""
import io
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer, PageBreak
from reportlab.lib.units import mm

from .pdf_engine import (
    get_styles, header_footer, cover_page_drawing, back_page_elements,
    section_divider, ZODIAC_SIGNS, PLANET_COLORS, SIGN_COLORS,
)
from .pdf_sections import (
    build_birth_details_section, build_kundli_chart_section,
    build_planet_positions_section, build_houses_section,
    build_nakshatra_section, build_dasha_section, build_yogas_section,
    build_doshas_section, build_planet_strengths_section,
    build_gemstone_section, build_remedies_section, build_lucky_section,
    build_navamsa_chart_section, build_hora_chart_section,
    build_career_predictions_section, build_health_predictions_section,
    build_love_predictions_section, build_finance_predictions_section,
    build_education_predictions_section, build_family_predictions_section,
    build_travel_predictions_section,
    build_ai_life_predictions_section,
    build_major_charts_svg_section,
    # New sections
    build_panchang_section, build_avakhada_section,
    build_bhava_chalit_section, build_kp_section,
    build_shadbala_section, build_char_dasha_section,
    build_sade_sati_section, build_varshaphal_section,
    build_rudraksha_section, build_lal_kitab_section,
    build_mantras_yantras_section, build_ashtakavarga_section,
    build_gandmool_section, build_ascendant_predictions_section,
    build_bhavabala_section, build_kp_ruling_planets_section,
    build_kp_cusps_section, build_planet_analysis_section,
    build_overall_summary_section, build_extended_dasha_section,
    build_ashtakavarga_chart_section,
)
from .utils import (
    to_julian, calc_planets, calc_houses, get_sign, get_nakshatra,
    ayanamsa_value, planet_status, ZODIAC_SIGNS as _SIGNS, SIGN_LORDS,
)

logger = logging.getLogger(__name__)


class KundliPDFGenerator:
    """Generates a complete Vedic Astrology PDF report."""

    def __init__(self, birth_date: str, birth_time: str, latitude: float,
                 longitude: float, timezone: str, house_system: str = 'W',
                 node_mode: str = 'mean', client_name: str = '',
                 client_logo_path: str = None, report_title: str = 'Vedic Birth Chart Report',
                 brand_name: str = None, brand_logo_path: str = None,
                 brand_tagline: str = None, astrologer_image_path: str = None,
                 background_image_path: str = None,
                 contact_mobile: str = None,
                 contact_email: str = None, contact_website: str = None,
                 user_id: int = None,
                 # ── Section selection ──
                 sections: list = None,
                 # ── Watermark ──
                 watermark_text: str = None,
                 watermark_image_path: str = None,
                 watermark_opacity: float = 0.08,
                 # ── Chart size ──
                 chart_dpi: int = 2):
        self.birth_date = birth_date
        self.birth_time = birth_time
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.house_system = house_system
        self.node_mode = node_mode
        self.client_name = client_name or 'Birth Chart Report'
        self.client_logo_path = client_logo_path
        self.report_title = report_title
        self.brand_name = brand_name or 'AstroVakta'
        self.brand_logo_path = brand_logo_path
        self.brand_tagline = brand_tagline
        self.astrologer_image_path = astrologer_image_path
        self.background_image_path = background_image_path
        self.contact_mobile = contact_mobile
        self.contact_email = contact_email
        self.contact_website = contact_website
        self.user_id = user_id

        # Section selection (None = all sections)
        self.sections = sections  # e.g. ['birth_details','charts','predictions']

        # Watermark
        self.watermark_text = watermark_text
        self.watermark_image_path = watermark_image_path
        self.watermark_opacity = watermark_opacity

        # Chart rendering
        self.chart_dpi = chart_dpi

        # Computed data (lazy)
        self._jd = None
        self._planets = None
        self._house_data = None
        self._pmap = None
        self._asc = None
        self._yogas = None
        self._doshas = None
        self._dasha = None

    def _compute(self):
        """Compute all astrological data."""
        if self._jd is not None:
            return

        from .main import detect_yogas, detect_doshas, vimshottari_full, parse_local_datetime

        self._jd = to_julian(self.birth_date, self.birth_time, self.timezone)
        self._planets = calc_planets(self._jd, None, self.node_mode)

        for p in self._planets:
            p['houseStatus'] = planet_status(p['name'], p['sign'])

        self._house_data = calc_houses(
            self._jd, self.latitude, self.longitude,
            self._planets, self.house_system
        )

        self._pmap = {p['name']: p for p in self._planets}
        self._asc = self._house_data['ascendant']

        self._yogas = detect_yogas(
            self._planets,
            self._house_data['houses'],
            self._asc['sign']
        )

        self._doshas = detect_doshas(self._planets)

        birth_local = parse_local_datetime(
            self.birth_date, self.birth_time, self.timezone
        )
        self._dasha = vimshottari_full(self._jd, birth_local)

    def generate(self, output_path: str = None) -> bytes:
        """
        Generate the full PDF report.
        If output_path is given, writes to file.
        Always returns the PDF bytes.
        """
        self._compute()

        # Determine which sections to include
        all_sections = [
            # Basic Details
            'birth_details', 'panchang', 'avakhada',
            # Charts
            'kundli_chart', 'navamsa_chart', 'hora_chart',
            # Planetary
            'planet_positions', 'nakshatras',
            # Dasha
            'dasha', 'extended_dasha', 'char_dasha',
            # Strength Analysis
            'shadbala', 'bhavabala',
            # KP Astrology
            'bhava_chalit', 'kp_system', 'kp_ruling_planets', 'kp_cusps',
            # Special Systems
            'ashtakavarga', 'ashtakavarga_chart', 'major_charts',
            # Per-planet & Houses
            'planet_analysis', 'houses', 'planet_strengths',
            # Yogas & Doshas
            'yogas', 'doshas', 'gandmool',
            # Predictions
            'career', 'finance', 'health', 'love', 'education', 'family', 'travel',
            'ai_predictions', 'sade_sati', 'varshaphal',
            # Remedies & Recommendations
            'gemstones', 'rudraksha', 'remedies', 'lal_kitab', 'mantras_yantras',
            # Lifestyle
            'lucky', 'ascendant_predictions',
            # Summary
            'overall_summary',
        ]
        if self.sections:
            active = [s for s in self.sections if s in all_sections]
        else:
            active = all_sections

        # Build the PDF document
        if output_path:
            doc = SimpleDocTemplate(
                output_path, pagesize=A4,
                leftMargin=25, rightMargin=25,
                topMargin=50, bottomMargin=45,
            )
        else:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer, pagesize=A4,
                leftMargin=25, rightMargin=25,
                topMargin=50, bottomMargin=45,
            )

        elements = []
        page_width = A4[0] - 50  # subtract margins

        # ──── COVER PAGE (always included) ────
        location_str = f"{self.latitude:.4f}°N, {self.longitude:.4f}°E ({self.timezone})"
        elements.extend(cover_page_drawing(
            client_name=self.client_name,
            report_title=self.report_title,
            birth_date=self.birth_date,
            birth_time=self.birth_time,
            location=location_str,
            logo_path=self.client_logo_path,
            brand_name=self.brand_name,
            brand_logo_path=self.brand_logo_path,
            brand_tagline=self.brand_tagline,
            astrologer_image_path=self.astrologer_image_path,
            background_image_path=self.background_image_path,
            contact_mobile=self.contact_mobile,
            contact_email=self.contact_email,
            contact_website=self.contact_website,
        ))

        # ──── Conditionally add sections (reorganized order) ────
        # 1. Basic Details
        if 'birth_details' in active:
            elements.extend(build_birth_details_section(
                {
                    'dateOfBirth': self.birth_date,
                    'timeOfBirth': self.birth_time,
                    'latitude': self.latitude,
                    'longitude': self.longitude,
                    'timezone': self.timezone,
                },
                self._asc,
                ayanamsa_value(self._jd),
            ))
        if 'panchang' in active:
            elements.extend(build_panchang_section(self._jd, self.latitude, self.longitude, self.timezone, self.birth_date))
        if 'avakhada' in active:
            elements.extend(build_avakhada_section(self._pmap.get('Moon', self._planets[0] if self._planets else {})))

        # 2. Charts
        if 'kundli_chart' in active:
            elements.extend(build_kundli_chart_section(self._planets, self._asc['sign'], self._asc.get('degree', 0)))
        if 'navamsa_chart' in active:
            elements.extend(build_navamsa_chart_section(self._planets, self._asc))
        if 'hora_chart' in active:
            elements.extend(build_hora_chart_section(self._planets))

        # 3. Planetary Positions
        if 'planet_positions' in active:
            elements.extend(build_planet_positions_section(self._planets))
        if 'nakshatras' in active:
            elements.extend(build_nakshatra_section(self._planets))

        # 4. Dasha
        if 'dasha' in active:
            elements.extend(build_dasha_section(self._dasha, self.timezone))
        if 'extended_dasha' in active:
            elements.extend(build_extended_dasha_section(self._dasha, self.timezone))
        if 'char_dasha' in active:
            elements.extend(build_char_dasha_section(self._planets, self._asc))

        # 5. Strength Analysis
        if 'shadbala' in active:
            elements.extend(build_shadbala_section(self._planets))
        if 'bhavabala' in active:
            elements.extend(build_bhavabala_section(self._planets, self._house_data['houses']))

        # 6. KP Astrology
        if 'bhava_chalit' in active:
            elements.extend(build_bhava_chalit_section(self._house_data))
        if 'kp_system' in active:
            elements.extend(build_kp_section(self._planets))
        if 'kp_ruling_planets' in active:
            elements.extend(build_kp_ruling_planets_section(self._planets, self._asc))
        if 'kp_cusps' in active:
            elements.extend(build_kp_cusps_section(self._planets))

        # 7. Special Systems
        if 'ashtakavarga' in active:
            elements.extend(build_ashtakavarga_section(self._planets))
        if 'ashtakavarga_chart' in active:
            elements.extend(build_ashtakavarga_chart_section(self._planets))
        if 'major_charts' in active:
            elements.extend(build_major_charts_svg_section(
                self._planets, self._asc['sign'], asc_degree=self._asc.get('degree', 0), user_id=self.user_id
            ))

        # 8. Per-planet & Houses
        if 'planet_analysis' in active:
            elements.extend(build_planet_analysis_section(self._planets, self._house_data['houses'], self._asc))
        if 'houses' in active:
            elements.extend(build_houses_section(self._house_data['houses'], self._pmap))
        if 'planet_strengths' in active:
            elements.extend(build_planet_strengths_section(self._planets))

        # 9. Yogas & Doshas
        if 'yogas' in active:
            elements.extend(build_yogas_section(self._yogas))
        if 'doshas' in active:
            elements.extend(build_doshas_section(self._doshas))
        if 'gandmool' in active:
            elements.extend(build_gandmool_section(self._planets))

        # 10. Predictions
        if 'career' in active:
            elements.extend(build_career_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'finance' in active:
            elements.extend(build_finance_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'health' in active:
            elements.extend(build_health_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'love' in active:
            elements.extend(build_love_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'education' in active:
            elements.extend(build_education_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'family' in active:
            elements.extend(build_family_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'travel' in active:
            elements.extend(build_travel_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha
            ))
        if 'ai_predictions' in active:
            elements.extend(build_ai_life_predictions_section(
                self._planets, self._house_data['houses'],
                self._pmap, self._yogas, self._doshas, self._dasha,
                self._asc, user_id=self.user_id
            ))
        if 'sade_sati' in active:
            elements.extend(build_sade_sati_section(self._planets))
        if 'varshaphal' in active:
            elements.extend(build_varshaphal_section(self._planets, self._asc))

        # 11. Remedies & Recommendations
        if 'gemstones' in active:
            elements.extend(build_gemstone_section(self._planets, self._pmap, self._asc['sign']))
        if 'rudraksha' in active:
            elements.extend(build_rudraksha_section(self._planets))
        if 'remedies' in active:
            elements.extend(build_remedies_section(self._doshas, self._yogas))
        if 'lal_kitab' in active:
            elements.extend(build_lal_kitab_section(self._planets, self._house_data['houses']))
        if 'mantras_yantras' in active:
            elements.extend(build_mantras_yantras_section(self._planets))

        # 12. Lifestyle
        if 'lucky' in active:
            elements.extend(build_lucky_section(self.birth_date))
        if 'ascendant_predictions' in active:
            elements.extend(build_ascendant_predictions_section(self._asc))

        # 13. Overall Summary
        if 'overall_summary' in active:
            elements.extend(build_overall_summary_section(self._planets, self._yogas, self._doshas, self._dasha, self._asc))

        # ──── BACK PAGE (always included) ────
        # ──── BACK PAGE (always included, starts new page) ────
        elements.append(PageBreak())
        elements.extend(back_page_elements(
            brand_name=self.brand_name,
            brand_logo_path=self.brand_logo_path,
            background_image_path=self.background_image_path,
            contact_mobile=self.contact_mobile,
            contact_email=self.contact_email,
            contact_website=self.contact_website,
        ))

        # ──── BUILD ────
        def on_page(canvas, doc):
            header_footer(
                canvas, doc, self.client_name, self.report_title,
                self.brand_name, self.contact_website,
                watermark_text=self.watermark_text,
                watermark_image_path=self.watermark_image_path,
                watermark_opacity=self.watermark_opacity,
            )

        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)

        if output_path:
            return b''
        else:
            buffer.seek(0)
            return buffer.read()

    def generate_info(self) -> Dict[str, Any]:
        """Return summary info of the report."""
        self._compute()
        all_section_meta = {
            'birth_details': 'Birth Details',
            'panchang': 'Birth Panchang',
            'avakhada': 'Avakhada Details',
            'kundli_chart': 'Kundli Chart (Rasi)',
            'navamsa_chart': 'Navamsa Chart (D9)',
            'hora_chart': 'Hora Chart (D2)',
            'planet_positions': 'Planet Positions',
            'nakshatras': 'Nakshatra Analysis',
            'dasha': 'Vimshottari Dasha',
            'extended_dasha': 'Extended Dasha (MD/AD/PD/Sookshma)',
            'char_dasha': 'Chara Dasha (Jaimini)',
            'shadbala': 'Shadbala (Planet Strength)',
            'bhavabala': 'Bhavabala (House Strength)',
            'bhava_chalit': 'Bhava Chalit Analysis',
            'kp_system': 'KP Astrology System',
            'kp_ruling_planets': 'KP Ruling Planets',
            'kp_cusps': 'KP Cuspal Lords',
            'ashtakavarga': 'Ashtakavarga (Table)',
            'ashtakavarga_chart': 'Ashtakavarga (Chart)',
            'major_charts': 'Divisional Charts (D1-D60)',
            'planet_analysis': 'Planets Deep Analysis',
            'houses': 'House Analysis',
            'planet_strengths': 'Planet Strengths & Avastha',
            'yogas': 'Yogas',
            'doshas': 'Doshas',
            'gandmool': 'Gandmool & Punarphoo Dosha',
            'career': 'Career Predictions',
            'finance': 'Finance Predictions',
            'health': 'Health Predictions',
            'love': 'Love & Marriage',
            'education': 'Education',
            'family': 'Family Life',
            'travel': 'Travel & Settlement',
            'ai_predictions': 'AI Life Predictions',
            'sade_sati': 'Sade Sati Analysis',
            'varshaphal': 'Varshaphal (Solar Return)',
            'gemstones': 'Gemstone Recommendations',
            'rudraksha': 'Rudraksha Recommendations',
            'remedies': 'Remedies & Guidance',
            'lal_kitab': 'Lal Kitab Remedies',
            'mantras_yantras': 'Mantras & Yantras',
            'lucky': 'Lucky Attributes',
            'ascendant_predictions': 'Ascendant & Personality',
            'overall_summary': 'Overall Summary',
        }
        if self.sections:
            active = [s for s in self.sections if s in all_section_meta]
        else:
            active = list(all_section_meta.keys())
        return {
            'birthDate': self.birth_date,
            'birthTime': self.birth_time,
            'ascendant': self._asc,
            'moonSign': self._pmap.get('Moon', {}).get('sign', ''),
            'sunSign': self._pmap.get('Sun', {}).get('sign', ''),
            'planets': len(self._planets),
            'yogas': len(self._yogas),
            'doshas': len([d for d in self._doshas if d.get('present')]),
            'sections': [all_section_meta[s] for s in active],
            'totalSections': len(active),
        }
