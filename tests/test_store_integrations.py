"""One-click store integrations: begin → provider callback → connection row.

The provider approval screens (Shopify oauth, WordPress authorize_application.php)
are external; here we verify the handshake mechanics around them:
- `begin` issues a single-use state and a correctly-shaped authorize URL
- the callbacks consume the state exactly once, create the connection only
  when the provider returns credentials, and never leak credentials in
  GET /integrations listings
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)

# The OAuth callbacks redirect to the frontend; we assert on the Location
# header, so never follow it (it points at a real https:// URL).
client_no_redirects = TestClient(app, follow_redirects=False)

_SITE_TABLES = ("site_bookings", "site_orders", "site_invoices", "site_clients",
                "tenant_users", "site_leads", "site_pages", "site_services",
                "site_products", "site_availability", "site_social_posts",
                "site_credits", "site_events", "store_connections",
                "oauth_handshakes")


@pytest.fixture
def owner_site():
    email = f"owner-{uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={"email": email, "name": "Owner", "password": "ownerpass123"})
    assert reg.status_code == 200, reg.text
    owner = {"Authorization": f"Bearer {reg.json()['token']}"}
    slug = f"oneclick-{uuid4().hex[:8]}"
    site = client.post("/sites/my", headers=owner, json={"slug": slug, "name": "One Click Test"})
    assert site.status_code == 200, site.text
    state = {"headers": owner, "site_id": site.json()["id"], "slug": slug}
    yield state
    db = get_db()
    for tbl in _SITE_TABLES:
        db.execute(f"DELETE FROM {tbl} WHERE site_id = ?", (state["site_id"],))
    db.execute("DELETE FROM store_connections WHERE site_id = ?", (state["site_id"],))
    db.execute("DELETE FROM oauth_handshakes WHERE site_id = ?", (state["site_id"],))
    db.execute("DELETE FROM sites WHERE id = ?", (state["site_id"],))
    db.commit()


def test_begin_returns_authorize_urls(owner_site, monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://api.test.example")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "csecret")
    h, sid = owner_site["headers"], owner_site["site_id"]

    providers = client.get(f"/sites/my/{sid}/integrations/providers", headers=h)
    assert providers.status_code == 200
    assert providers.json()["shopify_one_click"] is True
    assert providers.json()["woocommerce_one_click"] is True

    shopify = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                          json={"provider": "shopify", "shop_domain": "https://My-Store.myshopify.com/admin"})
    assert shopify.status_code == 200, shopify.text
    url = shopify.json()["authorize_url"]
    assert url.startswith("https://my-store.myshopify.com/admin/oauth/authorize?")
    assert "client_id=cid" in url
    assert "redirect_uri=https%3A%2F%2Fapi.test.example%2Fsites%2Fintegrations%2Fcallback%2Fshopify" in url

    woo = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                      json={"provider": "woocommerce", "shop_domain": "shop.example.com"})
    assert woo.status_code == 200, woo.text
    wurl = woo.json()["authorize_url"]
    assert wurl.startswith("https://shop.example.com/wp-admin/authorize_application.php?")
    assert "app_name=AstroVakta" in wurl
    # state rides inside success_url — WordPress drops unknown params
    assert "state%3D" in wurl or "state=" in wurl
    assert "callback%2Fwoocommerce%3Fstate%3D" in wurl


def test_begin_validates_domain(owner_site):
    h, sid = owner_site["headers"], owner_site["site_id"]
    bad = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                      json={"provider": "shopify", "shop_domain": "notadomain"})
    assert bad.status_code == 400
    # XSS-style domains are normalized away, not reflected
    evil = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                       json={"provider": "woocommerce", "shop_domain": "evil.com/path?x=1"})
    assert evil.status_code == 200
    assert "evil.com/path" not in evil.json()["authorize_url"]


def test_woo_callback_creates_and_verifies_connection(owner_site, monkeypatch):
    """Simulate WordPress redirecting back with user_login + password, with the
    store verification mocked (no real WooCommerce store in tests)."""
    monkeypatch.setenv("FRONTEND_URL", "https://app.test.example")
    h, sid = owner_site["headers"], owner_site["site_id"]

    begin = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                        json={"provider": "woocommerce", "shop_domain": "shop.example.com"})
    assert begin.status_code == 200, begin.text
    state = begin.json()["state"]

    import app.store_integrations as si
    monkeypatch.setattr(si, "test_connection", lambda conn: {"ok": True})

    cb = client_no_redirects.get(f"/sites/integrations/callback/woocommerce",
                    params={"state": state, "user_login": "admin", "password": "abcd ABCD 1234 ?!$"})
    assert cb.status_code == 307 or cb.status_code == 302, cb.text
    assert "status=ok" in cb.headers["location"]
    assert "shop.example.com" in cb.headers["location"]

    listing = client.get(f"/sites/my/{sid}/integrations", headers=h)
    conns = listing.json()["integrations"]
    assert len(conns) == 1
    assert conns[0]["provider"] == "woocommerce"
    assert conns[0]["shop_domain"] == "shop.example.com"
    # credentials never leak back out
    assert "api_key" not in conns[0] and "api_secret" not in conns[0]

    # the state is single-use: replaying must not create a second connection
    replay = client_no_redirects.get(f"/sites/integrations/callback/woocommerce",
                        params={"state": state, "user_login": "admin", "password": "abcd ABCD 1234 ?!$"})
    assert "status=error" in replay.headers["location"]
    still = client.get(f"/sites/my/{sid}/integrations", headers=h).json()["integrations"]
    assert len(still) == 1


def test_woo_callback_rejected_approval(owner_site):
    h, sid = owner_site["headers"], owner_site["site_id"]
    begin = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                        json={"provider": "woocommerce", "shop_domain": "shop.example.com"})
    state = begin.json()["state"]
    # user clicked Reject on the WordPress approval screen
    cb = client_no_redirects.get(f"/sites/integrations/callback/woocommerce", params={"state": state})
    assert "status=error" in cb.headers["location"]
    conns = client.get(f"/sites/my/{sid}/integrations", headers=h).json()["integrations"]
    assert conns == []


def test_shopify_callback_rejects_bad_code(owner_site, monkeypatch):
    """Shopify callback with a code that fails the token exchange must not
    leave a connection behind."""
    monkeypatch.setenv("FRONTEND_URL", "https://app.test.example")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "csecret")
    h, sid = owner_site["headers"], owner_site["site_id"]

    begin = client.post(f"/sites/my/{sid}/integrations/begin", headers=h,
                        json={"provider": "shopify", "shop_domain": "my-store.myshopify.com"})
    state = begin.json()["state"]

    import app.store_integrations as si
    monkeypatch.setattr(
        si, "shopify_exchange_code",
        lambda shop, code, redirect_uri: {"ok": False, "error": "invalid code"})
    cb = client_no_redirects.get("/sites/integrations/callback/shopify",
                    params={"code": "bogus", "state": state, "shop": "my-store.myshopify.com"})
    assert "status=error" in cb.headers["location"]
    conns = client.get(f"/sites/my/{sid}/integrations", headers=h).json()["integrations"]
    assert conns == []


def test_begin_requires_auth(owner_site):
    sid = owner_site["site_id"]
    anon = client.post(f"/sites/my/{sid}/integrations/begin",
                       json={"provider": "shopify", "shop_domain": "x.myshopify.com"})
    assert anon.status_code in (401, 403)
