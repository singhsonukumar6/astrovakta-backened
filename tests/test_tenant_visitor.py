"""Tenant visitor accounts: sign-in gated booking & store checkout, and the
visitor's My Account (consultations + orders)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)

TOMORROW = (date.today() + timedelta(days=1)).isoformat()

_SITE_TABLES = ("site_bookings", "site_orders", "site_invoices", "site_clients",
                "tenant_users", "site_leads", "site_pages", "site_services",
                "site_products", "site_availability", "site_social_posts",
                "site_credits", "site_events", "store_connections",
                "oauth_handshakes")


@pytest.fixture
def astro_site():
    """Published site with a service, all-week hours and a stocked product.
    Cleans up after itself (conftest wipes `users`, not tenant site data)."""
    state = {}
    yield state
    if "site_id" not in state:
        return
    db = get_db()
    for tbl in _SITE_TABLES:
        db.execute(f"DELETE FROM {tbl} WHERE site_id = ?", (state["site_id"],))
    db.execute("DELETE FROM sites WHERE id = ?", (state["site_id"],))
    db.commit()


def _visitor_signup(site_slug):
    email = f"visitor-{uuid4().hex[:8]}@example.com"
    reg = client.post(f"/sites/site/auth/register?slug={site_slug}", json={
        "email": email, "password": "visitorpass123", "name": "Vish Visitor"})
    assert reg.status_code == 200, reg.text
    return reg.json()["tenant_token"], email


def test_booking_requires_visitor_account(astro_site):
    email = f"owner-{uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={"email": email, "name": "Astro Owner", "password": "ownerpass123"})
    assert reg.status_code == 200, reg.text
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}

    slug = f"vis-{uuid4().hex[:8]}"
    site = client.post("/sites/my", headers=owner, json={"slug": slug, "name": "Visitor Test Astro"})
    assert site.status_code == 200, site.text
    astro_site["site_id"] = site.json()["id"]

    svc = client.post(f"/sites/my/{site.json()['id']}/services", headers=owner, json={
        "name": "Career Reading", "duration_minutes": 30, "price": 500})
    assert svc.status_code == 200, svc.text
    service_id = svc.json()["id"]

    rules = [{"weekday": d, "start_time": "09:00", "end_time": "17:00"} for d in range(7)]
    assert client.put(f"/sites/my/{site.json()['id']}/availability", headers=owner, json={"rules": rules}).status_code == 200
    assert client.post(f"/sites/my/{site.json()['id']}/publish", headers=owner).status_code == 200

    # anonymous booking is rejected
    anon = client.post(f"/sites/site/book?slug={slug}", json={
        "service_id": service_id, "date": TOMORROW, "start_time": "10:00"})
    assert anon.status_code == 401, anon.text

    # a platform (owner) token is NOT a visitor token on the tenant site
    platform = client.post(f"/sites/site/book?slug={slug}", headers={
        "Authorization": owner["Authorization"]}, json={
        "service_id": service_id, "date": TOMORROW, "start_time": "10:00"})
    assert platform.status_code in (401, 403), platform.text

    # signed-up visitor books successfully
    token, _ = _visitor_signup(slug)
    res = client.post(f"/sites/site/book?slug={slug}", headers={
        "Authorization": f"Bearer {token}"}, json={
        "service_id": service_id, "date": TOMORROW, "start_time": "10:00"})
    assert res.status_code == 200, res.text
    booking = res.json()["booking"]
    assert booking["date"] == TOMORROW and booking["start_time"] == "10:00"
    assert booking["client_name"] == "Vish Visitor"          # defaulted from the account
    assert booking["client_email"].endswith("@example.com")  # captured from the account

    # it shows up in the visitor's consultations
    mine = client.get(f"/sites/site/my/bookings?slug={slug}", headers={"Authorization": f"Bearer {token}"})
    assert mine.status_code == 200, mine.text
    bookings = mine.json()["bookings"]
    assert len(bookings) == 1 and bookings[0]["service_id"] == service_id

    # and can be cancelled by the visitor
    cancel = client.post(f"/sites/site/my/bookings/{bookings[0]['id']}/cancel?slug={slug}",
                         headers={"Authorization": f"Bearer {token}"})
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["booking"]["status"] == "cancelled"

    # the freed slot can be booked again — availability isn't leaked by cancels
    again = client.post(f"/sites/site/book?slug={slug}", headers={
        "Authorization": f"Bearer {token}"}, json={
        "service_id": service_id, "date": TOMORROW, "start_time": "10:00"})
    assert again.status_code == 200, again.text


def test_order_requires_visitor_account_and_is_listed(astro_site):
    email = f"owner-{uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={"email": email, "name": "Astro Owner", "password": "ownerpass123"})
    assert reg.status_code == 200, reg.text
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}

    slug = f"vis-{uuid4().hex[:8]}"
    site = client.post("/sites/my", headers=owner, json={"slug": slug, "name": "Visitor Test Astro"})
    assert site.status_code == 200, site.text
    site_id = site.json()["id"]
    astro_site["site_id"] = site_id

    prod = client.post(f"/sites/my/{site_id}/products", headers=owner, json={
        "name": "Ruby Bracelet", "price": 1500, "stock": 5})
    assert prod.status_code == 200, prod.text
    product_id = prod.json()["id"]
    assert client.post(f"/sites/my/{site_id}/publish", headers=owner).status_code == 200

    # anonymous checkout is rejected
    anon = client.post(f"/sites/site/order?slug={slug}", json={
        "items": [{"product_id": product_id, "qty": 1}]})
    assert anon.status_code == 401, anon.text

    token, vEmail = _visitor_signup(slug)
    res = client.post(f"/sites/site/order?slug={slug}", headers={
        "Authorization": f"Bearer {token}"}, json={
        "items": [{"product_id": product_id, "qty": 2}]})
    assert res.status_code == 200, res.text
    order = res.json()["order"]
    assert order["amount"] == 3000

    # the order landed with the owner, tied to the visitor's email
    owner_orders = client.get(f"/sites/my/{site_id}/orders", headers=owner).json()["orders"]
    assert len(owner_orders) == 1 and owner_orders[0]["client_email"] == vEmail

    # the visitor sees it under My Account and cancels it — stock is restored
    mine = client.get(f"/sites/site/my/orders?slug={slug}", headers={"Authorization": f"Bearer {token}"})
    assert mine.status_code == 200, mine.text
    orders = mine.json()["orders"]
    assert len(orders) == 1 and orders[0]["status"] == "new"

    cancel = client.post(f"/sites/site/my/orders/{order['id']}/cancel?slug={slug}",
                         headers={"Authorization": f"Bearer {token}"})
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["order"]["status"] == "cancelled"
    products = client.get(f"/sites/my/{site_id}/products", headers=owner).json()["products"]
    assert next(p for p in products if p["id"] == product_id)["stock"] == 5


def test_visitor_session_is_site_scoped(astro_site):
    email = f"owner-{uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={"email": email, "name": "Astro Owner", "password": "ownerpass123"})
    assert reg.status_code == 200, reg.text
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}

    slug = f"vis-{uuid4().hex[:8]}"
    site = client.post("/sites/my", headers=owner, json={"slug": slug, "name": "Visitor Test Astro"})
    assert site.status_code == 200, site.text
    astro_site["site_id"] = site.json()["id"]
    assert client.post(f"/sites/my/{site.json()['id']}/publish", headers=owner).status_code == 200

    token, _ = _visitor_signup(slug)

    # a second site must not accept the first site's visitor session
    reg2 = client.post("/auth/register", json={
        "email": f"owner2-{uuid4().hex[:8]}@example.com", "name": "Owner Two", "password": "ownerpass123"})
    other = client.post("/sites/my", headers={"Authorization": f"Bearer {reg2.json()['token']}"},
                        json={"slug": f"vis-{uuid4().hex[:8]}", "name": "Other Astro"})
    other_slug = other.json()["slug"]
    assert client.post(f"/sites/my/{other.json()['id']}/publish",
                       headers={"Authorization": f"Bearer {reg2.json()['token']}"}).status_code == 200

    cross = client.get(f"/sites/site/my/bookings?slug={other_slug}",
                       headers={"Authorization": f"Bearer {token}"})
    assert cross.status_code == 403, cross.text

    # cleanup for the second site too
    db = get_db()
    for tbl in _SITE_TABLES:
        db.execute(f"DELETE FROM {tbl} WHERE site_id = ?", (other.json()["id"],))
    db.execute("DELETE FROM sites WHERE id = ?", (other.json()["id"],))
    db.commit()
