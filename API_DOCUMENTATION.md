# AstroVakta Vedic Astrology API — Developer Documentation

> **Version 2.0** | **Base URL:** `http://localhost:5000` (or your deployed URL)  
> **216+ endpoints** | **PDF Report Generation** | **AI-Powered Insights** | **North Indian Diamond Charts**

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Rate Limits](#3-rate-limits)
4. [Core API Endpoints](#4-core-api-endpoints)
5. [PDF Report Generation](#5-pdf-report-generation)
6. [AI-Powered Endpoints](#6-ai-powered-endpoints)
7. [SVG Chart Generation](#7-svg-chart-generation)
8. [Async Job System](#8-async-job-system)
9. [Error Handling](#9-error-handling)
10. [Integration Examples](#10-integration-examples)
11. [Endpoint Reference](#11-endpoint-reference)

---

## 1. Quick Start

### Get Your API Key

1. Register: `POST /auth/register`
2. Login: `POST /auth/login` → get JWT token
3. Create API key: `POST /auth/keys` (with JWT)

### First API Call

```bash
curl -X POST http://localhost:5000/api/kundli \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_api_key_here" \
  -d '{
    "dateOfBirth": "1990-05-15",
    "timeOfBirth": "10:30",
    "latitude": 28.6139,
    "longitude": 77.209,
    "timezone": "Asia/Kolkata"
  }'
```

### Response Format

```json
{
  "success": true,
  "data": {
    "basicDetails": { "dateOfBirth": "1990-05-15", "ascendant": "Taurus", ... },
    "planets": [ { "name": "Sun", "sign": "Taurus", "house": 1, ... } ],
    "houses": [ { "number": 1, "sign": "Taurus", "planets": ["Sun"] } ],
    "yogas": [ { "name": "Gajakesari", ... } ],
    "doshas": [ { "name": "Manglik", "present": false } ]
  }
}
```

---

## 2. Authentication

### API Key Authentication (Recommended)

All protected endpoints require an `X-API-Key` header:

```
X-API-Key: <your-api-key-here>
```

### JWT Authentication (for user/admin endpoints)

```
Authorization: Bearer <jwt_token>
```

### Key Tiers & Rate Limits

| Tier | Requests/Day | Charts | PDF Reports | AI Calls |
|------|-------------|--------|-------------|----------|
| Free | 100 | Basic | Watermarked | Limited |
| Starter | 1,000 | All | Full | 50/day |
| Pro | 10,000 | All | Full + Custom | 500/day |
| Enterprise | Unlimited | All + White-label | Full + API | Unlimited |

---

## 3. Rate Limits

Rate limits are per API key per day. Response headers include:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9987
X-RateLimit-Tier: pro
X-Response-Time: 0.142s
```

When rate limited, you'll receive HTTP 402:
```json
{
  "detail": "Rate limit exceeded",
  "tier": "pro",
  "rate_limit": 10000,
  "requests_today": 10000
}
```

---

## 4. Core API Endpoints

### 4.1 Birth Chart (Kundli)

```http
POST /api/kundli
```

Complete birth chart with planets, houses, nakshatras, yogas, and doshas.

**Request Body:**
```json
{
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata"
}
```

**Response:** Full kundli data including planet positions, house placements, nakshatra details, yoga detection, and dosha analysis.

### 4.2 Horoscope Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /horoscope/daily` | Daily horoscope by Moon sign |
| `POST /horoscope/weekly` | Weekly forecast |
| `POST /horoscope/monthly` | Monthly overview |
| `POST /horoscope/yearly` | Annual predictions |
| `POST /horoscope/career` | Career-specific predictions |
| `POST /horoscope/love` | Love & relationship guidance |
| `POST /horoscope/finance` | Financial outlook |
| `POST /horoscope/health` | Health predictions |

All horoscope endpoints accept the same birth data body as `/api/kundli`.

### 4.3 Compatibility (Kundli Milan)

```http
POST /horoscope/compat
```

```json
{
  "maleDateOfBirth": "1990-05-15",
  "maleTimeOfBirth": "10:30",
  "maleLatitude": 28.6139,
  "maleLongitude": 77.209,
  "maleTimezone": "Asia/Kolkata",
  "femaleDateOfBirth": "1992-03-20",
  "femaleTimeOfBirth": "14:30",
  "femaleLatitude": 19.076,
  "femaleLongitude": 72.8777,
  "femaleTimezone": "Asia/Kolkata"
}
```

Returns: Ashtakoot gun milan score, Nadi/Bhakoot/Manglik dosha analysis, compatibility percentage.

### 4.4 Dasha (Planetary Periods)

| Endpoint | Description |
|----------|-------------|
| `POST /horoscope/dasha/vimshottari` | Full Vimshottari dasha timeline |
| `POST /horoscope/dasha/current` | Currently active dasha/bhukti |
| `POST /horoscope/dasha/chara` | Jaimini Chara dasha |
| `POST /dasha/yogini` | Yogini dasha |
| `POST /dasha/kalachakra` | Kalachakra dasha |

### 4.5 Panchang (Hindu Calendar)

```http
POST /horoscope/panchang
```

Returns: Tithi, Nakshatra, Yoga, Karana, Vara, Rahu Kaal, Gulika Kaal, Yamaganda, Choghadiya, Hora, Moonrise/Moonset.

Additional endpoints: `/horoscope/panchang/rahu-kaal`, `/horoscope/panchang/choghadiya`, `/horoscope/panchang/hora`, etc.

### 4.6 Transit (Gochar)

| Endpoint | Description |
|----------|-------------|
| `POST /horoscope/transit` | Full transit analysis |
| `POST /horoscope/transit/prediction` | Transit-based predictions |
| `POST /horoscope/transit/by-planet` | Single planet transit |
| `POST /api/transit/retrograde` | Currently retrograde planets |
| `POST /api/transit/combust` | Currently combust planets |

### 4.7 Dosha Analysis

| Endpoint | Description |
|----------|-------------|
| `POST /horoscope/dosha/compute` | Detect all doshas |
| `POST /horoscope/dosha/severity` | Severity assessment |
| `POST /horoscope/dosha/remedies` | Remedies for doshas |
| `POST /api/dosha/manglik-detailed` | Detailed Manglik analysis |
| `POST /api/dosha/nadi-dosha` | Nadi dosha check |
| `POST /api/dosha/bhakoot-dosha` | Bhakoot dosha check |

### 4.8 Calculator Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/calculator/lagna` | Ascendant calculator |
| `POST /api/calculator/moon-sign` | Moon sign calculator |
| `POST /api/calculator/sun-sign` | Sun sign calculator |
| `POST /api/calculator/shadbala` | Planet strength (Shadbala) |
| `POST /api/calculator/ashtakavarga` | Ashtakavarga points |

### 4.9 Location Service

```http
GET /api/location/search?q=Delhi&limit=5
GET /api/location/reverse?lat=28.6139&lon=77.209
GET /api/location/timezone?lat=28.6139&lon=77.209
GET /api/location/popular?country=IN
```

Use these to get latitude, longitude, and timezone for any location. The search endpoint returns autocomplete-friendly results.

### 4.10 Numerology

| Endpoint | Description |
|----------|-------------|
| `POST /api/numerology/life-path` | Life path number from DOB |
| `POST /api/numerology/destiny` | Destiny number from name |
| `POST /api/numerology/soul` | Soul urge number |
| `POST /api/numerology/name-compatibility` | Name compatibility score |

### 4.11 Lucky Attributes

```http
POST /lucky/color
POST /lucky/number
POST /lucky/day
POST /lucky/metal
```

```json
{ "dateOfBirth": "1990-05-15" }
```

Returns lucky colors, numbers, day of week, and metal based on numerology life path.

---

## 5. PDF Report Generation

### 5.1 Full PDF Report (Basic)

```http
POST /reports/full-pdf
```

Generates a complete, branded PDF birth chart report with all 23 sections.

**Response:** Binary PDF file with `Content-Type: application/pdf`.

```bash
curl -X POST http://localhost:5000/reports/full-pdf \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_key" \
  -d '{
    "dateOfBirth": "1990-05-15",
    "timeOfBirth": "10:30",
    "latitude": 28.6139,
    "longitude": 77.209,
    "timezone": "Asia/Kolkata",
    "clientName": "Rahul Sharma",
    "brandName": "My Astrology App"
  }' -o report.pdf
```

### 5.2 Customizable PDF Report (Advanced)

```http
POST /reports/full-pdf
```

The same endpoint supports full customization via additional fields:

```json
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

  "sections": [
    "birth_details",
    "kundli_chart",
    "navamsa_chart",
    "planet_positions",
    "houses",
    "yogas",
    "doshas",
    "career",
    "finance",
    "health",
    "love",
    "gemstones",
    "remedies"
  ],

  "watermarkText": "DRAFT - NOT FOR DISTRIBUTION",
  "watermarkOpacity": 0.06,

  "houseSystem": "W",
  "nodeMode": "mean"
}
```

### Available Sections

| Section Key | Description |
|------------|-------------|
| `birth_details` | Birth date, time, place, ayanamsa |
| `kundli_chart` | North Indian Diamond Rasi chart (D1) |
| `navamsa_chart` | Navamsa chart (D9) |
| `hora_chart` | Hora wealth chart (D2) |
| `planet_positions` | Full planet position table |
| `houses` | House (Bhava) analysis |
| `nakshatras` | Nakshatra analysis |
| `dasha` | Vimshottari dasha timeline |
| `yogas` | Yoga detection & analysis |
| `doshas` | Dosha detection (Manglik, Kaal Sarp, etc.) |
| `planet_strengths` | Planet strength analysis |
| `career` | Career & profession predictions |
| `finance` | Finance & wealth predictions |
| `health` | Health predictions |
| `love` | Love & marriage predictions |
| `education` | Education predictions |
| `family` | Family life predictions |
| `travel` | Travel & foreign settlement |
| `ai_predictions` | AI-generated life predictions |
| `major_charts` | All divisional charts (D1-D60) as SVGs |
| `gemstones` | Gemstone recommendations |
| `remedies` | Remedies & spiritual guidance |
| `lucky` | Lucky attributes |

### Watermark Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `watermarkText` | string | null | Diagonal text watermark on every page |
| `watermarkImageUrl` | string | null | Image watermark overlay |
| `watermarkOpacity` | float | 0.08 | Opacity 0.0-0.3 (0.08 is very light) |

Watermarks are drawn at 45° angle, centered on each page, with very low opacity so they don't destroy chart/text visibility.

### Branding Options

| Field | Type | Description |
|-------|------|-------------|
| `logoUrl` | string | Logo image path/URL (cover page) |
| `brandName` | string | Brand name in header/footer |
| `clientName` | string | Client name on cover page |
| `reportTitle` | string | Report title on cover page |
| `contactMobile` | string | Contact phone |
| `contactEmail` | string | Contact email |
| `contactWebsite` | string | Website in header/footer |

### 5.3 PDF Report Info (Preview)

```http
POST /reports/pdf-info
```

Returns metadata about the report without generating the PDF:

```json
{
  "success": true,
  "data": {
    "birthDate": "1990-05-15",
    "ascendant": { "sign": "Taurus", "degree": 30.38 },
    "moonSign": "Sagittarius",
    "sunSign": "Taurus",
    "planets": 12,
    "yogas": 5,
    "doshas": 4,
    "sections": ["Birth Details", "Kundli Chart (Rasi)", ...],
    "totalSections": 23,
    "availableSections": { ... },
    "brandingOptions": { ... },
    "watermarkOptions": { ... }
  }
}
```

---

## 6. AI-Powered Endpoints

> **Note:** AI endpoints require configuring an AI provider (OpenAI, Anthropic, Groq, etc.) via the Admin panel or API. Without a configured provider, they return rule-based fallback responses.

| Endpoint | Description |
|----------|-------------|
| `POST /ai/chat` | Free-form astrology question |
| `POST /ai/kundli-interpretation` | Full kundli interpretation |
| `POST /ai/horoscope-generation` | AI-generated horoscope |
| `POST /ai/remedies` | AI-powered remedies |
| `POST /ai/prediction` | Life predictions |
| `POST /ai/gemstone-advisor` | Gemstone recommendations |
| `POST /ai/career-analysis` | Career analysis |
| `POST /ai/marriage-analysis` | Marriage analysis (requires partner data) |

**Example — AI Chat:**
```json
{
  "question": "What does my chart indicate about career growth in 2026?",
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata"
}
```

---

## 7. SVG Chart Generation

### North Indian Diamond Chart

```http
POST /chart/svg
```

```json
{
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata",
  "theme": "dark"
}
```

Returns raw SVG (`Content-Type: image/svg+xml`) of the North Indian diamond chart.

### Other Chart Types

| Endpoint | Description |
|----------|-------------|
| `POST /chart/svg` | North Indian Diamond (default) |
| `POST /chart/grid-svg` | Grid/Box chart |
| `POST /chart/east-svg` | East Indian chart |
| `POST /chart/moon-svg` | Moon-centered chart |
| `POST /chart/navamsa-svg` | Navamsa (D9) chart |
| `POST /chart/hora-svg` | Hora (D2) chart |
| `POST /chart/sudarshana-svg` | Sudarshana Chakra |
| `POST /chart/divisional-svg?d=N` | Any divisional chart (D1-D60) |

### Divisional Charts (Vargas)

The divisional chart endpoint supports all 60 vargas:

```bash
# Navamsa (D9)
POST /chart/divisional-svg?d=9

# Dashamamsa (D10) - Career
POST /chart/divisional-svg?d=10

# Shashtiamsa (D60) - Past Life
POST /chart/divisional-svg?d=60
```

**Request body:**
```json
{
  "name": "D9",
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata",
  "theme": "light"
}
```

---

## 8. Async Job System

For long-running operations (PDF generation, AI analysis), use the job queue:

### Submit a Job

```http
POST /jobs/submit-pdf
```

```json
{
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "10:30",
  "latitude": 28.6139,
  "longitude": 77.209,
  "timezone": "Asia/Kolkata",
  "clientName": "Rahul Sharma"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued",
  "message": "PDF generation job submitted"
}
```

### Check Job Status

```http
GET /jobs/{job_id}
```

```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "result_url": "/jobs/abc123/download"
}
```

### Download Result

```http
GET /jobs/{job_id}/download
```

Returns the generated PDF or AI analysis result.

---

## 9. Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 401 | Missing or invalid API key |
| 402 | Rate limit exceeded |
| 404 | Endpoint not found |
| 500 | Internal server error |

### Error Response Format

```json
{
  "detail": "Description of the error"
}
```

### Common Errors

**Missing API Key:**
```json
{ "detail": "Missing X-API-Key header" }
```

**Invalid API Key:**
```json
{ "detail": "Invalid or revoked API key" }
```

**Rate Limited:**
```json
{
  "detail": "Rate limit exceeded",
  "tier": "starter",
  "rate_limit": 1000,
  "requests_today": 1000
}
```

---

## 10. Integration Examples

### JavaScript / Node.js

```javascript
const axios = require('axios');

const API_KEY = 'avk_your_key_here';
const BASE = 'http://localhost:5000';

async function getBirthChart(dateOfBirth, timeOfBirth, lat, lon, tz) {
  const { data } = await axios.post(`${BASE}/api/kundli`, {
    dateOfBirth, timeOfBirth,
    latitude: lat, longitude: lon, timezone: tz
  }, {
    headers: { 'X-API-Key': API_KEY }
  });
  return data;
}

async function generatePDF(birthData, options = {}) {
  const { data } = await axios.post(`${BASE}/reports/full-pdf`, {
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
  return data; // Blob
}

// Usage
const chart = await getBirthChart('1990-05-15', '10:30', 28.6139, 77.209, 'Asia/Kolkata');
console.log(chart.data.planets);
```

### Python

```python
import requests

API_KEY = 'avk_your_key_here'
BASE = 'http://localhost:5000'

def get_birth_chart(date_of_birth, time_of_birth, lat, lon, tz):
    resp = requests.post(f'{BASE}/api/kundli', json={
        'dateOfBirth': date_of_birth,
        'timeOfBirth': time_of_birth,
        'latitude': lat,
        'longitude': lon,
        'timezone': tz
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
pdf_bytes = generate_pdf(
    chart_data,
    sections=['birth_details', 'kundli_chart', 'career', 'finance'],
    watermark='CONFIDENTIAL'
)
with open('report.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

### PHP

```php
<?php
$apiKey = 'avk_your_key_here';
$base = 'http://localhost:5000';

function getBirthChart($dob, $tob, $lat, $lon, $tz) {
    global $apiKey, $base;
    $ch = curl_init("$base/api/kundli");
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode([
            'dateOfBirth' => $dob,
            'timeOfBirth' => $tob,
            'latitude' => $lat,
            'longitude' => $lon,
            'timezone' => $tz
        ]),
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            "X-API-Key: $apiKey"
        ],
        CURLOPT_RETURNTRANSFER => true
    ]);
    return json_decode(curl_exec($ch), true);
}

// Usage
$chart = getBirthChart('1990-05-15', '10:30', 28.6139, 77.209, 'Asia/Kolkata');
print_r($chart['data']['planets']);
?>
```

### cURL Examples

```bash
# Get birth chart
curl -X POST http://localhost:5000/api/kundli \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_key" \
  -d '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}'

# Generate PDF with watermark
curl -X POST http://localhost:5000/reports/full-pdf \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_key" \
  -d '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","clientName":"Client","sections":["birth_details","kundli_chart","career"],"watermarkText":"DRAFT"}' \
  -o report.pdf

# Get SVG chart
curl -X POST http://localhost:5000/chart/svg \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_key" \
  -d '{"dateOfBirth":"1990-05-15","timeOfBirth":"10:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata","theme":"dark"}' \
  -o chart.svg

# Search location
curl "http://localhost:5000/api/location/search?q=Mumbai&limit=3" \
  -H "X-API-Key: avk_your_key"

# Get lucky color
curl -X POST http://localhost:5000/lucky/color \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_key" \
  -d '{"dateOfBirth":"1990-05-15"}'

# Compatibility check
curl -X POST http://localhost:5000/horoscope/compat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_your_key" \
  -d '{
    "maleDateOfBirth":"1990-05-15","maleTimeOfBirth":"10:30",
    "maleLatitude":28.6139,"maleLongitude":77.209,"maleTimezone":"Asia/Kolkata",
    "femaleDateOfBirth":"1992-03-20","femaleTimeOfBirth":"14:30",
    "femaleLatitude":19.076,"femaleLongitude":72.8777,"femaleTimezone":"Asia/Kolkata"
  }'
```

---

## 11. Endpoint Reference

### Charts & Kundli (9 endpoints)
- `POST /api/kundli` — Full birth chart
- `POST /chart/svg` — North Indian Diamond SVG
- `POST /chart/grid-svg` — Grid chart SVG
- `POST /chart/east-svg` — East Indian SVG
- `POST /chart/moon-svg` — Moon chart SVG
- `POST /chart/navamsa-svg` — Navamsa D9 SVG
- `POST /chart/hora-svg` — Hora D2 SVG
- `POST /chart/sudarshana-svg` — Sudarshana Chakra SVG
- `POST /chart/divisional-svg?d=N` — Divisional chart (D1-D60)

### Horoscope (12 endpoints)
- `POST /horoscope/daily` — Daily horoscope
- `POST /horoscope/weekly` — Weekly forecast
- `POST /horoscope/monthly` — Monthly overview
- `POST /horoscope/yearly` — Annual predictions
- `POST /horoscope/career` — Career predictions
- `POST /horoscope/love` — Love predictions
- `POST /horoscope/finance` — Finance predictions
- `POST /horoscope/health` — Health predictions
- `POST /horoscope/business` — Business predictions
- `POST /horoscope/education` — Education predictions
- `POST /horoscope/child` — Child predictions
- `POST /horoscope/foreign` — Foreign travel predictions

### Dasha (8 endpoints)
- `POST /horoscope/dasha/vimshottari` — Vimshottari
- `POST /horoscope/dasha/current` — Current dasha
- `POST /horoscope/dasha/details` — Dasha details
- `POST /horoscope/dasha/timeline` — Dasha timeline
- `POST /horoscope/dasha/chara` — Chara dasha
- `POST /dasha/yogini` — Yogini dasha
- `POST /dasha/kalachakra` — Kalachakra dasha
- `POST /dasha/ashtottari` — Ashtottari dasha

### Panchang (12 endpoints)
- `POST /horoscope/panchang` — Full panchang
- `POST /horoscope/panchang/rahu-kaal` — Rahu Kaal
- `POST /horoscope/panchang/gulika-kaal` — Gulika Kaal
- `POST /horoscope/panchang/yamaganda` — Yamaganda
- `POST /horoscope/panchang/choghadiya` — Choghadiya
- `POST /horoscope/panchang/hora` — Hora
- `POST /horoscope/panchang/moonrise` — Moonrise
- `POST /horoscope/panchang/moonset` — Moonset
- `POST /horoscope/panchang/abhijit-muhurat` — Abhijit Muhurat
- `POST /horoscope/panchang/panchaka` — Panchaka
- `POST /horoscope/panchang/gulika-position` — Gulika Position
- `POST /horoscope/panchang/roga-nidana` — Roga Nidana

### Transit (12 endpoints)
- `POST /horoscope/transit` — Full transit
- `POST /horoscope/transit/current` — Current transit
- `POST /horoscope/transit/prediction` — Transit predictions
- `POST /horoscope/transit/by-planet` — Transit by planet
- `POST /horoscope/transit/monthly` — Monthly transit
- `POST /horoscope/transit/timing` — Transit timing
- `POST /api/transit/planet-transit` — Planet transit detail
- `POST /api/transit/retrograde` — Retrograde planets
- `POST /api/transit/combust` — Combust planets
- `POST /api/transit/exalted` — Exalted planets
- `POST /api/transit/debilitated` — Debilitated planets
- `POST /api/transit/aspect` — Transit aspects

### Compatibility (8 endpoints)
- `POST /horoscope/compat` — Ashtakoot milan
- `POST /horoscope/compat/detailed` — Detailed compatibility
- `POST /api/compat/gun-milan` — Gun milan
- `POST /api/compat/nadi` — Nadi check
- `POST /api/compat/bhakoot` — Bhakoot check
- `POST /api/compat/yoni` — Yoni match
- `POST /api/compat/gana` — Gana match
- `POST /api/compat/tara` — Tara match

### Dosha (11 endpoints)
- `POST /horoscope/dosha/compute` — Compute all doshas
- `POST /horoscope/dosha/remedies` — Dosha remedies
- `POST /horoscope/dosha/severity` — Severity assessment
- `POST /horoscope/dosha/compatibility-impact` — Compatibility impact
- `POST /horoscope/dosha/dhaiya` — Dhaiya & Sade Sati
- `POST /api/dosha/grahan` — Grahan dosha
- `POST /api/dosha/shrapit` — Shrapit dosha
- `POST /api/dosha/manglik-detailed` — Manglik detailed
- `POST /api/dosha/nadi-dosha` — Nadi dosha
- `POST /api/dosha/bhakoot-dosha` — Bhakoot dosha
- `POST /api/dosha/yoni-compatibility` — Yoni compatibility

### PDF Reports (6 endpoints)
- `POST /reports/full-pdf` — Full customizable PDF
- `POST /reports/pdf-info` — Report info/preview
- `POST /reports/birth-chart` — Birth chart report
- `POST /reports/predictions` — Predictions report
- `POST /reports/career` — Career report
- `POST /reports/comprehensive` — Comprehensive report

### AI (8 endpoints)
- `POST /ai/chat` — AI chat
- `POST /ai/kundli-interpretation` — Kundli interpretation
- `POST /ai/horoscope-generation` — Horoscope generation
- `POST /ai/remedies` — AI remedies
- `POST /ai/prediction` — AI prediction
- `POST /ai/gemstone-advisor` — Gemstone advisor
- `POST /ai/career-analysis` — Career analysis
- `POST /ai/marriage-analysis` — Marriage analysis

### Calculator (6 endpoints)
- `POST /api/calculator/lagna` — Lagna calculator
- `POST /api/calculator/moon-sign` — Moon sign
- `POST /api/calculator/sun-sign` — Sun sign
- `POST /api/calculator/planet-strength` — Planet strength
- `POST /api/calculator/shadbala` — Shadbala
- `POST /api/calculator/ashtakavarga` — Ashtakavarga

### Gemstone (8 endpoints)
- `POST /api/gemstone/recommendation` — Recommendation
- `POST /api/gemstone/by-planet` — By planet
- `POST /api/gemstone/by-lagna` — By lagna
- `POST /api/gemstone/by-dasha` — By dasha
- `POST /api/gemstone/wearing` — Wearing guide
- `POST /api/gemstone/weight` — Weight calculator
- `POST /api/gemstone/metal` — Metal guide
- `POST /api/gemstone/finger` — Finger guide

### Numerology (10 endpoints)
- `POST /api/numerology/life-path` — Life path number
- `POST /api/numerology/destiny` — Destiny number
- `POST /api/numerology/soul` — Soul number
- `POST /api/numerology/expression` — Expression number
- `POST /api/numerology/mobile` — Mobile number
- `POST /api/numerology/vehicle` — Vehicle number
- `POST /api/numerology/business-name` — Business name
- `POST /api/numerology/baby-name` — Baby name
- `POST /api/numerology/name-number` — Name number
- `POST /api/numerology/name-compatibility` — Name compatibility

### Festival (9 endpoints)
- `POST /api/festival/hindu-festival` — Hindu festivals
- `POST /api/festival/ekadashi` — Ekadashi dates
- `POST /api/festival/sankranti` — Sankranti dates
- `POST /api/festival/purnima` — Purnima dates
- `POST /api/festival/amavasya` — Amavasya dates
- `POST /api/festival/chaturthi` — Chaturthi dates
- `POST /api/festival/navratri` — Navratri dates
- `POST /api/festival/diwali` — Diwali dates
- `POST /api/festival/holi` — Holi dates

### Calendar (11 endpoints)
- `POST /api/calendar/hindu` — Hindu calendar
- `POST /api/calendar/panchang` — Calendar panchang
- `POST /api/calendar/festival` — Calendar festivals
- `POST /api/calendar/muhurat` — Calendar muhurat
- `POST /calendar-api/hindu` — Calendar API Hindu
- `POST /calendar-api/panchang` — Calendar API Panchang
- `POST /calendar-api/festival` — Calendar API Festival
- `POST /calendar-api/muhurat` — Calendar API Muhurat
- `POST /api/calendar/year` — Year calendar
- `POST /api/calendar/year/monthly-summary` — Monthly summary
- `POST /api/calendar/year/auspicious-dates` — Auspicious dates

### Muhurat (9 endpoints)
- `POST /horoscope/muhurat/marriage` — Marriage muhurat
- `POST /horoscope/muhurat/vehicle-purchase` — Vehicle purchase
- `POST /horoscope/muhurat/house-warming` — House warming
- `POST /horoscope/muhurat/property-purchase` — Property purchase
- `POST /horoscope/muhurat/business-opening` — Business opening
- `POST /horoscope/muhurat/naming-ceremony` — Naming ceremony
- `POST /horoscope/muhurat/griha-pravesh` — Griha Pravesh
- `POST /horoscope/muhurat/engagement` — Engagement
- `POST /horoscope/muhurat/cesarean` — Cesarean muhurat

### Other Endpoints
- `POST /horoscope/bhava-chalit` — Bhava chalit chart
- `POST /horoscope/bhava-chalit/compare` — Bhava comparison
- `POST /horoscope/bhava-chalit/cusps` — Bhava cusps
- `POST /horoscope/yoga/predictions` — Yoga predictions
- `POST /horoscope/yoga/detailed` — Detailed yoga
- `POST /horoscope/yoga/score` — Yoga score
- `POST /horoscope/varshaphal` — Annual varshaphal
- `POST /horoscope/varshaphal/prediction` — Varshaphal prediction
- `POST /horoscope/varshaphal/tajika-aspects` — Tajika aspects
- `POST /pooja/recommendation` — Pooja recommendation
- `POST /pooja/temple` — Temple suggestion
- `POST /pooja/sankalp` — Sankalp
- `POST /pooja/booking` — Pooja booking
- `POST /pooja/availability` — Pooja availability
- `POST /lucky/color` — Lucky color
- `POST /lucky/number` — Lucky number
- `POST /lucky/day` — Lucky day
- `POST /lucky/metal` — Lucky metal
- `POST /api/rudraksha/recommendation` — Rudraksha recommendation
- `POST /api/rudraksha/mukhi-identification` — Mukhi identification
- `POST /api/rudraksha/wearing-method` — Wearing method
- `POST /api/rudraksha/mantra` — Rudraksha mantra
- `POST /api/rudraksha/benefits` — Rudraksha benefits
- `POST /api/prashna/chart` — Prashna chart
- `POST /api/prashna/judgement` — Prashna judgement
- `POST /api/utility/ayanamsa` — Ayanamsa calculator
- `POST /api/utility/ephemeris` — Ephemeris data
- `POST /api/utility/planet-speed` — Planet speed
- `POST /api/utility/lunar-phase` — Lunar phase
- `POST /api/utility/eclipse` — Eclipse data
- `POST /api/utility/sunrise-sunset` — Sunrise/sunset
- `POST /api/utility/julian-day` — Julian day number
- `POST /api/utility/rectify` — Birth rectification
- `POST /api/utility/ascendant-scan` — Ascendant scan
- `POST /api/utility/transit-verify` — Transit verify

### Location (4 endpoints)
- `GET /api/location/search?q=Delhi&limit=5` — Search locations
- `GET /api/location/reverse?lat=28.6139&lon=77.209` — Reverse geocode
- `GET /api/location/timezone?lat=28.6139&lon=77.209` — Timezone lookup
- `GET /api/location/popular?country=IN` — Popular locations

### Auth & Admin
- `POST /auth/register` — Register user
- `POST /auth/login` — Login
- `GET /auth/me` — Get current user
- `POST /auth/keys` — Create API key
- `GET /auth/keys` — List API keys
- `DELETE /auth/keys/{id}` — Revoke API key
- `GET /admin/users` — List users (admin)
- `PUT /admin/users/{id}/plan` — Update plan (admin)
- `GET /admin/stats` — Dashboard stats (admin)

### Jobs (4 endpoints)
- `POST /jobs/submit-pdf` — Submit PDF job
- `POST /jobs/submit-ai` — Submit AI job
- `GET /jobs/{id}` — Job status
- `GET /jobs/{id}/download` — Download result

---

## Appendix: Timezone Reference

Common timezones for birth data:

| Country | Timezone | Example |
|---------|----------|---------|
| India | `Asia/Kolkata` | IST (UTC+5:30) |
| USA (EST) | `America/New_York` | EST (UTC-5) |
| USA (PST) | `America/Los_Angeles` | PST (UTC-8) |
| UK | `Europe/London` | GMT (UTC+0) |
| UAE | `Asia/Dubai` | GST (UTC+4) |
| Singapore | `Asia/Singapore` | SGT (UTC+8) |
| Australia (AEST) | `Australia/Sydney` | AEST (UTC+10) |

---

**AstroVakta** — Built with FastAPI, Swiss Ephemeris, ReportLab, and CairoSVG.  
**216+ endpoints** | **North Indian Diamond Charts** | **D1-D60 Divisional Vargas** | **AI-Powered Insights**
