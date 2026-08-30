"""Shared data-access for page configuration, blogs, and payments.
All functions work on both SQLite and PostgreSQL via get_db().
"""
import json
from datetime import datetime, timezone

from .database import get_db, USE_POSTGRES


def _to_dict(row):
    if row is None:
        return None
    try:
        return dict(row)
    except (TypeError, ValueError):
        return row


def _convert(sql):
    return sql.replace("?", "%s") if USE_POSTGRES else sql


def _insert_get_id(db, sql, params):
    sql = _convert(sql)
    return db.execute(sql, params)


# ═══════════════════════════════════════════════
#  Page Configuration
# ═══════════════════════════════════════════════

DEFAULT_CONFIG = {
    "site_title": "AstroVakta — Vedic Astrology API | Kundli, Birth Charts, Horoscopes & AI Predictions",
    "site_tagline": "The Vedic Astrology API for Modern Developers",
    "logo_url": "/favicon.svg",
    "primary_color": "#7c3aed",
    "secondary_color": "#eab308",
    "homepage_hero_title": "AstroVakta",
    "homepage_hero_subtitle": "for developers",
    "homepage_tagline": "The Vedic Astrology API for Modern Developers",
    "homepage_description": "Birth charts, horoscopes, doshas, compatibility, panchang, divisional charts, PDF reports, and AI interpretations — a complete sidereal astrology engine behind a single REST API.",
    "contact_email": "hello@astrovakta.com",
    "contact_phone": "+91-62394-02519",
    "contact_address": "India",
    "footer_text": "© 2026 AstroVakta. All rights reserved.",
    "seo_title": "AstroVakta — Vedic Astrology API | Kundli, Birth Charts, Horoscopes & AI Predictions",
    "seo_description": "AstroVakta is the most complete Vedic astrology API for developers. 180+ endpoints for kundli birth charts, daily horoscopes, gun milan compatibility, mangal dosha, panchang, vimshottari dasha, PDF reports and AI astrology predictions. Free tier — no credit card required.",
    "seo_keywords": "vedic astrology api, astrology api, kundli api, birth chart api, horoscope api, jyotish api, kundali matching api, gun milan api, panchang api",
    "seo_og_image": "/og-image.png",
}


def get_all_config() -> dict:
    db = get_db()
    rows = db.execute("SELECT key, value FROM page_config").fetchall()
    store = {}
    for r in rows:
        raw = r["value"]
        if raw is None:
            store[r["key"]] = None
            continue
        try:
            store[r["key"]] = json.loads(raw)
        except Exception:
            store[r["key"]] = raw
    return {**DEFAULT_CONFIG, **store}


def get_config(key: str):
    store = get_all_config()
    return store.get(key)


def set_config(key: str, value) -> None:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    ser = json.dumps(value)
    existing = db.execute(
        _convert("SELECT id FROM page_config WHERE key = ?"), (key,)
    ).fetchone()
    if existing:
        db.execute(
            _convert("UPDATE page_config SET value = ?, updated_at = ? WHERE key = ?"),
            (ser, now, key),
        )
    else:
        db.execute(
            _convert("INSERT INTO page_config (key, value, updated_at) VALUES (?, ?, ?)"),
            (key, ser, now),
        )
    db.commit()


def update_config(payload: dict) -> dict:
    for key, value in payload.items():
        set_config(key, value)
    return get_all_config()


# ═══════════════════════════════════════════════
#  Blogs
# ═══════════════════════════════════════════════

def _blog_row(row):
    d = _to_dict(row)
    if d is None:
        return None
    return d


def list_blogs(include_unpublished: bool = False, search: str = "", page: int = 1, per_page: int = 12):
    db = get_db()
    where = []
    params = []
    if not include_unpublished:
        where.append("is_published = TRUE")
    if search:
        where.append("(title LIKE ? OR excerpt LIKE ? OR tag LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    total = db.execute(
        _convert(f"SELECT COUNT(*) AS c FROM blogs {where_sql}"), params
    ).fetchone()["c"]
    offset = (page - 1) * per_page
    rows = db.execute(
        _convert(f"SELECT * FROM blogs {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?"),
        params + [per_page, offset],
    ).fetchall()
    return {
        "blogs": [_blog_row(r) for r in rows],
        "total": total,
        "page": page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


def get_blog_by_slug(slug: str, include_unpublished: bool = False):
    db = get_db()
    if include_unpublished:
        row = db.execute(_convert("SELECT * FROM blogs WHERE slug = ?"), (slug,)).fetchone()
    else:
        row = db.execute(
            _convert("SELECT * FROM blogs WHERE slug = ? AND is_published = TRUE"), (slug,)
        ).fetchone()
    return _blog_row(row)


def get_blog_by_id(blog_id: int):
    row = get_db().execute(_convert("SELECT * FROM blogs WHERE id = ?"), (blog_id,)).fetchone()
    return _blog_row(row)


def create_blog(data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO blogs (slug, title, excerpt, body, cover_image, author, author_id, tag, read_time, is_published) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            data.get("slug"),
            data.get("title"),
            data.get("excerpt"),
            data.get("body"),
            data.get("cover_image"),
            data.get("author"),
            data.get("author_id"),
            data.get("tag"),
            data.get("read_time"),
            1 if data.get("is_published", True) else 0,
        ),
    ).fetchone()
    db.commit()
    return get_blog_by_id(cur["id"])


def update_blog(blog_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["slug", "title", "excerpt", "body", "cover_image", "author", "tag", "read_time"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if "is_published" in data:
        fields.append("is_published = ?")
        params.append(1 if data["is_published"] else 0)
    if not fields:
        return get_blog_by_id(blog_id)
    fields.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(blog_id)
    db.execute(_convert(f"UPDATE blogs SET {', '.join(fields)} WHERE id = ?"), params)
    db.commit()
    return get_blog_by_id(blog_id)


def delete_blog(blog_id: int) -> bool:
    db = get_db()
    cur = db.execute(_convert("DELETE FROM blogs WHERE id = ?"), (blog_id,))
    db.commit()
    return cur.rowcount > 0


def slug_exists(slug: str, exclude_id: int = None) -> bool:
    db = get_db()
    if exclude_id is not None:
        row = db.execute(
            _convert("SELECT id FROM blogs WHERE slug = ? AND id != ?"), (slug, exclude_id)
        ).fetchone()
    else:
        row = db.execute(_convert("SELECT id FROM blogs WHERE slug = ?"), (slug,)).fetchone()
    return row is not None


# ═══════════════════════════════════════════════
#  Payments
# ═══════════════════════════════════════════════

def create_payment(data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO payments (user_id, email, name, amount, currency, plan, provider, "
            "dodo_payment_id, dodo_checkout_id, status, payment_method, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            data.get("user_id"),
            data.get("email"),
            data.get("name"),
            data.get("amount"),
            data.get("currency", "USD"),
            data.get("plan"),
            data.get("provider", "dodo"),
            data.get("dodo_payment_id"),
            data.get("dodo_checkout_id"),
            data.get("status", "pending"),
            data.get("payment_method"),
            json.dumps(data.get("metadata")) if data.get("metadata") else None,
        ),
    ).fetchone()
    db.commit()
    return get_payment_by_id(cur["id"])


def get_payment_by_id(payment_id: int):
    row = get_db().execute(_convert("SELECT * FROM payments WHERE id = ?"), (payment_id,)).fetchone()
    d = _to_dict(row)
    if d and d.get("metadata"):
        try:
            d["metadata"] = json.loads(d["metadata"])
        except Exception:
            pass
    return d


def get_payment_by_dodo_payment(payment_id: str):
    row = get_db().execute(
        _convert("SELECT * FROM payments WHERE dodo_payment_id = ?"), (payment_id,)
    ).fetchone()
    return _to_dict(row)


def update_payment(payment_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["status", "dodo_payment_id", "dodo_checkout_id", "payment_method", "plan"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if "metadata" in data:
        fields.append("metadata = ?")
        params.append(json.dumps(data["metadata"]) if data["metadata"] else None)
    params.append(payment_id)
    db.execute(_convert(f"UPDATE payments SET {', '.join(fields)} WHERE id = ?"), params)
    db.commit()
    return get_payment_by_id(payment_id)


def list_payments(user_id: int = None, page: int = 1, per_page: int = 20, status: str = ""):
    db = get_db()
    where, params = [], []
    if user_id is not None:
        where.append("user_id = ?")
        params.append(user_id)
    if status:
        where.append("status = ?")
        params.append(status)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    total = db.execute(
        _convert(f"SELECT COUNT(*) AS c FROM payments {where_sql}"), params
    ).fetchone()["c"]
    offset = (page - 1) * per_page
    rows = db.execute(
        _convert(f"SELECT * FROM payments {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?"),
        params + [per_page, offset],
    ).fetchall()
    payments = []
    for r in rows:
        d = _to_dict(r)
        if d and d.get("metadata"):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except Exception:
                pass
        payments.append(d)
    return {
        "payments": payments,
        "total": total,
        "page": page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


def payments_totals() -> dict:
    db = get_db()
    completed = db.execute(
        _convert("SELECT COALESCE(SUM(amount), 0) AS s, COUNT(*) AS c FROM payments WHERE status IN ('completed', 'paid')")
    ).fetchone()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_row = db.execute(
        _convert("SELECT COALESCE(SUM(amount), 0) AS s, COUNT(*) AS c FROM payments WHERE status IN ('completed', 'paid') AND DATE(created_at) = ?"),
        (today,),
    ).fetchone()
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    month_row = db.execute(
        _convert("SELECT COALESCE(SUM(amount), 0) AS s, COUNT(*) AS c FROM payments WHERE status IN ('completed', 'paid') AND created_at >= ?"),
        (month_start,),
    ).fetchone()
    return {
        "total_revenue": (completed["s"] or 0) if completed else 0,
        "total_payments": (completed["c"] or 0) if completed else 0,
        "today_revenue": (today_row["s"] or 0) if today_row else 0,
        "today_payments": (today_row["c"] or 0) if today_row else 0,
        "month_revenue": (month_row["s"] or 0) if month_row else 0,
        "month_payments": (month_row["c"] or 0) if month_row else 0,
    }
