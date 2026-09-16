"""White-label booking confirmation emails: client + astrologer notifications.

The emails must carry ONLY the astrologer's brand (site name, colors, contact)
— never the platform's — with replies routed to the right person."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.email_service as email_service
from app.database import get_db
from app.main import app

client = TestClient(app)

TOMORROW = (date.today() + timedelta(days=1)).isoformat()

SITE = {
    "id": 6,
    "user_id": 1,
    "slug": "pandit-sharma",
    "name": "Pandit Sharma Jyotish",
    "tagline": "Vedic Astrologer · 20+ years",
    "logo_url": None,
    "custom_domain": None,
    "theme": {"primaryColor": "#b45309", "accentColor": "#d97706"},
    "settings": {"email": "pandit@sharma.in", "phone": "+91 98765 43210",
                 "city": "Jaipur", "paymentsMode": "later", "bookingAlerts": True},
}

BOOKING = {
    "id": 42,
    "service_id": 3,
    "client_name": "Ravi Kumar",
    "client_phone": "+91 90000 11111",
    "client_email": "ravi@example.com",
    "notes": "Born in Delhi, 1990-05-15 14:30",
    "date": TOMORROW,
    "start_time": "10:00",
    "end_time": "10:45",
    "amount": 500,
    "currency": "INR",
    "status": "confirmed",
}

SERVICE = {"id": 3, "name": "Career & Business Consultation", "duration_minutes": 45, "price": 500}


@pytest.fixture
def sent_emails(monkeypatch):
    """Capture every _send_html call instead of hitting Resend."""
    outbox = []

    def fake_send(to, subject, html_body, from_display="", reply_to=""):
        outbox.append({"to": to, "subject": subject, "html": html_body,
                       "from": from_display, "reply_to": reply_to})
        return True

    monkeypatch.setattr(email_service, "_send_html", fake_send)
    return outbox


def test_client_confirmation_is_white_labelled(sent_emails):
    result = email_service.send_booking_emails(dict(SITE), dict(BOOKING), dict(SERVICE))
    # owner alert goes to the site contact email (no matching platform user needed)
    assert result == {"client": True, "owner": True}
    assert sorted(m["to"] for m in sent_emails) == ["pandit@sharma.in", "ravi@example.com"]

    client_mail = next(m for m in sent_emails if m["to"] == "ravi@example.com")
    assert "Pandit Sharma Jyotish" in client_mail["from"]           # sender shows the astrologer…
    assert "noreply@astrovakta.com" in client_mail["from"]          # …over the verified domain
    assert client_mail["reply_to"] == "pandit@sharma.in"            # replies reach the astrologer
    assert "Pandit Sharma Jyotish" in client_mail["subject"]

    body = client_mail["html"]
    assert "Pandit Sharma Jyotish" in body
    assert "Career &amp; Business Consultation" in body   # escaped: HTML-safe rendering
    assert "Ravi" in body
    assert "+91 98765 43210" in body
    assert "10:00" in body and "10:45" in body
    assert "&#8377;500" in body                                   # ₹ as an entity — charset-proof
    assert "1990-05-15" not in body or "Delhi" not in body          # no client notes in client mail
    # white-label: the platform brand never appears in the email body
    assert "AstroVakta" not in body


def test_owner_alert_contains_client_details_and_reply_to_client(sent_emails, ):
    email_service.send_booking_emails(dict(SITE), dict(BOOKING), dict(SERVICE), notify_owner=False)
    # explicit owner send with a resolved address
    email_service.send_booking_alert_to_owner(dict(SITE), dict(BOOKING), dict(SERVICE),
                                              owner_email="owner@sharma.in")
    owner_mail = next(m for m in sent_emails if m["to"] == "owner@sharma.in")
    assert "Ravi Kumar" in owner_mail["html"]
    assert "ravi@example.com" in owner_mail["html"]
    assert "+91 90000 11111" in owner_mail["html"]
    assert "Born in Delhi" in owner_mail["html"]                    # notes only in the owner mail
    assert owner_mail["reply_to"] == "ravi@example.com"             # one-tap reply to the client
    assert "AstroVakta" not in owner_mail["html"]


def test_booking_alerts_setting_opts_out_owner(sent_emails):
    site = dict(SITE)
    site["settings"] = {**SITE["settings"], "bookingAlerts": False}
    email_service.send_booking_emails(site, dict(BOOKING), dict(SERVICE), notify_owner=False)
    email_service.send_booking_emails(site, dict(BOOKING), dict(SERVICE))
    # the client mail fires in both calls, but the owner (contact email) never gets an alert
    assert "pandit@sharma.in" not in [m["to"] for m in sent_emails]


# ─────────────── end-to-end: the booking flow sends the emails ───────────────

_SITE_TABLES = ("site_bookings", "site_orders", "site_invoices", "site_clients",
                "tenant_users", "site_leads", "site_pages", "site_services",
                "site_products", "site_availability", "site_social_posts",
                "site_credits", "site_events", "store_connections",
                "oauth_handshakes")


@pytest.fixture
def astro_site():
    state = {}
    yield state
    if "site_id" not in state:
        return
    db = get_db()
    for tbl in _SITE_TABLES:
        db.execute(f"DELETE FROM {tbl} WHERE site_id = ?", (state["site_id"],))
    db.execute("DELETE FROM sites WHERE id = ?", (state["site_id"],))
    db.commit()


def test_public_booking_sends_both_emails(astro_site, sent_emails):
    reg = client.post("/auth/register", json={
        "email": f"owner-{uuid4().hex[:8]}@example.com", "name": "Astro Owner", "password": "ownerpass123"})
    owner_email = reg.json()["user"]["email"]
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}

    slug = f"vis-{uuid4().hex[:8]}"
    site = client.post("/sites/my", headers=owner, json={"slug": slug, "name": "Email Test Astro"})
    assert site.status_code == 200, site.text
    site_id = site.json()["id"]
    astro_site["site_id"] = site_id

    assert client.post(f"/sites/my/{site_id}/services", headers=owner, json={
        "name": "Email Reading", "duration_minutes": 30, "price": 250}).status_code == 200
    rules = [{"weekday": d, "start_time": "09:00", "end_time": "17:00"} for d in range(7)]
    client.put(f"/sites/my/{site_id}/availability", headers=owner, json={"rules": rules})
    assert client.post(f"/sites/my/{site_id}/publish", headers=owner).status_code == 200

    vreg = client.post(f"/sites/site/auth/register?slug={slug}", json={
        "email": "walkin@example.com", "password": "visitorpass123", "name": "Walk In"})
    token = vreg.json()["tenant_token"]
    res = client.post(f"/sites/site/book?slug={slug}", headers={
        "Authorization": f"Bearer {token}"}, json={
        "date": TOMORROW, "start_time": "10:00"})
    assert res.status_code == 200, res.text

    # platform emails (verification) also pass through the outbox — filter to the white-label ones
    booking_mails = [m for m in sent_emails if "Verify" not in m["subject"]]
    assert sorted(m["to"] for m in booking_mails) == sorted([owner_email, "walkin@example.com"])
    owner_mail = next(m for m in booking_mails if m["to"] == owner_email)
    client_mail = next(m for m in booking_mails if m["to"] == "walkin@example.com")
    assert "walkin@example.com" in owner_mail["html"]
    assert "Email Test Astro" in client_mail["html"]
    assert "AstroVakta" not in client_mail["html"]


def test_manual_owner_booking_sends_client_only(astro_site, sent_emails):
    reg = client.post("/auth/register", json={
        "email": f"owner-{uuid4().hex[:8]}@example.com", "name": "Astro Owner", "password": "ownerpass123"})
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}

    slug = f"vis-{uuid4().hex[:8]}"
    site = client.post("/sites/my", headers=owner, json={"slug": slug, "name": "Manual Test Astro"})
    site_id = site.json()["id"]
    astro_site["site_id"] = site_id

    res = client.post(f"/sites/my/{site_id}/bookings", headers=owner, json={
        "client_name": "Phone Client", "client_email": "phoneclient@example.com",
        "date": TOMORROW, "start_time": "11:00", "end_time": "11:30", "amount": 0, "currency": "INR"})
    assert res.status_code == 200, res.text

    booking_mails = [m for m in sent_emails if "Verify" not in m["subject"]]
    assert [m["to"] for m in booking_mails] == ["phoneclient@example.com"]  # client only, no self-alert
    assert "Manual Test Astro" in booking_mails[0]["html"]
    assert "AstroVakta" not in booking_mails[0]["html"]
