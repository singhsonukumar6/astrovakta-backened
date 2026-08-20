"""Test panchang calculations."""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.nodb

from app.utils import (
    panchang_at_jd, compute_panchang, to_julian,
    TITHI_NAMES, NAKSHATRAS, YOGA_NAMES, KARANA_SEQUENCE,
)
from app.models import PanchangRequest
from app.i18n import detect_language, translate_response, t as translate_t
from app.i18n.registry import get_category_translations


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

    def test_karana_valid(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert p["karana"] in KARANA_SEQUENCE

    def test_yoga_valid(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert p["yoga"] in YOGA_NAMES

    def test_paksha_values(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert p["paksha"] in ("Shukla", "Krishna")

    def test_moon_phase_values(self):
        jd = to_julian("2025-06-15", "12:00", "Asia/Kolkata")
        p = panchang_at_jd(jd)
        assert p["moonPhase"] in ("Waxing", "Waning", "Full Moon", "Amavasya")

    def test_karana_varies_across_dates(self):
        karanas = set()
        for month in range(1, 13):
            jd = to_julian(f"2025-{month:02d}-15", "12:00", "Asia/Kolkata")
            p = panchang_at_jd(jd)
            karanas.add(p["karana"])
        assert len(karanas) > 2, "Karana should vary across dates, not just 2 values"


class TestComputePanchang:
    def test_returns_sunrise_sunset(self):
        data = compute_panchang("2025-06-15", "12:00", "Asia/Kolkata", 28.6139, 77.2090)
        assert "sunrise" in data
        assert "sunset" in data
        assert data["sunrise"] is not None
        assert data["sunset"] is not None

    def test_returns_all_core_fields(self):
        data = compute_panchang("2025-06-15", "12:00", "Asia/Kolkata", 28.6139, 77.2090)
        for field in ["tithi", "tithiNumber", "nakshatra", "yoga", "karana", "paksha", "moonPhase"]:
            assert field in data

    def test_different_locations(self):
        delhi = compute_panchang("2025-06-15", "12:00", "Asia/Kolkata", 28.6139, 77.2090)
        mumbai = compute_panchang("2025-06-15", "12:00", "Asia/Kolkata", 19.0760, 72.8777)
        assert delhi["sunrise"] != mumbai["sunrise"] or delhi["sunset"] != mumbai["sunset"]


class TestPanchangRequestModel:
    def test_new_field_names(self):
        req = PanchangRequest(
            date="2025-06-15",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
        )
        assert req.date == "2025-06-15"
        assert req.latitude == 28.6139

    def test_legacy_field_names(self):
        req = PanchangRequest(
            dateOfBirth="2025-06-15",
            timeOfBirth="14:30",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
        )
        assert req.date == "2025-06-15"
        assert req.time == "14:30"

    def test_missing_date_raises_error(self):
        with pytest.raises(ValidationError):
            PanchangRequest(
                latitude=28.6139,
                longitude=77.2090,
                timezone="Asia/Kolkata",
            )

    def test_time_is_optional(self):
        req = PanchangRequest(
            date="2025-06-15",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
        )
        assert req.time is None

    def test_latitude_out_of_range(self):
        with pytest.raises(ValidationError):
            PanchangRequest(
                date="2025-06-15",
                latitude=91,
                longitude=77.2090,
                timezone="Asia/Kolkata",
            )


class TestI18n:
    def test_detect_language_default(self):
        assert detect_language() == "en"

    def test_detect_language_from_query(self):
        assert detect_language(query_lang="hi") == "hi"

    def test_detect_language_from_header(self):
        assert detect_language(header_lang="hi-IN") == "hi"

    def test_detect_language_query_takes_priority(self):
        assert detect_language(query_lang="ta", header_lang="hi") == "ta"

    def test_detect_language_invalid_falls_back(self):
        assert detect_language(query_lang="xx") == "en"

    def test_translate_value_hindi(self):
        result = translate_t("hi", "tithi", "Ekadashi")
        assert result == "एकादशी"

    def test_translate_value_english_passthrough(self):
        result = translate_t("en", "tithi", "Ekadashi")
        assert result == "Ekadashi"

    def test_translate_value_unknown_falls_back(self):
        result = translate_t("hi", "tithi", "UnknownTithi")
        assert result == "UnknownTithi"

    def test_translate_response_dict(self):
        data = {"tithi": "Ekadashi", "nakshatra": "Rohini", "count": 42}
        field_map = {"tithi": "tithi", "nakshatra": "nakshatra"}
        result = translate_response(data, "hi", field_map)
        assert result["tithi"] == "एकादशी"
        assert result["nakshatra"] == "रोहिणी"
        assert result["count"] == 42

    def test_translate_response_nested(self):
        data = {"outer": {"weekday": "Sunday"}}
        result = translate_response(data, "hi", {"weekday": "weekday"})
        assert result["outer"]["weekday"] == "रविवार"

    def test_translate_response_list(self):
        data = [{"name": "Amrit"}, {"name": "Rog"}]
        result = translate_response(data, "hi", {"name": "choghadiya"})
        assert result[0]["name"] == "अमृत"
        assert result[1]["name"] == "रोग"

    def test_hindi_tithi_translations_complete(self):
        hi_tithi = get_category_translations("hi", "tithi")
        assert len(hi_tithi) >= 16  # At least all unique tithi names

    def test_hindi_nakshatra_translations_complete(self):
        hi_nak = get_category_translations("hi", "nakshatra")
        assert len(hi_nak) == 27

    def test_hindi_weekday_translations_complete(self):
        hi_wd = get_category_translations("hi", "weekday")
        assert len(hi_wd) == 7

    def test_lang_field_on_request_model(self):
        req = PanchangRequest(
            date="2025-06-15",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
            lang="hi",
        )
        assert req.lang == "hi"

    def test_lang_field_defaults_to_en(self):
        req = PanchangRequest(
            date="2025-06-15",
            latitude=28.6139,
            longitude=77.2090,
            timezone="Asia/Kolkata",
        )
        assert req.lang == "en"
