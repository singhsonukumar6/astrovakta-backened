"""Test authentication and API key management."""

import pytest

from app.auth import (
    create_user, authenticate_user, get_user_by_id, get_user_by_email,
    create_api_key, validate_api_key, revoke_api_key, list_api_keys,
    get_usage_stats, hash_password, verify_password, generate_api_key,
    change_password, update_email, update_user_profile,
)


class TestAuth:
    def test_hash_and_verify_password(self):
        pw = "my-secret-password!123"
        h = hash_password(pw)
        assert h != pw
        assert verify_password(pw, h)
        assert not verify_password("wrong-password", h)

    def test_create_user(self):
        user = create_user("test@example.com", "Test User", "password123")
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"
        assert user["plan"] == "free"

    def test_create_duplicate_email_raises_error(self):
        create_user("dup@example.com", "First", "pw1")
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            create_user("dup@example.com", "Second", "pw2")

    def test_authenticate_user_valid(self):
        create_user("auth@example.com", "Auth User", "correctpw")
        user = authenticate_user("auth@example.com", "correctpw")
        assert user is not None
        assert user["email"] == "auth@example.com"

    def test_authenticate_user_invalid(self):
        create_user("auth2@example.com", "Auth2", "pw")
        assert authenticate_user("auth2@example.com", "wrongpw") is None
        assert authenticate_user("nonexistent@example.com", "pw") is None

    def test_get_user_by_id(self):
        user = create_user("byid@example.com", "By ID", "pw")
        fetched = get_user_by_id(user["id"])
        assert fetched is not None
        assert fetched["email"] == "byid@example.com"

    def test_get_user_by_email(self):
        create_user("byemail@example.com", "By Email", "pw")
        fetched = get_user_by_email("byemail@example.com")
        assert fetched is not None
        assert fetched["name"] == "By Email"

    def test_generate_api_key_format(self):
        key = generate_api_key()
        assert key.startswith("avk_")
        assert len(key) == 36  # avk_ + 32 hex chars


class TestAPIKey:
    def test_create_and_validate_key(self):
        user = create_user("apikey@example.com", "Key User", "pw")
        ak = create_api_key(user["id"], "Test Key")
        assert ak["key"].startswith("avk_")
        assert ak["tier"] == "free"
        assert ak["is_active"] is True or ak["is_active"] == 1

        validated = validate_api_key(ak["key"])
        assert validated is not None
        assert validated["email"] == "apikey@example.com"

    def test_validate_invalid_key(self):
        assert validate_api_key("avk_invalid_key_12345") is None

    def test_revoke_key(self):
        user = create_user("revoke@example.com", "Revoke", "pw")
        ak = create_api_key(user["id"], "To Revoke")
        assert revoke_api_key(ak["id"], user["id"])
        assert validate_api_key(ak["key"]) is None

    def test_revoke_wrong_user(self):
        user1 = create_user("rev1@example.com", "U1", "pw")
        user2 = create_user("rev2@example.com", "U2", "pw")
        ak = create_api_key(user1["id"], "U1 Key")
        assert not revoke_api_key(ak["id"], user2["id"])

    def test_list_keys(self):
        user = create_user("listkeys@example.com", "List", "pw")
        create_api_key(user["id"], "Key A")
        create_api_key(user["id"], "Key B")
        keys = list_api_keys(user["id"])
        assert len(keys) >= 2


class TestProfile:
    def test_change_password(self):
        user = create_user("chpw@example.com", "ChPw", "oldpw")
        assert change_password(user["id"], "oldpw", "newpw")
        assert authenticate_user("chpw@example.com", "newpw") is not None
        assert authenticate_user("chpw@example.com", "oldpw") is None

    def test_change_password_wrong_current(self):
        user = create_user("chpww@example.com", "ChPwW", "pw")
        assert not change_password(user["id"], "wrongpw", "newpw")

    def test_update_email(self):
        user = create_user("updemail@example.com", "Upd", "pw")
        updated = update_email(user["id"], "newemail@example.com")
        assert updated["email"] == "newemail@example.com"

    def test_update_email_duplicate(self):
        create_user("existing@example.com", "Existing", "pw")
        user2 = create_user("dupcheck@example.com", "Dup", "pw")
        assert update_email(user2["id"], "existing@example.com") is None


class TestUsage:
    def test_usage_stats(self):
        from app.auth import log_usage
        user = create_user("usage@example.com", "Usage", "pw")
        ak = create_api_key(user["id"], "Usage Key")
        log_usage(ak["id"], "/test/endpoint", 200, 42)
        stats = get_usage_stats(ak["id"])
        assert stats["requests_total"] >= 1
        assert stats["key_name"] == "Usage Key"
