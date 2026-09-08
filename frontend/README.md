# AstroVakta Frontend — Developer Portal

React + Vite SPA deployed at **https://dev.astrovakta.com** (Vercel), backed by the
FastAPI astrology API at **https://api.astrovakta.com**.

## Build pipeline (SEO-critical)

`npm run build` does two things:

1. **`vite build`** — standard SPA bundle into `dist/`.
2. **`node scripts/prerender.mjs`** — serves `dist/` on a local preview server,
   loads all 14 public routes in headless Chromium (playwright-core), waits for
   React to render, settles fade-in animations, and overwrites each route with
   a fully-rendered `dist/<route>/index.html`.

The prerendered files are what crawlers (Googlebot, GPTBot, ClaudeBot,
PerplexityBot) and AI chatbots actually read. Without them, every page is an
empty `<div id="root">` shell — unindexable and uncitable. If the prerender
step ever fails, the build still succeeds (SPA fallback) but logs a loud
warning; treat that warning as a deployment blocker for SEO.

### Browser resolution for prerendering

The script looks for a browser in this order:

1. `CHROME_EXECUTABLE` / `CHROME_PATH` env vars
2. System Chrome/Chromium (macOS Chrome, Linux `/usr/bin/google-chrome*`, `/usr/bin/chromium*`)
3. Downloads playwright's managed headless chromium automatically (`npx playwright-core install chromium --only-shell`)

Local macOS builds use installed Google Chrome automatically. On CI/Vercel,
step 3 downloads ~100 MB into the build cache on first run and is cached after.

Useful scripts:

- `npm run build:spa` — vite build only, skip prerendering
- `npm run prerender` — re-run prerendering against an existing `dist/`

## Environment variables

Set in Vercel → Settings → Environment Variables (see `.env.example`):

- `VITE_API_BASE_URL` — e.g. `https://api.astrovakta.com` (leave empty only in local dev; vite proxies `/api` etc. to `127.0.0.1:8000`)
- `VITE_CLERK_PUBLISHABLE_KEY` — Clerk publishable key (`pk_test_…` / `pk_live_…`)

If the Clerk key is missing or malformed, the site still renders fully with auth
controls in signed-out state (see `src/lib/clerk.jsx`). A bad key must never
blank the site — that was previously fatal for SEO.

## SEO surfaces to keep in sync

- `index.html` — base meta tags, Organization/WebSite/SoftwareApplication/FAQPage JSON-LD (`@graph`)
- `src/components/SEO.jsx` — per-route title/description/canonical/OG + breadcrumbs JSON-LD; `SITE_URL` must match the deployed domain
- `src/pages/BlogPost.jsx` — per-post title/description/canonical + BlogPosting JSON-LD
- `public/robots.txt` — allows search + AI crawlers (GPTBot, ClaudeBot, PerplexityBot, …), points to sitemap
- `public/sitemap.xml` — all 14 public URLs; update `lastmod` on real changes; add new blog slugs when added
- `public/llms.txt` — llms.txt-style summary for AI assistants; keep facts (pricing, endpoint count) in sync
- `vercel.json` — `trailingSlash: false` (canonical URL form) + cache headers

## Adding a new public route

1. Add the route + per-route meta in `src/App.jsx` / `src/components/SEO.jsx`.
2. Add it to `ROUTES` in `scripts/prerender.mjs`.
3. Add it to `public/sitemap.xml`.
