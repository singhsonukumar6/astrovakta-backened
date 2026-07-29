#!/usr/bin/env python3
"""Bootstrap admin user and a pro-tier API key on first run."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, get_db
from app.auth import (
    hash_password, get_user_by_email, get_user_by_id, create_api_key, list_api_keys,
)


def create_admin():
    init_db()
    db = get_db()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@astrovakta.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_name = os.getenv("ADMIN_NAME", "Admin")

    if not admin_password:
        print("ERROR: ADMIN_PASSWORD env var is not set.")
        print("  Set ADMIN_EMAIL and ADMIN_PASSWORD before running in production.")
        if os.getenv("NODE_ENV") == "production":
            sys.exit(1)
        admin_password = "admin123"
        print(f"  WARNING: Using default password (dev mode only)")

    existing = get_user_by_email(admin_email)
    if existing:
        print(f"Admin user already exists: {admin_email}")
        if not existing.get("is_admin"):
            db.execute(
                "UPDATE users SET is_admin = TRUE WHERE id = ?",
                (existing["id"],),
            ) if os.getenv("DATABASE_URL", "").startswith("postgresql") else db.execute(
                "UPDATE users SET is_admin = 1 WHERE id = ?",
                (existing["id"],),
            )
            db.commit()
            print("Promoted existing user to admin.")
    else:
        is_pg = os.getenv("DATABASE_URL", "").startswith("postgresql")
        if is_pg:
            cur = db.execute(
                "INSERT INTO users (email, name, password_hash, plan, is_admin) "
                "VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
                (admin_email, admin_name, hash_password(admin_password), "enterprise"),
            )
            new_id = cur.fetchone()["id"]
        else:
            cur = db.execute(
                "INSERT INTO users (email, name, password_hash, plan, is_admin) "
                "VALUES (?, ?, ?, ?, 1)",
                (admin_email, admin_name, hash_password(admin_password), "enterprise"),
            )
            new_id = cur.lastrowid
        db.commit()
        print(f"Admin user created: {admin_email}")
        existing = get_user_by_id(new_id)

    keys = list_api_keys(existing["id"])
    if not keys:
        key_info = create_api_key(existing["id"], "Production Key", tier="pro")
        print(f"\n  ┌─────────────────────────────────────────────────┐")
        print(f"  │  API Key: {key_info['key']}")
        print(f"  │  Tier:    {key_info['tier']}")
        print(f"  │  Limit:   {key_info['rate_limit']} req/day")
        print(f"  └─────────────────────────────────────────────────┘")
        print(f"\n  Save this key — it won't be shown again.")
    else:
        print(f"API keys already exist for admin ({len(keys)} keys).")

    print(f"\n  Email:    {admin_email}")
    print(f"  Plan:     enterprise")
    print(f"  Admin:    Yes")


if __name__ == "__main__":
    create_admin()