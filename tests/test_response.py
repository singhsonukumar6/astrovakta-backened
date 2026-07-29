"""Test unified response format."""

import json
import pytest

pytestmark = pytest.mark.nodb

from app.response import success, error, not_found, validation_error


class TestResponse:
    def _parse(self, resp):
        return json.loads(resp.body)

    def test_success_response(self):
        r = success({"planet": "Sun"})
        body = self._parse(r)
        assert body["success"] is True
        assert body["data"] == {"planet": "Sun"}
        assert r.status_code == 200

    def test_success_without_data(self):
        r = success(message="OK")
        body = self._parse(r)
        assert body["success"] is True
        assert body["message"] == "OK"
        assert r.status_code == 200

    def test_error_response(self):
        r = error("Something went wrong", 400)
        body = self._parse(r)
        assert body["success"] is False
        assert body["message"] == "Something went wrong"
        assert r.status_code == 400

    def test_not_found(self):
        r = not_found("Key not found")
        assert r.status_code == 404
        body = self._parse(r)
        assert body["success"] is False

    def test_validation_error(self):
        r = validation_error("Invalid date format")
        assert r.status_code == 422
        body = self._parse(r)
        assert body["success"] is False
