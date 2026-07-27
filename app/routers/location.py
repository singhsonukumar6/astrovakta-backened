from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import httpx
import logging

router = APIRouter()

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "AstroVakta/2.0 (astrology-app)"


@router.get('/location/search')
async def search_location(
    q: str = Query(..., min_length=2, max_length=100, example="New Delhi", description="Search query (city name, address, etc.)"),
    limit: int = Query(5, ge=1, le=20, example=5, description="Number of results to return"),
    countrycode: Optional[str] = Query(None, example="in", description="ISO 3166-1 country code to filter results"),
) -> Dict[str, Any]:
    """
    Search for locations using OpenStreetMap Nominatim (free, no API key needed).
    Returns place names with latitude, longitude, and administrative details.
    Rate limited to 1 request per second by Nominatim policy.
    """
    params = {
        'q': q,
        'format': 'json',
        'limit': limit,
        'addressdetails': 1,
        'accept-language': 'en',
    }
    if countrycode:
        params['countrycodes'] = countrycode

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NOMINATIM_URL}/search",
                params=params,
                headers={'User-Agent': USER_AGENT}
            )
            response.raise_for_status()
            results = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Location service timeout. Please try again.")
    except httpx.HTTPStatusError as e:
        logging.error(f"Nominatim HTTP error: {e}")
        raise HTTPException(status_code=502, detail="Location service error.")
    except Exception as e:
        logging.error(f"Location search error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search locations.")

    locations = []
    for r in results:
        addr = r.get('address', {})
        location = {
            'displayName': r.get('display_name', ''),
            'name': r.get('name', ''),
            'latitude': float(r.get('lat', 0)),
            'longitude': float(r.get('lon', 0)),
            'type': r.get('type', ''),
            'category': r.get('category', ''),
            'importance': r.get('importance', 0),
            'address': {
                'city': addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county', ''),
                'state': addr.get('state', ''),
                'country': addr.get('country', ''),
                'countryCode': addr.get('country_code', ''),
                'postcode': addr.get('postcode', ''),
            }
        }
        locations.append(location)

    return {
        'status': 200,
        'query': q,
        'count': len(locations),
        'locations': locations,
    }


@router.get('/location/reverse')
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90, example=28.6139, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, example=77.2090, description="Longitude"),
) -> Dict[str, Any]:
    """
    Reverse geocode: convert latitude/longitude to a human-readable address.
    """
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'addressdetails': 1,
        'accept-language': 'en',
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NOMINATIM_URL}/reverse",
                params=params,
                headers={'User-Agent': USER_AGENT}
            )
            response.raise_for_status()
            result = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Location service timeout.")
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="Location service error.")
    except Exception as e:
        logging.error(f"Reverse geocode error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reverse geocode.")

    addr = result.get('address', {})
    return {
        'status': 200,
        'displayName': result.get('display_name', ''),
        'latitude': lat,
        'longitude': lon,
        'address': {
            'city': addr.get('city') or addr.get('town') or addr.get('village', ''),
            'state': addr.get('state', ''),
            'country': addr.get('country', ''),
            'countryCode': addr.get('country_code', ''),
            'postcode': addr.get('postcode', ''),
        }
    }


@router.get('/location/timezone')
async def get_timezone(
    lat: float = Query(..., ge=-90, le=90, example=28.6139),
    lon: float = Query(..., ge=-180, le=180, example=77.2090),
) -> Dict[str, Any]:
    """
    Get the IANA timezone for given coordinates using Nominatim's timezone data.
    Falls back to a common mapping for Indian cities.
    """
    # For India, quick check
    if 6.0 <= lat <= 37.0 and 68.0 <= lon <= 97.5:
        return {
            'status': 200,
            'timezone': 'Asia/Kolkata',
            'offset': '+05:30',
            'country': 'India',
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NOMINATIM_URL}/reverse",
                params={'lat': lat, 'lon': lon, 'format': 'json', 'accept-language': 'en'},
                headers={'User-Agent': USER_AGENT}
            )
            response.raise_for_status()
            result = response.json()
            addr = result.get('address', {})
            country = addr.get('country', '')

            # Common timezone mappings
            timezone_map = {
                'India': 'Asia/Kolkata',
                'United States': 'America/New_York',
                'United Kingdom': 'Europe/London',
                'Australia': 'Australia/Sydney',
                'Canada': 'America/Toronto',
                'Germany': 'Europe/Berlin',
                'France': 'Europe/Paris',
                'Japan': 'Asia/Tokyo',
                'China': 'Asia/Shanghai',
                'Brazil': 'America/Sao_Paulo',
                'Russia': 'Europe/Moscow',
                'South Africa': 'Africa/Johannesburg',
                'UAE': 'Asia/Dubai',
                'Saudi Arabia': 'Asia/Riyadh',
                'Singapore': 'Asia/Singapore',
                'Sri Lanka': 'Asia/Colombo',
                'Nepal': 'Asia/Kathmandu',
                'Bangladesh': 'Asia/Dhaka',
                'Pakistan': 'Asia/Karachi',
            }

            tz = timezone_map.get(country, 'UTC')
            return {
                'status': 200,
                'timezone': tz,
                'country': country,
                'city': addr.get('city') or addr.get('town', ''),
            }
    except Exception:
        return {
            'status': 200,
            'timezone': 'UTC',
            'country': 'Unknown',
            'note': 'Could not determine timezone. Please enter manually.',
        }


# Popular Indian cities for quick selection
POPULAR_CITIES = [
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "timezone": "Asia/Kolkata", "state": "Maharashtra"},
    {"name": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata", "state": "Delhi"},
    {"name": "Bangalore", "latitude": 12.9716, "longitude": 77.5946, "timezone": "Asia/Kolkata", "state": "Karnataka"},
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867, "timezone": "Asia/Kolkata", "state": "Telangana"},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata", "state": "Tamil Nadu"},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "timezone": "Asia/Kolkata", "state": "West Bengal"},
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567, "timezone": "Asia/Kolkata", "state": "Maharashtra"},
    {"name": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714, "timezone": "Asia/Kolkata", "state": "Gujarat"},
    {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873, "timezone": "Asia/Kolkata", "state": "Rajasthan"},
    {"name": "Varanasi", "latitude": 25.3176, "longitude": 82.9739, "timezone": "Asia/Kolkata", "state": "Uttar Pradesh"},
    {"name": "Lucknow", "latitude": 26.8467, "longitude": 80.9462, "timezone": "Asia/Kolkata", "state": "Uttar Pradesh"},
    {"name": "Kanpur", "latitude": 26.4499, "longitude": 80.3319, "timezone": "Asia/Kolkata", "state": "Uttar Pradesh"},
    {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882, "timezone": "Asia/Kolkata", "state": "Maharashtra"},
    {"name": "Indore", "latitude": 22.7196, "longitude": 75.8577, "timezone": "Asia/Kolkata", "state": "Madhya Pradesh"},
    {"name": "Thiruvananthapuram", "latitude": 8.5241, "longitude": 76.9366, "timezone": "Asia/Kolkata", "state": "Kerala"},
    {"name": "Bhopal", "latitude": 23.2599, "longitude": 77.4126, "timezone": "Asia/Kolkata", "state": "Madhya Pradesh"},
    {"name": "Patna", "latitude": 25.6093, "longitude": 85.1376, "timezone": "Asia/Kolkata", "state": "Bihar"},
    {"name": "Chandigarh", "latitude": 30.7333, "longitude": 76.7794, "timezone": "Asia/Kolkata", "state": "Chandigarh"},
    {"name": "Guwahati", "latitude": 26.1445, "longitude": 91.7362, "timezone": "Asia/Kolkata", "state": "Assam"},
    {"name": "Dehradun", "latitude": 30.3165, "longitude": 78.0322, "timezone": "Asia/Kolkata", "state": "Uttarakhand"},
    {"name": "Rishikesh", "latitude": 30.0869, "longitude": 78.2676, "timezone": "Asia/Kolkata", "state": "Uttarakhand"},
    {"name": "Haridwar", "latitude": 29.9457, "longitude": 78.1642, "timezone": "Asia/Kolkata", "state": "Uttarakhand"},
    {"name": "Ujjain", "latitude": 23.1765, "longitude": 75.7885, "timezone": "Asia/Kolkata", "state": "Madhya Pradesh"},
    {"name": "Mathura", "latitude": 27.4924, "longitude": 77.6737, "timezone": "Asia/Kolkata", "state": "Uttar Pradesh"},
    {"name": "Ayodhya", "latitude": 26.7922, "longitude": 82.1998, "timezone": "Asia/Kolkata", "state": "Uttar Pradesh"},
    {"name": "Prayagraj", "latitude": 25.4358, "longitude": 81.8463, "timezone": "Asia/Kolkata", "state": "Uttar Pradesh"},
]


@router.get('/location/popular')
async def popular_cities(
    country: Optional[str] = Query(None, example="in", description="Filter by country code"),
) -> Dict[str, Any]:
    """
    Return popular cities for quick selection (no external API call).
    """
    cities = POPULAR_CITIES
    if country and country.lower() == 'in':
        cities = [c for c in cities if c.get('timezone') == 'Asia/Kolkata']
    return {
        'status': 200,
        'count': len(cities),
        'cities': cities,
    }
