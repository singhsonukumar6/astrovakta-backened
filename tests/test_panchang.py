"""Test panchang calculations."""

import pytest

pytestmark = pytest.mark.nodb

from app.utils import panchang_at_jd, to_julian, TITHI_NAMES, NAKSHATRAS


class TestPanchang:
    def test_panchang_at_jd_returns_all_fields(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert "tithi" in p
        assert "tithiNumber" in p
        assert "nakshatra" in p
        assert "yoga" in p
        assert "karana" in p
        assert "paksha" in p
        assert "moonPhase" in p

    def test_tithi_number_range(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert 1 <= p["tithiNumber"] <= 30

    def test_tithi_name_valid(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert p["tithi"] in TITHI_NAMES

    def test_nakshatra_valid(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        nakshatras = [n[0] for n in NAKSHATRAS]
        assert p["nakshatra"] in nakshatras
