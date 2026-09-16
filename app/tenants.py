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
from datetime import datetime, timedelta, timezone

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

TEMPLATES = [
    "aurora", "classic", "minimal", "devotional",
    "celestial", "royal", "tantra", "modern-light",
]
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
            "statsYears": "15+",
            "statsYearsLabel": "Years of Practice",
            "statsReadings": "10,000+",
            "statsReadingsLabel": "Kundlis Read",
            "statsRating": "4.9",
            "statsRatingLabel": "Client Rating",
            "whyPoints": [
                {"title": "Accurate Calculations", "text": "Swiss-ephemeris precision — the same engine used by professional software."},
                {"title": "Honest Guidance", "text": "Clear, practical answers. No fear-selling of costly remedies."},
                {"title": "Complete Privacy", "text": "Your birth details and consultations stay strictly confidential."},
                {"title": "Personal Attention", "text": "Every reading is done personally by me — never outsourced."},
            ],
            "testimonialsTitle": "What Clients Say",
            "testimonials": [
                {"name": "Rakesh S.", "text": "His reading of my career period was spot on. Simple remedies, and they worked.", "rating": 5},
                {"name": "Meera T.", "text": "Very patient and honest. Explained my kundli in words I could actually understand.", "rating": 5},
                {"name": "Ankit P.", "text": "Booked online at night, got a confirmation on WhatsApp instantly. Great experience.", "rating": 5},
            ],
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
    # High-profile themes
    "celestial": {"primaryColor": "#4338ca", "accentColor": "#f472b6", "bgStyle": "dark", "fontHeading": "'Cormorant Garamond', 'Playfair Display', Georgia, serif", "heroPattern": "stars"},
    "royal": {"primaryColor": "#7c2d12", "accentColor": "#eab308", "bgStyle": "dark", "fontHeading": "'Playfair Display', Georgia, serif", "heroPattern": "mandala"},
    "tantra": {"primaryColor": "#be123c", "accentColor": "#f97316", "bgStyle": "dark", "heroPattern": "yantra"},
    "modern-light": {"primaryColor": "#2563eb", "accentColor": "#8b5cf6", "bgStyle": "light", "heroPattern": "grid"},
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
    # social links shown in the site header/footer
    "instagram": "",
    "youtube": "",
    "facebook": "",
    "twitter": "",
    "linkedin": "",
    "telegram": "",
    "websiteUrl": "",
    # section toggles so astrologers can hide what they don't use
    "showStore": False,
    "showTestimonials": True,
    "showGallery": False,
    # contact block on the site
    "email": "",
    "phone": "",
    "city": "",
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
                "VALUES (?, ?, ?, ?, TRUE, ?)"
            ),
            (site_id, page_key, page["title"], json.dumps(page["content"]), now),
        )
    # Seed default services
    for i, svc in enumerate(DEFAULT_SERVICES):
        db.execute(
            _convert(
                "INSERT INTO site_services (site_id, name, description, duration_minutes, price, currency, is_active, sort_order, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'INR', TRUE, ?, ?)"
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
    for table in ["site_bookings", "site_availability", "site_services", "site_pages",
                  "site_leads", "site_orders", "site_products"]:
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
            _convert("SELECT * FROM site_pages WHERE site_id = ? AND page_key = ? AND is_published = TRUE"),
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
            (data.get("title"), content, bool(data.get("is_published", True)), _now(), site_id, page_key),
        )
    else:
        db.execute(
            _convert("INSERT INTO site_pages (site_id, page_key, title, content, is_published, updated_at) VALUES (?, ?, ?, ?, ?, ?)"),
            (site_id, page_key, data.get("title"), content, bool(data.get("is_published", True)), _now()),
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
            _convert("SELECT * FROM site_services WHERE site_id = ? AND is_active = TRUE ORDER BY sort_order, id"),
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
            bool(data.get("is_active", True)),
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
        params.append(bool(data["is_active"]))
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

def list_bookings(site_id: int, date_from: str = None, date_to: str = None, status: str = "",
                  tenant_user_id: int = None):
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
    if tenant_user_id:
        where.append("tenant_user_id = ?")
        params.append(tenant_user_id)
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
            "INSERT INTO site_bookings (site_id, service_id, tenant_user_id, client_name, client_phone, client_email, notes, date, start_time, end_time, status, amount, currency, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("service_id"),
            data.get("tenant_user_id"),
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
    for col in ["status", "notes", "payment_status"]:
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
#  Clients (converted leads + manual additions)
# ═══════════════════════════════════════════════

def list_clients(site_id: int, limit: int = 500) -> list:
    rows = get_db().execute(
        _convert("SELECT * FROM site_clients WHERE site_id = ? ORDER BY created_at DESC LIMIT ?"),
        (site_id, limit),
    ).fetchall()
    return [_to_dict(r) for r in rows]


def get_client(site_id: int, client_id: int):
    row = get_db().execute(
        _convert("SELECT * FROM site_clients WHERE site_id = ? AND id = ?"), (site_id, client_id)
    ).fetchone()
    return _to_dict(row)


def create_client(site_id: int, data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO site_clients (site_id, name, email, phone, notes, source, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (site_id, data.get("name"), data.get("email"), data.get("phone"),
         data.get("notes"), data.get("source") or "manual", _now()),
    ).fetchone()
    db.commit()
    return get_client(site_id, cur["id"])


def update_client(site_id: int, client_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["name", "email", "phone", "notes"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if fields:
        params.extend([site_id, client_id])
        db.execute(_convert(f"UPDATE site_clients SET {', '.join(fields)} WHERE site_id = ? AND id = ?"), params)
        db.commit()
    return get_client(site_id, client_id)


def delete_client(site_id: int, client_id: int) -> bool:
    db = get_db()
    cur = db.execute(_convert("DELETE FROM site_clients WHERE site_id = ? AND id = ?"), (site_id, client_id))
    db.commit()
    return cur.rowcount > 0


def convert_lead_to_client(site_id: int, lead_id: int) -> dict:
    """Turn a captured lead into a client record. The lead row is kept (it holds
    the birth details) and linked via client_id so the Leads tab shows 'converted'."""
    db = get_db()
    lead = db.execute(_convert("SELECT * FROM site_leads WHERE site_id = ? AND id = ?"), (site_id, lead_id)).fetchone()
    lead = _to_dict(lead)
    if not lead:
        return None
    if lead.get("client_id"):
        return get_client(site_id, lead["client_id"])

    # re-use an existing client with the same email instead of duplicating
    if lead.get("email"):
        existing = db.execute(
            _convert("SELECT id FROM site_clients WHERE site_id = ? AND LOWER(email) = LOWER(?)"),
            (site_id, lead["email"]),
        ).fetchone()
        if existing:
            client_id = existing["id"]
            db.execute(
                _convert("UPDATE site_leads SET client_id = ?, converted_at = ? WHERE id = ?"),
                (client_id, _now(), lead_id),
            )
            db.commit()
            return get_client(site_id, client_id)

    details = _parse_content(lead.get("details"))
    birth_note = (f" · Born {details.get('date', '')} {details.get('time', '')}".rstrip()
                  if isinstance(details, dict) else "")
    client = create_client(site_id, {
        "name": lead.get("name") or "Unnamed lead",
        "email": lead.get("email"),
        "phone": lead.get("phone"),
        "notes": f"From {lead.get('tool') or 'lead'} tool{birth_note}",
        "source": "lead",
    })
    db.execute(
        _convert("UPDATE site_leads SET client_id = ?, converted_at = ? WHERE id = ?"),
        (client["id"], _now(), lead_id),
    )
    db.commit()
    return client


# ═══════════════════════════════════════════════
#  Invoices
# ═══════════════════════════════════════════════

INVOICE_STATUSES = ("draft", "sent", "paid")


def _next_invoice_number(site_id: int) -> str:
    """Sequential per-site number: INV-2026-0007."""
    year = _now()[:4]
    row = get_db().execute(
        _convert("SELECT COUNT(*) AS n FROM site_invoices WHERE site_id = ?"),
        (site_id,),
    ).fetchone()
    n = (row["n"] if isinstance(row, dict) else row[0]) + 1
    return f"INV-{year}-{n:04d}"


def _invoice_totals(items: list, tax_rate: float):
    subtotal = sum(int((it.get("price") or 0) * (it.get("qty") or 1)) for it in items)
    tax_amount = round(subtotal * (float(tax_rate or 0) / 100))
    return subtotal, tax_amount, subtotal + tax_amount


def _normalize_invoice_items(items) -> list:
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        out.append({"name": name[:120],
                    "qty": max(1, min(999, int(it.get("qty") or 1))),
                    "price": max(0, int(it.get("price") or 0))})
    return out


def list_invoices(site_id: int, client_id: int = None, limit: int = 300) -> list:
    where = ["i.site_id = ?"]
    params = [site_id]
    if client_id:
        where.append("i.client_id = ?")
        params.append(client_id)
    rows = get_db().execute(
        _convert(
            f"SELECT i.*, c.name AS client_name, c.email AS client_email, c.phone AS client_phone "
            f"FROM site_invoices i JOIN site_clients c ON c.id = i.client_id "
            f"WHERE {' AND '.join(where)} ORDER BY i.id DESC LIMIT ?"
        ),
        (*params, limit),
    ).fetchall()
    out = []
    for r in rows:
        d = _to_dict(r)
        d["items"] = _parse_content(d.get("items"))
        out.append(d)
    return out


def get_invoice(site_id: int, invoice_id: int):
    row = get_db().execute(
        _convert(
            "SELECT i.*, c.name AS client_name, c.email AS client_email, c.phone AS client_phone "
            "FROM site_invoices i JOIN site_clients c ON c.id = i.client_id "
            "WHERE i.site_id = ? AND i.id = ?"
        ),
        (site_id, invoice_id),
    ).fetchone()
    d = _to_dict(row)
    if d:
        d["items"] = _parse_content(d.get("items"))
    return d


def get_invoice_by_token(token: str):
    """Public lookup for the shareable invoice link — site-scoped data only."""
    row = get_db().execute(
        _convert(
            "SELECT i.*, c.name AS client_name, c.email AS client_email, c.phone AS client_phone "
            "FROM site_invoices i JOIN site_clients c ON c.id = i.client_id WHERE i.token = ?"
        ),
        (token,),
    ).fetchone()
    d = _to_dict(row)
    if d:
        d["items"] = _parse_content(d.get("items"))
    return d


def create_invoice(site_id: int, data: dict) -> dict:
    import secrets
    db = get_db()
    items = _normalize_invoice_items(data.get("items"))
    tax_rate = float(data.get("tax_rate") or 0)
    subtotal, tax_amount, total = _invoice_totals(items, tax_rate)
    cur = db.execute(
        _convert(
            "INSERT INTO site_invoices (site_id, client_id, number, token, status, items, subtotal, tax_rate, tax_amount, total, currency, due_date, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (site_id, data.get("client_id"), data.get("number") or _next_invoice_number(site_id),
         secrets.token_urlsafe(18), data.get("status") or "draft", json.dumps(items),
         subtotal, tax_rate, tax_amount, total, data.get("currency") or "INR",
         data.get("due_date"), data.get("notes"), _now()),
    ).fetchone()
    db.commit()
    return get_invoice(site_id, cur["id"])


def update_invoice(site_id: int, invoice_id: int, data: dict) -> dict:
    db = get_db()
    existing = get_invoice(site_id, invoice_id)
    if not existing:
        return None
    fields, params = [], []
    if "items" in data and data["items"] is not None:
        items = _normalize_invoice_items(data["items"])
        tax_rate = float(data.get("tax_rate") if data.get("tax_rate") is not None else existing.get("tax_rate") or 0)
        subtotal, tax_amount, total = _invoice_totals(items, tax_rate)
        fields += ["items = ?", "subtotal = ?", "tax_rate = ?", "tax_amount = ?", "total = ?"]
        params += [json.dumps(items), subtotal, tax_rate, tax_amount, total]
    elif data.get("tax_rate") is not None:
        items = existing.get("items") or []
        tax_rate = float(data["tax_rate"])
        subtotal, tax_amount, total = _invoice_totals(items, tax_rate)
        fields += ["tax_rate = ?", "tax_amount = ?", "total = ?"]
        params += [tax_rate, tax_amount, total]
    for col in ["status", "due_date", "notes"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if data.get("status") == "sent" and not existing.get("sent_at"):
        fields.append("sent_at = ?")
        params.append(_now())
    if data.get("status") == "paid" and not existing.get("paid_at"):
        fields.append("paid_at = ?")
        params.append(_now())
    if fields:
        params.extend([site_id, invoice_id])
        db.execute(_convert(f"UPDATE site_invoices SET {', '.join(fields)} WHERE site_id = ? AND id = ?"), params)
        db.commit()
    return get_invoice(site_id, invoice_id)


def delete_invoice(site_id: int, invoice_id: int) -> bool:
    db = get_db()
    cur = db.execute(_convert("DELETE FROM site_invoices WHERE site_id = ? AND id = ?"), (site_id, invoice_id))
    db.commit()
    return cur.rowcount > 0


# ═══════════════════════════════════════════════
#  Products (store)
# ═══════════════════════════════════════════════

def list_products(site_id: int, active_only: bool = False):
    db = get_db()
    if active_only:
        rows = db.execute(
            _convert("SELECT * FROM site_products WHERE site_id = ? AND is_active = TRUE ORDER BY sort_order, id"),
            (site_id,),
        ).fetchall()
    else:
        rows = db.execute(
            _convert("SELECT * FROM site_products WHERE site_id = ? ORDER BY sort_order, id"),
            (site_id,),
        ).fetchall()
    return [_to_dict(r) for r in rows]


def get_product(site_id: int, product_id: int):
    row = get_db().execute(
        _convert("SELECT * FROM site_products WHERE site_id = ? AND id = ?"), (site_id, product_id)
    ).fetchone()
    return _to_dict(row)


def adjust_product_stock(site_id: int, product_id: int, delta: int) -> None:
    """Move tracked stock by `delta` (negative = a sale). Unlimited (stock < 0)
    products are never touched. sqlite: GREATEST-free clamp keeps stock >= 0."""
    db = get_db()
    db.execute(
        _convert(
            "UPDATE site_products SET stock = MAX(stock + ?, 0) "
            "WHERE site_id = ? AND id = ? AND stock >= 0"
        ),
        (delta, site_id, product_id),
    )
    db.commit()


def create_product(site_id: int, data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO site_products (site_id, name, description, price, currency, image, stock, is_active, sort_order, category, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("name"),
            data.get("description"),
            int(data.get("price", 0) or 0),
            data.get("currency", "INR"),
            data.get("image"),
            int(data.get("stock", -1)),
            bool(data.get("is_active", True)),
            int(data.get("sort_order", 0) or 0),
            (data.get("category") or None),
            _now(),
        ),
    ).fetchone()
    db.commit()
    return get_product(site_id, cur["id"])


def update_product(site_id: int, product_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["name", "description", "currency", "image"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    for col in ["price", "stock", "sort_order"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(int(data[col]))
    if "is_active" in data and data["is_active"] is not None:
        fields.append("is_active = ?")
        params.append(bool(data["is_active"]))
    if fields:
        params.append(site_id)
        params.append(product_id)
        db.execute(
            _convert(f"UPDATE site_products SET {', '.join(fields)} WHERE site_id = ? AND id = ?"), params
        )
        db.commit()
    return get_product(site_id, product_id)


def delete_product(site_id: int, product_id: int) -> bool:
    db = get_db()
    cur = db.execute(
        _convert("DELETE FROM site_products WHERE site_id = ? AND id = ?"), (site_id, product_id)
    )
    db.commit()
    return cur.rowcount > 0


# ═══════════════════════════════════════════════
#  Orders (store)
# ═══════════════════════════════════════════════

def list_orders(site_id: int, status: str = "", limit: int = 300, tenant_user_id: int = None):
    db = get_db()
    where = ["site_id = ?"]
    params = [site_id]
    if status:
        where.append("status = ?")
        params.append(status)
    if tenant_user_id:
        where.append("tenant_user_id = ?")
        params.append(tenant_user_id)
    rows = db.execute(
        _convert(f"SELECT * FROM site_orders WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ?"),
        (*params, limit),
    ).fetchall()
    out = []
    for r in rows:
        d = _to_dict(r)
        d["items"] = _parse_content(d.get("items"))
        out.append(d)
    return out


def get_order(site_id: int, order_id: int):
    row = get_db().execute(
        _convert("SELECT * FROM site_orders WHERE site_id = ? AND id = ?"), (site_id, order_id)
    ).fetchone()
    d = _to_dict(row)
    if d:
        d["items"] = _parse_content(d.get("items"))
    return d


ORDER_STATUSES = ("new", "confirmed", "fulfilled", "cancelled")


def create_order(site_id: int, data: dict) -> dict:
    db = get_db()
    items = data.get("items") or []
    if isinstance(items, (list, dict)):
        items = json.dumps(items)
    cur = db.execute(
        _convert(
            "INSERT INTO site_orders (site_id, tenant_user_id, client_name, client_phone, client_email, address, items, amount, currency, status, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("tenant_user_id"),
            data.get("client_name"),
            data.get("client_phone"),
            data.get("client_email"),
            data.get("address"),
            items,
            int(data.get("amount", 0) or 0),
            data.get("currency", "INR"),
            data.get("status", "new"),
            data.get("notes"),
            _now(),
        ),
    ).fetchone()
    db.commit()
    return get_order(site_id, cur["id"])


def update_order(site_id: int, order_id: int, data: dict) -> dict:
    db = get_db()
    fields, params = [], []
    for col in ["status", "notes"]:
        if col in data and data[col] is not None:
            fields.append(f"{col} = ?")
            params.append(data[col])
    if fields:
        params.append(site_id)
        params.append(order_id)
        db.execute(
            _convert(f"UPDATE site_orders SET {', '.join(fields)} WHERE site_id = ? AND id = ?"), params
        )
        db.commit()
    return get_order(site_id, order_id)


# ═══════════════════════════════════════════════
#  Social media queue
# ═══════════════════════════════════════════════

def list_social_posts(site_id: int) -> list:
    rows = get_db().execute(
        _convert("SELECT * FROM site_social_posts WHERE site_id = ? ORDER BY created_at DESC, id DESC"),
        (site_id,),
    ).fetchall()
    return [_to_dict(r) for r in rows]


def get_social_post(site_id: int, post_id: int):
    row = get_db().execute(
        _convert("SELECT * FROM site_social_posts WHERE site_id = ? AND id = ?"), (site_id, post_id)
    ).fetchone()
    return _to_dict(row)


def create_social_post(site_id: int, data: dict) -> dict:
    db = get_db()
    cur = db.execute(
        _convert(
            "INSERT INTO site_social_posts (site_id, content, kind, platforms, scheduled_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?) RETURNING id"
        ),
        (
            site_id,
            data.get("content", ""),
            data.get("kind", "custom"),
            data.get("platforms", ""),
            data.get("scheduled_at"),
            data.get("status", "draft"),
        ),
    )
    post_id = cur.fetchone()[0]
    db.commit()
    return get_social_post(site_id, post_id)


def update_social_post(site_id: int, post_id: int, data: dict) -> dict:
    db = get_db()
    existing = get_social_post(site_id, post_id)
    if not existing:
        return existing
    fields = {
        "content": data.get("content", existing.get("content")),
        "platforms": data.get("platforms", existing.get("platforms")),
        "scheduled_at": data.get("scheduled_at", existing.get("scheduled_at")),
        "status": data.get("status", existing.get("status")),
    }
    posted_at = existing.get("posted_at")
    if data.get("status") == "posted" and not posted_at:
        from datetime import datetime as _dt
        posted_at = _dt.utcnow().isoformat()
    if data.get("status") != "posted":
        posted_at = None if data.get("status") in ("draft", "scheduled", "cancelled") else posted_at
    db.execute(
        _convert("UPDATE site_social_posts SET content = ?, platforms = ?, scheduled_at = ?, status = ?, posted_at = ? WHERE site_id = ? AND id = ?"),
        (fields["content"], fields["platforms"], fields["scheduled_at"], fields["status"], posted_at, site_id, post_id),
    )
    db.commit()
    return get_social_post(site_id, post_id)


def delete_social_post(site_id: int, post_id: int) -> None:
    db = get_db()
    db.execute(_convert("DELETE FROM site_social_posts WHERE site_id = ? AND id = ?"), (site_id, post_id))
    db.commit()


# ═══════════════════════════════════════════════
#  Owner dashboard stats
# ═══════════════════════════════════════════════

def site_stats(site_id: int) -> dict:
    db = get_db()
    today = datetime.now(timezone.utc).date().isoformat()

    def one(sql, params=()):
        return db.execute(_convert(sql), params).fetchone()

    bookings_total = one("SELECT COUNT(*) AS n FROM site_bookings WHERE site_id = ? AND status != 'cancelled'", (site_id,))["n"]
    bookings_upcoming = one(
        "SELECT COUNT(*) AS n FROM site_bookings WHERE site_id = ? AND date >= ? AND status = 'confirmed'", (site_id, today)
    )["n"]
    bookings_pending_revenue = one(
        "SELECT COALESCE(SUM(amount), 0) AS n FROM site_bookings WHERE site_id = ? AND status = 'confirmed'", (site_id,)
    )["n"]
    completed_revenue = one(
        "SELECT COALESCE(SUM(amount), 0) AS n FROM site_bookings WHERE site_id = ? AND status = 'completed'", (site_id,)
    )["n"]
    leads_total = one("SELECT COUNT(*) AS n FROM site_leads WHERE site_id = ?", (site_id,))["n"]
    services_active = one("SELECT COUNT(*) AS n FROM site_services WHERE site_id = ? AND is_active = TRUE", (site_id,))["n"]
    products_active = one("SELECT COUNT(*) AS n FROM site_products WHERE site_id = ? AND is_active = TRUE", (site_id,))["n"]
    orders_new = one("SELECT COUNT(*) AS n FROM site_orders WHERE site_id = ? AND status = 'new'", (site_id,))["n"]
    orders_total = one("SELECT COUNT(*) AS n FROM site_orders WHERE site_id = ?", (site_id,))["n"]
    orders_revenue = one(
        "SELECT COALESCE(SUM(amount), 0) AS n FROM site_orders WHERE site_id = ? AND status IN ('confirmed', 'fulfilled')", (site_id,)
    )["n"]

    upcoming = list_bookings(site_id, date_from=today, status="confirmed")[:5]
    for b in upcoming:
        svc = get_service(site_id, b["service_id"]) if b.get("service_id") else None
        b["service_name"] = svc["name"] if svc else None

    return {
        "bookings": {"total": bookings_total, "upcoming": bookings_upcoming,
                     "confirmedRevenue": bookings_pending_revenue, "completedRevenue": completed_revenue},
        "leads": {"total": leads_total},
        "services": {"active": services_active},
        "store": {"products": products_active, "ordersNew": orders_new,
                  "ordersTotal": orders_total, "revenue": orders_revenue},
        "upcoming": upcoming,
    }


# ═══════════════════════════════════════════════
#  Public site bundle (everything the renderer needs, in one call)
# ═══════════════════════════════════════════════

def products_with_category(site_id: int) -> list:
    """Active shop products with their master category name (for the shop page)."""
    rows = get_db().execute(_convert(
        "SELECT sp.*, mc.name AS category FROM site_products sp "
        "LEFT JOIN master_products mp ON mp.id = sp.master_product_id "
        "LEFT JOIN master_categories mc ON mc.id = mp.category_id "
        "WHERE sp.site_id = ? AND sp.is_active = TRUE ORDER BY mc.sort_order, sp.sort_order, sp.id"
    ), (site_id,)).fetchall()
    import json as _json
    out = []
    for r in rows:
        d = _to_dict(r)
        if d.get("images") and isinstance(d.get("images"), str):
            try: d["images"] = _json.loads(d["images"])
            except Exception: d["images"] = []
        if d.get("image") and not d.get("images"):
            d["images"] = [d["image"]]
        out.append(d)
    return out


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
            # Renderers show the custom domain only once it's verified &
            # serving (domain_status 'active') — until then the free
            # subdomain is the site's real address.
            "domain_status": site.get("domain_status") or "none",
            "logo_url": site.get("logo_url"),
            "hero_image": site.get("hero_image"),
            "settings": site.get("settings"),
        },
        "pages": pages,
        "services": list_services(site_id, active_only=True),
        "products": products_with_category(site_id),
    }


# ═══════════════════════════════════════════════
#  Dropshipping master catalog
# ═══════════════════════════════════════════════

def list_master_categories() -> list:
    rows = get_db().execute(_convert("SELECT * FROM master_categories ORDER BY sort_order, name")).fetchall()
    return [_to_dict(r) for r in rows]


def create_master_category(name: str, slug: str, sort_order: int = 0) -> dict:
    db = get_db()
    cur = db.execute(_convert("INSERT INTO master_categories (name, slug, sort_order) VALUES (?, ?, ?) RETURNING id"),
                     (name, slug, sort_order))
    cid = cur.fetchone()[0]
    db.commit()
    row = db.execute(_convert("SELECT * FROM master_categories WHERE id = ?"), (cid,)).fetchone()
    return _to_dict(row)


def update_master_category(cid: int, data: dict):
    db = get_db()
    db.execute(_convert("UPDATE master_categories SET name = COALESCE(?, name), sort_order = COALESCE(?, sort_order) WHERE id = ?"),
               (data.get("name"), data.get("sort_order"), cid))
    db.commit()


def delete_master_category(cid: int):
    db = get_db()
    db.execute(_convert("DELETE FROM master_categories WHERE id = ?"), (cid,))
    db.commit()


def _parse_attributes(row: dict) -> dict:
    import json as _json
    raw = row.get("attributes")
    if raw and isinstance(raw, str):
        try: row["attributes"] = _json.loads(raw)
        except Exception: row["attributes"] = []
    elif not isinstance(raw, list):
        row["attributes"] = []
    return row


def _parse_images(row: dict) -> dict:
    import json as _json
    if row.get("images") and isinstance(row.get("images"), str):
        try: row["images"] = _json.loads(row["images"])
        except Exception: row["images"] = []
    elif not row.get("images"):
        row["images"] = []
    if row.get("image") and row["image"] not in row["images"]:
        row["images"] = [row["image"]] + row["images"]
    return row


def list_master_products(category_id=None, active_only=False) -> list:
    sql = ("SELECT mp.*, mc.name AS category_name FROM master_products mp "
           "LEFT JOIN master_categories mc ON mc.id = mp.category_id")
    conds, params = [], []
    if category_id:
        conds.append("mp.category_id = ?"); params.append(category_id)
    if active_only:
        conds.append("mp.active = TRUE")
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY mc.sort_order, mp.name"
    rows = get_db().execute(_convert(sql), params).fetchall()
    return [_parse_attributes(_parse_images(_to_dict(r))) for r in rows]


def get_master_product(mid: int):
    row = get_db().execute(_convert("SELECT * FROM master_products WHERE id = ?"), (mid,)).fetchone()
    return _parse_attributes(_parse_images(_to_dict(row)))


def create_master_product(data: dict) -> dict:
    import json as _json
    images = data.get("images")
    attrs = data.get("attributes")
    db = get_db()
    cur = db.execute(_convert(
        "INSERT INTO master_products (category_id, name, description, image, images, attributes, mrp, margin, active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1) RETURNING id"),
        (data.get("category_id"), data.get("name"), data.get("description"), data.get("image"),
         _json.dumps(images) if images else None,
         _json.dumps(attrs) if attrs else None,
         data.get("mrp", 0), data.get("margin", 0)))
    mid = cur.fetchone()[0]
    db.commit()
    return get_master_product(mid)


def update_master_product(mid: int, data: dict):
    db = get_db()
    import json as _json
    images = data.get("images")
    attrs = data.get("attributes")
    db.execute(_convert(
        "UPDATE master_products SET category_id = COALESCE(?, category_id), name = COALESCE(?, name), "
        "description = COALESCE(?, description), image = COALESCE(?, image), images = COALESCE(?, images), "
        "attributes = COALESCE(?, attributes), mrp = COALESCE(?, mrp), margin = COALESCE(?, margin), "
        "active = COALESCE(?, active) WHERE id = ?"),
        (data.get("category_id"), data.get("name"), data.get("description"), data.get("image"),
         _json.dumps(images) if images else None,
         _json.dumps(attrs) if attrs else None,
         data.get("mrp"), data.get("margin"), data.get("active"), mid))
    db.commit()


def delete_master_product(mid: int):
    db = get_db()
    db.execute(_convert("DELETE FROM master_products WHERE id = ?"), (mid,))
    db.commit()


def import_master_product(site_id: int, master_product: dict, price: int):
    """Copy a master product into the tenant's shop. Tenant cost = MRP - margin;
    they sell at `price` (must be >= their cost)."""
    import json as _json
    cost = max(0, int(master_product.get("mrp", 0)) - int(master_product.get("margin", 0)))
    db = get_db()
    images = master_product.get("images") or ([master_product["image"]] if master_product.get("image") else [])
    attrs = master_product.get("attributes") or []
    category = master_product.get("category_name") or master_product.get("category")
    cur = db.execute(_convert(
        "INSERT INTO site_products (site_id, name, description, price, currency, image, stock, is_active, sort_order, "
        "master_product_id, cost_price, images, attributes, category) VALUES (?, ?, ?, ?, 'INR', ?, -1, 1, 0, ?, ?, ?, ?, ?) RETURNING id"),
        (site_id, master_product["name"], master_product.get("description"),
         int(price), images[0] if images else None, master_product["id"], cost,
         _json.dumps(images[:8]) if images else None,
         _json.dumps(attrs) if attrs else None,
         category))
    pid = cur.fetchone()[0]
    db.commit()
    row = db.execute(_convert("SELECT * FROM site_products WHERE id = ?"), (pid,)).fetchone()
    out = _to_dict(row)
    out["images"] = images[:8]
    return out


# ═══════════════════════════════════════════════
#  External store integrations (Shopify / WooCommerce)
# ═══════════════════════════════════════════════

def list_store_connections(site_id: int) -> list:
    rows = get_db().execute(_convert("SELECT * FROM store_connections WHERE site_id = ? ORDER BY id DESC"), (site_id,)).fetchall()
    return [_to_dict(r) for r in rows]


def get_store_connection(site_id: int, cid: int):
    row = get_db().execute(_convert("SELECT * FROM store_connections WHERE site_id = ? AND id = ?"), (site_id, cid)).fetchone()
    return _to_dict(row)


def create_store_connection(site_id: int, data: dict) -> dict:
    db = get_db()
    cur = db.execute(_convert(
        "INSERT INTO store_connections (site_id, provider, shop_domain, api_key, api_secret, access_token) "
        "VALUES (?, ?, ?, ?, ?, ?) RETURNING id"),
        (site_id, data["provider"], data["shop_domain"], data.get("api_key"), data.get("api_secret"), data.get("access_token")))
    cid = cur.fetchone()[0]
    db.commit()
    return get_store_connection(site_id, cid)


def delete_store_connection(site_id: int, cid: int):
    db = get_db()
    db.execute(_convert("DELETE FROM integration_products WHERE connection_id = ?"), (cid,))
    db.execute(_convert("DELETE FROM store_connections WHERE site_id = ? AND id = ?"), (site_id, cid))
    db.commit()


def record_integration_product(connection_id: int, site_product_id: int, external_id: str):
    db = get_db()
    existing = db.execute(_convert(
        "SELECT id FROM integration_products WHERE connection_id = ? AND site_product_id = ?"),
        (connection_id, site_product_id)).fetchone()
    if existing:
        rid = existing[0] if not isinstance(existing, dict) else existing["id"]
        db.execute(_convert("UPDATE integration_products SET external_id = ?, pushed_at = CURRENT_TIMESTAMP WHERE id = ?"),
                   (external_id, rid))
    else:
        db.execute(_convert("INSERT INTO integration_products (connection_id, site_product_id, external_id) VALUES (?, ?, ?)"),
                   (connection_id, site_product_id, external_id))
    db.commit()


def get_integration_product_map(connection_id: int) -> dict:
    rows = get_db().execute(_convert(
        "SELECT site_product_id, external_id FROM integration_products WHERE connection_id = ?"), (connection_id,)).fetchall()
    return {(r[1] if not isinstance(r, dict) else r["site_product_id"]):
            (r[1] if not isinstance(r, dict) else r["external_id"]) for r in rows}


# ── one-click OAuth handshake state (Shopify / WooCommerce) ──
# A handshake row is created when the tenant clicks "Connect", carries the
# shop domain through the provider's approval screen, and is consumed exactly
# once by the callback (single-use CSRF state).

def create_oauth_state(site_id: int, provider: str, shop_domain: str) -> str:
    import secrets as _secrets
    state = _secrets.token_urlsafe(24)
    db = get_db()
    # one pending handshake per (site, provider, shop) — replace any stale one
    db.execute(_convert("DELETE FROM oauth_handshakes WHERE site_id = ? AND provider = ? AND shop_domain = ?"),
               (site_id, provider, shop_domain))
    db.execute(_convert("INSERT INTO oauth_handshakes (state, site_id, provider, shop_domain, created_at) VALUES (?, ?, ?, ?, ?)"),
               (state, site_id, provider, shop_domain, _now()))
    db.commit()
    return state


def get_oauth_state(state: str):
    row = get_db().execute(_convert(
        "SELECT * FROM oauth_handshakes WHERE state = ?"), (state,)).fetchone()
    return _to_dict(row)


def delete_oauth_state(state: str):
    db = get_db()
    db.execute(_convert("DELETE FROM oauth_handshakes WHERE state = ?"), (state,))
    db.commit()


def delete_oauth_state_for_site(site_id: int, provider: str, shop_domain: str):
    db = get_db()
    db.execute(_convert("DELETE FROM oauth_handshakes WHERE site_id = ? AND provider = ? AND shop_domain = ?"),
               (site_id, provider, shop_domain))
    db.commit()


# ═══════════════════════════════════════════════
#  Site credits (API/tool consumption + recharge)
# ═══════════════════════════════════════════════

# Credit costs for tenant-facing features. API-key users keep their own
# plan; these charges apply to the astrologer's own site tools.
SITE_CREDIT_COSTS = {
    "kundli": 2,          # full kundli detail (chart svg, dasha, planets)
    "kundli_basic": 1,
    "matching": 3,        # gun milan + double manglik
    "dosha": 2,
    "horoscope": 1,
    "panchang": 1,
    "ai_content": 5,      # AI-generated text (copy, social)
    "media_render": 2,    # branded image/video render
}


STARTER_CREDITS = 100  # granted per new site so tools work out of the box


def grant_starter_credits(site_id: int) -> None:
    adjust_site_credits(site_id, STARTER_CREDITS, "starter:welcome")


def site_credit_balance(site_id: int) -> int:
    row = get_db().execute(_convert(
        "SELECT balance_after FROM site_credits WHERE site_id = ? ORDER BY id DESC LIMIT 1"
    ), (site_id,)).fetchone()
    return (row[0] if not isinstance(row, dict) else row["balance_after"]) if row else 0


def adjust_site_credits(site_id: int, delta: int, reason: str = "") -> int:
    """Apply a credit change; returns the new balance (never below 0)."""
    db = get_db()
    bal = max(0, site_credit_balance(site_id) + delta)
    db.execute(_convert(
        "INSERT INTO site_credits (site_id, delta, balance_after, reason) VALUES (?, ?, ?, ?)"),
        (site_id, delta, bal, reason[:200]))
    db.commit()
    return bal


def site_has_credit_rows(site_id: int) -> bool:
    row = get_db().execute(_convert(
        "SELECT id FROM site_credits WHERE site_id = ? LIMIT 1"), (site_id,)).fetchone()
    return row is not None


def ensure_starter_credits(site_id: int) -> None:
    """Sites created before the credits feature have no ledger — grant them
    the starter pack once, lazily, so their tools keep working."""
    if not site_has_credit_rows(site_id):
        adjust_site_credits(site_id, STARTER_CREDITS, "starter:welcome")


def charge_site_credits(site_id: int, feature: str) -> bool:
    """Charge the feature cost if affordable. Returns False when out of credits."""
    ensure_starter_credits(site_id)
    cost = SITE_CREDIT_COSTS.get(feature, 0)
    if cost <= 0:
        return True
    bal = site_credit_balance(site_id)
    if bal < cost:
        return False
    adjust_site_credits(site_id, -cost, f"usage:{feature}")
    return True


def site_credit_history(site_id: int, limit: int = 30) -> list:
    rows = get_db().execute(_convert(
        "SELECT * FROM site_credits WHERE site_id = ? ORDER BY id DESC LIMIT ?"), (site_id, limit)).fetchall()
    return [_to_dict(r) for r in rows]


# ═══════════════════════════════════════════════
#  Site analytics events (pageviews / visitors)
# ═══════════════════════════════════════════════

def record_site_event(site_id: int, kind: str, path: str = None) -> None:
    db = get_db()
    db.execute(_convert("INSERT INTO site_events (site_id, kind, path) VALUES (?, ?, ?)"),
               (site_id, kind[:40], (path or "")[:200]))
    db.commit()


def site_analytics(site_id: int, days: int = 30) -> dict:
    db = get_db()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    total = db.execute(_convert(
        "SELECT COUNT(*) FROM site_events WHERE site_id = ? AND kind = 'pageview' AND created_at >= ?"),
        (site_id, since)).fetchone()[0]
    # unique-ish visitors: distinct minute-bucketed sessions
    visitors = db.execute(_convert(
        "SELECT COUNT(DISTINCT substr(CAST(created_at AS TEXT), 1, 16)) FROM site_events "
        "WHERE site_id = ? AND kind = 'pageview' AND created_at >= ?"), (site_id, since)).fetchone()[0]
    daily = db.execute(_convert(
        "SELECT substr(CAST(created_at AS TEXT), 1, 10) AS d, COUNT(*) FROM site_events "
        "WHERE site_id = ? AND kind = 'pageview' AND created_at >= ? GROUP BY d ORDER BY d"),
        (site_id, since)).fetchall()
    tools = db.execute(_convert(
        "SELECT path, COUNT(*) FROM site_events WHERE site_id = ? AND kind = 'tool' "
        "AND created_at >= ? GROUP BY path ORDER BY COUNT(*) DESC LIMIT 6"), (site_id, since)).fetchall()
    return {
        "pageviews": total,
        "visitors": visitors,
        "daily": [{"date": r[0], "views": r[1]} for r in daily],
        "topTools": [{"tool": r[0], "count": r[1]} for r in tools],
        "days": days,
    }
