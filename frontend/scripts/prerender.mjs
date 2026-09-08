/**
 * Build-time prerender for AstroVakta SPA.
 *
 * Loads each route in headless Chrome (system Chrome via playwright-core), waits for
 * the app to render, and writes the resulting HTML — including per-route <title>,
 * meta description, canonical, OG tags and route JSON-LD managed by SEO.jsx — to
 * dist/<route>/index.html. Crawlers (Googlebot, GPTBot, ClaudeBot, PerplexityBot)
 * then get real HTML content instead of an empty SPA shell.
 *
 * Runs automatically as part of `npm run build` (see package.json).
 */
import { spawn } from 'node:child_process'
import { access, mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DIST = path.join(__dirname, '..', 'dist')
const PREVIEW_PORT = 4173
const PREVIEW_HOST = 'http://localhost' // vite preview binds IPv6 localhost

// Public routes worth prerendering. Private/auth routes stay SPA-only (robots disallows them).
const ROUTES = [
  { path: '/', dir: '.' },
  { path: '/pricing', dir: 'pricing' },
  { path: '/docs', dir: 'docs' },
  { path: '/sandbox', dir: 'sandbox' },
  { path: '/kundali-report', dir: 'kundali-report' },
  { path: '/blogs', dir: 'blogs' },
  { path: '/blogs/build-astrology-app', dir: 'blogs/build-astrology-app' },
  { path: '/blogs/vedic-charts-developer-guide', dir: 'blogs/vedic-charts-developer-guide' },
  { path: '/blogs/top-astrology-api-features-2026', dir: 'blogs/top-astrology-api-features-2026' },
  { path: '/blogs/ai-vedic-astrology-overview', dir: 'blogs/ai-vedic-astrology-overview' },
  { path: '/about', dir: 'about' },
  { path: '/contact', dir: 'contact' },
  { path: '/privacy', dir: 'privacy' },
  { path: '/terms', dir: 'terms' },
]

const PREVIEW_READY_MS = 2500
const RENDER_WAIT_MS = 3500

function log(msg) {
  console.log(`[prerender] ${msg}`)
}

async function waitForServer(url, timeoutMs = 30000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url)
      if (res.ok) return true
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 400))
  }
  throw new Error(`Preview server at ${url} did not become ready`)
}

async function startPreview() {
  const proc = spawn('npm', ['run', 'preview', '--', '--port', String(PREVIEW_PORT), '--strictPort'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'ignore',
    detached: true,
  })
  await waitForServer(`${PREVIEW_HOST}:${PREVIEW_PORT}/`)
  return proc
}

// Candidate browsers, in priority order: env override, macOS Chrome, Linux
// Chromium/Chrome (Vercel/CI), then playwright's managed download.
const BROWSER_CANDIDATES = [
  process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  process.env.PLAYWRIGHT_CHROMIUM_PATH,
  '/usr/bin/google-chrome-stable',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  process.env.HOME && `${process.env.HOME}/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing`,
].filter(Boolean)

async function resolveExecutable() {
  if (process.env.CHROME_EXECUTABLE) return process.env.CHROME_EXECUTABLE
  for (const candidate of BROWSER_CANDIDATES) {
    try {
      await access(candidate)
      return candidate
    } catch {
      /* try next */
    }
  }
  // No system browser (e.g. Vercel build container): download playwright's own
  // headless chromium into the build cache and use it.
  log('no system browser found — installing playwright headless chromium')
  try {
    await new Promise((resolve, reject) => {
      const proc = spawn('npx', ['playwright-core', 'install', 'chromium', '--only-shell'], {
        cwd: path.join(__dirname, '..'),
        stdio: 'inherit',
      })
      proc.on('exit', (code) => (code === 0 ? resolve() : reject(new Error(`install exited ${code}`))))
      proc.on('error', reject)
    })
  } catch (err) {
    log(`browser install failed: ${err.message}`)
  }
  return undefined
}

async function renderRoutes() {
  const { chromium } = await import('playwright-core')

  const executablePath = await resolveExecutable()
  log(executablePath ? `using browser: ${executablePath}` : 'using playwright managed chromium')

  const browser = await chromium.launch(executablePath ? { executablePath, args: ['--no-sandbox'] } : { args: ['--no-sandbox'] })
  const page = await browser.newPage()

  let rendered = 0
  for (const route of ROUTES) {
    const url = `${PREVIEW_HOST}:${PREVIEW_PORT}${route.path}`
    await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => {})
    await page.waitForTimeout(RENDER_WAIT_MS)

    // Scroll through the page so framer-motion whileInView animations fire and
    // fade-in content settles at opacity 1 before the HTML snapshot is taken.
    await page.evaluate(async () => {
      const step = Math.round(window.innerHeight * 0.75)
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y)
        await new Promise((r) => setTimeout(r, 120))
      }
      window.scrollTo(0, 0)
    })
    await page.waitForTimeout(1200)

    // Safety net: framer-motion elements whose whileInView never fired (fast
    // programmatic scroll can outpace the IntersectionObserver) would be frozen
    // at opacity 0 — invisible to crawlers. Force-settle them before snapshot.
    const settled = await page.evaluate(() => {
      let fixed = 0
      document.querySelectorAll('main [style*="opacity: 0"], main [style*="opacity:0"]').forEach((el) => {
        el.style.opacity = '1'
        el.style.transform = 'none'
        fixed++
      })
      return fixed
    })
    if (settled) log(`settled ${settled} fade-in elements on ${route.path}`)
    await page.waitForTimeout(200)

    // The app's SEO.jsx has set per-route tags by now; grab the full DOM.
    const html = await page.evaluate(() => {
      const doc = document.documentElement
      return '<!doctype html>\n' + doc.outerHTML
    })

    const outDir = path.join(DIST, route.dir)
    await mkdir(outDir, { recursive: true })
    await writeFile(path.join(outDir, 'index.html'), html)
    rendered++
    log(`rendered ${route.path} → dist/${route.dir}/index.html (${(html.length / 1024).toFixed(0)} KB)`)
  }

  await browser.close()
  return rendered
}

async function main() {
  const argDist = path.join(DIST, 'index.html')
  if (!(await readFile(argDist).then(() => true).catch(() => false))) {
    throw new Error('dist/index.html not found — run `vite build` first')
  }

  let preview
  try {
    preview = await startPreview()
    await new Promise((r) => setTimeout(r, PREVIEW_READY_MS))
    const rendered = await renderRoutes()
    log(`done — ${rendered} routes prerendered`)
  } finally {
    if (preview) {
      try {
        process.kill(-preview.pid, 'SIGTERM')
      } catch {
        preview.kill('SIGTERM')
      }
    }
  }
}

main().catch((err) => {
  console.error('[prerender] FAILED:', err.message)
  console.error('[prerender] NOTE: site still deploys as a plain SPA — crawlers will only see the')
  console.error('[prerender] empty shell. Fix browser availability (see README) and re-deploy.')
  process.exit(0)
})
