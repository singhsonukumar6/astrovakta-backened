# Vedic Astrology Python Backend (FastAPI)

This service exposes a FastAPI backend with Swagger UI for computing Vedic astrology Kundli outputs using Swiss Ephemeris (sidereal, Lahiri).

## Features
- Planets (Sun..Saturn, Rahu/Ketu; optional Uranus/Neptune/Pluto)
- Houses (Whole Sign or Placidus)
- Nakshatras, padas, lords
- Avastha (Baladi with odd/even sign rule)
- Status (Exalted/Debilitated/Own/Mooltrikona/Friendly/Enemy)
- Panchang (tithi, yoga, karana) at sunrise
- Sunrise/Sunset times
- Vimshottari Dasha (current + subperiods)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
```

Notes:
- Ensure the venv is activated in VS Code (Python: Select Interpreter → choose .venv).
- pyswisseph wheels are included for macOS arm64; for other platforms, pip will build from source.

Open Swagger UI: http://localhost:5000/docs

## Endpoint
- POST /api/kundli

Request body:
```
{
  "dateOfBirth": "1990-05-15",
  "timeOfBirth": "14:30",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timezone": "Asia/Kolkata",
  "propertyProfile": "traditional|astrotalk",
  "propertySource": "moon|ascendant|sunriseMoon",
  "houseSystem": "P|W",
  "nodeMode": "mean|true",
  "debug": true
}
```
