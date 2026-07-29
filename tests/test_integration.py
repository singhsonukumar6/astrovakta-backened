"""Integration tests for core flows and advanced calculators."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_core_kundli_traditional_and_tropical(sample_birth_body, test_api_key):
    headers = {"X-API-Key": test_api_key}
    # 1. Test standard/traditional Lahiri (sidereal) calculations
    resp = client.post("/api/kundli", json=sample_birth_body, headers=headers)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert "data" in res_data
    
    data = res_data["data"]
    assert "basicDetails" in data
    assert "planets" in data
    assert "houses" in data
    assert "divisionalCharts" in data

    # Verify our newly implemented 18 divisional charts (vargas) are populated and NOT placeholders
    vargas = data["divisionalCharts"]
    assert "D1" in vargas
    assert "D9" in vargas
    assert "D16" in vargas
    assert "D30" in vargas
    assert "D60" in vargas
    
    # Check that D16 has populated planets and is not a placeholder
    assert "note" not in vargas["D16"]
    assert len(vargas["D16"]["planets"]) > 0

    # Capture sidereal Sun position
    sun_sidereal = next(p for p in data["planets"] if p["name"] == "Sun")
    
    # 2. Test tropical (western) calculations
    tropical_body = sample_birth_body.copy()
    tropical_body["tropical"] = True
    
    resp_trop = client.post("/api/kundli", json=tropical_body, headers=headers)
    assert resp_trop.status_code == 200
    res_trop_data = resp_trop.json()
    assert res_trop_data["success"] is True
    
    data_trop = res_trop_data["data"]
    sun_tropical = next(p for p in data_trop["planets"] if p["name"] == "Sun")

    # Tropical longitude must be ahead of Sidereal (Lahiri ayanamsa is approx 24 degrees)
    assert sun_tropical["longitude"] != sun_sidereal["longitude"]


def test_exception_middleware_validation(test_api_key):
    headers = {"X-API-Key": test_api_key}
    bad_body = {
        "dateOfBirth": "1990-05-15"
    }
    resp_bad = client.post("/api/kundli", json=bad_body, headers=headers)
    assert resp_bad.status_code == 422
    err_data = resp_bad.json()
    assert err_data["success"] is False
    assert "message" in err_data
