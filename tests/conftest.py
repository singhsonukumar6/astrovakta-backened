"""Test fixtures and configuration."""

import os
import pytest

os.environ["JWT_SECRET"] = "test-secret-for-testing-only"

from app.database import get_db, init_db, USE_POSTGRES


@pytest.fixture(autouse=True)
def setup_test_db(request):
    if "nodb" in request.keywords:
        yield
        return
    if USE_POSTGRES:
        pytest.skip("Tests require SQLite (set DATABASE_URL='' or unset)")
    init_db()
    db = get_db()
    db.execute("PRAGMA foreign_keys=OFF")
    db.execute("DELETE FROM usage_logs")
    db.execute("DELETE FROM job_results")
    db.execute("DELETE FROM background_jobs")
    db.execute("DELETE FROM ai_providers")
    db.execute("DELETE FROM api_keys")
    db.execute("DELETE FROM password_resets")
    db.execute("DELETE FROM users")
    db.commit()
    db.execute("PRAGMA foreign_keys=ON")
    yield
    db.execute("PRAGMA foreign_keys=OFF")
    db.execute("DELETE FROM usage_logs")
    db.execute("DELETE FROM job_results")
    db.execute("DELETE FROM background_jobs")
    db.execute("DELETE FROM ai_providers")
    db.execute("DELETE FROM api_keys")
    db.execute("DELETE FROM password_resets")
    db.execute("DELETE FROM users")
    db.commit()
    db.execute("PRAGMA foreign_keys=ON")


@pytest.fixture
def test_api_key():
    from app.auth import create_user, create_api_key
    user = create_user("integration@example.com", "Integration Test", "secretpw123")
    key_info = create_api_key(user["id"], "Integration Key")
    return key_info["key"]


@pytest.fixture
def sample_birth_body():
    return {
        "dateOfBirth": "1990-05-15",
        "timeOfBirth": "14:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "Asia/Kolkata",
    }
