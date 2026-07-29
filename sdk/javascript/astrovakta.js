/**
 * AstroVakta JavaScript SDK
 * Lightweight, production-ready developer client for the AstroVakta Vedic Astrology API.
 */

class AstroVaktaClient {
  /**
   * Create an AstroVakta API client.
   * @param {string} apiKey - Your AstroVakta API Key.
   * @param {string} [baseUrl="http://localhost:5000"] - Base URL of the API.
   */
  constructor(apiKey, baseUrl = "http://localhost:5000") {
    if (!apiKey) {
      throw new Error("AstroVakta SDK: API Key is required.");
    }
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  /**
   * Internal request helper.
   * @private
   */
  async _request(method, path, body = null) {
    const url = `${this.baseUrl}/${path.replace(/^\//, "")}`;
    const headers = {
      "X-API-Key": this.apiKey,
      "Content-Type": "application/json",
      "User-Agent": "AstroVakta-JS-SDK/1.0.0"
    };

    const config = {
      method,
      headers,
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.message || `HTTP error! Status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`AstroVakta API Request failed on ${path}:`, error.message);
      throw error;
    }
  }

  // --- Core Astrology ---
  
  /**
   * Get complete Vedic birth chart (Kundli), including planets, houses, divisional charts, yogas, doshas, etc.
   * @param {Object} birthDetails 
   * @returns {Promise<Object>}
   */
  getKundli(birthDetails) {
    return this._request("POST", "/api/kundli", birthDetails);
  }

  /**
   * Get per-planet local/global degrees, lord status, avastha, and predictions.
   * @param {Object} birthDetails
   * @returns {Promise<Object>}
   */
  getPlanetDetails(birthDetails) {
    return this._request("POST", "/horoscope/planet-details", birthDetails);
  }

  // --- Calculations & Charts ---

  /**
   * Get Tithi, Nakshatra, Yoga, Karana, Sunrise, and Sunset.
   * @param {Object} requestParams
   * @returns {Promise<Object>}
   */
  getPanchang(requestParams) {
    return this._request("POST", "/horoscope/panchang", requestParams);
  }

  // --- New Modules (Yogini, Lal Kitab, KP) ---

  /**
   * Calculate Yogini Dosha based on Moon's birth nakshatra.
   * @param {Object} birthDetails
   * @returns {Promise<Object>}
   */
  getYoginiDosha(birthDetails) {
    return this._request("POST", "/yogini/dosha", birthDetails);
  }

  /**
   * Get full Lal Kitab chart analysis, house significations, and planetary traits.
   * @param {Object} birthDetails
   * @returns {Promise<Object>}
   */
  getLalKitabAnalysis(birthDetails) {
    return this._request("POST", "/lal-kitab/chart-analysis", birthDetails);
  }

  /**
   * Get KP cuspal lords, sub-lords, and star-lords for planets.
   * @param {Object} birthDetails
   * @returns {Promise<Object>}
   */
  getKpPlanetDetails(birthDetails) {
    return this._request("POST", "/kp/planet-details", birthDetails);
  }

  /**
   * Solve a horary query using KP systems and significator strength.
   * @param {Object} queryParams
   * @returns {Promise<Object>}
   */
  kpHoraryQuery(queryParams) {
    return this._request("POST", "/kp/horary", queryParams);
  }

  // --- Gemstones & Remediations ---

  /**
   * Get primary and alternate gemstone recommendations with wearing instructions.
   * @param {Object} birthDetails
   * @returns {Promise<Object>}
   */
  getGemstoneRecommendation(birthDetails) {
    return this._request("POST", "/api/gemstone/recommendation", birthDetails);
  }

  // --- Astronomical Festivals ---

  /**
   * Get dynamically calculated major Hindu festival dates for any year.
   * @param {number} year
   * @param {number} [month]
   * @returns {Promise<Object>}
   */
  getHinduFestivals(year, month = null) {
    const params = { year };
    if (month) {
      params.month = month;
    }
    return this._request("POST", "/api/festival/hindu-festival", params);
  }
}

// Support CommonJS & ES6 Module environments
if (typeof module !== "undefined" && module.exports) {
  module.exports = { AstroVaktaClient };
} else if (typeof window !== "undefined") {
  window.AstroVaktaClient = AstroVaktaClient;
}
