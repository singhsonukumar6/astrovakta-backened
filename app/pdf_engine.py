"""
PDF Engine — Core drawing utilities for generating Vedic Astrology reports.
Uses ReportLab for vector-quality PDF output.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Image, ListFlowable, ListItem
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Ellipse, Path, Polygon
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ──────────────────────────── COLOR PALETTE ────────────────────────────
# Brand colors
PRIMARY        = colors.HexColor('#1a237e')   # Deep Indigo
SECONDARY      = colors.HexColor('#ff6f00')   # Saffron Orange
ACCENT         = colors.HexColor('#00695c')   # Teal
LIGHT_BG       = colors.HexColor('#f5f5f5')   # Off-white
CREAM          = colors.HexColor('#fff8e1')   # Warm cream
DARK_TEXT       = colors.HexColor('#212121')
MID_TEXT        = colors.HexColor('#424242')
LIGHT_TEXT      = colors.HexColor('#757575')

# Element colors
FIRE_COLOR     = colors.HexColor('#d32f2f')   # Red
EARTH_COLOR    = colors.HexColor('#388e3c')   # Green
AIR_COLOR      = colors.HexColor('#1565c0')   # Blue
WATER_COLOR    = colors.HexColor('#00838f')   # Cyan

# Planet colors
PLANET_COLORS = {
    'Sun':     colors.HexColor('#ff8f00'),
    'Moon':    colors.HexColor('#e0e0e0'),
    'Mars':    colors.HexColor('#d32f2f'),
    'Mercury': colors.HexColor('#2e7d32'),
    'Jupiter': colors.HexColor('#f9a825'),
    'Venus':   colors.HexColor('#ec407a'),
    'Saturn':  colors.HexColor('#37474f'),
    'Rahu':    colors.HexColor('#4a148c'),
    'Ketu':    colors.HexColor('#795548'),
}

# Sign colors (element-based)
SIGN_COLORS = {
    'Aries':       colors.HexColor('#ffcdd2'),
    'Taurus':      colors.HexColor('#c8e6c9'),
    'Gemini':      colors.HexColor('#bbdefb'),
    'Cancer':      colors.HexColor('#e0f7fa'),
    'Leo':         colors.HexColor('#fff9c4'),
    'Virgo':       colors.HexColor('#dcedc8'),
    'Libra':       colors.HexColor('#f3e5f5'),
    'Scorpio':     colors.HexColor('#ffccbc'),
    'Sagittarius': colors.HexColor('#ffe0b2'),
    'Capricorn':   colors.HexColor('#d7ccc8'),
    'Aquarius':    colors.HexColor('#b2ebf2'),
    'Pisces':      colors.HexColor('#e1bee7'),
}

NAKSHATRA_COLORS = [
    colors.HexColor('#ef5350'), colors.HexColor('#ec407a'), colors.HexColor('#ab47bc'),
    colors.HexColor('#7e57c2'), colors.HexColor('#5c6bc0'), colors.HexColor('#42a5f5'),
    colors.HexColor('#29b6f6'), colors.HexColor('#26c6da'), colors.HexColor('#26a69a'),
    colors.HexColor('#66bb6a'), colors.HexColor('#9ccc65'), colors.HexColor('#d4e157'),
    colors.HexColor('#ffee58'), colors.HexColor('#ffca28'), colors.HexColor('#ffa726'),
    colors.HexColor('#ff7043'), colors.HexColor('#8d6e63'), colors.HexColor('#78909c'),
    colors.HexColor('#78909c'), colors.HexColor('#8d6e63'), colors.HexColor('#ff7043'),
    colors.HexColor('#ffa726'), colors.HexColor('#ffca28'), colors.HexColor('#ffee58'),
    colors.HexColor('#d4e157'), colors.HexColor('#9ccc65'), colors.HexColor('#66bb6a'),
]

ELEMENT_COLORS = {
    'Fire': FIRE_COLOR,
    'Earth': EARTH_COLOR,
    'Air': AIR_COLOR,
    'Water': WATER_COLOR,
}

ZODIAC_SIGNS = [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo',
    'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]


def _kv_block(data_dict, title=None):
    """Convert a dict to a key-value table."""
    rows = [(str(k).replace('_', ' ').title(), str(v)) for k, v in data_dict.items() if v is not None]
    if title:
        return [colored_heading(title, ACCENT, 11), Spacer(1, 4), make_left_table(rows)]
    return [make_left_table(rows)]

SIGN_LORDS = {
    'Aries': 'Mars','Taurus': 'Venus','Gemini': 'Mercury','Cancer': 'Moon',
    'Leo': 'Sun','Virgo': 'Mercury','Libra': 'Venus','Scorpio': 'Mars',
    'Sagittarius': 'Jupiter','Capricorn': 'Saturn','Aquarius': 'Saturn','Pisces': 'Jupiter'
}


PLANET_PROPS = {
    'Sun':     {'exalted':'Aries','debil':'Libra','own':['Leo'],'mool':'Leo','friends':['Moon','Mars','Jupiter'],'enemies':['Venus','Saturn']},
    'Moon':    {'exalted':'Taurus','debil':'Scorpio','own':['Cancer'],'mool':'Taurus','friends':['Sun','Mercury'],'enemies':[]},
    'Mars':    {'exalted':'Capricorn','debil':'Cancer','own':['Aries','Scorpio'],'mool':'Aries','friends':['Sun','Moon','Jupiter'],'enemies':['Mercury']},
    'Mercury': {'exalted':'Virgo','debil':'Pisces','own':['Gemini','Virgo'],'mool':'Virgo','friends':['Sun','Venus'],'enemies':['Moon','Mars']},
    'Jupiter': {'exalted':'Cancer','debil':'Capricorn','own':['Sagittarius','Pisces'],'mool':'Sagittarius','friends':['Sun','Moon','Mars'],'enemies':['Mercury','Venus']},
    'Venus':   {'exalted':'Pisces','debil':'Virgo','own':['Taurus','Libra'],'mool':'Libra','friends':['Mercury','Saturn'],'enemies':['Sun','Moon']},
    'Saturn':  {'exalted':'Libra','debil':'Aries','own':['Capricorn','Aquarius'],'mool':'Aquarius','friends':['Mercury','Venus'],'enemies':['Sun','Moon','Mars']},
}


def planet_status(name: str, sign: str) -> str:
    props = PLANET_PROPS.get(name)
    if not props:
        return 'Neutral'
    if props['exalted'] == sign:
        return 'Exalted'
    if props['debil'] == sign:
        return 'Debilitated'
    if sign in props['own']:
        return 'Own Sign'
    if props['mool'] == sign:
        return 'Mooltrikona'
    lord = SIGN_LORDS.get(sign, '')
    if lord in props.get('friends', []):
        return 'Friendly'
    if lord in props.get('enemies', []):
        return 'Enemy'
    return 'Neutral'

SIGN_ELEMENT = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water',
}

# ──────────────────────────── STYLES ────────────────────────────
def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=28, leading=34, textColor=PRIMARY,
        spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle', parent=styles['Normal'],
        fontSize=14, leading=18, textColor=MID_TEXT,
        spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', parent=styles['Heading1'],
        fontSize=16, leading=20, textColor=PRIMARY,
        spaceBefore=16, spaceAfter=8, fontName='Helvetica-Bold',
        borderWidth=0, borderColor=PRIMARY, borderPadding=4,
    ))
    styles.add(ParagraphStyle(
        'SubSection', parent=styles['Heading2'],
        fontSize=12, leading=15, textColor=ACCENT,
        spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['Normal'],
        fontSize=9, leading=12, textColor=DARK_TEXT,
        fontName='Helvetica', alignment=TA_JUSTIFY
    ))
    styles.add(ParagraphStyle(
        'SmallText', parent=styles['Normal'],
        fontSize=7.5, leading=10, textColor=MID_TEXT,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontSize=8, leading=10, textColor=colors.white,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontSize=8, leading=10, textColor=DARK_TEXT,
        fontName='Helvetica', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'TableCellLeft', parent=styles['Normal'],
        fontSize=8, leading=10, textColor=DARK_TEXT,
        fontName='Helvetica', alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=7, leading=9, textColor=LIGHT_TEXT,
        fontName='Helvetica', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'Disclaimer', parent=styles['Normal'],
        fontSize=8, leading=11, textColor=LIGHT_TEXT,
        fontName='Helvetica-Oblique', alignment=TA_JUSTIFY
    ))
    return styles


# ──────────────────────────── KUNDLI CHART DRAWING ────────────────────────────
def draw_south_indian_kundli(planets_by_sign: dict, asc_sign: str, size: float = 200) -> Drawing:
    """
    Draw a South Indian style Kundli chart.
    planets_by_sign: {'Aries': ['Mars','Rahu'], 'Leo': ['Sun'], ...}
    asc_sign: 'Leo'
    Returns a ReportLab Drawing object.
    """
    d = Drawing(size + 20, size + 20)

    cell = size / 4.0
    ox, oy = 10, 10  # offset

    # South Indian layout: signs are fixed positions
    # Row 0: Pisces(11), Aries(0), Taurus(1), Gemini(2)
    # Row 1: Aquarius(10), [center], [center], Cancer(3)
    # Row 2: Capricorn(9), [center], [center], Leo(4)
    # Row 3: Sagittarius(8), Scorpio(7), Libra(6), Virgo(5)
    layout = [
        [(11, 'Pisces'),    (0, 'Aries'),    (1, 'Taurus'),   (2, 'Gemini')],
        [(10, 'Aquarius'),  None,             None,             (3, 'Cancer')],
        [(9, 'Capricorn'),  None,             None,             (4, 'Leo')],
        [(8, 'Sagittarius'),(7, 'Scorpio'),  (6, 'Libra'),    (5, 'Virgo')],
    ]

    # Background
    d.add(Rect(ox, oy, size, size, fillColor=colors.white, strokeColor=PRIMARY, strokeWidth=2))

    # Draw cells
    for row in range(4):
        for col in range(4):
            cell_data = layout[row][col]
            if cell_data is None:
                continue  # center area

            sign_idx, sign_name = cell_data
            cx = ox + col * cell
            cy = oy + (3 - row) * cell  # flip y

            # Cell background
            bg = SIGN_COLORS.get(sign_name, colors.white)
            is_asc = sign_name == asc_sign
            d.add(Rect(cx, cy, cell, cell,
                       fillColor=bg if not is_asc else colors.HexColor('#fff176'),
                       strokeColor=PRIMARY, strokeWidth=0.5))

            # Ascendant marker
            if is_asc:
                d.add(String(cx + 2, cy + cell - 10, 'ASC',
                             fontSize=6, fillColor=FIRE_COLOR, fontName='Helvetica-Bold'))

            # Sign name (small, top-left)
            d.add(String(cx + 2, cy + 2, sign_name[:3].upper(),
                         fontSize=5.5, fillColor=LIGHT_TEXT, fontName='Helvetica'))

            # Planets in this sign
            planet_list = planets_by_sign.get(sign_name, [])
            if planet_list:
                py = cy + cell - 16 if is_asc else cy + cell - 10
                for pname in planet_list[:4]:  # max 4 per cell
                    symbol = _planet_symbol(pname)
                    pcol = PLANET_COLORS.get(pname, DARK_TEXT)
                    d.add(String(cx + cell / 2 - 3, py, symbol,
                                 fontSize=7, fillColor=pcol, fontName='Helvetica-Bold'))
                    py -= 9
            else:
                # Empty sign - draw dot
                d.add(Circle(cx + cell / 2, cy + cell / 2, 1,
                             fillColor=LIGHT_TEXT, strokeColor=None))

    # Border decoration
    d.add(Rect(ox - 2, oy - 2, size + 4, size + 4,
               fillColor=None, strokeColor=SECONDARY, strokeWidth=1.5))

    return d


def _planet_symbol(name: str) -> str:
    symbols = {
        'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma',
        'Mercury': 'Me', 'Jupiter': 'Ju', 'Venus': 'Ve',
        'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke',
        'Uranus': 'Ur', 'Neptune': 'Ne', 'Pluto': 'Pl',
    }
    return symbols.get(name, name[:2])


# ──────────────────────────── TABLE HELPERS ────────────────────────────
def make_table(headers, rows, col_widths=None, available_width=480):
    """Create a styled table with colored header."""
    if col_widths is None:
        n = len(headers)
        col_widths = [available_width / n] * n

    styles = get_styles()
    header_cells = [Paragraph(h, styles['TableHeader']) for h in headers]
    data = [header_cells]
    for row in rows:
        data.append([Paragraph(str(c), styles['TableCell']) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def make_left_table(headers_rows, col_widths=None, available_width=480):
    """Two-column key-value table. headers_rows = [('Key', 'Value'), ...]"""
    if col_widths is None:
        col_widths = [available_width * 0.4, available_width * 0.6]

    styles = get_styles()
    data = []
    for k, v in headers_rows:
        data.append([
            Paragraph(str(k), styles['TableCellLeft']),
            Paragraph(str(v), styles['TableCellLeft']),
        ])

    t = Table(data, colWidths=col_widths, repeatRows=0)
    style_cmds = [
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, CREAM]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


def colored_heading(text, color=PRIMARY, size=14):
    """Return a colored heading paragraph."""
    styles = get_styles()
    return Paragraph(f'<font color="{color.hexval()}">{text}</font>',
                     ParagraphStyle('colored_h', parent=styles['SectionTitle'],
                                    textColor=color, fontSize=size))


def section_divider():
    return HRFlowable(width="100%", thickness=1, color=SECONDARY,
                      spaceBefore=8, spaceAfter=8)


# ──────────────────────────── PAGE TEMPLATES ────────────────────────────
def cover_page_drawing(client_name: str, report_title: str, birth_date: str,
                       birth_time: str, location: str, logo_path: str = None,
                       brand_name: str = None, contact_mobile: str = None,
                       contact_email: str = None, contact_website: str = None) -> list:
    """Build cover page flowables with branding."""
    styles = get_styles()
    elements = []

    elements.append(Spacer(1, 60))

    # Decorative top bar
    d = Drawing(480, 6)
    d.add(Rect(0, 0, 480, 6, fillColor=PRIMARY, strokeColor=None))
    d.add(Rect(0, 0, 160, 6, fillColor=SECONDARY, strokeColor=None))
    d.add(Rect(320, 0, 160, 6, fillColor=ACCENT, strokeColor=None))
    elements.append(d)
    elements.append(Spacer(1, 10))

    # Floral corner decorations
    # Floral corner decorations
    fc = Drawing(480, 480)
    # Top-left
    fc.add(Rect(24, 444, 60, 2, fillColor=PRIMARY, strokeColor=None))
    fc.add(Rect(24, 444, 2, 60, fillColor=PRIMARY, strokeColor=None))
    fc.add(String(30, 450, '\u273D', fontSize=18, fillColor=PRIMARY, fontName='Helvetica'))
    fc.add(String(78, 430, '\u2740', fontSize=14, fillColor=ACCENT, fontName='Helvetica'))
    # Top-right
    fc.add(Rect(396, 444, 60, 2, fillColor=PRIMARY, strokeColor=None))
    fc.add(Rect(478, 444, 2, 60, fillColor=PRIMARY, strokeColor=None))
    fc.add(String(440, 450, '\u273D', fontSize=18, fillColor=PRIMARY, fontName='Helvetica'))
    fc.add(String(392, 430, '\u2740', fontSize=14, fillColor=ACCENT, fontName='Helvetica'))
    # Bottom-left
    fc.add(Rect(24, 14, 60, 2, fillColor=SECONDARY, strokeColor=None))
    fc.add(Rect(24, 14, 2, 60, fillColor=SECONDARY, strokeColor=None))
    fc.add(String(30, 20, '\u273D', fontSize=18, fillColor=SECONDARY, fontName='Helvetica'))
    fc.add(String(78, 40, '\u2740', fontSize=14, fillColor=ACCENT, fontName='Helvetica'))
    # Bottom-right
    fc.add(Rect(396, 14, 60, 2, fillColor=SECONDARY, strokeColor=None))
    fc.add(Rect(478, 14, 2, 16, fillColor=SECONDARY, strokeColor=None))
    fc.add(String(440, 20, '\u273D', fontSize=18, fillColor=SECONDARY, fontName='Helvetica'))
    fc.add(String(392, 40, '\u2740', fontSize=14, fillColor=ACCENT, fontName='Helvetica'))

    elements.append(fc)
    elements.append(Spacer(1, 20))

    # Decorative floral border bar
    fb = Drawing(480, 14)
    fb.add(Rect(0, 6, 480, 1, fillColor=PRIMARY, strokeColor=None))
    fb.add(String(224, 0, '\u2748 \u273F \u2748', fontSize=12, fillColor=PRIMARY, fontName='Helvetica'))
    elements.append(fb)
    elements.append(Spacer(1, 20))

    # Ganesha icon
    g = Drawing(480, 120)

    # Golden aura
    g.add(Circle(240, 60, 50, fillColor=colors.HexColor('#FFF8E1'), strokeColor=colors.HexColor('#FFD54F'), strokeWidth=1))
    # Head
    g.add(Circle(240, 65, 22, fillColor=PRIMARY, strokeColor=SECONDARY, strokeWidth=1.5))
    # Left ear
    g.add(Ellipse(214, 66, 14, 22, fillColor=PRIMARY, strokeColor=SECONDARY, strokeWidth=1))
    # Right ear
    g.add(Ellipse(266, 66, 14, 22, fillColor=PRIMARY, strokeColor=SECONDARY, strokeWidth=1))
    # Crown
    g.add(Path().moveTo(231, 43).lineTo(240, 30).lineTo(249, 43).close().moveTo(235, 45).lineTo(240, 35).lineTo(245, 45).close())
    g.add(Circle(240, 28, 3, fillColor=colors.red, strokeColor=None))
    # Eyes
    g.add(Circle(233, 62, 2.5, fillColor=rl_colors.white, strokeColor=None))
    g.add(Circle(247, 62, 2.5, fillColor=rl_colors.white, strokeColor=None))
    # Trunk
    g.add(Path().moveTo(253, 68).curveTo(265, 85, 255, 105, 240, 100).curveTo(235, 98, 238, 95, 240, 97))
    # Body
    g.add(Ellipse(240, 110, 24, 16, fillColor=SECONDARY, strokeColor=colors.HexColor('#E65100'), strokeWidth=1))
    # Blessing hand
    g.add(Path().moveTo(214, 105).curveTo(200, 95, 198, 85, 205, 82))
    # Hand with modak
    g.add(Path().moveTo(266, 105).curveTo(278, 112, 272, 125, 265, 120))
    g.add(Circle(268, 123, 6, fillColor=colors.HexColor('#FFD54F'), strokeColor=colors.HexColor('#F9A825'), strokeWidth=1))

    elements.append(g)
    elements.append(Spacer(1, 6))

    # Brand name (if different from client name)
    if brand_name:
        elements.append(Paragraph(brand_name.upper(), ParagraphStyle(
            'brand_title', parent=styles['CoverSubtitle'],
            fontSize=12, textColor=SECONDARY, fontName='Helvetica-Bold'
        )))
        elements.append(Spacer(1, 8))

    elements.append(Paragraph(client_name.upper(), styles['CoverTitle']))
    elements.append(Spacer(1, 6))

    # Decorative line
    d3 = Drawing(480, 4)
    d3.add(Rect(140, 0, 200, 2, fillColor=SECONDARY, strokeColor=None))
    elements.append(d3)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(report_title, ParagraphStyle(
        'cover_report', parent=styles['CoverSubtitle'],
        fontSize=20, textColor=ACCENT, fontName='Helvetica-Bold'
    )))
    elements.append(Spacer(1, 30))

    # Birth details box
    detail_data = [
        [Paragraph('<b>Date of Birth</b>', styles['TableCell']),
         Paragraph(birth_date, styles['TableCell'])],
        [Paragraph('<b>Time of Birth</b>', styles['TableCell']),
         Paragraph(birth_time, styles['TableCell'])],
        [Paragraph('<b>Place</b>', styles['TableCell']),
         Paragraph(location, styles['TableCell'])],
    ]
    detail_table = Table(detail_data, colWidths=[140, 200])
    detail_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, SECONDARY),
        ('BACKGROUND', (0, 0), (0, -1), CREAM),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 30))

    # Contact details box
    contact_rows = []
    if contact_mobile:
        contact_rows.append(('Mobile', contact_mobile))
    if contact_email:
        contact_rows.append(('Email', contact_email))
    if contact_website:
        contact_rows.append(('Website', contact_website))
    if contact_rows:
        contact_data = [[Paragraph(f'<b>{k}</b>', styles['TableCell']),
                         Paragraph(v, styles['TableCell'])] for k, v in contact_rows]
        contact_table = Table(contact_data, colWidths=[140, 200])
        contact_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, ACCENT),
            ('BACKGROUND', (0, 0), (0, -1), CREAM),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(contact_table)
        elements.append(Spacer(1, 20))

    # Footer of cover
    elements.append(Paragraph(
        f'Generated by {brand_name or "AstroVakta"} Vedic Astrology Engine',
        styles['SmallText']
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f'Report Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        styles['SmallText']
    ))

    elements.append(PageBreak())
    return elements


def back_page_elements(disclaimer_text: str = None, brand_name: str = None,
                       contact_mobile: str = None, contact_email: str = None,
                       contact_website: str = None) -> list:
    """Build back page with disclaimer and contact info."""
    styles = get_styles()
    elements = []

    elements.append(Spacer(1, 40))
    elements.append(section_divider())

    elements.append(colored_heading('Disclaimer', SECONDARY, 14))
    elements.append(Spacer(1, 8))

    default_disclaimer = (
        "This report is generated based on Vedic astrological principles and the birth data provided. "
        "Astrology is an interpretive art and science; the predictions and recommendations herein are "
        "guidelines based on classical texts. Individual results may vary based on karma, free will, "
        "and environmental factors. This report should not be used as a substitute for professional "
        "medical, legal, financial, or psychological advice. Consult qualified professionals for "
        "decisions in those areas. The remedies suggested are traditional and optional — follow them "
        "only if they resonate with your beliefs."
    )
    elements.append(Paragraph(disclaimer_text or default_disclaimer, styles['Disclaimer']))
    elements.append(Spacer(1, 20))

    # Contact info box
    contact_rows = []
    if contact_mobile:
        contact_rows.append(('Mobile', contact_mobile))
    if contact_email:
        contact_rows.append(('Email', contact_email))
    if contact_website:
        contact_rows.append(('Website', contact_website))
    if brand_name:
        contact_rows.insert(0, ('Provider', brand_name))

    if contact_rows:
        elements.append(colored_heading('Contact Information', ACCENT, 11))
        elements.append(Spacer(1, 6))
        elements.extend(_kv_block(dict(contact_rows)))
        elements.append(Spacer(1, 20))

    # Bottom decorative bar
    d = Drawing(480, 6)
    d.add(Rect(0, 0, 480, 6, fillColor=PRIMARY, strokeColor=None))
    d.add(Rect(0, 0, 160, 6, fillColor=SECONDARY, strokeColor=None))
    d.add(Rect(320, 0, 160, 6, fillColor=ACCENT, strokeColor=None))
    elements.append(d)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f'{brand_name or "AstroVakta"} — Vedic Astrology Platform', styles['Footer']))
    if contact_website:
        elements.append(Paragraph(contact_website, styles['Footer']))
    elif contact_email:
        elements.append(Paragraph(contact_email, styles['Footer']))

    return elements


# ──────────────────────────── WATERMARK ────────────────────────────
def draw_watermark(canvas, doc, watermark_text: str = None,
                   watermark_image_path: str = None, watermark_opacity: float = 0.08):
    """Draw diagonal text or image watermark on every page (light, non-destructive)."""
    if not watermark_text and not watermark_image_path:
        return
    canvas.saveState()
    w, h = A4
    if watermark_text:
        canvas.setFont('Helvetica-Bold', 52)
        canvas.setFillColor(colors.Color(0.5, 0.5, 0.5, alpha=watermark_opacity))
        canvas.saveState()
        canvas.translate(w / 2, h / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, watermark_text)
        canvas.restoreState()
    if watermark_image_path and os.path.exists(watermark_image_path):
        try:
            from reportlab.lib.utils import ImageReader
            img_r = ImageReader(watermark_image_path)
            iw, ih = img_r.getSize()
            max_w, max_h = w * 0.35, h * 0.35
            scale = min(max_w / iw, max_h / ih)
            dw, dh = iw * scale, ih * scale
            canvas.setFillAlpha(watermark_opacity)
            canvas.drawImage(watermark_image_path, (w - dw) / 2, (h - dh) / 2,
                             dw, dh, mask='auto')
            canvas.setFillAlpha(1.0)
        except Exception as e:
            logger.warning(f"Watermark image draw failed: {e}")
    canvas.restoreState()


# ──────────────────────────── HEADER / FOOTER ────────────────────────────
def header_footer(canvas, doc, client_name: str = '', report_type: str = '',
                   brand_name: str = None, contact_website: str = None,
                   watermark_text: str = None, watermark_image_path: str = None,
                   watermark_opacity: float = 0.08):
    """Draw header, footer, and optional watermark on each page."""
    canvas.saveState()
    w, h = A4

    # Header line
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(30, h - 40, w - 30, h - 40)

    # Header text
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(PRIMARY)
    canvas.drawString(30, h - 35, f'{brand_name or client_name}' if brand_name or client_name else 'AstroVakta Report')
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(LIGHT_TEXT)
    canvas.drawRightString(w - 30, h - 35, report_type)

    # Saffron accent bar
    canvas.setStrokeColor(SECONDARY)
    canvas.setLineWidth(0.5)
    canvas.line(30, h - 42, w - 30, h - 42)

    # Footer
    canvas.setStrokeColor(PRIMARY)
    canvas.setLineWidth(0.5)
    canvas.line(30, 35, w - 30, 35)

    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(LIGHT_TEXT)
    canvas.drawString(30, 22, f'{brand_name or "AstroVakta"} Vedic Astrology')
    canvas.drawCentredString(w / 2, 22, f'Page {doc.page}')
    canvas.drawRightString(w - 30, 22, contact_website or 'Confidential')

    canvas.restoreState()

    # Watermark on top
    draw_watermark(canvas, doc, watermark_text, watermark_image_path, watermark_opacity)


# ──────────────────────────── SVG TO IMAGE ────────────────────────────
def svg_to_image_flowable(svg_string: str, width: float = 200, height: float = 150):
    """Convert an SVG string to a ReportLab Image flowable using cairosvg."""
    import os as _os

    # macOS-only: ensure cairo can find Homebrew's libcairo
    if sys.platform == 'darwin':
        _old_dyld = _os.environ.get('DYLD_LIBRARY_PATH', '')
        if '/opt/homebrew/lib' not in _old_dyld:
            _os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib' + (f':{_old_dyld}' if _old_dyld else '')
    try:
        import importlib
        # Remove cached cairo modules so they re-import with the new env var
        for mod_name in list(sys.modules.keys()):
            if 'cairo' in mod_name.lower():
                del sys.modules[mod_name]

        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_string.encode('utf-8'),
                                     output_width=int(width * 2),
                                     output_height=int(height * 2))
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(png_data))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Image(buf, width=width, height=height)
    except Exception as e:
        logger.warning(f"SVG-to-image conversion failed: {e}")
        return Spacer(1, 1)
    finally:
        if sys.platform == 'darwin' and _old_dyld:
            _os.environ['DYLD_LIBRARY_PATH'] = _old_dyld
        elif 'DYLD_LIBRARY_PATH' in _os.environ:
            del _os.environ['DYLD_LIBRARY_PATH']


def make_dual_chart_table(chart1_flowable, chart2_flowable,
                          label1: str = '', label2: str = '',
                          chart_width: float = 220, available_width: float = 480) -> Table:
    """Place two chart flowables side-by-side with labels."""
    styles = get_styles()
    data = [[
        Paragraph(f'<b>{label1}</b>', styles['TableHeader']),
        Paragraph(f'<b>{label2}</b>', styles['TableHeader']),
    ], [
        chart1_flowable,
        chart2_flowable,
    ]]
    col_w = available_width / 2
    t = Table(data, colWidths=[col_w, col_w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t
