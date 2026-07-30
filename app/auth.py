import secrets
import bcrypt
import json
from datetime import datetime, timezone
from typing import Optional, List

from .database import get_db, USE_POSTGRES


def _to_dict(row):
    """Convert a database row to dict — works with sqlite3.Row and psycopg dict_row."""
    if row is None:
        return None
    try:
        return dict(row)
    except (TypeError, ValueError):
        return row


def _convert_placeholders(sql):
    """Convert SQLite ? placeholders to PostgreSQL %s."""
    return sql.replace("?", "%s") if USE_POSTGRES else sql


def _insert_and_get_id(table, returning_cols, db, sql, params):
    """Execute INSERT and return the new row. Works on both backends.
    Uses RETURNING clause (SQLite 3.35+ and PostgreSQL both support it)."""
    sql_returning = sql.rstrip().rstrip(";") + f" RETURNING {returning_cols}"
    if USE_POSTGRES:
        sql_returning = sql_returning.replace("?", "%s")
    cur = db.execute(sql_returning, params)
    return cur.fetchone()

TIER_LIMITS = {
    "free": 500,
    "starter": 5000,
    "pro": 50000,
    "enterprise": 999999999,
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def generate_api_key() -> str:
    return "avk_" + secrets.token_hex(16)


# ──────────────── USER CRUD ────────────────
def create_user(email: str, name: str, password: str) -> dict:
    db = get_db()
    row = _insert_and_get_id(
        "users", "id", db,
        "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
        (email.lower().strip(), name.strip(), hash_password(password)),
    )
    db.commit()
    new_id = row["id"] if row else None
    return get_user_by_id(new_id) if new_id else None


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = get_user_by_email(email)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _to_dict(row) if row else None


def sync_clerk_user(clerk_id: str, email: str, name: str) -> Optional[dict]:
    db = get_db()
    existing = db.execute(
        "SELECT * FROM users WHERE clerk_id = ? OR email = ?",
        (clerk_id, email.lower().strip()),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE users SET clerk_id = ?, name = ?, email = ? WHERE id = ?",
            (clerk_id, name.strip(), email.lower().strip(), existing["id"]),
        )
        db.commit()
        return _to_dict(db.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone())
    row = _insert_and_get_id(
        "users", "id", db,
        "INSERT INTO users (email, name, password_hash, clerk_id) VALUES (?, ?, ?, ?)",
        (email.lower().strip(), name.strip(), hash_password("clerk_" + secrets.token_hex(16)), clerk_id),
    )
    db.commit()
    new_id = row["id"] if row else None
    return _to_dict(db.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()) if new_id else None


def get_user_by_email(email: str) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    return _to_dict(row) if row else None


# ──────────────── API KEY CRUD ────────────────
def create_api_key(user_id: int, name: str, tier: str = "free") -> dict:
    key = generate_api_key()
    db = get_db()
    row = _insert_and_get_id(
        "api_keys", "id", db,
        "INSERT INTO api_keys (user_id, key, name, tier) VALUES (?, ?, ?, ?)",
        (user_id, key, name.strip(), tier),
    )
    db.commit()
    new_id = row["id"] if row else None
    row = db.execute("SELECT * FROM api_keys WHERE id = ?", (new_id,)).fetchone()
    return _to_dict(row)


def _get_month_start():
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def validate_api_key(key: str) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT ak.*, u.email, u.name AS user_name, u.plan, u.is_admin, "
        "u.monthly_limit "
        "FROM api_keys ak JOIN users u ON ak.user_id = u.id "
        "WHERE ak.key = ? AND ak.is_active = TRUE",
        (key,),
    ).fetchone()
    if not row:
        return None

    user_id = row["user_id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    month_start = _get_month_start().isoformat()

    today_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ? AND DATE(ul.timestamp) = ?",
        (user_id, today),
    ).fetchone()
    requests_today = today_row["cnt"] if today_row else 0

    month_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ? AND ul.timestamp >= ?",
        (user_id, month_start),
    ).fetchone()
    requests_this_month = month_row["cnt"] if month_row else 0

    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
        (now, row["id"]),
    )
    db.commit()
    info = _to_dict(row)
    info["requests_today"] = requests_today
    info["requests_this_month"] = requests_this_month
    return info


def revoke_api_key(key_id: int, user_id: int) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    cur = get_db().execute(
        "UPDATE api_keys SET is_active = FALSE, revoked_at = ? WHERE id = ? AND user_id = ?",
        (now, key_id, user_id),
    )
    get_db().commit()
    return cur.rowcount > 0


def list_api_keys(user_id: int) -> list:
    rows = get_db().execute(
        "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# ──────────────── USAGE ────────────────
def log_usage(api_key_id: int, endpoint: str, status_code: int,
              response_time_ms: int = None, endpoint_group: str = None) -> None:
    get_db().execute(
        "INSERT INTO usage_logs (api_key_id, endpoint, status_code, response_time_ms, endpoint_group) "
        "VALUES (?, ?, ?, ?, ?)",
        (api_key_id, endpoint, status_code, response_time_ms, endpoint_group),
    )
    get_db().commit()


def get_usage_stats(api_key_id: int) -> dict:
    db = get_db()
    key_row = db.execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
    if not key_row:
        return {}

    key = dict(key_row)
    user_id = key["user_id"]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    month_start = _get_month_start().isoformat()

    today_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ? AND DATE(ul.timestamp) = ?",
        (user_id, today),
    ).fetchone()

    total_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ?", (user_id,)
    ).fetchone()

    month_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ? AND ul.timestamp >= ?",
        (user_id, month_start),
    ).fetchone()

    errors_row = db.execute(
        "SELECT COUNT(*) AS cnt FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ? AND ul.status_code >= 400",
        (user_id,),
    ).fetchone()

    top_endpoints = db.execute(
        "SELECT ul.endpoint, COUNT(*) AS hits FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        "WHERE ak.user_id = ? "
        "GROUP BY ul.endpoint ORDER BY hits DESC LIMIT 10",
        (user_id,),
    ).fetchall()

    user = get_user_by_id(user_id)

    return {
        "key_id": key["id"],
        "key_name": key["name"],
        "tier": key["tier"],
        "monthly_limit": user.get("monthly_limit", 0),
        "requests_today": today_row["cnt"] if today_row else 0,
        "requests_this_month": month_row["cnt"] if month_row else 0,
        "requests_total": total_row["cnt"] if total_row else 0,
        "errors_total": errors_row["cnt"] if errors_row else 0,
        "top_endpoints": [dict(r) for r in top_endpoints],
    }


def change_password(user_id: int, current_password: str, new_password: str) -> bool:
    user = get_user_by_id(user_id)
    if not user or not verify_password(current_password, user["password_hash"]):
        return False
    db = get_db()
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    db.commit()
    return True


def update_email(user_id: int, new_email: str) -> Optional[dict]:
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email.lower().strip(), user_id)).fetchone()
    if existing:
        return None
    db.execute("UPDATE users SET email = ? WHERE id = ?", (new_email.lower().strip(), user_id))
    db.commit()
    return get_user_by_id(user_id)


def update_user_profile(user_id: int, name: Optional[str] = None, plan: Optional[str] = None, email: Optional[str] = None) -> Optional[dict]:
    db = get_db()
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name.strip())
    if email is not None:
        existing = db.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email.lower().strip(), user_id)).fetchone()
        if existing:
            return None
        updates.append("email = ?")
        params.append(email.lower().strip())
    if plan is not None:
        updates.append("plan = ?")
        params.append(plan)
    if not updates:
        return get_user_by_id(user_id)
    params.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()

    if plan is not None:
        new_limit = TIER_LIMITS.get(plan, TIER_LIMITS["free"])
        db.execute(
            "UPDATE users SET monthly_limit = ? WHERE id = ?",
            (new_limit, user_id),
        )
        db.commit()

    return get_user_by_id(user_id)


# ──────────────── ADMIN FUNCTIONS ────────────────
def is_admin(user_id: int) -> bool:
    user = get_user_by_id(user_id)
    return bool(user and user.get("is_admin"))


def set_user_admin(user_id: int, admin: bool) -> bool:
    cur = get_db().execute("UPDATE users SET is_admin = ? WHERE id = ?", (admin, user_id))
    get_db().commit()
    return cur.rowcount > 0


def get_all_users(page: int = 1, per_page: int = 20, search: str = "",
                  plan_filter: str = "") -> dict:
    db = get_db()
    offset = (page - 1) * per_page
    conditions = []
    params = []

    if search:
        conditions.append("(name LIKE ? OR email LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if plan_filter:
        conditions.append("plan = ?")
        params.append(plan_filter)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = db.execute(f"SELECT COUNT(*) as cnt FROM users {where}", params).fetchone()["cnt"]
    rows = db.execute(
        f"SELECT * FROM users {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    users = []
    for r in rows:
        u = dict(r)
        u.pop("password_hash", None)
        key_count = db.execute(
            "SELECT COUNT(*) as cnt FROM api_keys WHERE user_id = ? AND is_active = TRUE", (u["id"],)
        ).fetchone()["cnt"]
        req_count = db.execute(
            "SELECT COUNT(*) as cnt FROM usage_logs ul "
            "JOIN api_keys ak ON ul.api_key_id = ak.id WHERE ak.user_id = ?", (u["id"],)
        ).fetchone()["cnt"]
        u["active_keys"] = key_count
        u["total_requests"] = req_count
        users.append(u)

    return {"users": users, "total": total, "page": page, "per_page": per_page,
            "total_pages": max(1, -(-total // per_page)),
            "tier_limits": TIER_LIMITS}


def admin_update_user_plan(user_id: int, new_plan: str) -> Optional[dict]:
    db = get_db()
    new_limit = TIER_LIMITS.get(new_plan, TIER_LIMITS["free"])
    db.execute(
        "UPDATE users SET plan = ?, monthly_limit = ? WHERE id = ?",
        (new_plan, new_limit, user_id),
    )
    db.commit()
    return get_user_by_id(user_id)


def admin_set_monthly_limit(user_id: int, monthly_limit: int) -> Optional[dict]:
    db = get_db()
    db.execute(
        "UPDATE users SET monthly_limit = ? WHERE id = ?",
        (monthly_limit, user_id),
    )
    db.commit()
    return get_user_by_id(user_id)


def admin_revoke_all_keys(user_id: int) -> int:
    """Revoke all active keys for a user. Returns count revoked."""
    now = datetime.now(timezone.utc).isoformat()
    cur = get_db().execute(
        "UPDATE api_keys SET is_active = FALSE, revoked_at = ? WHERE user_id = ? AND is_active = TRUE",
        (now, user_id),
    )
    get_db().commit()
    return cur.rowcount


def admin_ban_user(user_id: int) -> bool:
    """Ban a user by revoking all keys and deactivating."""
    admin_revoke_all_keys(user_id)
    return True


def admin_reset_password(user_id: int, new_password: str) -> bool:
    """Admin reset a user's password."""
    user = get_user_by_id(user_id)
    if not user:
        return False
    db = get_db()
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    db.commit()
    return True


def admin_create_key_for_user(user_id: int, name: str, tier: str = "free") -> Optional[dict]:
    """Admin creates an API key for a user."""
    user = get_user_by_id(user_id)
    if not user:
        return None
    return create_api_key(user_id, name, tier)


def admin_get_user_keys(user_id: int) -> list:
    """Get all keys for a specific user."""
    return list_api_keys(user_id)


def admin_get_user_usage(user_id: int) -> dict:
    """Get usage stats across all keys for a user."""
    db = get_db()
    user = get_user_by_id(user_id)
    if not user:
        return {}

    keys = list_api_keys(user_id)
    key_ids = [k["id"] for k in keys]

    total_requests = 0
    today_requests = 0
    error_count = 0
    top_endpoints = []
    daily_usage = []

    if key_ids:
        placeholders = ",".join("?" * len(key_ids))
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        total_requests = db.execute(
            f"SELECT COUNT(*) as cnt FROM usage_logs WHERE api_key_id IN ({placeholders})", key_ids
        ).fetchone()["cnt"]

        today_requests = db.execute(
            f"SELECT COUNT(*) as cnt FROM usage_logs WHERE api_key_id IN ({placeholders}) AND DATE(timestamp) = ?",
            key_ids + [today],
        ).fetchone()["cnt"]

        error_count = db.execute(
            f"SELECT COUNT(*) as cnt FROM usage_logs WHERE api_key_id IN ({placeholders}) AND status_code >= 400",
            key_ids,
        ).fetchone()["cnt"]

        top_endpoints = db.execute(
            f"SELECT endpoint, COUNT(*) as hits FROM usage_logs WHERE api_key_id IN ({placeholders}) "
            f"GROUP BY endpoint ORDER BY hits DESC LIMIT 10",
            key_ids,
        ).fetchall()

        daily_usage = db.execute(
            f"SELECT DATE(timestamp) as day, COUNT(*) as requests, "
            f"SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors "
            f"FROM usage_logs WHERE api_key_id IN ({placeholders}) AND timestamp >= DATE('now', '-30 days') "
            f"GROUP BY DATE(timestamp) ORDER BY day",
            key_ids,
        ).fetchall()

    return {
        "user_id": user_id,
        "user_name": user["name"],
        "user_email": user["email"],
        "total_keys": len(keys),
        "active_keys": len([k for k in keys if k["is_active"]]),
        "total_requests": total_requests,
        "today_requests": today_requests,
        "error_count": error_count,
        "top_endpoints": [dict(r) for r in top_endpoints],
        "daily_usage": [dict(r) for r in daily_usage],
    }


def admin_get_all_usage_daily(days: int = 30) -> list:
    """Get daily usage across ALL users for admin overview."""
    db = get_db()
    rows = db.execute(
        "SELECT DATE(ul.timestamp) as day, COUNT(*) as requests, "
        "COUNT(DISTINCT ak.user_id) as unique_users, "
        "SUM(CASE WHEN ul.status_code >= 400 THEN 1 ELSE 0 END) as errors "
        "FROM usage_logs ul "
        "JOIN api_keys ak ON ul.api_key_id = ak.id "
        f"WHERE ul.timestamp >= DATE('now', '-{days} days') "
        "GROUP BY DATE(ul.timestamp) ORDER BY day",
    ).fetchall()
    return [dict(r) for r in rows]


def admin_get_all_usage_by_user(limit: int = 50) -> list:
    """Get usage breakdown by user."""
    db = get_db()
    rows = db.execute(
        "SELECT u.id as user_id, u.name, u.email, u.plan, "
        "COUNT(ul.id) as total_requests, "
        "SUM(CASE WHEN ul.status_code >= 400 THEN 1 ELSE 0 END) as errors, "
        "MAX(ul.timestamp) as last_active "
        "FROM users u "
        "LEFT JOIN api_keys ak ON u.id = ak.user_id "
        "LEFT JOIN usage_logs ul ON ak.id = ul.api_key_id "
        "GROUP BY u.id ORDER BY total_requests DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def admin_get_stats() -> dict:
    db = get_db()
    users_total = db.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    users_today = db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE DATE(created_at) = DATE('now')"
    ).fetchone()["cnt"]
    keys_total = db.execute("SELECT COUNT(*) as cnt FROM api_keys").fetchone()["cnt"]
    keys_active = db.execute("SELECT COUNT(*) as cnt FROM api_keys WHERE is_active = TRUE").fetchone()["cnt"]
    requests_total = db.execute("SELECT COUNT(*) as cnt FROM usage_logs").fetchone()["cnt"]
    requests_today = db.execute(
        "SELECT COUNT(*) as cnt FROM usage_logs WHERE DATE(timestamp) = DATE('now')"
    ).fetchone()["cnt"]
    jobs_pending = db.execute(
        "SELECT COUNT(*) as cnt FROM background_jobs WHERE status = 'pending'"
    ).fetchone()["cnt"]
    jobs_processing = db.execute(
        "SELECT COUNT(*) as cnt FROM background_jobs WHERE status = 'processing'"
    ).fetchone()["cnt"]

    plan_dist = db.execute(
        "SELECT plan, COUNT(*) as cnt FROM users GROUP BY plan"
    ).fetchall()

    return {
        "total_users": users_total,
        "new_users_today": users_today,
        "total_keys": keys_total,
        "active_keys": keys_active,
        "total_requests": requests_total,
        "requests_today": requests_today,
        "pending_jobs": jobs_pending,
        "processing_jobs": jobs_processing,
        "plan_distribution": {r["plan"]: r["cnt"] for r in plan_dist},
    }


def admin_get_all_keys(page: int = 1, per_page: int = 50) -> dict:
    db = get_db()
    offset = (page - 1) * per_page
    total = db.execute("SELECT COUNT(*) as cnt FROM api_keys").fetchone()["cnt"]
    rows = db.execute(
        "SELECT ak.*, u.name as user_name, u.email as user_email "
        "FROM api_keys ak JOIN users u ON ak.user_id = u.id "
        "ORDER BY ak.created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset),
    ).fetchall()
    return {"keys": [dict(r) for r in rows], "total": total, "page": page}


def admin_revoke_key(key_id: int) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    cur = get_db().execute(
        "UPDATE api_keys SET is_active = FALSE, revoked_at = ? WHERE id = ?", (now, key_id)
    )
    get_db().commit()
    return cur.rowcount > 0


def admin_update_key_tier(key_id: int, new_tier: str) -> bool:
    cur = get_db().execute(
        "UPDATE api_keys SET tier = ? WHERE id = ?",
        (new_tier, key_id),
    )
    get_db().commit()
    return cur.rowcount > 0


def admin_get_usage_daily(days: int = 30) -> list:
    db = get_db()
    rows = db.execute(
        "SELECT DATE(timestamp) as day, COUNT(*) as requests, "
        "SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors "
        "FROM usage_logs WHERE timestamp >= DATE('now', ?) "
        "GROUP BY DATE(timestamp) ORDER BY day",
        (f"-{days} days",),
    ).fetchall()
    return [dict(r) for r in rows]


def admin_get_usage_endpoints(limit: int = 20) -> list:
    db = get_db()
    rows = db.execute(
        "SELECT endpoint, COUNT(*) as hits, "
        "AVG(response_time_ms) as avg_response_ms "
        "FROM usage_logs GROUP BY endpoint ORDER BY hits DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


# ──────────────── AI PROVIDER FUNCTIONS ────────────────
def create_ai_provider(user_id: int, provider: str, api_key_encrypted: str,
                       model: str = None) -> dict:
    db = get_db()
    row = _insert_and_get_id(
        "ai_providers", "id", db,
        "INSERT INTO ai_providers (user_id, provider, api_key_encrypted, model) VALUES (?, ?, ?, ?)",
        (user_id, provider, api_key_encrypted, model),
    )
    db.commit()
    new_id = row["id"] if row else None
    row = db.execute("SELECT * FROM ai_providers WHERE id = ?", (new_id,)).fetchone()
    return _to_dict(row)


def list_ai_providers(user_id: int) -> list:
    rows = get_db().execute(
        "SELECT * FROM ai_providers WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_ai_provider(provider_id: int, user_id: int) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM ai_providers WHERE id = ? AND user_id = ?",
        (provider_id, user_id),
    ).fetchone()
    return _to_dict(row) if row else None


def get_active_ai_provider(user_id: int, preferred_provider: str = None) -> Optional[dict]:
    """Get the user's active AI provider, optionally filtering by provider name."""
    db = get_db()
    if preferred_provider:
        row = db.execute(
            "SELECT * FROM ai_providers WHERE user_id = ? AND provider = ? AND is_active = TRUE",
            (user_id, preferred_provider),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT * FROM ai_providers WHERE user_id = ? AND is_active = TRUE "
            "ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return _to_dict(row) if row else None


def update_ai_provider(provider_id: int, user_id: int, **kwargs) -> bool:
    db = get_db()
    updates = []
    params = []
    for key in ("provider", "api_key_encrypted", "model", "is_active"):
        if key in kwargs:
            updates.append(f"{key} = ?")
            params.append(kwargs[key])
    if not updates:
        return False
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([provider_id, user_id])
    cur = db.execute(
        f"UPDATE ai_providers SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
        params,
    )
    db.commit()
    return cur.rowcount > 0


def delete_ai_provider(provider_id: int, user_id: int) -> bool:
    cur = get_db().execute(
        "DELETE FROM ai_providers WHERE id = ? AND user_id = ?",
        (provider_id, user_id),
    )
    get_db().commit()
    return cur.rowcount > 0


# ──────────────── BACKGROUND JOB FUNCTIONS ────────────────
def create_job(user_id: int, job_type: str, input_data: dict) -> dict:
    db = get_db()
    row = _insert_and_get_id(
        "background_jobs", "id", db,
        "INSERT INTO background_jobs (user_id, job_type, input_data) VALUES (?, ?, ?)",
        (user_id, job_type, json.dumps(input_data)),
    )
    db.commit()
    new_id = row["id"] if row else None
    row = db.execute("SELECT * FROM background_jobs WHERE id = ?", (new_id,)).fetchone()
    return _to_dict(row)


def update_job_status(job_id: int, status: str, celery_task_id: str = None,
                      result_data: str = None, error_message: str = None) -> bool:
    db = get_db()
    updates = ["status = ?"]
    params = [status]
    if celery_task_id:
        updates.append("celery_task_id = ?")
        params.append(celery_task_id)
    if status == "processing":
        updates.append("started_at = CURRENT_TIMESTAMP")
    if status in ("completed", "failed"):
        updates.append("completed_at = CURRENT_TIMESTAMP")
    if result_data:
        updates.append("result_data = ?")
        params.append(result_data)
    if error_message:
        updates.append("error_message = ?")
        params.append(error_message)
    params.append(job_id)
    cur = db.execute(f"UPDATE background_jobs SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return cur.rowcount > 0


def get_job(job_id: int) -> Optional[dict]:
    row = get_db().execute("SELECT * FROM background_jobs WHERE id = ?", (job_id,)).fetchone()
    return _to_dict(row) if row else None


def get_user_jobs(user_id: int, status: str = None, limit: int = 20) -> list:
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT * FROM background_jobs WHERE user_id = ? AND status = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, status, limit),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM background_jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def store_job_result(job_id: int, result_type: str, result_blob: bytes,
                     filename: str = None) -> dict:
    db = get_db()
    row = _insert_and_get_id(
        "job_results", "id", db,
        "INSERT INTO job_results (job_id, result_type, result_blob, file_size, filename) "
        "VALUES (?, ?, ?, ?, ?)",
        (job_id, result_type, result_blob, len(result_blob), filename),
    )
    db.commit()
    new_id = row["id"] if row else None
    row = db.execute("SELECT id, job_id, result_type, file_size, filename, created_at FROM job_results WHERE id = ?",
                     (new_id,)).fetchone()
    return _to_dict(row) if row else None


def get_job_result(job_id: int) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM job_results WHERE job_id = ?", (job_id,)
    ).fetchone()
    return _to_dict(row) if row else None


def get_job_result_blob(job_id: int) -> Optional[bytes]:
    row = get_db().execute(
        "SELECT result_blob FROM job_results WHERE job_id = ?", (job_id,)
    ).fetchone()
    return row["result_blob"] if row else None


def get_all_jobs(page: int = 1, per_page: int = 50, status: str = None) -> dict:
    db = get_db()
    offset = (page - 1) * per_page
    conditions = []
    params = []
    if status:
        conditions.append("bj.status = ?")
        params.append(status)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = db.execute(
        f"SELECT COUNT(*) as cnt FROM background_jobs bj {where}", params
    ).fetchone()["cnt"]
    rows = db.execute(
        f"SELECT bj.*, u.name as user_name, u.email as user_email "
        f"FROM background_jobs bj JOIN users u ON bj.user_id = u.id "
        f"{where} ORDER BY bj.created_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()
    return {"jobs": [dict(r) for r in rows], "total": total, "page": page}


# ──────────────── EMAIL VERIFICATION ────────────────
import secrets as _secrets


def create_verification_token(user_id: int) -> str:
    token = _secrets.token_urlsafe(48)
    db = get_db()
    if USE_POSTGRES:
        db.execute(
            "UPDATE users SET verification_token = %s WHERE id = %s",
            (token, user_id),
        )
    else:
        db.execute(
            "UPDATE users SET verification_token = ? WHERE id = ?",
            (token, user_id),
        )
    db.commit()
    return token


def verify_email_token(token: str) -> Optional[dict]:
    db = get_db()
    if USE_POSTGRES:
        row = db.execute(
            "SELECT * FROM users WHERE verification_token = %s", (token,)
        ).fetchone()
    else:
        row = db.execute(
            "SELECT * FROM users WHERE verification_token = ?", (token,)
        ).fetchone()
    if not row:
        return None
    user = _to_dict(row)
    db.execute(
        "UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE id = ?"
        if not USE_POSTGRES else
        "UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE id = %s",
        (user["id"],),
    )
    db.commit()
    return user


# ──────────────── PASSWORD RESET ────────────────
def create_password_reset_token(user_id: int) -> str:
    token = _secrets.token_urlsafe(48)
    db = get_db()
    from datetime import timedelta
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    expires_str = expires.isoformat()
    row = _insert_and_get_id(
        "password_resets", "id", db,
        "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_str),
    )
    db.commit()
    return token


def verify_password_reset_token(token: str) -> Optional[dict]:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    if USE_POSTGRES:
        row = db.execute(
            "SELECT pr.*, u.id as uid, u.email, u.name "
            "FROM password_resets pr JOIN users u ON pr.user_id = u.id "
            "WHERE pr.token = %s AND pr.used = FALSE AND pr.expires_at > %s",
            (token, now),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT pr.*, u.id as uid, u.email, u.name "
            "FROM password_resets pr JOIN users u ON pr.user_id = u.id "
            "WHERE pr.token = ? AND pr.used = 0 AND pr.expires_at > ?",
            (token, now),
        ).fetchone()
    return _to_dict(row) if row else None


def use_password_reset_token(token: str) -> bool:
    db = get_db()
    if USE_POSTGRES:
        cur = db.execute(
            "UPDATE password_resets SET used = TRUE WHERE token = %s", (token,)
        )
    else:
        cur = db.execute(
            "UPDATE password_resets SET used = 1 WHERE token = ?", (token,)
        )
    db.commit()
    return cur.rowcount > 0


def reset_password_with_token(token: str, new_password: str) -> bool:
    reset_info = verify_password_reset_token(token)
    if not reset_info:
        return False
    user_id = reset_info["uid"]
    db = get_db()
    if USE_POSTGRES:
        db.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(new_password), user_id),
        )
    else:
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
    use_password_reset_token(token)
    db.commit()
    return True
