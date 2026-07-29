# AstroVakta — Vedic Astrology API

**216+ endpoints** covering birth charts, dasha, panchang, doshas, yogas, compatibility, muhurat, transit, numerology, gemstones, rudraksha, AI interpretations, PDF reports, and more.

Built with FastAPI + Swiss Ephemeris (sidereal, Lahiri ayanamsa). Dual-backend (SQLite for dev, PostgreSQL for production), Docker-ready, with a React admin dashboard.

---

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set required env vars
export JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

uvicorn app.main:app --reload --port 5000
```

Open **Swagger UI**: http://localhost:5000/docs

---

## Features (216+ Endpoints)

### Core Astrology
| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Birth Chart** | `POST /api/kundli` | Full chart: planets, houses, nakshatras, lords, divisional charts D1-D60, yogas, doshas, dasha, panchang, KP details |
| **Planet Details** | `POST /horoscope/planet-details` | Per-planet degree, nakshatra, lord status, avastha, personalized predictions |
| **Charts - Visual** | 8 endpoints | SVG charts: North Indian, South Indian, East Indian, Grid, Moon-centered, Navamsa D9, Hora D2, Sudarshana |
| **Charts - Divisional** | `POST /api/kundli` | All 16 vargas D1-D60 with planet placements |
| **Bhava Chalit** | 3 endpoints | Bhava chart with cusps, house midpoints |

### Dasha Systems
| System | Endpoints | Details |
|--------|-----------|---------|
| **Vimshottari** | `POST /dasha` | 120-yr cycle, MD/AD/PD/Sookshma (4 levels) |
| **Yogini** | `POST /dasha/yogini` | 36-yr cycle, 16 yoginis |
| **Kalachakra** | `POST /dasha/kalachakra` | Based on Moon's nakshatra padas |
| **Ashtottari** | `POST /dasha/ashtottari` | 108-yr cycle |
| **Chara** | `POST /dasha/chara` | Sign-based dasha |

### Panchang & Muhurat
| Feature | Endpoints | Description |
|---------|-----------|-------------|
| **Panchang** | `POST /panchang` | Tithi, nakshatra, yoga, karana, sunrise/sunset |
| **Abhijit Muhurat** | `POST /panchang/abhijit-muhurat` | Most auspicious 48-min window daily |
| **Muhurat Engine** | 8 endpoints | Marriage, vehicle, house-warming, business, naming, engagement, property, cesarean |
| **Choghadiya** | Included in muhurat | Day/night choghadiya with ratings |

### Dosha Detection (9 types)
- Mangal Dosha, Kaal Sarp Dosha, Pitra Dosha, Shani Dosha
- Guru Chandal Dosha, Kemadruma Dosha, Sade Sati Indicator
- Angarak Dosha, Rahu-Ketu Kendra Dosha
- Each with severity, remedies, and cancellation factors

### Yoga Detection (20+ types)
Pancha Mahapurusha, Gajakesari, Neecha Bhanga, Budha Aditya, Chandra Mangala, Dhana, Raja Yoga, Viparita Raja, Guru Chandal, Saraswati, Lakshmi, and more.

### Transit Analysis
| Feature | Endpoints | Description |
|---------|-----------|-------------|
| **Current Transit** | `POST /transit` | Planet positions with house transit |
| **Transit Predictions** | `POST /transit/predictions` | Transit effects on natal chart |
| **Transit Detail** | `POST /transit/detail` | Detailed transit analysis |

### Compatibility (Matchmaking)
- **Ashtakoot Milan**: 8 kootas (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi)
- Gun matching with total score and per-koota breakdown
- Marriage compatibility analysis

### Muhurat Engine
Computationally calculates auspicious windows using:
- Sunrise/sunset, Rahu Kaal, Gulika Kaal, Yamaganda
- Choghadiya (day/night) with tithi/nakshatra/yoga filtering
- Rating system: excellent / good / avoid

### KP Astrology (6 endpoints)
- Planet star lord & sub lord table
- Cuspal lords with significations
- Bhava Chalit with midpoints
- Ruling planets (asc lord, star lord, sub lord, day lord)
- Horary astrology with keyword-to-house mapping

### Lal Kitab (3 endpoints)
- 12 house significations with remedies
- 9 planet interpretations
- Full chart analysis with house-by-house breakdown

### Yogini Dosha
- Moon-based yogini calculation (16 yoginis across 27 nakshatras)
- Severity assessment with cross-references to Mars/Saturn placement

### Numerology (8+ endpoints)
- Life Path, Destiny, Soul Urge, Expression numbers
- Name-based numerology (Business, Baby, Mobile, Vehicle names)
- Lucky color, number, day, metal

### Festivals (astronomically computed)
- 17+ major Hindu festivals computed dynamically via Swiss Ephemeris
- Ekadashi (24/year), Sankranti (12), Purnima, Amavasya
- Works for ANY year (not limited to hardcoded date ranges)

### Gemstone Recommendations (9 endpoints)
- Per-planet gemstone: Ruby, Pearl, Red Coral, Emerald, Yellow Sapphire, Diamond, Blue Sapphire, Hessonite, Cat's Eye
- Weight calculation (body weight → ratti → carat)
- Wearing instructions, metal, finger, mantra, dos/donts
- Image URLs included for UI display

### Rudraksha Recommendations
- Rudraksha identification by face count
- Recommendations based on birth chart / planet

### Horoscope Text (8 endpoints)
- Daily, Weekly, Monthly, Yearly
- Career, Love, Finance, Health

### Predictions (4 endpoints)
- Business, Education, Child, Foreign Travel

### Varshaphal (Annual Solar Return)
- Tajika aspects, yearly chart, prediction

### Prashna (Horary Astrology)
- Question-based analysis using KP principles

### Pooja Recommendations
- Remedial pooja suggestions based on chart analysis

### PDF Reports
- 23 configurable sections (Kundli, Dasha, Dosha, Yogas, Gemstone, Rudraksha, Predictions, etc.)
- Custom branding, watermark, company details
- Async job system with status polling

### AI Interpretations
- Multi-provider: OpenAI, Anthropic, Groq, Together AI
- Encrypted API key storage
- Specialized agents: career, relationship, finance, health, education, gemstone advisor

### Calendar (4 endpoints)
- Hindu calendar, festival calendar, monthly calendar
- Auspicious date suggestions by purpose

### Location Services
- City search (Nominatim), reverse geocode, timezone lookup

---

## Authentication

Register, get an API key, and pass it via the `X-API-Key` header:

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","name":"Dev","password":"secret123"}'

# Response includes api_key: avk_xxxxxxxx...
curl -X POST http://localhost:5000/api/kundli \
  -H "Content-Type: application/json" \
  -H "X-API-Key: avk_xxxxxxxx..." \
  -d '{"dateOfBirth":"1990-05-15","timeOfBirth":"14:30","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}'
```

### Rate Limits (per key, daily, resets at midnight UTC)
| Tier | Limit |
|------|-------|
| Free | 100 req/day |
| Starter | 1,000 req/day |
| Pro | 10,000 req/day |
| Enterprise | Unlimited |

---

## One-Click Example

```bash
# Get full birth chart
curl -s -X POST http://localhost:5000/api/kundli \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "dateOfBirth": "1990-05-15",
    "timeOfBirth": "14:30",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata"
  }' | python3 -m json.tool
```

---

## Docker Deployment

```bash
docker-compose up --build
```

This starts:
- **api**: FastAPI on port 5000
- **worker**: Celery worker for async PDF/AI jobs
- **redis**: Message broker for Celery

Production deployment included: `deploy.sh` + `nginx.conf` with SSL via Certbot.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI (Python 3.11+) |
| Ephemeris | Swiss Ephemeris (`pyswisseph`) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Async Jobs | Celery + Redis |
| Frontend | React + Vite |
| Auth | bcrypt + JWT |
| Encryption | Fernet (AES-128) |
| AI | OpenAI, Anthropic, Groq, Together AI |

---

## Full API Documentation

See **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** (1000+ lines) for the complete endpoint reference with request/response examples in curl, Python, JavaScript, and PHP.
