"""Push products to / pull orders from external WooCommerce & Shopify stores."""
import base64
import hashlib
import hmac
import httpx


def _woo_auth(conn):
    return (conn.get("api_key") or "", conn.get("api_secret") or "")


def _woo_base(conn):
    domain = conn["shop_domain"].replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{domain}/wp-json/wc/v3"


def _shopify_base(conn):
    domain = conn["shop_domain"].replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{domain}/admin/api/2024-01"


def _shopify_headers(conn):
    return {"X-Shopify-Access-Token": conn.get("access_token") or "", "Content-Type": "application/json"}


def test_connection(conn) -> dict:
    try:
        if conn["provider"] == "woocommerce":
            r = httpx.get(f"{_woo_base(conn)}/products?per_page=1", auth=_woo_auth(conn), timeout=15)
        else:
            r = httpx.get(f"{_shopify_base(conn)}/shop.json", headers=_shopify_headers(conn), timeout=15)
        if r.status_code in (200, 201):
            return {"ok": True}
        return {"ok": False, "status": r.status_code, "error": r.text[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def push_product(conn, product) -> dict:
    """Create/update the product on the external store. Returns external id."""
    if conn["provider"] == "woocommerce":
        payload = {
            "name": product["name"],
            "regular_price": str(product.get("price", 0)),
            "description": product.get("description") or "",
            "catalog_visibility": "visible",
            "manage_stock": False,
        }
        if product.get("image"):
            payload["images"] = [{"src": product["image"]}]
        sku = f"av-{product['id']}"
        payload["sku"] = sku
        base = _woo_base(conn)
        # update if we pushed before
        lookup = httpx.get(f"{base}/products", params={"sku": sku}, auth=_woo_auth(conn), timeout=15)
        if lookup.status_code == 200 and isinstance(lookup.json(), list) and lookup.json():
            ext_id = lookup.json()[0]["id"]
            r = httpx.put(f"{base}/products/{ext_id}", json=payload, auth=_woo_auth(conn), timeout=20)
        else:
            r = httpx.post(f"{base}/products", json=payload, auth=_woo_auth(conn), timeout=20)
        if r.status_code in (200, 201):
            return {"ok": True, "external_id": str(r.json()["id"]), "url": r.json().get("permalink")}
        return {"ok": False, "status": r.status_code, "error": r.text[:200]}

    # shopify
    payload = {
        "product": {
            "title": product["name"],
            "body_html": product.get("description") or "",
            "variants": [{"price": str(product.get("price", 0)), "sku": f"av-{product['id']}"}],
            "status": "active",
        }
    }
    base = _shopify_base(conn)
    pmap_key = f"av-{product['id']}"
    lookup = httpx.get(f"{base}/products.json?handle={pmap_key}", headers=_shopify_headers(conn), timeout=15)
    found = lookup.json().get("products", []) if lookup.status_code == 200 else []
    if found:
        ext_id = found[0]["id"]
        r = httpx.put(f"{base}/products/{ext_id}.json", json=payload, headers=_shopify_headers(conn), timeout=20)
    else:
        payload["product"]["handle"] = pmap_key
        r = httpx.post(f"{base}/products.json", json=payload, headers=_shopify_headers(conn), timeout=20)
    if r.status_code in (200, 201):
        prod = r.json().get("product", {})
        return {"ok": True, "external_id": str(prod["id"]), "url": f"https://{conn['shop_domain']}/products/{prod.get('handle', '')}"}
    return {"ok": False, "status": r.status_code, "error": r.text[:200]}


def verify_woo_webhook(raw_body: bytes, signature_header: str, secret: str) -> bool:
    if not secret or not signature_header:
        return False
    expected = base64.b64encode(hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(expected, signature_header)


def woo_order_to_site_order(woo_order: dict) -> dict:
    """Map a WooCommerce order payload to our site_orders shape."""
    items = [{
        "product_id": int(line.get("product_id") or 0),
        "name": line.get("name") or "Item",
        "qty": int(line.get("quantity") or 1),
        "price": int(float(line.get("price") or 0)),
    } for line in (woo_order.get("line_items") or [])]
    total = int(float(woo_order.get("total") or 0))
    billing = woo_order.get("billing") or {}
    return {
        "external_ref": f"woo:{woo_order.get('id')}",
        "client_name": f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or (woo_order.get("customer_note") and 'Woo Customer') or "Woo Customer",
        "client_phone": billing.get("phone") or "",
        "client_email": billing.get("email") or "",
        "address": ", ".join(x for x in [billing.get("address_1"), billing.get("city"), billing.get("state"), billing.get("postcode")] if x),
        "items": items,
        "amount": total,
        "status": "new",
        "notes": f"Imported from WooCommerce order #{woo_order.get('number') or woo_order.get('id')}",
    }


def pull_shopify_orders(conn, limit=20) -> list:
    """Fetch recent paid/unfulfilled Shopify orders mapped to our shape."""
    base = _shopify_base(conn)
    r = httpx.get(f"{base}/orders.json?status=any&limit={limit}",
                  headers=_shopify_headers(conn), timeout=20)
    if r.status_code != 200:
        return [{"error": r.text[:200], "status": r.status_code}]
    out = []
    for o in r.json().get("orders", []):
        items = [{
            "product_id": int(li.get("product_id") or 0),
            "name": li.get("title") or "Item",
            "qty": int(li.get("quantity") or 1),
            "price": int(float(li.get("price") or 0)),
        } for li in (o.get("line_items") or [])]
        cust = o.get("customer") or {}
        name = f"{cust.get('first_name', '')} {cust.get('last_name', '')}".strip() or "Shopify Customer"
        out.append({
            "external_ref": f"shopify:{o.get('id')}",
            "client_name": name,
            "client_phone": (o.get("phone") or (o.get("customer") or {}).get("phone") or ""),
            "client_email": (o.get("email") or (o.get("customer") or {}).get("email") or ""),
            "address": ", ".join(x for x in [(o.get("shipping_address") or {}).get("address_1"), (o.get("shipping_address") or {}).get("city")] if x),
            "items": items,
            "amount": int(float(o.get("total_price") or 0)),
            "status": "new",
            "notes": f"Imported from Shopify order #{o.get('order_number') or o.get('id')}",
        })
    return out
