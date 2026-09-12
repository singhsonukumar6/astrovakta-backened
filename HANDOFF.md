# AstroVakta — Project Handoff & Roadmap

_Last updated: 2026-09-11. Start here when resuming work._

## What the product is

Multi-tenant website builder on the AstroVakta astrology API. An astrologer signs up,
creates a site (slug.astrovakta.com or custom domain), and manages everything from the
`/mysite` dashboard: content, themes, services, store, hours, bookings, leads, **social
media**, custom domain, payments, settings (+ developer tools: API keys, usage).

## Deploy

- **Backend**: DigitalOcean droplet 159.65.144.202 — `ssh root@159.65.144.202; cd /opt/astrovakta-backened; git pull origin main; docker compose up -d --build` (needed whenever `app/` changes; DDL uses `CREATE TABLE IF NOT EXISTS` so new tables self-create on container start).
- **Frontend**: Vercel auto-deploys on push (dev.astrovakta.com). `VITE_API_BASE_URL=https://api.astrovakta.com`.
- **DNS**: Vercel nameservers. `api` A record → 159.65.144.202. Wildcard `*` serves tenant subdomains.
- **Local dev**: uvicorn on 8901 (`DATABASE_URL="sqlite:///./astrovakta.db" .venv/bin/uvicorn app.main:app --port 8901`) + vite on 4188.

## Recently shipped (in commit order)

- Login/Register redesign (Clerk removed; email/password JWT), 10-tab dashboard, complete
  tenant landing page, store (stock lifecycle), 8 themes, payments (pay-later / UPI /
  Razorpay checkout), public kundli + match-making + dosha tools on hash routes
  (`#/kundli`, `#/matching`), birth-place autocomplete (public `/api/location/*`, 30 req/min
  per-IP limit), dedicated onboarding route, developer dashboard merged into `/mysite`.
- **Social media automation** (Social tab): content engine (daily panchang post, festival
  greetings from `HINDU_FESTIVALS`, promos, custom topic), auto-daily queue setting
  (`settings.socialAutoDaily`, ensure=1 idempotent per day), scheduled queue, one-tap
  share links (WhatsApp/Telegram/X/Facebook/LinkedIn), copy-for-Instagram, mark-posted.
- **Phase-1 media pipeline** (`app/social_media.py`): branded 1080×1080 image cards
  (Pillow, theme gradient + astrologer branding) and short square slideshow videos
  (ffmpeg h264). `POST /sites/my/{id}/social/media {content, format}` returns a base64
  data URL; Social tab has per-post/composer "Image/Video" buttons with download.
  Dockerfile now installs `ffmpeg fonts-dejavu-core`.

## Phase 2 — platform connections (NOT started)

Goal: astrologer OAuth-connects Instagram/Facebook, YouTube, LinkedIn, X.

- New table `social_accounts (id, site_id, platform, external_id, username, access_token,
  refresh_token, token_expires_at, scopes, status, created_at)`.
- OAuth connect/callback endpoints per platform; client IDs/secrets from server env:
  `META_APP_ID/SECRET` (Instagram needs IG **Business/Creator** account + linked FB Page;
  App Review for `pages_manage_posts`, `instagram_content_publish`), `GOOGLE_CLIENT_ID/SECRET`
  (YouTube upload; video-only), `LINKEDIN_CLIENT_ID/SECRET` (`w_member_social`), `X_*`
  (write access is PAID — Basic ~$200/mo).
- Connect buttons in the Social tab render dormant until env credentials exist — no code
  change needed to activate.
- Persisting generated media (currently on-demand base64) likely needed for IG/YouTube:
  add a `media` column or file storage.

## Phase 3 — auto-poster (NOT started)

- Celery beat (worker exists: `celery -A app.celery_app worker -Q pdf,ai,default`) with a
  periodic task that fires due `site_social_posts` (status='scheduled', scheduled_at passed).
- Per-platform posting adapters using stored tokens; record per-post delivery status +
  retries; rate-limit conservatively (few posts/day/account — platforms flag spam).
- Social tab: per-post delivery status badges; failure alerts via existing WhatsApp setting.

## Known notes / gotchas

- `tests/conftest.py` autouse fixture wipes the dev DB `users` table per test — re-login
  after running pytest.
- `AnimatePresence mode="wait"` is banned in app surfaces: throttled-rAF environments
  freeze exit animations. Use the CSS-fade pattern (`mysite-tab-fade`, `wiz-step-in`).
- Embedded-browser automation sometimes drops synthetic clicks; React handler invocation
  via `__reactProps$` is the reliable test path.
- `/api/*` is API-key protected by `APIKeyMiddleware` except `PUBLIC_CONTENT_PREFIXES`
  (page-config, blogs, `/api/location/`). Tenant public tools live under `/sites/site/tools/*`.
- Sites endpoints return unwrapped JSON; `/api/*` and `/sites/*` (after ResponseWrap
  middleware) may wrap in `{success, data}` — frontend unwraps both shapes.

## Backend audit (2026-09-11) — gaps, bugs, opportunities

### Known bugs / inconsistencies (fix candidates)
1. **Envelope inconsistency**: `/sites/*` successes return raw JSON; error paths and `/api/*`
   return `{success, message, data}`. Frontend unwraps both, but API consumers see two shapes.
   Standardize (register ResponseWrapMiddleware, or drop it) — touching many clients, do deliberately.
2. **lal_kitab.py sync-endpoint translate bug pattern**: other modules may also call
   `translate_paragraphs` without await inside sync endpoints — grep `= translate_paragraphs(`
   (without await) across routers; only chart-analysis was fixed.
3. `update_social_post` posted_at logic is convoluted (double-assignment); simplify.
4. `_rate_bucket` in location.py is per-process only — with multiple workers/gunicorn it's
   per-worker; fine today (single uvicorn), revisit if scaling.
5. `/sites/site/tools/kundli-full` calls `tenant_kundli_tool` directly → `_resolve_site` runs
   twice (harmless, minor).
6. No request size/rate limits on public tool endpoints (`/sites/site/tools/*`) beyond
   location — candidate for the same per-IP limiter (kundli is CPU-heavy).

### Missing endpoints worth adding
- `POST /payments/razorpay/webhook` — server-side payment verification (needs
  `RAZORPAY_KEY_SECRET`); currently payments are honor-system.
- `GET /sites/my/{id}/leads/export` — CSV export of leads/bookings/orders.
- `POST /sites/my/{id}/social/{post_id}/render-auto` — pre-render media at schedule time
  (phase-3 poster will need stored media files, not on-demand base64).
- `GET /sites/my/{id}/bookings.ics` — calendar feed for bookings.
- Tenant-site SEO: `GET /sitemap.xml` per custom domain (tenant blogs exist under /api/blogs).
- Notifications digest: daily email/WhatsApp summary of bookings+leads to the astrologer.

### Ops
- Prod DDL drift risk: SQLite and `_PG_DDL` blocks in database.py must stay in sync
  (bit us once — AUTOINCREMENT in PG). Consider a single schema source transpiled.

## Audit implementation (commit 4b52f5e, 2026-09-11)

DONE: Razorpay webhook (set RAZORPAY_KEY_SECRET env on droplet + same secret as webhook
secret in Razorpay dashboard; checkout sends receipt `booking:<id>`; `site_bookings.payment_status`
column added via DDL + migrations) · CSV exports (`/sites/my/{id}/leads|bookings|orders/export.csv`)
· ICS feed (`/sites/my/{id}/bookings.ics`) · per-IP 12/min limits on kundli-full/matching/dosha
· swept 34 un-awaited `translate_paragraphs` calls across 13 routers (systemic 500-bug).

STILL OPEN: envelope standardization (deliberate, breaks clients) · daily digest (needs
email/WA infra) · phase-2 OAuth + phase-3 auto-poster (see phases above) · stored media for
scheduled posts · single-schema-source for DDL · rate limiting is per-process.
