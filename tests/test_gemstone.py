"""Test gemstone recommendations."""

import pytest

pytestmark = pytest.mark.nodb

from app.routers.gemstone import GEMSTONE_DATA, PLANET_NAMES, _get_gemstone_info, _build_response


class TestGemstoneData:
    def test_all_planets_have_data(self):
        for p in PLANET_NAMES:
            assert p in GEMSTONE_DATA, f"{p} missing from GEMSTONE_DATA"

    def test_all_gemstones_have_required_fields(self):
        required = ["name", "hindiName", "imageUrl", "finger", "metal", "day",
                     "weightRange", "mantra", "color", "origin", "quality", "dos", "donts"]
        for p, data in GEMSTONE_DATA.items():
            for field in required:
                assert field in data, f"{p} gemstone missing field: {field}"

    def test_all_gemstones_have_image_url(self):
        for p, data in GEMSTONE_DATA.items():
            assert data["imageUrl"].startswith("/images/gemstones/"), f"{p} imageUrl invalid"
            assert data["imageUrl"].endswith(".webp"), f"{p} imageUrl not .webp"

    def test_dos_donts_are_lists(self):
        for p, data in GEMSTONE_DATA.items():
            assert isinstance(data["dos"], list), f"{p} dos is not list"
            assert isinstance(data["donts"], list), f"{p} donts is not list"
            assert len(data["dos"]) > 0, f"{p} has empty dos"
            assert len(data["donts"]) > 0, f"{p} has empty donts"

    def test_gemstone_names_differ(self):
        names = [data["name"] for data in GEMSTONE_DATA.values()]
        assert len(names) == len(set(names)), "Duplicate gemstone names"


class TestGemstoneAPI:
    def test_get_gemstone_info(self):
        sun = _get_gemstone_info("Sun")
        assert sun["name"] == "Ruby"
        assert sun["hindiName"] == "Manikya"
        assert "imageUrl" in sun

    def test_get_gemstone_info_with_weight(self):
        moon = _get_gemstone_info("Moon", 70)
        assert moon is not None
        assert "recommendedWeightRatti" in moon
        assert "recommendedWeightCarat" in moon

    def test_get_gemstone_info_invalid_planet(self):
        assert _get_gemstone_info("Pluto") is None

    def test_build_response_includes_image_url(self):
        info = _get_gemstone_info("Jupiter")
        resp = _build_response("Jupiter", info)
        assert resp["status"] == 200
        assert "imageUrl" in resp["gemstone"]
        assert resp["gemstone"]["imageUrl"] == "/images/gemstones/yellow-sapphire.webp"

    def test_build_response_404_for_none(self):
        resp = _build_response("Pluto", None)
        assert resp["status"] == 404
        assert "error" in resp
