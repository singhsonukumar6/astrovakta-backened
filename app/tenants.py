"""Shared data-access for the multi-tenant website builder.

Tenants (sites) are owned by a user. Each site has:
- a slug subdomain  (slug.astrovakta.site) and optional custom domain
- a template + theme (JSON: colors, fonts, hero copy)
- site_pages: editable content blocks per page (home, about, services, contact)
- site_services + site_availability + site_bookings: the appointment engine

All functions work on both SQLite and PostgreSQL via get_db(), mirroring content.py.
"""
import json
import re
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


def _now():
    return datetime.now(timezone.utc).isoformat()


SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,30}[a-z0-9])?$")
RESERVED_SLUGS = {
    "www", "api", "app", "admin", "dashboard", "mail", "ftp", "blog",
    "support", "help", "status", "about", "pricing", "developer", "developers",
    "docs", "sandbox", "login", "register", "signup", "astrovakta", "astro",
}

TEMPLATES = ["aurora", "classic", "minimal", "devotional"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def validate_slug(slug: str) -> str | None:
    """Return an error message if the slug is invalid, else None."""
    slug = (slug or "").strip().lower()
    if not slug:
        return "Slug is required"
    if not SLUG_RE.match(slug):
        return "Use 3-32 lowercase letters, numbers or hyphens (must start and end with a letter or number)"
    if slug in RESERVED_SLUGS:
        return "That name is reserved — try another"
    return None


def normalize_domain(domain: str) -> str:
    """Strip scheme/path/www and lowercase a custom domain."""
    d = (domain or "").strip().lower()
    d = re.sub(r"^[a-z]+://", "", d)
    d = d.split("/")[0].split(":")[0]
    if d.startswith("www."):
        d = d[4:]
    return d


# ═══════════════════════════════════════════════
#  Sites
# ═══════════════════════════════════════════════

DEFAULT_PAGES = {
    "home": {
        "title": "Home",
        "content": {
            "heroTitle": "Vedic Astrology Consultations",
            "heroSubtitle": "Accurate kundli readings, remedies and guidance for career, marriage, health and prosperity.",
            "aboutTitle": "About",
            "aboutText": "I am a Vedic astrologer with years of experience helping people find clarity through their birth chart. Share your birth details and receive a detailed, honest reading.",
        },
    },
    "about": {
        "title": "About Me",
        "content": {
            "title": "About Me",
            "text": "Tell your story here — your training, your lineage, your experience, and what clients can expect from a consultation with you.",
        },
    },
    "contact": {
        "title": "Contact",
        "content": {
            "title": "Get in Touch",
            "text": "Reach out for consultations, questions or bookings. I usually reply within a few hours.",
        },
    },
}

DEFAULT_THEME = {
    "primaryColor": "#4f46e5",   # indigo-600 — professional light default
    "accentColor": "#d97706",    # amber-600
    "bgStyle": "light",          # dark | light
    "fontHeading": "'Inter', sans-serif",
    "heroImage": "",
}

# Starting palette per template — a site created with a template should
# look like that template, not like the default aurora colors.
TEMPLATE_THEMES = {
    "aurora": {},
    "classic": {"primaryColor": "#b45309", "accentColor": "#dc2626", "bgStyle": "dark"},
    "minimal": {"primaryColor": "#0f766e", "accentColor": "#0ea5e9", "bgStyle": "light"},
    "devotional": {"primaryColor": "#ea580c", "accentColor": "#facc15", "bgStyle": "light"},
}

DEFAULT_SERVICES = [
    {"name": "Full Kundli Reading", "description": "Complete birth chart analysis with predictions and remedies", "duration_minutes": 45, "price": 500},
    {"name": "Career & Business Consultation", "description": "Focused guidance on job, business and finances", "duration_minutes": 30, "price": 300},
    {"name": "Marriage & Compatibility", "description": "Kundali matching and relationship guidance", "duration_minutes": 30, "price": 400},
]

DEFAULT_AVAILABILITY = [
    {"weekday": 0, "start_time": "10:00", "end_time": "18:00"},
    {"weekday": 1, "start_time": "10:00", "end_time": "18:00"},
    {"weekday": 2, "start_time": "10:00", "end_time": "18:00"},
    {"weekday": 3, "start_time": "10:00", "end_time": "18:00"},
    {"weekday": 4, "start_time": "10:00", "end_time": "18:00"},
]


def _parse_theme(raw):
    if not raw:
        return dict(DEFAULT_THEME)
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return {**DEFAULT_THEME, **(parsed or {})}
    except Exception:
        return dict(DEFAULT_THEME)


def _parse_content(raw):
    if raw is None:
        return None
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return raw


DEFAULT_SETTINGS = {
    "whatsappNumber": "",
    "bookingAlerts": True,
    "reminderHours": 24,
}


def _parse_settings(raw):
    if not raw:
        return dict(DEFAULT_SETTINGS)
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return {**DEFAULT_SETTINGS, **(parsed or {})}
    except Exception:
        return dict(DEFAULT_SETTINGS)


def _site_row(row, include_unpublished: bool = False):
    d = _to_dict(row)
    if d is None:
        return None
    d["theme"] = _parse_theme(d.get("theme"))
    d["settings"] = _parse_settings(d.get("settings"))
    return d


def get_site_by_id(site_id: int):
    row = get_db().execute(_convert("SELECT * FROM sites WHERE id = ?"), (site_id,)).fetchone()
    return _site_row(row)


def get_site_by_slug(slug: str, published_only: bool = True):
    db = get_db()
    if published_only:
        row = db.execute(
            _convert("SELECT * FROM sites WHERE slug = ? AND status = 'published'"), (slug,)
        ).fetchone()
    else:
        row = db.execute(_convert("SELECT * FROM sites WHERE slug = ?"), (slug,)).fetchone()
    return _site_row(row)


def get_site_by_domain(domain: str):
    d = normalize_domain(domain)
    row = get_db().execute(
        _convert("SELECT * FROM sites WHERE custom_domain = ? AND domain_status = 'active'"), (d,)
    ).fetchone()
    return _site_row(row)


def slug_exists(slug: str, exclude_id: int = None) -> bool:
    db = get_db()
    if exclude_id is not None:
        row = db.execute(
            _convert("SELECT id FROM sites WHERE slug = ? AND id != ?"), (slug, exclude_id)
        ).fetchone()
    else:
        row = db.execute(_convert("SELECT id FROM sites WHERE slug = ?"), (slug,)).fetchone()
    return row is not None


def domain_exists(domain: str, exclude_id: int = None) -> bool:
    d = normalize_domain(domain)
    db = get_db()
    if exclude_id is not None:
        row = db.execute(
            _convert("SELECT id FROM sites WHERE custom_domain = ? AND id != ?"), (d, exclude_id)
        ).fetchone()
    else:
        row = db.execute(_convert("SELECT id FROM sites WHERE custom_domain = ?"), (d,)).fetchone()
    return row is not None


def list_sites(user_id: int):
    rows = get_db().execute(
        _convert("SELECT * FROM sites WHERE user_id = ? ORDER BY created_at DESC"), (user_id,)
    ).fetchall()
    return [_site_row(r) for r in rows]


def create_site(user_id: int, data: dict) -> dict:
    db = get_db()
    now = _now()
    template = data.get("template") or "aurora"
    if template not in TEMPLATES:
        template = "aurora"
    theme = data.get("theme") or {
        **DEFAULT_THEME, **TEMPLATE_THEMES.get(template, {})
    }
    cur = db.execute(
        _convert(
            "INSERT INTO sites (user_id, slug, name, tagline, template, theme, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?) RETURNING id"
        ),
        (
            user_id,
            data["slug"],
            data.get("name") or data["slug"].replace("-", " ").title(),
            data.get("tagline") or "Vedic Astrologer",
            template,
            json.dumps(theme),
            now,
            now,
        ),
    ).fetchone()
    site_id = cur["id"]
    db.commit()

    # Seed default pages
    for page_key, page in DEFAULT_PAGES.items():
        db.execute(
            _convert(
                "INSERT INTO site_pages (site_id, page_key, title, content, is_published, updated_at) "
                "VALUES (?, ?, ?, ?, 1, ?)"
            ),
            (site_id, page_key, page["title"], json.dumps(page["content"]), now),
        )
    # Seed default services
    for i, svc in enumerate(DEFAULT_SERVICES):
        db.execute(
            _convert(
                "INSERT INTO site_services (site_id, name, description, duration_minutes, price, currency, is_active, sort_order, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'INR', 1, ?, ?)"
            ),
            (site_id, svc["name"], svc["description"], svc["duration_minutes"], svc["price"], i, now),
        )
    # Seed default availability (Mon-Fri 10-6)
    for av in DEFAULT_AVAILABILITY:
        db.execute(
            _convert(
                "INSERT INTO site_availability (site_id, weekday, start_time, end_time) VALUES (?, ?, ?, ?)"
            ),
            (site_id, av["weekday"], av["start_time"], av["end_time"]),
        )
    db.commit()
    return get_site_by_id(site_id)


def update_site(site_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["name", "tagline", "template", "custom_domain", "domain_status", "status",
                "logo_url", "hero_image"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if "theme" in data and data["theme"] is not None:
        fields.append("theme = ?")
        params.append(json.dumps(data["theme"]) if not isinstance(data["theme"], str) else data["theme"])
    if "settings" in data and data["settings"] is not None:
        fields.append("settings = ?")
        params.append(json.dumps(data["settings"]) if not isinstance(data["settings"], str) else data["settings"])
    if fields:
        fields.append("updated_at = ?")
        params.append(_now())
        params.append(site_id)
        db.execute(_convert(f"UPDATE sites SET {', '.join(fields)} WHERE id = ?"), params)
        db.commit()
    return get_site_by_id(site_id)


def set_site_status(site_id: int, status: str) -> dict:
    db = get_db()
    published_at = _now() if status == "published" else None
    if status == "published":
        db.execute(
            _convert("UPDATE sites SET status = ?, published_at = ?, updated_at = ? WHERE id = ?"),
            (status, published_at, _now(), site_id),
        )
    else:
        db.execute(
            _convert("UPDATE sites SET status = ?, updated_at = ? WHERE id = ?"),
            (status, _now(), site_id),
        )
    db.commit()
    return get_site_by_id(site_id)


def delete_site(site_id: int) -> bool:
    db = get_db()
    for table in ["site_bookings", "site_availability", "site_services", "site_pages", "site_leads"]:
        db.execute(_convert(f"DELETE FROM {table} WHERE site_id = ?"), (site_id,))
    cur = db.execute(_convert("DELETE FROM sites WHERE id = ?"), (site_id,))
    db.commit()
    return cur.rowcount > 0


# ═══════════════════════════════════════════════
#  Site pages
# ═══════════════════════════════════════════════

def list_pages(site_id: int):
    rows = get_db().execute(
        _convert("SELECT * FROM site_pages WHERE site_id = ? ORDER BY page_key"), (site_id,)
    ).fetchall()
    out = []
    for r in rows:
        d = _to_dict(r)
        d["content"] = _parse_content(d.get("content"))
        out.append(d)
    return out


def get_page(site_id: int, page_key: str, published_only: bool = True):
    db = get_db()
    if published_only:
        row = db.execute(
            _convert("SELECT * FROM site_pages WHERE site_id = ? AND page_key = ? AND is_published = 1"),
            (site_id, page_key),
        ).fetchone()
    else:
        row = db.execute(
            _convert("SELECT * FROM site_pages WHERE site_id = ? AND page_key = ?"),
            (site_id, page_key),
        ).fetchone()
    if row is None:
        return None
    d = _to_dict(row)
    d["content"] = _parse_content(d.get("content"))
    return d


def upsert_page(site_id: int, page_key: str, data: dict) -> dict:
    db = get_db()
    content = data.get("content")
    if content is not None and not isinstance(content, str):
        content = json.dumps(content)
    existing = db.execute(
        _convert("SELECT id FROM site_pages WHERE site_id = ? AND page_key = ?"),
        (site_id, page_key),
    ).fetchone()
    if existing:
        db.execute(
            _convert("UPDATE site_pages SET title = ?, content = ?, is_published = ?, updated_at = ? WHERE site_id = ? AND page_key = ?"),
            (data.get("title"), content, 1 if data.get("is_published", True) else 0, _now(), site_id, page_key),
        )
    else:
        db.execute(
            _convert("INSERT INTO site_pages (site_id, page_key, title, content, is_published, updated_at) VALUES (?, ?, ?, ?, ?, ?)"),
            (site_id, page_key, data.get("title"), content, 1 if data.get("is_published", True) else 0, _now()),
        )
    db.commit()
    return get_page(site_id, page_key, published_only=False)


# ═══════════════════════════════════════════════
#  Services
# ═══════════════════════════════════════════════

def list_services(site_id: int, active_only: bool = False):
    db = get_db()
    if active_only:
        rows = db.execute(
            _convert("SELECT * FROM site_services WHERE site_id = ? AND is_active = 1 ORDER BY sort_order, id"),
            (site_id,),
        ).fetchall()
    else:
        rows = db.execute(
            _convert("SELECT * FROM site_services WHERE site_id = ? ORDER BY sort_order, id"),
            (site_id,),
        ).fetchall()
    return [_to_dict(r) for r in rows]


def get_service(site_id: int, service_id: int):
    row = get_db().execute(
        _convert("SELECT * FROM site_services WHERE site_id = ? AND id = ?"), (site_id, service_id)
    ).fetchone()
    return _to_dict(row)


def create_service(site_id: int, data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO site_services (site_id, name, description, duration_minutes, price, currency, is_active, sort_order, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("name"),
            data.get("description"),
            data.get("duration_minutes", 30),
            data.get("price", 0),
            data.get("currency", "INR"),
            1 if data.get("is_active", True) else 0,
            data.get("sort_order", 0),
            _now(),
        ),
    ).fetchone()
    db.commit()
    return get_service(site_id, cur["id"])


def update_service(site_id: int, service_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["name", "description", "duration_minutes", "price", "currency", "sort_order"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if "is_active" in data:
        fields.append("is_active = ?")
        params.append(1 if data["is_active"] else 0)
    if fields:
        params.append(site_id)
        params.append(service_id)
        db.execute(
            _convert(f"UPDATE site_services SET {', '.join(fields)} WHERE site_id = ? AND id = ?"), params
        )
        db.commit()
    return get_service(site_id, service_id)


def delete_service(site_id: int, service_id: int) -> bool:
    db = get_db()
    db.execute(
        _convert("UPDATE site_bookings SET service_id = NULL WHERE service_id = ?"), (service_id,)
    )
    cur = db.execute(
        _convert("DELETE FROM site_services WHERE site_id = ? AND id = ?"), (site_id, service_id)
    )
    db.commit()
    return cur.rowcount > 0


# ═══════════════════════════════════════════════
#  Availability
# ═══════════════════════════════════════════════

def list_availability(site_id: int):
    rows = get_db().execute(
        _convert("SELECT * FROM site_availability WHERE site_id = ? ORDER BY weekday, start_time"), (site_id,)
    ).fetchall()
    return [_to_dict(r) for r in rows]


def set_availability(site_id: int, rules: list) -> list:
    """Replace all availability rules for a site in one shot."""
    db = get_db()
    db.execute(_convert("DELETE FROM site_availability WHERE site_id = ?"), (site_id,))
    for rule in rules or []:
        weekday = int(rule.get("weekday", 0))
        start_time = str(rule.get("start_time", "10:00"))[:5]
        end_time = str(rule.get("end_time", "18:00"))[:5]
        if 0 <= weekday <= 6:
            db.execute(
                _convert("INSERT INTO site_availability (site_id, weekday, start_time, end_time) VALUES (?, ?, ?, ?)"),
                (site_id, weekday, start_time, end_time),
            )
    db.commit()
    return list_availability(site_id)


# ═══════════════════════════════════════════════
#  Bookings
# ═══════════════════════════════════════════════

def list_bookings(site_id: int, date_from: str = None, date_to: str = None, status: str = ""):
    db = get_db()
    where = ["site_id = ?"]
    params = [site_id]
    if date_from:
        where.append("date >= ?")
        params.append(date_from)
    if date_to:
        where.append("date <= ?")
        params.append(date_to)
    if status:
        where.append("status = ?")
        params.append(status)
    rows = db.execute(
        _convert(f"SELECT * FROM site_bookings WHERE {' AND '.join(where)} ORDER BY date, start_time"),
        params,
    ).fetchall()
    return [_to_dict(r) for r in rows]


def get_booking(site_id: int, booking_id: int):
    row = get_db().execute(
        _convert("SELECT * FROM site_bookings WHERE site_id = ? AND id = ?"), (site_id, booking_id)
    ).fetchone()
    return _to_dict(row)


def create_booking(site_id: int, data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO site_bookings (site_id, service_id, client_name, client_phone, client_email, notes, date, start_time, end_time, status, amount, currency, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("service_id"),
            data.get("client_name"),
            data.get("client_phone"),
            data.get("client_email"),
            data.get("notes"),
            data.get("date"),
            str(data.get("start_time"))[:5],
            str(data.get("end_time"))[:5],
            data.get("status", "confirmed"),
            data.get("amount", 0) or 0,
            data.get("currency", "INR"),
            _now(),
        ),
    ).fetchone()
    db.commit()
    return get_booking(site_id, cur["id"])


def update_booking(site_id: int, booking_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["status", "notes"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if fields:
        params.append(site_id)
        params.append(booking_id)
        db.execute(
            _convert(f"UPDATE site_bookings SET {', '.join(fields)} WHERE site_id = ? AND id = ?"), params
        )
        db.commit()
    return get_booking(site_id, booking_id)


# ═══════════════════════════════════════════════
#  Leads (captured by free tools on tenant sites)
# ═══════════════════════════════════════════════

def create_lead(site_id: int, data: dict) -> dict:
    db = get_db()
    now = _now()
    cur = db.execute(
        _convert(
            "INSERT INTO site_leads (site_id, tool, name, phone, email, details, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("tool") or "kundli",
            data.get("name"),
            data.get("phone"),
            data.get("email"),
            json.dumps(data["details"]) if isinstance(data.get("details"), dict) else data.get("details"),
            now,
        ),
    ).fetchone()
    db.commit()
    lead_id = cur["id"]
    row = db.execute(_convert("SELECT * FROM site_leads WHERE id = ?"), (lead_id,)).fetchone()
    return _to_dict(row)


def list_leads(site_id: int, limit: int = 200) -> list:
    rows = get_db().execute(
        _convert("SELECT * FROM site_leads WHERE site_id = ? ORDER BY created_at DESC LIMIT ?"),
        (site_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        d = _to_dict(r)
        d["details"] = _parse_content(d.get("details"))
        out.append(d)
    return out


# ═══════════════════════════════════════════════
#  Public site bundle (everything the renderer needs, in one call)
# ═══════════════════════════════════════════════

def public_site_bundle(site: dict) -> dict:
    site_id = site["id"]
    pages = {p["page_key"]: p for p in list_pages(site_id) if p.get("is_published")}
    return {
        "site": {
            "id": site_id,
            "slug": site["slug"],
            "name": site["name"],
            "tagline": site["tagline"],
            "template": site["template"],
            "theme": site["theme"],
            "custom_domain": site.get("custom_domain"),
            "logo_url": site.get("logo_url"),
            "hero_image": site.get("hero_image"),
            "settings": site.get("settings"),
        },
        "pages": pages,
        "services": list_services(site_id, active_only=True),
    }
