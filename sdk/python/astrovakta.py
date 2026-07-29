"""
AstroVakta Python SDK
Lightweight, production-ready developer client for the AstroVakta Vedic Astrology API.
"""

import logging
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger("astrovakta")


class AstroVaktaClient:
    """Client wrapper for interacting with the AstroVakta API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:5000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "AstroVakta-Python-SDK/1.0.0"
        })

    def _request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self.session.request(method, url, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AstroVakta API Request failed: {e}")
            raise RuntimeError(f"AstroVakta request failed: {e}")

    # --- Core Astrology ---
    def get_kundli(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete Vedic birth chart (Kundli), including planets, houses, divisional charts, yogas, doshas, etc.
        
        Example birth_details:
        {
            "dateOfBirth": "1990-05-15",
            "timeOfBirth": "14:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata"
        }
        """
        return self._request("POST", "/api/kundli", birth_details)

    def get_planet_details(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get per-planet local/global degrees, lord status, avastha, and predictions."""
        return self._request("POST", "/horoscope/planet-details", birth_details)

    # --- Calculations & Charts ---
    def get_panchang(self, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Tithi, Nakshatra, Yoga, Karana, Sunrise, and Sunset."""
        return self._request("POST", "/horoscope/panchang", request_params)

    # --- New Modules (Yogini, Lal Kitab, KP) ---
    def get_yogini_dosha(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Yogini Dosha based on Moon's birth nakshatra."""
        return self._request("POST", "/yogini/dosha", birth_details)

    def get_lal_kitab_analysis(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get full Lal Kitab chart analysis, house significations, and planetary traits."""
        return self._request("POST", "/lal-kitab/chart-analysis", birth_details)

    def get_kp_planet_details(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get KP cuspal lords, sub-lords, and star-lords for planets."""
        return self._request("POST", "/kp/planet-details", birth_details)

    def kp_horary_query(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve a horary query using KP systems and significator strength."""
        return self._request("POST", "/kp/horary", query_params)

    # --- Gemstones & Remediations ---
    def get_gemstone_recommendation(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get primary and alternate gemstone recommendations with wearing instructions."""
        return self._request("POST", "/api/gemstone/recommendation", birth_details)

    # --- Astronomical Festivals ---
    def get_hindu_festivals(self, year: int, month: Optional[int] = None) -> Dict[str, Any]:
        """Get dynamically calculated major Hindu festival dates for any year."""
        params = {"year": year}
        if month:
            params["month"] = month
        return self._request("POST", "/api/festival/hindu-festival", params)
