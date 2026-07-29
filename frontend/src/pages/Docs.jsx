import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, ChevronDown, Copy, BookOpen, Search, Zap, Shield, FileText, Image, Brain, Calendar, Heart, Star, MapPin, Calculator, Gem, Home, Clock, Activity, Sun, Wrench } from 'lucide-react'
import toast from 'react-hot-toast'

const B = '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}'
const COM = '{"maleDateOfBirth":"1990-05-15","maleTimeOfBirth":"10:30","maleLatitude":28.6139,"maleLongitude":77.209,"maleTimezone":"Asia/Kolkata","femaleDateOfBirth":"1992-03-20","femaleTimeOfBirth":"14:30","femaleLatitude":19.076,"femaleLongitude":72.8777,"femaleTimezone":"Asia/Kolkata"}'

const categories = [
  {
    id: 'quickstart', label: 'Quick Start', icon: Zap,
    sections: [
      {
        title: 'Base URL & Authentication',
        content: `**Base URL:** \`http://localhost:5000\` (or your deployed URL)

All protected endpoints require an \`X-API-Key\` header:

\`\`\`
X-API-Key: avk_your_api_key_here
\`\`\`

**Get your API key:**
1. Register: \`POST /auth/register\`
2. Login: \`POST /auth/login\` → get JWT token
3. Create API key: \`POST /auth/keys\` (with JWT in Authorization header)

**Rate Limits:** 100 req/day (Free) | 1,000 (Starter) | 10,000 (Pro) | Unlimited (Enterprise)

Rate limit headers are included in every response:
\`\`\`
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9987
X-RateLimit-Tier: pro
X-Response-Time: 0.142s
\`\`\`

**Error Format:**
\`\`\`json
{ "detail": "Missing X-API-Key header" }
\`\`\`

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Missing/invalid API key |
| 402 | Rate limit exceeded |
| 404 | Endpoint not found |
| 500 | Server error |`,
      },
      {
        title: 'First API Call',
        content: `**Get a complete birth chart (Kundli):**

\`\`\`bash
curl -X POST http://localhost:5000/api/kundli \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: avk_your_key" \\
  -d '${B}'
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "data": {
    "basicDetails": { "dateOfBirth": "1990-05-15", "ascendant": "Cancer", ... },
    "planets": [
      { "name": "Sun", "sign": "Taurus", "house": 1, "degreeDMS": "0°23'19\"", ... },
      { "name": "Moon", "sign": "Sagittarius", "house": 8, ... }
    ],
    "houses": [ { "number": 1, "sign": "Cancer", "planets": [] } ],
    "yogas": [ { "name": "Gajakesari Yoga", ... } ],
    "doshas": [ { "name": "Manglik Dosha", "present": false } ]
  }
}
\`\`\``,
      },
      {
        title: 'JavaScript / Node.js',
        content: `\`\`\`javascript
const axios = require('axios');

const API_KEY = 'avk_your_key_here';
const BASE = 'http://localhost:5000';

// Get birth chart
async function getBirthChart(dob, tob, lat, lon, tz) {
  const { data } = await axios.post(\`\${BASE}/api/kundli\`, {
    dateOfBirth: dob, timeOfBirth: tob,
    latitude: lat, longitude: lon, timezone: tz
  }, { headers: { 'X-API-Key': API_KEY } });
  return data;
}

// Generate PDF report
async function generatePDF(birthData, options = {}) {
  const { data } = await axios.post(\`\${BASE}/reports/full-pdf\`, {
    ...birthData,
    clientName: options.clientName,
    brandName: options.brandName,
    sections: options.sections,
    watermarkText: options.watermark,
    watermarkOpacity: 0.06,
  }, {
    headers: { 'X-API-Key': API_KEY },
    responseType: 'blob'
  });
  return data;
}

// Get SVG chart
async function getChartSVG(dob, tob, lat, lon, tz) {
  const { data } = await axios.post(\`\${BASE}/chart/svg\`, {
    dateOfBirth: dob, timeOfBirth: tob,
    latitude: lat, longitude: lon, timezone: tz,
    theme: 'dark'
  }, { headers: { 'X-API-Key': API_KEY } });
  return data; // Raw SVG string
}

// Usage
const chart = await getBirthChart('1990-05-15', '10:30', 28.6139, 77.209, 'Asia/Kolkata');
console.log(chart.data.planets);
\`\`\``,
      },
      {
        title: 'Python',
        content: `\`\`\`python
import requests

API_KEY = 'avk_your_key_here'
BASE = 'http://localhost:5000'

def get_birth_chart(dob, tob, lat, lon, tz):
    resp = requests.post(f'{BASE}/api/kundli', json={
        'dateOfBirth': dob, 'timeOfBirth': tob,
        'latitude': lat, 'longitude': lon, 'timezone': tz
    }, headers={'X-API-Key': API_KEY})
    return resp.json()

def generate_pdf(birth_data, sections=None, watermark=None):
    payload = {**birth_data}
    if sections:
        payload['sections'] = sections
    if watermark:
        payload['watermarkText'] = watermark
        payload['watermarkOpacity'] = 0.06
    resp = requests.post(f'{BASE}/reports/full-pdf', json=payload,
                         headers={'X-API-Key': API_KEY})
    return resp.content  # PDF bytes

# Usage
chart = get_birth_chart('1990-05-15', '10:30', 28.6139, 77.209, 'Asia/Kolkata')
pdf = generate_pdf(chart, sections=['birth_details','kundli_chart','career'],
                   watermark='CONFIDENTIAL')
with open('report.pdf', 'wb') as f:
    f.write(pdf)
\`\`\``,
      },
    ],
  },
  {
    id: 'pdf', label: 'PDF Reports', icon: FileText,
    endpoints: [
      { method: 'POST', path: '/reports/full-pdf', desc: 'Generate full customizable PDF report', body: B, response: '(Binary PDF file — Content-Type: application/pdf)' },
      { method: 'POST', path: '/reports/pdf-info', desc: 'Get PDF report info & available sections', body: B, response: '{"success":true,"data":{"sections":["Birth Details","Kundli Chart",...],"totalSections":23,"availableSections":{...},"brandingOptions":{...},"watermarkOptions":{...}}}' },
      { method: 'POST', path: '/reports/birth-chart', desc: 'Birth chart text report', body: B },
      { method: 'POST', path: '/reports/predictions', desc: 'Predictions text report', body: B },
      { method: 'POST', path: '/reports/career', desc: 'Career text report', body: B },
      { method: 'POST', path: '/reports/comprehensive', desc: 'Comprehensive text report', body: B },
    ],
    sections: [
      {
        title: 'PDF Customization',
        content: `The \`/reports/full-pdf\` endpoint supports full customization:

\`\`\`json
{
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata",

  "clientName": "Rahul Sharma",
  "reportTitle": "Personalized Birth Chart Report",
  "brandName": "My Astrology Platform",
  "logoUrl": "/path/to/logo.png",
  "contactMobile": "+91 98765 43210",
  "contactEmail": "support@myastrology.com",
  "contactWebsite": "www.myastrology.com",

  "sections": ["birth_details","kundli_chart","navamsa_chart","career","finance"],
  "watermarkText": "CONFIDENTIAL",
  "watermarkOpacity": 0.06
}
\`\`\``,
      },
      {
        title: 'Available Sections',
        content: `Include only the sections you need in the \`sections\` array:

| Key | Section |
|-----|---------|
| \`birth_details\` | Birth date, time, place, ayanamsa |
| \`kundli_chart\` | North Indian Diamond Rasi chart (D1) |
| \`navamsa_chart\` | Navamsa chart (D9) |
| \`hora_chart\` | Hora wealth chart (D2) |
| \`planet_positions\` | Full planet position table |
| \`houses\` | House (Bhava) analysis |
| \`nakshatras\` | Nakshatra analysis |
| \`dasha\` | Vimshottari dasha timeline |
| \`yogas\` | Yoga detection & analysis |
| \`doshas\` | Dosha detection (Manglik, Kaal Sarp, etc.) |
| \`planet_strengths\` | Planet strength analysis |
| \`career\` | Career & profession predictions |
| \`finance\` | Finance & wealth predictions |
| \`health\` | Health predictions |
| \`love\` | Love & marriage predictions |
| \`education\` | Education predictions |
| \`family\` | Family life predictions |
| \`travel\` | Travel & foreign settlement |
| \`ai_predictions\` | AI-generated life predictions |
| \`major_charts\` | All divisional chart SVGs (D1-D60) |
| \`gemstones\` | Gemstone recommendations |
| \`remedies\` | Remedies & spiritual guidance |
| \`lucky\` | Lucky attributes (color, number, day, metal) |

\`null\` or omit = all 23 sections included.`,
      },
      {
        title: 'Watermark & Branding',
        content: `**Watermark Options:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| \`watermarkText\` | string | null | Diagonal 45° text on every page |
| \`watermarkImageUrl\` | string | null | Image overlay on every page |
| \`watermarkOpacity\` | float | 0.08 | Opacity 0.0-0.3 (very light) |

**Branding Options:**

| Field | Type | Description |
|-------|------|-------------|
| \`logoUrl\` | string | Logo image on cover page |
| \`brandName\` | string | Brand name in header/footer on every page |
| \`clientName\` | string | Client name on cover page |
| \`reportTitle\` | string | Report title on cover page |
| \`contactMobile\` | string | Contact phone on cover/back page |
| \`contactEmail\` | string | Contact email |
| \`contactWebsite\` | string | Website URL in header/footer |

**Example with watermark:**
\`\`\`bash
curl -X POST http://localhost:5000/reports/full-pdf \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: avk_your_key" \\
  -d '${B.replace('{', '{\"clientName\":\"Client\",\"watermarkText\":\"DRAFT\",\"watermarkOpacity\":0.06,')}
' -o report.pdf
\`\`\``,
      },
    ],
  },
  {
    id: 'charts', label: 'Charts (Kundli)', icon: Image,
    endpoints: [
      { method: 'POST', path: '/api/kundli', desc: 'Full birth chart (planets, houses, yogas, doshas)', body: B },
      { method: 'POST', path: '/chart/svg', desc: 'North Indian Diamond SVG chart', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/grid-svg', desc: 'Grid/Box chart SVG', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/east-svg', desc: 'East Indian chart SVG', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/moon-svg', desc: 'Moon-centered chart SVG', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/navamsa-svg', desc: 'Navamsa (D9) chart SVG', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/hora-svg', desc: 'Hora (D2) wealth chart SVG', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/sudarshana-svg', desc: 'Sudarshana Chakra SVG', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' },
      { method: 'POST', path: '/chart/divisional-svg?d=9', desc: 'Any divisional chart D1-D60 (append ?d=N)', body: '{"name":"D9","dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"light"}' },
      { method: 'POST', path: '/horoscope/planet-details', desc: 'Detailed planet positions & attributes', body: B },
    ],
    sections: [
      {
        title: 'Tropical Zodiac Support',
        content: `The \`/api/kundli\` endpoint accepts an optional \`tropical\` parameter (default: \`false\`).

| Value | Zodiac System |
|-------|--------------|
| \`false\` | Sidereal (default — Vedic/Lahiri ayanamsa) |
| \`true\` | Tropical (Western-style, no ayanamsa correction) |

\`\`\`json
{
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata",
  "tropical": true
}
\`\`\`

When \`tropical: true\`, both planet positions and house cusps are computed in the tropical zodiac.`,
      },
      {
        title: 'Divisional Charts (Vargas)',
        content: `The \`/chart/divisional-svg\` endpoint supports all 18 divisional charts (D1–D60), now fully computed. Pass \`?d=N\` as query parameter.

**Common vargas:**

| Param | Name | Focus |
|-------|------|-------|
| \`?d=1\` | Rasi | General life |
| \`?d=2\` | Hora | Wealth |
| \`?d=3\` | Drekkana | Siblings |
| \`?d=7\` | Saptamsa | Children |
| \`?d=9\` | Navamsa | Marriage/Dharma |
| \`?d=10\` | Dashamamsa | Career |
| \`?d=12\` | Dwadasamsa | Parents |
| \`?d=16\` | Shodasamsa | Vehicles/Comforts |
| \`?d=20\` | Vimsamsa | Spirituality |
| \`?d=24\` | Siddhamsa | Education |
| \`?d=27\` | Nakshatramsa | Strength |
| \`?d=30\` | Trimshamsa | Mishaps |
| \`?d=40\` | Khavedamsa | Purva Punya |
| \`?d=45\` | Akshavedamsa | Character |
| \`?d=60\` | Shashtiamsa | Past Life |

\`\`\`bash
# Get Navamsa chart
curl -X POST "http://localhost:5000/chart/divisional-svg?d=9" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: avk_your_key" \\
  -d '${B}' > navamsa.svg
\`\`\`

SVG charts are returned as \`Content-Type: image/svg+xml\` and can be embedded directly in web pages.`,
      },
    ],
  },
  {
    id: 'horoscope', label: 'Horoscope', icon: Star,
    endpoints: [
      { method: 'POST', path: '/horoscope/daily', desc: 'Daily horoscope predictions', body: B },
      { method: 'POST', path: '/horoscope/weekly', desc: 'Weekly horoscope', body: B },
      { method: 'POST', path: '/horoscope/monthly', desc: 'Monthly horoscope', body: B },
      { method: 'POST', path: '/horoscope/yearly', desc: 'Yearly horoscope', body: B },
      { method: 'POST', path: '/horoscope/career', desc: 'Career horoscope', body: B },
      { method: 'POST', path: '/horoscope/love', desc: 'Love horoscope', body: B },
      { method: 'POST', path: '/horoscope/finance', desc: 'Finance horoscope', body: B },
      { method: 'POST', path: '/horoscope/health', desc: 'Health horoscope', body: B },
      { method: 'POST', path: '/horoscope/business', desc: 'Business predictions', body: B },
      { method: 'POST', path: '/horoscope/education', desc: 'Education predictions', body: B },
      { method: 'POST', path: '/horoscope/child', desc: 'Child predictions', body: B },
      { method: 'POST', path: '/horoscope/foreign', desc: 'Foreign travel/settlement', body: B },
    ],
  },
  {
    id: 'dasha', label: 'Dasha (Planetary Periods)', icon: Calendar,
    endpoints: [
      { method: 'POST', path: '/horoscope/dasha/vimshottari', desc: 'Full Vimshottari dasha timeline', body: B },
      { method: 'POST', path: '/horoscope/dasha/current', desc: 'Currently active dasha/bhukti', body: B },
      { method: 'POST', path: '/horoscope/dasha/details', desc: 'Dasha details for a specific planet', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","planet":"Jupiter"}' },
      { method: 'POST', path: '/horoscope/dasha/timeline', desc: 'Dasha timeline for year range', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","startYear":2024,"endYear":2030}' },
      { method: 'POST', path: '/horoscope/dasha/chara', desc: 'Jaimini Chara dasha', body: B },
      { method: 'POST', path: '/dasha/yogini', desc: 'Yogini dasha', body: B },
      { method: 'POST', path: '/dasha/kalachakra', desc: 'Kalachakra dasha', body: B },
      { method: 'POST', path: '/dasha/ashtottari', desc: 'Ashtottari dasha', body: B },
    ],
  },
  {
    id: 'compatibility', label: 'Compatibility', icon: Heart,
    endpoints: [
      { method: 'POST', path: '/horoscope/compat', desc: 'Ashtakoot gun milan (36-point matching)', body: COM },
      { method: 'POST', path: '/horoscope/compat/detailed', desc: 'Detailed compatibility report', body: COM },
      { method: 'POST', path: '/api/compat/gun-milan', desc: 'Gun milan score', body: COM },
      { method: 'POST', path: '/api/compat/nadi', desc: 'Nadi dosha check', body: COM },
      { method: 'POST', path: '/api/compat/bhakoot', desc: 'Bhakoot check', body: COM },
      { method: 'POST', path: '/api/compat/yoni', desc: 'Yoni match', body: COM },
      { method: 'POST', path: '/api/compat/gana', desc: 'Gana match', body: COM },
      { method: 'POST', path: '/api/compat/tara', desc: 'Tara match', body: COM },
    ],
    sections: [
      {
        title: 'Compatibility Request Body',
        content: `Compatibility endpoints use male/female birth data:

\`\`\`json
${COM.split('').map((c, i) => i < 500 ? c : '').join('')}
\`\`\``,
      },
    ],
  },
  {
    id: 'dosha', label: 'Dosha Analysis', icon: Shield,
    endpoints: [
      { method: 'POST', path: '/horoscope/dosha/compute', desc: 'Detect all doshas', body: B },
      { method: 'POST', path: '/horoscope/dosha/severity', desc: 'Dosha severity assessment', body: B },
      { method: 'POST', path: '/horoscope/dosha/remedies', desc: 'Remedies for doshas', body: B },
      { method: 'POST', path: '/horoscope/dosha/compatibility-impact', desc: 'Dosha impact on compatibility', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","partnerDateOfBirth":"1992-03-20","partnerTimeOfBirth":"14:30","partnerLatitude":19.076,"partnerLongitude":72.8777,"partnerTimezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/dosha/dhaiya', desc: 'Dhaiya & Sade Sati analysis', body: B },
      { method: 'POST', path: '/api/dosha/grahan', desc: 'Grahan dosha', body: B },
      { method: 'POST', path: '/api/dosha/shrapit', desc: 'Shrapit dosha', body: B },
      { method: 'POST', path: '/api/dosha/manglik-detailed', desc: 'Detailed Manglik analysis', body: B },
      { method: 'POST', path: '/api/dosha/nadi-dosha', desc: 'Nadi dosha', body: COM },
      { method: 'POST', path: '/api/dosha/bhakoot-dosha', desc: 'Bhakoot dosha', body: COM },
      { method: 'POST', path: '/api/dosha/yoni-compatibility', desc: 'Yoni compatibility', body: COM },
      { method: 'POST', path: '/yogini/dosha', desc: 'Yogini dosha analysis', body: B },
    ],
  },
  {
    id: 'transit', label: 'Transit (Gochar)', icon: Zap,
    endpoints: [
      { method: 'POST', path: '/horoscope/transit', desc: 'Full transit analysis', body: B },
      { method: 'POST', path: '/horoscope/transit/current', desc: 'Current transit positions', body: B },
      { method: 'POST', path: '/horoscope/transit/prediction', desc: 'Transit predictions', body: B },
      { method: 'POST', path: '/horoscope/transit/by-planet', desc: 'Single planet transit', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","planet":"Jupiter"}' },
      { method: 'POST', path: '/horoscope/transit/monthly', desc: 'Monthly transit report', body: B },
      { method: 'POST', path: '/horoscope/transit/timing', desc: 'Transit timing for events', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","event":"marriage"}' },
      { method: 'POST', path: '/api/transit/planet-transit', desc: 'Single planet transit detail', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","planetName":"Jupiter"}' },
      { method: 'POST', path: '/api/transit/retrograde', desc: 'Currently retrograde planets', body: B },
      { method: 'POST', path: '/api/transit/combust', desc: 'Currently combust planets', body: B },
      { method: 'POST', path: '/api/transit/exalted', desc: 'Exalted planets', body: B },
      { method: 'POST', path: '/api/transit/debilitated', desc: 'Debilitated planets', body: B },
      { method: 'POST', path: '/api/transit/aspect', desc: 'Transit aspects', body: B },
    ],
  },
  {
    id: 'panchang', label: 'Panchang & Calendar', icon: Calendar,
    endpoints: [
      { method: 'POST', path: '/horoscope/panchang', desc: 'Full panchang (Tithi, Nakshatra, Yoga, Karana)', body: B },
      { method: 'POST', path: '/horoscope/panchang/rahu-kaal', desc: 'Rahu Kaal', body: B },
      { method: 'POST', path: '/horoscope/panchang/gulika-kaal', desc: 'Gulika Kaal', body: B },
      { method: 'POST', path: '/horoscope/panchang/yamaganda', desc: 'Yamaganda', body: B },
      { method: 'POST', path: '/horoscope/panchang/choghadiya', desc: 'Choghadiya', body: B },
      { method: 'POST', path: '/horoscope/panchang/hora', desc: 'Hora', body: B },
      { method: 'POST', path: '/horoscope/panchang/moonrise', desc: 'Moonrise time', body: B },
      { method: 'POST', path: '/horoscope/panchang/moonset', desc: 'Moonset time', body: B },
      { method: 'POST', path: '/horoscope/panchang/panchaka', desc: 'Panchaka analysis', body: B },
      { method: 'POST', path: '/horoscope/panchang/abhijit-muhurat', desc: 'Abhijit muhurat time', body: B },
      { method: 'POST', path: '/horoscope/panchang/gulika-position', desc: 'Gulika position', body: B },
      { method: 'POST', path: '/horoscope/panchang/roga-nidana', desc: 'Roga nidana analysis', body: B },
      { method: 'POST', path: '/api/calendar/hindu', desc: 'Hindu calendar for month', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/calendar/panchang', desc: 'Calendar with panchang', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/calendar/festival', desc: 'Calendar with festivals', body: '{"year":2026}' },
      { method: 'POST', path: '/api/calendar/muhurat', desc: 'Calendar with muhurat', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/calendar-api/hindu', desc: 'Calendar API - hindu calendar', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/calendar-api/panchang', desc: 'Calendar API - panchang', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/calendar-api/festival', desc: 'Calendar API - festivals', body: '{"year":2026}' },
      { method: 'POST', path: '/calendar-api/muhurat', desc: 'Calendar API - muhurat', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/calendar/year', desc: 'Yearly calendar overview', body: '{"year":2026,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/calendar/year/monthly-summary', desc: 'Monthly summary for a year', body: '{"year":2026,"month":7,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/calendar/year/auspicious-dates', desc: 'Auspicious dates for the year', body: '{"year":2026,"latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","purpose":"marriage"}' },
    ],
  },
  {
    id: 'ai', label: 'AI-Powered', icon: Brain,
    endpoints: [
      { method: 'POST', path: '/ai/chat', desc: 'Free-form astrology question', body: '{"question":"What does my birth chart reveal about my career?","dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/ai/kundli-interpretation', desc: 'Full kundli interpretation', body: B },
      { method: 'POST', path: '/ai/horoscope-generation', desc: 'AI-generated horoscope', body: B },
      { method: 'POST', path: '/ai/remedies', desc: 'AI-powered remedies', body: B },
      { method: 'POST', path: '/ai/prediction', desc: 'AI life predictions', body: B },
      { method: 'POST', path: '/ai/gemstone-advisor', desc: 'Gemstone recommendations', body: B },
      { method: 'POST', path: '/ai/career-analysis', desc: 'Career analysis', body: B },
      { method: 'POST', path: '/ai/marriage-analysis', desc: 'Marriage analysis (with partner data)', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","partnerDateOfBirth":"1992-03-20","partnerTimeOfBirth":"14:30","partnerLatitude":19.076,"partnerLongitude":72.8777,"partnerTimezone":"Asia/Kolkata"}' },
    ],
    sections: [
      {
        title: 'AI Provider Setup',
        content: `AI endpoints require a configured AI provider (OpenAI, Anthropic, Groq, Together AI, Ollama, etc.).

**Without a provider:** Endpoints return rule-based fallback responses (no error).

**Configure via:**
- Admin panel: \`http://localhost:5173/admin\` → AI Providers tab
- API: \`POST /ai-providers\`

**Supported providers:** OpenAI, Anthropic, Groq, Together AI, Ollama, and any OpenAI-compatible API.`,
      },
    ],
  },
  {
    id: 'lucky', label: 'Lucky Attributes', icon: Star,
    endpoints: [
      { method: 'POST', path: '/lucky/color', desc: 'Lucky colors based on life path', body: '{"dateOfBirth":"1990-05-15"}' },
      { method: 'POST', path: '/lucky/number', desc: 'Lucky numbers', body: '{"dateOfBirth":"1990-05-15"}' },
      { method: 'POST', path: '/lucky/day', desc: 'Lucky day of week', body: '{"dateOfBirth":"1990-05-15"}' },
      { method: 'POST', path: '/lucky/metal', desc: 'Lucky metal & gemstone', body: '{"dateOfBirth":"1990-05-15"}' },
    ],
  },
  {
    id: 'numerology', label: 'Numerology', icon: Calculator,
    endpoints: [
      { method: 'POST', path: '/api/numerology/life-path', desc: 'Life path number from DOB', body: '{"dateOfBirth":"1990-05-15"}' },
      { method: 'POST', path: '/api/numerology/destiny', desc: 'Destiny number from name', body: '{"fullName":"Rahul Sharma"}' },
      { method: 'POST', path: '/api/numerology/soul', desc: 'Soul urge number', body: '{"fullName":"Rahul Sharma"}' },
      { method: 'POST', path: '/api/numerology/expression', desc: 'Expression number', body: '{"fullName":"Rahul Sharma"}' },
      { method: 'POST', path: '/api/numerology/name-number', desc: 'Name number', body: '{"name":"Rahul Sharma"}' },
      { method: 'POST', path: '/api/numerology/name-compatibility', desc: 'Name compatibility', body: '{"name1":"Rahul","name2":"Priya"}' },
      { method: 'POST', path: '/api/numerology/mobile', desc: 'Mobile number numerology', body: '{"mobileNumber":"9876543210"}' },
      { method: 'POST', path: '/api/numerology/vehicle', desc: 'Vehicle number numerology', body: '{"vehicleNumber":"DL01AB1234"}' },
      { method: 'POST', path: '/api/numerology/business-name', desc: 'Business name analysis', body: '{"businessName":"Celestial Solutions","dateOfBirth":"1990-05-15"}' },
      { method: 'POST', path: '/api/numerology/baby-name', desc: 'Baby name suggestions', body: '{"dateOfBirth":"1990-05-15","gender":"male","parentName":"Sharma"}' },
    ],
  },
  {
    id: 'location', label: 'Location Service', icon: MapPin,
    endpoints: [
      { method: 'GET', path: '/api/location/search?q=Delhi&limit=5', desc: 'Search locations (autocomplete)' },
      { method: 'GET', path: '/api/location/reverse?lat=28.6139&lon=77.209', desc: 'Reverse geocode' },
      { method: 'GET', path: '/api/location/timezone?lat=28.6139&lon=77.209', desc: 'Timezone lookup' },
      { method: 'GET', path: '/api/location/popular?country=IN', desc: 'Popular locations by country' },
    ],
    sections: [
      {
        title: 'Location Search Response',
        content: `\`\`\`json
{
  "status": 200,
  "query": "Delhi",
  "count": 5,
  "locations": [
    {
      "displayName": "New Delhi, Delhi, India",
      "latitude": 28.6138954,
      "longitude": 77.2090057,
      "address": { "city": "New Delhi", "country": "India", "countryCode": "in" }
    }
  ]
}
\`\`\`

Use this to get latitude, longitude, and timezone for birth data entry forms.`,
      },
    ],
  },
  {
    id: 'calculator', label: 'Calculators', icon: Calculator,
    endpoints: [
      { method: 'POST', path: '/api/calculator/lagna', desc: 'Ascendant calculator', body: B },
      { method: 'POST', path: '/api/calculator/moon-sign', desc: 'Moon sign calculator', body: B },
      { method: 'POST', path: '/api/calculator/sun-sign', desc: 'Sun sign calculator', body: B },
      { method: 'POST', path: '/api/calculator/planet-strength', desc: 'Planet strength', body: B },
      { method: 'POST', path: '/api/calculator/shadbala', desc: 'Shadbala (6-fold strength)', body: B },
      { method: 'POST', path: '/api/calculator/ashtakavarga', desc: 'Ashtakavarga points', body: B },
    ],
  },
  {
    id: 'gemstone', label: 'Gemstone & Rudraksha', icon: Gem,
    endpoints: [
      { method: 'POST', path: '/api/gemstone/recommendation', desc: 'Gemstone recommendation', body: B },
      { method: 'POST', path: '/api/gemstone/by-planet', desc: 'Gemstone by planet', body: '{"planet":"Jupiter","bodyWeightKg":70}' },
      { method: 'POST', path: '/api/gemstone/by-lagna', desc: 'Gemstone by lagna', body: B },
      { method: 'POST', path: '/api/gemstone/by-dasha', desc: 'Gemstone by dasha period', body: B },
      { method: 'POST', path: '/api/gemstone/wearing', desc: 'Wearing guide', body: B },
      { method: 'POST', path: '/api/gemstone/weight', desc: 'Weight calculator', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","bodyWeightKg":70}' },
      { method: 'POST', path: '/api/gemstone/metal', desc: 'Metal guide for gemstones', body: B },
      { method: 'POST', path: '/api/gemstone/finger', desc: 'Finger guide for gemstones', body: B },
      { method: 'POST', path: '/api/rudraksha/recommendation', desc: 'Rudraksha recommendation', body: B },
      { method: 'POST', path: '/api/rudraksha/mukhi-identification', desc: 'Mukhi identification', body: '{"description":"5 mukhi dark brown","visualFeatures":"5 lines visible"}' },
      { method: 'POST', path: '/api/rudraksha/wearing-method', desc: 'Wearing method', body: '{"mukhiCount":5,"gender":"male"}' },
      { method: 'POST', path: '/api/rudraksha/mantra', desc: 'Rudraksha mantra', body: '{"mukhiCount":5}' },
      { method: 'POST', path: '/api/rudraksha/benefits', desc: 'Rudraksha benefits', body: '{"mukhiCount":5}' },
    ],
    sections: [
      {
        title: 'Gemstone Images',
        content: `All gemstone response objects now include an \`imageUrl\` field pointing to a gemstone image asset:

\`\`\`json
{
  "gemstone": {
    "name": "Ruby",
    "hindiName": "Manikya",
    "imageUrl": "/images/gemstones/ruby.webp",
    "color": "Red / Pinkish Red",
    "origin": "Burma, India, Sri Lanka",
    "quality": "Transparent, deep red with fluorescence"
  }
}
\`\`\`

The \`imageUrl\` is a relative path — prepend your base URL or static asset prefix to use it in an \`<img>\` tag.`,
      },
    ],
  },
  {
    id: 'muhurat', label: 'Muhurat (Auspicious Times)', icon: Star,
    endpoints: [
      { method: 'POST', path: '/horoscope/muhurat/marriage', desc: 'Marriage muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/house-warming', desc: 'Griha Pravesh muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/vehicle-purchase', desc: 'Vehicle purchase muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/business-opening', desc: 'Business opening muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/engagement', desc: 'Engagement muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/property-purchase', desc: 'Property purchase muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/naming-ceremony', desc: 'Naming ceremony muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/griha-pravesh', desc: 'Griha Pravesh muhurat', body: '{"dateOfBirth":"1990-05-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/horoscope/muhurat/cesarean', desc: 'Cesarean muhurat', body: B },
    ],
  },
  {
    id: 'festival', label: 'Festivals & Events', icon: Home,
    endpoints: [
      { method: 'POST', path: '/api/festival/hindu-festival', desc: 'Hindu festivals list', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/ekadashi', desc: 'Ekadashi dates', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/sankranti', desc: 'Sankranti dates', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/diwali', desc: 'Diwali dates', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/navratri', desc: 'Navratri dates', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/purnima', desc: 'Purnima (full moon) dates', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/amavasya', desc: 'Amavasya (new moon) dates', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/chaturthi', desc: 'Chaturthi dates (Ganesh Chaturthi)', body: '{"year":2026}' },
      { method: 'POST', path: '/api/festival/holi', desc: 'Holi dates', body: '{"year":2026}' },
    ],
  },
  {
    id: 'auth', label: 'Auth & API Keys', icon: Shield,
    endpoints: [
      { method: 'POST', path: '/auth/register', desc: 'Register new account', body: '{"email":"user@example.com","name":"User","password":"password123"}', headers: true },
      { method: 'POST', path: '/auth/login', desc: 'Login with credentials', body: '{"email":"user@example.com","password":"password123"}', headers: true },
      { method: 'GET', path: '/auth/me', desc: 'Get current user profile', headers: true },
      { method: 'PUT', path: '/auth/profile', desc: 'Update profile', body: '{"name":"New Name"}', headers: true },
      { method: 'POST', path: '/auth/change-password', desc: 'Change password', body: '{"current_password":"old123","new_password":"new456"}', headers: true },
      { method: 'GET', path: '/auth/verify-email', desc: 'Verify email via token (query: ?token=...)', headers: true },
      { method: 'POST', path: '/auth/resend-verification', desc: 'Resend verification email', body: '{"email":"user@example.com"}' },
      { method: 'POST', path: '/auth/forgot-password', desc: 'Forgot password request', body: '{"email":"user@example.com"}' },
      { method: 'POST', path: '/auth/reset-password', desc: 'Reset password with token', body: '{"token":"...","new_password":"new456"}' },
      { method: 'POST', path: '/auth/keys', desc: 'Create API key', body: '{"name":"My App Key","tier":"free"}', headers: true },
      { method: 'GET', path: '/auth/keys', desc: 'List API keys', headers: true },
      { method: 'DELETE', path: '/auth/keys/{id}', desc: 'Revoke API key', headers: true },
      { method: 'GET', path: '/auth/usage/{key_id}', desc: 'Get API key usage stats', headers: true },
    ],
    sections: [
      {
        title: 'API Key Tiers',
        content: `| Tier | Requests/Day | Description |
|------|-------------|-------------|
| \`free\` | 100 | Basic access, watermarked PDFs |
| \`starter\` | 1,000 | Full access, 50 AI calls/day |
| \`pro\` | 10,000 | Full access, 500 AI calls/day |
| \`enterprise\` | Unlimited | White-label, unlimited AI |

**Admin endpoints** (JWT auth, not API key):
- \`GET /admin/users\` — List users
- \`PUT /admin/users/{id}/plan\` — Update user plan
- \`GET /admin/stats\` — Dashboard stats
- \`GET /admin/usage/daily\` — Daily usage
- \`GET /admin/usage/endpoints\` — Endpoint usage`,
      },
    ],
  },
  {
    id: 'yoga', label: 'Yoga (Planetary Combos)', icon: Sun,
    endpoints: [
      { method: 'POST', path: '/horoscope/yoga/predictions', desc: 'Yoga-based predictions', body: B },
      { method: 'POST', path: '/horoscope/yoga/detailed', desc: 'Detailed yoga analysis', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","yogaName":"Gajakesari"}' },
      { method: 'POST', path: '/horoscope/yoga/score', desc: 'Yoga strength score', body: B },
    ],
  },
  {
    id: 'bhava', label: 'Bhava Chalit', icon: Home,
    endpoints: [
      { method: 'POST', path: '/horoscope/bhava-chalit', desc: 'Bhava chalit chart', body: B },
      { method: 'POST', path: '/horoscope/bhava-chalit/compare', desc: 'Compare bhava with rasi', body: B },
      { method: 'POST', path: '/horoscope/bhava-chalit/cusps', desc: 'Bhava cusp positions', body: B },
    ],
  },
  {
    id: 'varshaphal', label: 'Varshaphal (Annual)', icon: Calendar,
    endpoints: [
      { method: 'POST', path: '/horoscope/varshaphal', desc: 'Annual solar return chart', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","year":2026}' },
      { method: 'POST', path: '/horoscope/varshaphal/prediction', desc: 'Varshaphal predictions', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","year":2026}' },
      { method: 'POST', path: '/horoscope/varshaphal/tajika-aspects', desc: 'Tajika aspects for the year', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","year":2026}' },
    ],
  },
  {
    id: 'prashna', label: 'Prashna (Horary)', icon: Star,
    endpoints: [
      { method: 'POST', path: '/api/prashna/chart', desc: 'Prashna chart for a question', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","question":"Will I get the job?"}' },
      { method: 'POST', path: '/api/prashna/judgement', desc: 'Prashna judgement', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","question":"Will I get the job?"}' },
    ],
  },
  {
    id: 'pooja', label: 'Pooja & Temple', icon: Home,
    endpoints: [
      { method: 'POST', path: '/pooja/recommendation', desc: 'Pooja recommendations', body: B },
      { method: 'POST', path: '/pooja/temple', desc: 'Temple suggestions', body: B },
      { method: 'POST', path: '/pooja/sankalp', desc: 'Sankalp details', body: B },
      { method: 'POST', path: '/pooja/booking', desc: 'Book a pooja', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","poojaName":"Mahamrityunjaya","name":"Rahul","phone":"9876543210"}' },
      { method: 'POST', path: '/pooja/availability', desc: 'Pooja availability check', body: '{"date":"2026-07-15","poojaName":"Mahamrityunjaya"}' },
    ],
  },
  {
    id: 'utility', label: 'Utility', icon: Wrench,
    endpoints: [
      { method: 'POST', path: '/api/utility/ayanamsa', desc: 'Ayanamsa value for a date', body: '{"date":"2026-07-15","time":"12:00","timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/utility/ephemeris', desc: 'Ephemeris data for a date', body: '{"date":"2026-07-15","time":"12:00","timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/utility/planet-speed', desc: 'Planet speed data', body: '{"date":"2026-07-15","time":"12:00","timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/utility/lunar-phase', desc: 'Lunar phase for a date', body: '{"date":"2026-07-15","time":"12:00","timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/utility/eclipse', desc: 'Eclipse search', body: '{"date":"2026-07-15","time":"12:00","timezone":"Asia/Kolkata","rangeDays":30}' },
      { method: 'POST', path: '/api/utility/sunrise-sunset', desc: 'Sunrise/sunset times', body: '{"date":"2026-07-15","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/utility/julian-day', desc: 'Julian day number', body: '{"date":"2026-07-15","time":"12:00","timezone":"Asia/Kolkata"}' },
      { method: 'POST', path: '/api/utility/rectify', desc: 'Birth time rectification', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","knownAscendant":"Leo"}' },
      { method: 'POST', path: '/api/utility/ascendant-scan', desc: 'Ascendant scan for rectification', body: B },
      { method: 'POST', path: '/api/utility/transit-verify', desc: 'Verify known events with transit', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","eventDate":"2020-06-01","eventType":"marriage"}' },
    ],
  },
  {
    id: 'admin', label: 'Admin', icon: Shield,
    endpoints: [
      { method: 'GET', path: '/admin/users', desc: 'List all users', headers: true },
      { method: 'GET', path: '/admin/users/{user_id}', desc: 'Get user details', headers: true },
      { method: 'PUT', path: '/admin/users/{user_id}/plan', desc: 'Update user plan', body: '{"plan":"pro"}', headers: true },
      { method: 'PUT', path: '/admin/users/{user_id}/admin', desc: 'Toggle admin status', headers: true },
      { method: 'DELETE', path: '/admin/users/{user_id}', desc: 'Delete user', headers: true },
      { method: 'PUT', path: '/admin/users/{user_id}/reset-password', desc: 'Reset user password', body: '{"new_password":"new456"}', headers: true },
      { method: 'POST', path: '/admin/users/{user_id}/keys', desc: 'Create API key for user', body: '{"name":"Key","tier":"free"}', headers: true },
      { method: 'GET', path: '/admin/users/{user_id}/usage', desc: 'Get user usage stats', headers: true },
      { method: 'GET', path: '/admin/keys', desc: 'List all API keys', headers: true },
      { method: 'PUT', path: '/admin/keys/{key_id}/revoke', desc: 'Revoke an API key', headers: true },
      { method: 'PUT', path: '/admin/keys/{key_id}/tier', desc: 'Update key tier', body: '{"tier":"pro"}', headers: true },
      { method: 'GET', path: '/admin/stats', desc: 'Dashboard statistics', headers: true },
      { method: 'GET', path: '/admin/usage/daily', desc: 'Daily usage statistics', headers: true },
      { method: 'GET', path: '/admin/usage/endpoints', desc: 'Endpoint usage stats', headers: true },
      { method: 'GET', path: '/admin/usage/by-user', desc: 'Usage grouped by user', headers: true },
      { method: 'GET', path: '/admin/jobs', desc: 'List all background jobs', headers: true },
    ],
  },
  {
    id: 'ai-providers', label: 'AI Providers', icon: Brain,
    endpoints: [
      { method: 'GET', path: '/ai-providers/supported', desc: 'List supported AI providers' },
      { method: 'POST', path: '/ai-providers', desc: 'Configure a new AI provider', body: '{"provider":"openai","apiKey":"sk-...","model":"gpt-4"}', headers: true },
      { method: 'GET', path: '/ai-providers', desc: 'List configured providers', headers: true },
      { method: 'PUT', path: '/ai-providers/{provider_id}', desc: 'Update provider config', body: '{"model":"gpt-4o"}', headers: true },
      { method: 'DELETE', path: '/ai-providers/{provider_id}', desc: 'Delete provider config', headers: true },
      { method: 'POST', path: '/ai-providers/test', desc: 'Test provider connection with config', body: '{"provider":"openai","apiKey":"sk-..."}', headers: true },
      { method: 'POST', path: '/ai-providers/{provider_id}/test', desc: 'Test configured provider', headers: true },
    ],
  },
  {
    id: 'jobs', label: 'Background Jobs', icon: Clock,
    endpoints: [
      { method: 'POST', path: '/jobs/submit-pdf', desc: 'Submit async PDF generation job', body: B, headers: true },
      { method: 'POST', path: '/jobs/submit-ai', desc: 'Submit async AI job', body: '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","question":"Career analysis"}', headers: true },
      { method: 'GET', path: '/jobs/{job_id}', desc: 'Get job status & result', headers: true },
      { method: 'GET', path: '/jobs/{job_id}/download', desc: 'Download job result (PDF)', headers: true },
      { method: 'GET', path: '/jobs', desc: 'List your jobs', headers: true },
    ],
  },
  {
    id: 'lal-kitab', label: 'Lal Kitab', icon: BookOpen,
    endpoints: [
      { method: 'POST', path: '/lal-kitab/house-significations', desc: 'Lal Kitab 12 house significations & remedies', body: '{}' },
      { method: 'POST', path: '/lal-kitab/planet-interpretations', desc: 'Lal Kitab planet nature, traits & remedies', body: '{}' },
      { method: 'POST', path: '/lal-kitab/chart-analysis', desc: 'Full Lal Kitab chart analysis (planets & houses)', body: B },
    ],
    sections: [
      {
        title: 'About Lal Kitab',
        content: `Lal Kitab ("Red Book") is a unique system of Vedic astrology with its own set of principles for house significations, planet placements, and remedies. Unlike classical Parashari astrology, Lal Kitab treats each house and planet with specific karmic significance and offers practical, inexpensive remedies (upayas).

**Endpoints:**
- \`/lal-kitab/house-significations\` — Returns all 12 houses with their names, descriptions, elements, and general remedies. No birth data required.
- \`/lal-kitab/planet-interpretations\` — Returns all 9 planets with their nature, positive/negative traits, and Lal Kitab remedies. No birth data required.
- \`/lal-kitab/chart-analysis\` — Requires birth data. Returns per-planet analysis (nature, house signification, traits, retrograde/combust effects, remedies) and per-house analysis (signification, planets, remedies).`,
      },
    ],
  },
  {
    id: 'kp', label: 'KP Astrology', icon: Star,
    endpoints: [
      { method: 'POST', path: '/kp/planet-details', desc: 'KP planet details with star lord & sub lord', body: B },
      { method: 'POST', path: '/kp/cuspal-lords', desc: 'KP cuspal lords, star lords & sub lords', body: B },
      { method: 'POST', path: '/kp/bhav-chalit', desc: 'KP Bhav Chalit (equal house)', body: B },
      { method: 'POST', path: '/kp/ruling-planets', desc: 'KP ruling planets (electional/horary)', body: B },
      { method: 'POST', path: '/kp/horary', desc: 'KP horary — answer a question', body: '{"questionDate":"2025-07-29","questionTime":"14:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","question":"Will I get a job this year?"}' },
      { method: 'POST', path: '/kp/star-lords', desc: 'KP star lords & sub lords for all planets', body: B },
    ],
    sections: [
      {
        title: 'About KP Astrology',
        content: `Krishnamurti Paddhati (KP) is a predictive astrology system developed by K.S. Krishnamurti. It uses the Placidus house system, stellar astrology (nakshatra-based star lords and sub lords), and ruling planets for precise event timing and horary predictions.

**Key concepts:**
- **Star Lord** — The nakshatra lord of a planet or cusp
- **Sub Lord** — The sub-division lord within a nakshatra (proportional to Vimshottari dasha years)
- **Ruling Planets** — Ascendant lord, Moon, Moon's star lord, Moon's sub lord, and day lord; used for electional and horary astrology
- **Horary** — Provide a question, date, and time; the API determines the relevant house, significators, and whether the outcome is favorable

The \`/kp/horary\` endpoint accepts \`questionDate\`, \`questionTime\`, \`latitude\`, \`longitude\`, \`timezone\`, and \`question\` instead of the standard birth data fields.`,
      },
    ],
  },
  {
    id: 'health', label: 'Health', icon: Activity,
    endpoints: [
      { method: 'GET', path: '/health', desc: 'API health check' },
    ],
  },
]

function CopyButton({ text }) {
  return (
    <button onClick={() => { navigator.clipboard.writeText(text); toast.success('Copied!') }}
      style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, padding: '2px 6px', borderRadius: 4 }}
      onMouseEnter={e => e.target.style.color = '#a78bfa'}
      onMouseLeave={e => e.target.style.color = '#64748b'}>
      <Copy size={12} /> Copy
    </button>
  )
}

function MarkdownContent({ text }) {
  const lines = text.split('\n')
  const elements = []
  let inCodeBlock = false
  let codeContent = ''
  let codeLanguage = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <div key={`code-${i}`} style={{ position: 'relative', marginBottom: 16 }}>
            <div style={{ position: 'absolute', top: 8, right: 8, zIndex: 2 }}>
              <CopyButton text={codeContent.trim()} />
            </div>
            <pre style={{ background: '#0d0d24', borderRadius: 10, padding: '16px 16px', fontSize: 12, lineHeight: 1.7, fontFamily: 'var(--font-mono)', color: '#94a3b8', overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word', border: '1px solid rgba(124,58,237,0.15)' }}>
              <code>{codeContent.trim()}</code>
            </pre>
          </div>
        )
        codeContent = ''
        inCodeBlock = false
      } else {
        inCodeBlock = true
        codeLanguage = line.slice(3)
      }
    } else if (inCodeBlock) {
      codeContent += line + '\n'
    } else if (line.startsWith('| ') && lines[i + 1]?.startsWith('|')) {
      const headers = line.split('|').filter(Boolean).map(h => h.trim())
      const rows = []
      let j = i + 2
      while (j < lines.length && lines[j].startsWith('|')) {
        rows.push(lines[j].split('|').filter(Boolean).map(c => c.trim()))
        j++
      }
      elements.push(
        <div key={`table-${i}`} style={{ overflowX: 'auto', marginBottom: 16, borderRadius: 8, border: '1px solid rgba(124,58,237,0.15)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>{headers.map((h, hi) => <th key={hi} style={{ padding: '8px 12px', textAlign: 'left', background: 'rgba(124,58,237,0.1)', color: '#a78bfa', fontWeight: 600, borderBottom: '1px solid rgba(124,58,237,0.2)' }}>{h}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => <tr key={ri}>{row.map((cell, ci) => <td key={ci} style={{ padding: '6px 12px', borderBottom: '1px solid rgba(100,116,139,0.1)', color: '#e2e8f0' }}>{cell}</td>)}</tr>)}
            </tbody>
          </table>
        </div>
      )
      i = j - 1
    } else if (line.startsWith('**') && line.endsWith('**')) {
      elements.push(<p key={i} style={{ fontWeight: 700, color: '#e2e8f0', marginTop: 16, marginBottom: 8 }}>{line.slice(2, -2)}</p>)
    } else if (line.startsWith('- ')) {
      elements.push(<li key={i} style={{ color: '#94a3b8', marginLeft: 16, marginBottom: 4, lineHeight: 1.6 }}>{renderInline(line.slice(2))}</li>)
    } else if (line.trim() === '') {
      elements.push(<div key={i} style={{ height: 8 }} />)
    } else {
      elements.push(<p key={i} style={{ color: '#94a3b8', lineHeight: 1.7, marginBottom: 6 }}>{renderInline(line)}</p>)
    }
  }
  return <div>{elements}</div>
}

function renderInline(text) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/)
  return parts.map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={i} style={{ padding: '2px 6px', borderRadius: 4, background: 'rgba(124,58,237,0.1)', color: '#a78bfa', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{part.slice(1, -1)}</code>
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i} style={{ color: '#e2e8f0', fontWeight: 600 }}>{part.slice(2, -2)}</strong>
    return part
  })
}

function EndpointCard({ ep }) {
  const [expanded, setExpanded] = useState(false)
  const mc = { GET: { bg: 'rgba(34,197,94,0.15)', text: '#22c55e', border: 'rgba(34,197,94,0.3)' }, POST: { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6', border: 'rgba(59,130,246,0.3)' }, DELETE: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444', border: 'rgba(239,68,68,0.3)' } }[ep.method] || { bg: 'rgba(59,130,246,0.15)', text: '#3b82f6', border: 'rgba(59,130,246,0.3)' }

  const curl = ep.method === 'GET'
    ? `curl "http://localhost:5000${ep.path.split('?')[0]}" \\\n  -H "X-API-Key: YOUR_KEY"`
    : `curl -X ${ep.method} "http://localhost:5000${ep.path.split('?')[0]}" \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: YOUR_KEY"${ep.body ? ` \\\n  -d '${ep.body.replace(/\n/g, ' ')}'` : ''}`

  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <button onClick={() => setExpanded(!expanded)} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: '14px 20px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}>
        <span style={{ padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)', background: mc.bg, color: mc.text, border: `1px solid ${mc.border}`, letterSpacing: 0.5, minWidth: 52, textAlign: 'center' }}>{ep.method}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: '#e2e8f0', flex: 1 }}>{ep.path}</span>
        <span style={{ color: '#94a3b8', fontSize: 13, flex: 2 }}>{ep.desc}</span>
        {expanded ? <ChevronDown size={16} color="#64748b" /> : <ChevronRight size={16} color="#64748b" />}
      </button>
      {expanded && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ borderTop: '1px solid var(--border-color)', padding: 20 }}>
          {ep.headers && (
            <div style={{ marginBottom: 12, padding: '8px 12px', background: 'rgba(251,191,36,0.08)', borderRadius: 8, border: '1px solid rgba(251,191,36,0.2)' }}>
              <span style={{ fontSize: 12, color: '#fbbf24' }}>Auth: <code style={{ fontFamily: 'var(--font-mono)' }}>Authorization: Bearer {'<jwt_token>'}</code></span>
            </div>
          )}
          {ep.body && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>Request Body</span>
                <CopyButton text={ep.body} />
              </div>
              <pre style={{ background: '#0d0d24', borderRadius: 8, padding: 14, fontSize: 12, lineHeight: 1.6, fontFamily: 'var(--font-mono)', color: '#94a3b8', overflow: 'auto', whiteSpace: 'pre-wrap' }}>{ep.body}</pre>
            </div>
          )}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>cURL Example</span>
              <CopyButton text={curl} />
            </div>
            <pre style={{ background: '#0d0d24', borderRadius: 8, padding: 14, fontSize: 11, lineHeight: 1.6, fontFamily: 'var(--font-mono)', color: '#64748b', overflow: 'auto', whiteSpace: 'pre-wrap' }}>{curl}</pre>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default function Docs() {
  const [activeCat, setActiveCat] = useState('quickstart')
  const [search, setSearch] = useState('')
  const category = categories.find(c => c.id === activeCat)

  const filteredEndpoints = useMemo(() => {
    if (!category?.endpoints) return []
    if (!search) return category.endpoints
    const q = search.toLowerCase()
    return category.endpoints.filter(ep => ep.path.toLowerCase().includes(q) || ep.desc.toLowerCase().includes(q))
  }, [category, search])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', paddingTop: 72 }}>
      {/* Sidebar */}
      <aside className="docs-sidebar" style={{ width: 260, borderRight: '1px solid var(--border-color)', padding: '24px 12px', position: 'sticky', top: 72, height: 'calc(100vh - 72px)', overflowY: 'auto', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0 12px', marginBottom: 20 }}>
          <BookOpen size={18} color="#7c3aed" />
          <span style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>Developer Docs</span>
        </div>
        <div style={{ padding: '0 12px', marginBottom: 16 }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="#64748b" style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }} />
            <input placeholder="Search docs..." value={search} onChange={e => setSearch(e.target.value)} style={{ width: '100%', padding: '7px 10px 7px 30px', background: 'rgba(10,10,26,0.5)', border: '1px solid var(--border-color)', borderRadius: 8, color: '#e2e8f0', fontSize: 12, outline: 'none' }} />
          </div>
        </div>
        {categories.map(cat => {
          const Icon = cat.icon
          const count = cat.endpoints?.length || 0
          return (
            <button key={cat.id} onClick={() => { setActiveCat(cat.id); setSearch('') }}
              style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', borderRadius: 8, border: 'none', background: activeCat === cat.id ? 'rgba(124,58,237,0.15)' : 'transparent', color: activeCat === cat.id ? '#a78bfa' : '#94a3b8', fontSize: 13, fontWeight: 500, cursor: 'pointer', textAlign: 'left', marginBottom: 2, transition: 'all 0.15s' }}>
              <Icon size={14} />
              <span style={{ flex: 1 }}>{cat.label}</span>
              {count > 0 && <span style={{ fontSize: 11, color: '#475569', background: 'rgba(100,116,139,0.15)', padding: '1px 6px', borderRadius: 10 }}>{count}</span>}
            </button>
          )
        })}
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '32px 40px', overflow: 'auto', maxWidth: 900 }}>
        <AnimatePresence mode="wait">
          <motion.div key={activeCat} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.15 }}>
            <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 6 }}>{category?.label}</h1>
            <p style={{ color: '#64748b', marginBottom: 28, fontSize: 14 }}>
              {category?.endpoints ? `${filteredEndpoints.length} endpoints` : 'Documentation & guides'}
              {search && ` matching "${search}"`}
            </p>

            {/* Content sections */}
            {category?.sections?.map((sec, i) => (
              <div key={i} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24, marginBottom: 20 }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0', marginBottom: 14 }}>{sec.title}</h2>
                <MarkdownContent text={sec.content} />
              </div>
            ))}

            {/* Endpoint cards */}
            {filteredEndpoints.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {filteredEndpoints.map(ep => <EndpointCard key={ep.path + ep.method} ep={ep} />)}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      <style>{`
        @media (max-width: 768px) {
          .docs-sidebar { display: none !important; }
        }
      `}</style>
    </div>
  )
}
