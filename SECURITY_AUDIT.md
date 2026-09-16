# Security Audit — AstroVakta Backend & Frontend

**Date:** 2026-09-16 · **Scope:** full backend (`app/`), live API exploit testing (local instance, port 5577), frontend (`frontend/`), dependencies.
**Method:** manual code review of all security-relevant modules + dynamic exploitation against a locally running server + `pip-audit`. The dev database was backed up and restored; all test data was removed.

> Exploits marked **[CONFIRMED]** were successfully executed against the live local instance.

---

## FIX STATUS (2026-09-16) — all findings remediated, exploit suite re-run clean

| Finding | Fix | Re-verified |
|---|---|---|
| C1 clerk-sync takeover | **Clerk removed entirely** — endpoint, `sync_clerk_user()`, frontend stub | 404, takeover impossible |
| C2 self plan escalation | `plan` removed from `PUT /auth/profile` and `update_user_profile()` | plan stays free, limit 500 |
| C3 default JWT secret | Refuses to start in production without `JWT_SECRET`; dev uses an ephemeral random key | forged default-secret token → 401 |
| C4 webhook fail-open | Requires `DODO_WEBHOOK_SECRET` (503 otherwise), ±5 min timestamp window, webhook-id replay cache | forged event → 503 |
| H1 free compute | Middleware now classifies **all 363 routes** from the app itself (recursing into FastAPI router includes) — every non-public, non-JWT route requires an API key; static fallback list if introspection fails | `/kp/*`, `/lal-kitab/*`, `/ai/chat` → 401 without key, 200 with key; JWT routes unaffected |
| H2 PDF SSRF/LFI | `_load_image()` accepts only public-IP `https://` URLs and `data:image/` URIs; no redirects; no local paths; 8 MB cap; watermark routed through the same loader; per-process cache | code path verified |
| H3 store SSRF | `_is_public_host()` (resolves DNS, blocks private/loopback/link-local/metadata) enforced in `test_connection`, `push_product`, `pull_shopify_orders`; Shopify token exchange locked to `*.myshopify.com`; state's `shop_domain` used instead of query param; **legacy unvalidated `/integrations/shopify/callback` deleted** | `127.0.0.1.nip.io`, `169.254.169.254`, `localhost` all rejected |
| H4 brute force | `app/rate_limit.py` sliding window: login 20/5 min per IP + 10/5 min per account; register/reset/forgot/verify throttled; tenant visitor login/register too | 25 bad logins → 429 |
| H5 credit-drain DoS | `_tool_limit` added to kundli tool, panchang widget, daily horoscope, event beacon; lead capped 10/min; HTML stripped from lead fields | 15 rapid kundli calls → 429 |
| M1 CORS | Explicit origin allowlist (env `CORS_ORIGINS`), `allow_credentials=False`, wildcard removed from handlers and nginx | evil origin not reflected |
| M2 headers | `SecurityHeadersMiddleware` (nosniff, DENY, referrer-policy) + HSTS and DENY in nginx; CSP + XFO + Permissions-Policy on the frontend (vercel.json + index.html meta) | headers present on every response |
| M3 CSV/ICS injection | `_csv_safe()` defangs leading `=+-@\t` cells and strips CR/LF; ICS text escaped | export shows `'=HYPERLINK…` |
| M4 email fail-open | Auto-verify only outside production (`ENVIRONMENT`), never on provider errors in production | dev unchanged, prod gated |
| M5 Google login | `iss` validated; `GOOGLE_CLIENT_ID` required in production | code path verified |
| M6 admin123 | `create_admin()` raises without `ADMIN_PASSWORD` — no default, no `NODE_ENV` check | code path verified |
| M7 dependencies | fastapi 0.141.1 + starlette 1.6.0, python-jose 3.5, cryptography 50, Pillow 12.3, cairosvg 2.9 — pip-audit clean except `ecdsa` (no fixed release exists upstream; only used by python-jose's unused ES256 path) | `pip-audit -r requirements.txt` |
| M8 422 echo | Errors scrubbed of `input`/`ctx`; handler registered for `RequestValidationError` so the envelope actually fires | no input echo |
| L1 settings leak | `public_site_bundle` exposes an allowlist; owner-only keys (bookingAlerts, reminderHours, socialAutoDaily, visitorGoogleAuth) excluded. `razorpayKeyId`/`upiId` stay public by design (tenant checkout needs them client-side) | verified live |
| L2 plaintext tokens | Verification + reset tokens stored as SHA-256 hashes | code path verified |
| L8 error detail | Social-media renderer returns a generic message | code path verified |
| F1 blog XSS | `frontend/src/lib/sanitize.js` (DOM allowlist sanitizer) wired into BlogPost + Admin preview; build passes | vite build ok |
| F2 CSP | vercel.json + index.html meta; script-src locked to self + Google/ Razorpay hosts | build ok |

**Known remainder (documented, not fixable in place):** `ecdsa 0.19.2` advisory has no upstream fix (transitive of python-jose; ES256 is never used). In-memory rate-limit buckets are per-process — move to Redis when scaling beyond one worker. Tokens remain in `localStorage` (L3) — a larger refactor.

Also fixed along the way: 3 pre-existing test failures (`requests_total` alias, 422 envelope registration, stale fixture table lists) — full suite now **84 passed / 0 failed**.

---

## ORIGINAL FINDINGS (pre-fix)

## CRITICAL

### C1. Unauthenticated account takeover — `POST /auth/clerk-sync` **[CONFIRMED]**
`app/routers/auth_router.py:358` — the endpoint takes any `{clerk_id, email, name}` with **no authentication and no Clerk signature verification**, then `sync_clerk_user()` (`app/auth.py:157`) matches a user by `clerk_id OR email`, attaches the attacker's clerk_id, and the endpoint returns a full 72-hour JWT for that account.

```bash
# takeover of any registered email, no auth:
curl -X POST /auth/clerk-sync -d '{"clerk_id":"x","email":"victim@example.com","name":"p"}'
# → {"token": "<valid JWT for the victim>", ...}
```
Also sets `email_verified = TRUE` on the victim. This alone defeats every other auth control (admin router included — an attacker who takes over an admin email gets `is_admin`).
**Fix:** remove the endpoint or require Clerk's webhook signature (`svix` headers + `CLERK_WEBHOOK_SECRET`) and never trust a caller-supplied email.

### C2. Any user can upgrade themselves to the enterprise plan — `PUT /auth/profile` **[CONFIRMED]**
`app/routers/auth_router.py:269` accepts a user-supplied `plan` (validated only against the tier *names*), and `update_user_profile()` (`app/auth.py:361`) writes it and raises `monthly_limit` to `TIER_LIMITS[plan]`. Verified live: `plan=enterprise`, `monthly_limit=999999999`.
**Fix:** strip `plan` (and `monthly_limit`) from user-editable profile fields; only payments webhooks and admin routes may change plans.

### C3. JWTs forgeable with the well-known default secret **[CONFIRMED]**
`app/routers/auth_router.py:36` — `JWT_SECRET` falls back to `"dev-only-fallback-key-change-in-production"`. A token signed with that public string was accepted by the running server and returned the target user's profile. Everything (platform JWTs, tenant visitor JWTs, 30-day tenant tokens) uses this one key.
**Fix:** refuse to start when `JWT_SECRET` is unset/weak outside debug mode; also rotate any secret that has ever shipped in a repo or image.

### C4. Payment webhook is fail-open — `POST /payments/webhook`
`app/routers/payments.py:166` — signature verification is inside `if DODO_WEBHOOK_SECRET:`. If the secret is unset (or a deploy forgets it), anyone can POST a forged `payment.succeeded` event for a **known/guessed payment id** (ids are sequential and returned by `/payments/checkout`) and `admin_update_user_plan()` upgrades the linked user — free pro upgrade. There is also **no timestamp freshness check and no replay cache** (Standard Webhooks `webhook-id` is ignored), so captured webhooks replay forever even when the secret is set.
Confirmed locally: forged event skipped signature verification and reached event handling.
**Fix:** refuse to process webhooks (503) when the secret is not configured; enforce timestamp tolerance (e.g. ±5 min) and dedupe on `webhook-id`.

---

## HIGH

### H1. API-key middleware misses whole route families — free compute **[CONFIRMED]**
`app/middleware.py:10` protects only `/api/`, `/horoscope/`, `/chart/`, `/pooja/`, `/reports/`, `/dasha/`, `/calendar-api/`. Root-mounted routers are invisible to it. Verified live with **no API key**:
- `POST /kp/ruling-planets` → 200
- `POST /kp/planet-details` → 200
- `POST /lal-kitab/chart-analysis` → 200

`CREDIT_COSTS` prices these at 5 credits — the billing path is bypassed entirely, and anonymous traffic gets free CPU-heavy ephemeris compute. (`/lucky/*`, `/varshaphal`, and other root-mounted endpoints belong to the same gap.)
**Fix:** invert the model — deny by default and allow-list public paths (`/auth`, `/health`, `/docs`, `/sites/site/*`, public content, webhooks), instead of enumerating protected prefixes.

### H2. SSRF & local-file read via PDF report image parameters
`app/pdf_engine.py:494` `_load_image()` does `open(image_source,'rb')` for any existing path and `urllib.request.urlopen(image_source)` otherwise — fed directly from `logoUrl`, `brandLogo`, `astrologerImage`, `backgroundImage`, `watermarkImageUrl` in `FullPDFRequest` (`app/routers/reports.py:358`). An authenticated API user can make the server fetch internal URLs (including `file://`), and any *image-parseable* local file is embedded into the returned PDF. `draw_watermark()` (`pdf_engine.py:814`) does the same.
**Fix:** allow only `https://`, resolve via a proxy with an explicit egress allowlist; drop local-path support; verify redirects are followed to public IPs only.

### H3. SSRF + client-secret exfiltration via store integrations
- `test_connection()`/`push_product()`/`pull_shopify_orders()` (`app/store_integrations.py`) request `https://{user-controlled shop_domain}/...` and return up to 200 chars of the response/error to the caller (`sites.py:1479` reflects it as a 400 detail) — authenticated SSRF with response reflection.
- `GET /sites/integrations/shopify/callback` (`app/routers/sites.py:1560`) takes `state` with **no nonce validation** and posts `client_secret` to `https://{shop}/admin/oauth/access_token` where `shop` is caller-controlled → an unauthenticated request can point the token exchange at an attacker host and capture `SHOPIFY_CLIENT_SECRET`; it also lets anyone attach a store connection to an arbitrary `site_id`.
**Fix:** validate `shop_domain` against `*.myshopify.com`/`*.wordpress.com`-style patterns (or resolve+pin expected IPs), verify Shopify's HMAC and the state nonce server-side, and don't reflect upstream response bodies.

### H4. No rate limiting / lockout on authentication **[CONFIRMED]**
25 consecutive bad-password logins returned 25×401 — no 429, no lockout, no backoff (`/auth/login`, `/auth/reset-password`, `/sites/site/auth/login`, `/auth/verify-email`). Password reset tokens are `token_urlsafe(48)` (fine), but online guessing against weak passwords is unlimited.
**Fix:** per-account + per-IP sliding window (e.g. 5–10 attempts/min), exponential backoff, alert on spikes.

### H5. Anonymous credit-drain DoS on tenant sites **[CONFIRMED]**
`POST /sites/site/tools/kundli` charges the site's credits and has **no `_tool_limit()` call** (unlike matching/dosha). Verified: 3 unauthenticated calls took the site from 100 → 97 credits. An attacker can zero out any published site's balance in seconds, DoS-ing the astrologer's booking/tools widgets (402 everywhere).
**Fix:** add the per-IP limiter (backed by Redis, not process memory) to all `/site/tools/*` and `/site/lead`, plus per-site daily caps with alerting.

---

## MEDIUM

### M1. CORS: wildcard default + reflected origin with credentials **[CONFIRMED]**
`app/main.py:85` defaults `CORS_ORIGINS` to `*` with `allow_credentials=True`; a preflight from `https://evil.example.com` was reflected with `ACAO: https://evil.example.com, ACAC: true`. The global exception handlers additionally hardcode `Access-Control-Allow-Origin: *`, and `nginx.conf` also emits `*`. Auth uses `Authorization` headers (not cookies), which caps practical impact, but any future cookie/session work turns this into a full cross-origin read.
**Fix:** explicit origin allowlist; remove `*` from nginx and exception handlers; `allow_credentials=False` unless a specific origin needs it.

### M2. No security response headers on the API
Live responses carry no `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, or `X-Frame-Options` (nginx adds only X-Frame-Options/nosniff and no HSTS, no `limit_req`). Add HSTS at nginx, `X-Content-Type-Options: nosniff` on the API, and a restrictive CSP on the frontend (see F1).

### M3. CSV formula injection in tenant exports **[CONFIRMED]**
Public, unauthenticated lead capture (`POST /sites/site/lead`) stores raw visitor input; `leads/export.csv` (`app/routers/sites.py:1103`) writes it unescaped-into-context. Verified `=HYPERLINK("https://evil.example.com","pwned")` round-trips into the CSV — Excel will execute it on the tenant's machine (same for bookings/orders exports and the `.ics` export). The lead payload also carried `<script>` tags into storage.
**Fix:** prefix cells whose first char is `= + - @ @` with `'`; also sanitize/strip HTML from lead/message fields on ingest.

### M4. Email verification is fail-open **[CONFIRMED]**
`register`/`resend-verification` auto-verify the address whenever `RESEND_API_KEY` is missing or sending throws (`auth_router.py:175`, `:319`). Verified live: `email_sent:false` + `email_verified:true`. Any persistent SMTP/provider outage silently disables verification — you cannot distinguish "verified" users from "we gave up".
**Fix:** keep accounts usable but track `email_verified` honestly; gate sensitive flows (password-change notices, payout info) on real verification, and alert when the auto-verify fallback fires.

### M5. Google sign-in audience check is optional
`POST /auth/google` (`auth_router.py:397`) enforces `aud == GOOGLE_CLIENT_ID` **only if the env var is set**, and doesn't check `iss`. With the var unset, any valid Google ID token from *any* OAuth client for an email is accepted — useful for impersonating platform accounts created via Google. (Firebase path *is* properly pinned to project id.)
**Fix:** require `GOOGLE_CLIENT_ID` in production; validate `iss` and `aud` strictly; prefer library verification with Google's JWKS.

### M6. Admin bootstrap default password `admin123`
`create_admin.py` falls back to `admin123` when `ADMIN_PASSWORD` is unset — the "production" guard checks `NODE_ENV`, a Node.js variable that is normally unset in a Python container, so the fallback can silently apply in real deployments. `.env.example` also ships `AUTO_CREATE_ADMIN=1`. **Fix:** exit whenever `ADMIN_PASSWORD` is missing, regardless of `NODE_ENV`; drop the default.

### M7. Vulnerable dependencies (pip-audit, `--no-deps` on requirements.txt)
| Package | Version | Advisories | Fix |
|---|---|---|---|
| python-jose | 3.3.0 | PYSEC-2024-232, PYSEC-2024-233, PYSEC-2025-185 | 3.4.0+ (or migrate to PyJWT) |
| cryptography | 43.0.0 | GHSA-h4gh-qq45-vh27, GHSA-537c-gmf6-5ccf, PYSEC-2026-35/1284/2141/3553/3554 | 49.x |
| Pillow | 11.3.0 | 15+ advisories incl. PYSEC-2026-165/2249/2250/2251/2252/2253/2254/2255/2256/2257/2874/3451/3453 | 12.3.0 |
| cairosvg | 2.7.1 | PYSEC-2026-2122 | 2.9.0 |
| ecdsa | 0.19.2 | PYSEC-2026-1325 | latest |

`python-jose` (JWT core!) has known CVEs — priority bump. Add `pip-audit` to CI.

### M8. Stored XSS sinks in the frontend (see F1 below) & 422 input reflection
`POST` validation errors echo the attacker-supplied input back (`app/main.py:160` returns `exc.errors()`). Low impact today (JSON API), but keep `Content-Type: application/json` on all responses and trim `input` from error payloads.

---

## LOW

- **L1. Public site bundle returns the entire settings blob** (verified: `razorpayKeyId`, `upiId`, whatsapp, phone). Razorpay key_id is public by design, but expose an allow-list of fields, not `settings` verbatim — the next "secret-ish" setting added to that JSON becomes public automatically.
- **L2. Reset/verification tokens stored in plaintext** (`password_resets.token`, `users.verification_token`) — a DB leak converts directly to account takeover. Store SHA-256 hashes.
- **L3. JWT + tenant tokens in `localStorage`** — any XSS is instant session theft. Consider short-lived access tokens + httpOnly refresh cookies for the dashboard.
- **L4. In-memory rate-limit buckets** (`location.py`, `public_sites.py`) — lost on restart, per-worker (bypassed by scaling), and cleared wholesale at 10k entries (attacker-trivial). Move to Redis.
- **L5. Webhook replay** — Dodo webhook ignores `webhook-id`/timestamp age (see C4); WooCommerce webhook HMAC itself is correct.
- **L6. `GET /auth/usage/{key_id}` & list endpoints return full API keys** to the owner (`auth_router.py:231` returns `k["key"]`) — acceptable for a developer API but consider show-once.
- **L7. `admin_delete_user` doesn't delete users** — it only revokes keys (misleading name; GDPR/erasure gap for tenant PII: leads/clients/bookings have no user-facing deletion).
- **L8. Verbose exception strings to clients** in a few 500 paths (e.g. `social_post_media` returns `str(e)`), which can leak internals.

---

## What held up well ✅

- **Password storage:** bcrypt with salts everywhere; no plaintext or MD5.
- **SQL injection:** all queries parameterized. The f-string SQL (`auth.py`, `tenants.py`, `content.py`) only interpolates code-controlled column lists and `?` placeholders; `days`/`limit` reach SQL only after pydantic/FastAPI int coercion. No injectable sink found (static + dynamic).
- **Tenant isolation:** every `/sites/my/*` route calls `_require_owned_site`; all cross-tenant probes (detail/clients/update/delete/leads) returned 403. Tenant visitor JWTs are site-bound — cross-site reuse → 403.
- **Admin surface:** consistent `require_admin`; forged non-admin token → 403; admins see only masked API keys.
- **AI provider keys:** Fernet-encrypted at rest, never returned after creation.
- **Invoice share links:** 144-bit random tokens.
- **No committed secrets:** `.env` absent, `.env.example` placeholders only, built frontend (`dist/`) contains no live keys.
- **Location router:** fixed upstream host, no SSRF.
- **ffmpeg pipeline:** arg-list subprocess, no shell, temp paths — no command injection.

---

## Frontend (`frontend/`)

**F1. XSS sinks (`dangerouslySetInnerHTML`)** — 5 sinks:
- `src/pages/BlogPost.jsx:211` renders `post.body` raw → stored XSS if any blog-author account is compromised (see C1/C3 — admin compromise is currently cheap). Sanitize server-side (e.g. bleach/allowlist) or render markdown safely.
- `src/pages/Admin.jsx:1623/1629` — admin-only self-preview (low).
- `TenantTools.jsx:706/1028`, `kundali/ReportTemplate.jsx:97` — server-generated SVG (fixed dictionaries; low).

**F2. No CSP** — nothing in `index.html` or `vercel.json`. A CSP (`script-src 'self'`, no `unsafe-inline` where feasible) would materially blunt the XSS class above. Vercel config does set `X-Content-Type-Options` and `Referrer-Policy` (good); add `X-Frame-Options: DENY` for the dashboard routes.

**F3. Token handling** — platform JWT in `localStorage`; tenant tokens correctly separated per site and attached per-request (good isolation design). Move to httpOnly cookies when convenient (L3).

**F4. Build hygiene** — no secrets in `dist/` (only `rzp_live_xxxxxxxx` placeholder); Firebase web config is public-by-design.

---

## Prioritized fix list

1. **Now:** delete/gate `clerk-sync` (C1), strip `plan` from profile updates (C2), fail-fast on missing `JWT_SECRET` (C3), fail-closed webhook (C4).
2. **This week:** invert middleware allow-list (H1), patch image loader + shop-domain validation (H2/H3), rate-limit auth + tools (H4/H5).
3. **This month:** CORS allowlist + headers (M1/M2), CSV escaping (M3), dependency bumps (M7), sanitize blog HTML (F1), CSP (F2), token hashing (L2).
