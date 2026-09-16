"""Leads → Clients conversion, manual clients, and the invoice generator
(white-label email + shareable public link)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.email_service as email_service
from app.database import get_db
from app.main import app

client = TestClient(app)

TOMORROW = (date.today() + timedelta(days=2)).isoformat()

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


@pytest.fixture
def outbox(monkeypatch):
    """Capture emails instead of hitting Resend."""
    out = []

    def fake_send(to, subject, html_body, from_display="", reply_to=""):
        out.append({"to": to, "subject": subject, "html": html_body,
                    "from": from_display, "reply_to": reply_to})
        return True

    monkeypatch.setattr(email_service, "_send_html", fake_send)
    return out


def _owner_and_site(astro_site, name="Client Test Astro"):
    reg = client.post("/auth/register", json={
        "email": f"owner-{uuid4().hex[:8]}@example.com", "name": "Astro Owner", "password": "ownerpass123"})
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}
    site = client.post("/sites/my", headers=owner, json={
        "slug": f"cli-{uuid4().hex[:8]}", "name": name})
    assert site.status_code == 200, site.text
    astro_site["site_id"] = site.json()["id"]
    return owner, site.json()["id"]


def _make_lead(site_id, name="Ramesh Lead", email=None, phone="+91 90000 11111"):
    from app.tenants import create_lead
    return create_lead(site_id, {
        "tool": "kundli", "name": name, "phone": phone, "email": email,
        "details": {"date": "1992-04-12", "time": "08:30", "place": "Pune"},
    })


def test_lead_conversion_and_manual_clients(astro_site):
    owner, site_id = _owner_and_site(astro_site)
    lead = _make_lead(site_id, email="ramesh@example.com")

    # convert the lead → appears in clients with birth info in notes
    res = client.post(f"/sites/my/{site_id}/leads/{lead['id']}/convert", headers=owner)
    assert res.status_code == 200, res.text
    client_row = res.json()
    assert client_row["name"] == "ramesh".title() or client_row["name"] == "Ramesh Lead"
    assert client_row["email"] == "ramesh@example.com"
    assert client_row["source"] == "lead"
    assert "1992-04-12" in (client_row.get("notes") or "")

    # the lead is marked converted
    leads = client.get(f"/sites/my/{site_id}/leads", headers=owner).json()["leads"]
    assert next(l for l in leads if l["id"] == lead["id"])["client_id"] == client_row["id"]

    # converting again returns the SAME client (no duplicate)
    again = client.post(f"/sites/my/{site_id}/leads/{lead['id']}/convert", headers=owner)
    assert again.json()["id"] == client_row["id"]
    clients = client.get(f"/sites/my/{site_id}/clients", headers=owner).json()["clients"]
    assert len(clients) == 1

    # a second lead with the same email re-uses the client
    lead2 = _make_lead(site_id, name="Ramesh Again", email="RAMESH@example.com")
    res2 = client.post(f"/sites/my/{site_id}/leads/{lead2['id']}/convert", headers=owner)
    assert res2.json()["id"] == client_row["id"]
    assert len(client.get(f"/sites/my/{site_id}/clients", headers=owner).json()["clients"]) == 1

    # manual client add + edit + delete
    created = client.post(f"/sites/my/{site_id}/clients", headers=owner, json={
        "name": "Sunita Manual", "email": "sunita@example.com", "phone": "+91 91234 56789"})
    assert created.status_code == 200, created.text
    cid = created.json()["id"]
    updated = client.put(f"/sites/my/{site_id}/clients/{cid}", headers=owner,
                         json={"name": "Sunita M."})
    assert updated.json()["name"] == "Sunita M."
    assert client.delete(f"/sites/my/{site_id}/clients/{cid}", headers=owner).status_code == 200

    # another owner cannot touch this site's clients
    other = client.post("/auth/register", json={
        "email": f"other-{uuid4().hex[:8]}@example.com", "name": "Other", "password": "otherpass123"})
    forbidden = client.get(f"/sites/my/{site_id}/clients",
                           headers={"Authorization": f"Bearer {other.json()['token']}"})
    assert forbidden.status_code in (403, 404)


def test_invoice_lifecycle_numbering_email_and_public_link(astro_site, outbox):
    owner, site_id = _owner_and_site(astro_site, name="Invoice Astro Sharma")
    # white-label contact info on the site
    from app.tenants import update_site
    update_site(site_id, {"settings": {"email": "sharma@astro.in", "phone": "+91 98765 43210",
                                       "city": "Jaipur", "paymentsMode": "upi", "upiId": "sharma@ybl"}})

    client_row = client.post(f"/sites/my/{site_id}/clients", headers=owner, json={
        "name": "Mahesh Client", "email": "mahesh@example.com", "phone": "+91 90000 22222"}).json()

    # create invoice with items + 18% tax
    inv = client.post(f"/sites/my/{site_id}/invoices", headers=owner, json={
        "client_id": client_row["id"],
        "items": [{"name": "Full kundli reading", "qty": 1, "price": 1500},
                  {"name": "Gemstone consultation", "qty": 2, "price": 500}],
        "tax_rate": 18, "due_date": TOMORROW, "notes": "Pay via UPI after the session"})
    assert inv.status_code == 200, inv.text
    inv = inv.json()
    assert inv["number"].startswith("INV-")
    assert inv["subtotal"] == 2500
    assert inv["tax_amount"] == 450          # 18% of 2500
    assert inv["total"] == 2950
    assert inv["status"] == "draft"
    assert inv["client_name"] == "Mahesh Client"

    # second invoice gets the next sequential number
    inv2 = client.post(f"/sites/my/{site_id}/invoices", headers=owner, json={
        "client_id": client_row["id"], "items": [{"name": "Follow-up", "qty": 1, "price": 300}]}).json()
    assert int(inv2["number"].split("-")[-1]) == int(inv["number"].split("-")[-1]) + 1

    # send by email: white-label, branded, link included, marks it sent
    sent = client.post(f"/sites/my/{site_id}/invoices/{inv['id']}/send", headers=owner)
    assert sent.status_code == 200, sent.text
    assert sent.json()["invoice"]["status"] == "sent"
    mails = [m for m in outbox if m["to"] == "mahesh@example.com"]
    assert len(mails) == 1
    mail = mails[0]
    assert "Invoice Astro Sharma" in mail["from"]                       # astrologer's name as sender
    assert "noreply@astrovakta.com" in mail["from"]                     # verified platform domain
    assert mail["reply_to"] == "sharma@astro.in"                        # replies reach the astrologer
    assert inv["number"] in mail["subject"] and "2950" in mail["subject"]
    assert f"/invoice/{inv['token']}" in mail["html"]                   # shareable link
    assert "AstroVakta" not in mail["html"]                             # white-label body

    # invoice without a client email can't be emailed
    no_email = client.post(f"/sites/my/{site_id}/clients", headers=owner, json={"name": "No Email"}).json()
    inv3 = client.post(f"/sites/my/{site_id}/invoices", headers=owner, json={
        "client_id": no_email["id"], "items": [{"name": "X", "qty": 1, "price": 100}]}).json()
    blocked = client.post(f"/sites/my/{site_id}/invoices/{inv3['id']}/send", headers=owner)
    assert blocked.status_code == 400

    # mark paid
    paid = client.post(f"/sites/my/{site_id}/invoices/{inv2['id']}/status", headers=owner,
                       json={"status": "paid"})
    assert paid.json()["status"] == "paid" and paid.json()["paid_at"]

    # public link: site brand + invoice, no owner-only data, no auth needed
    pub = client.get(f"/sites/invoice/{inv['token']}")
    assert pub.status_code == 200, pub.text
    body = pub.json()
    assert body["site"]["name"] == "Invoice Astro Sharma"
    assert body["site"]["contact"]["phone"] == "+91 98765 43210"
    assert body["invoice"]["total"] == 2950
    assert body["invoice"]["client_name"] == "Mahesh Client"
    assert "settings" not in body["site"]                                # no secrets leak
    assert "razorpayKeyId" not in str(body) and "api_secret" not in str(body)

    # unknown token 404s
    assert client.get("/sites/invoice/nonexistent-token").status_code == 404
