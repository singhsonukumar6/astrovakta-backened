import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import blogPosts from '../pages/blogData.js'

export const SITE_URL = 'https://devs.astrovakta.com'
const OG_IMAGE = `${SITE_URL}/og-image.png`

const HOME = {
  title: 'AstroVakta — Vedic Astrology API | Kundli, Birth Charts, Horoscopes & AI Predictions',
  description:
    'AstroVakta is the most complete Vedic astrology API for developers. 180+ endpoints for kundli birth charts, daily horoscopes, gun milan compatibility, mangal dosha, panchang, vimshottari dasha, PDF reports and AI astrology predictions. Free tier — no credit card required.',
}

const ROUTE_META = {
  '/': {
    title: HOME.title,
    description: HOME.description,
  },
  '/pricing': {
    title: 'AstroVakta API Pricing — Free Plan & Affordable Paid Tiers',
    description:
      'Simple, transparent pricing for the AstroVakta astrology API. Start free with 500 calls/month — no credit card. Starter at $29/mo, Pro at $99/mo with 99.9% SLA. Custom enterprise plans with self-hosting available.',
  },
  '/docs': {
    title: 'API Documentation — Vedic Astrology REST API Endpoints | AstroVakta',
    description:
      'Complete developer documentation for the AstroVakta Vedic astrology API. Birth chart, navamsa, horoscope, kundali matching, dosha, panchang, dasha, gemstone and AI endpoints with request/response examples in every language.',
  },
  '/sandbox': {
    title: 'Free API Sandbox — Test Every Astrology Endpoint Live | AstroVakta',
    description:
      'Try all 180+ Vedic astrology API endpoints directly in your browser. Generate real birth charts, horoscopes and kundali matches live — no code required. Bring your API key and start testing.',
  },
  '/kundali-report': {
    title: 'Free Online Kundli Report — Vedic Birth Chart PDF | AstroVakta',
    description:
      'Generate a free online kundali (Vedic birth chart) report instantly. Get planetary positions, nakshatras, dashas, dosha analysis, gemstone recommendations and download a branded 22-section PDF report.',
  },
  '/about': {
    title: 'About AstroVakta — Building the Most Complete Astrology API',
    description:
      'Learn about AstroVakta: our mission to make accurate Swiss Ephemeris-powered Vedic astrology accessible to every developer through a clean, fast and affordable REST API.',
  },
  '/contact': {
    title: 'Contact AstroVakta — Sales & Support for the Astrology API',
    description:
      'Get in touch with the AstroVakta team. Questions about pricing, integration, enterprise plans or custom astrology app development? Chat on WhatsApp or email hello@astrovakta.com.',
  },
  '/privacy': {
    title: 'Privacy Policy | AstroVakta',
    description:
      'How AstroVakta collects, uses and protects your data. AES-256 encrypted API keys, no birth data logging, GDPR-friendly account deletion and enterprise on-premise options.',
  },
  '/terms': {
    title: 'Terms of Service | AstroVakta',
    description:
      'The terms governing use of the AstroVakta Vedic astrology API — acceptable use, billing, rate limits, refunds and liability.',
  },
  '/blogs': {
    title: 'Astrology API Blog — Tutorials & Developer Guides | AstroVakta',
    description:
      'Learn to build astrology apps: step-by-step tutorials, divisional chart deep-dives, AI astrologer guides and API feature roundups from the AstroVakta engineering blog.',
  },
}

const NOINDEX_ROUTES = new Set([
  '/dashboard',
  '/admin',
  '/verify-email',
  '/verify-email-prompt',
  '/forgot-password',
  '/reset-password',
])

function upsertMeta(attr, key, content) {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function upsertCanonical(href) {
  let link = document.head.querySelector('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  link.setAttribute('href', href)
}

function setJsonLd(id, data) {
  const existing = document.getElementById(id)
  if (existing) existing.remove()
  if (!data) return
  const script = document.createElement('script')
  script.type = 'application/ld+json'
  script.id = id
  script.textContent = JSON.stringify(data)
  document.head.appendChild(script)
}

function resolveMeta(pathname) {
  if (pathname.startsWith('/blogs/')) {
    const slug = pathname.replace('/blogs/', '').replace(/\/$/, '')
    const post = blogPosts.find((p) => p.slug === slug)
    if (post) {
      return {
        title: `${post.title} | AstroVakta Blog`,
        description: post.excerpt,
        type: 'article',
        jsonLd: {
          '@context': 'https://schema.org',
          '@type': 'BlogPosting',
          headline: post.title,
          description: post.excerpt,
          datePublished: new Date(post.date).toISOString(),
          dateModified: new Date(post.date).toISOString(),
          author: { '@type': 'Person', name: post.author },
          publisher: { '@type': 'Organization', name: 'AstroVakta', url: SITE_URL },
          mainEntityOfPage: `${SITE_URL}/blogs/${post.slug}`,
          image: OG_IMAGE,
          articleSection: post.tag,
          inLanguage: 'en',
        },
      }
    }
  }

  if (pathname === '/blogs') {
    return {
      ...ROUTE_META['/blogs'],
      jsonLd: {
        '@context': 'https://schema.org',
        '@type': 'Blog',
        name: 'AstroVakta Blog',
        url: `${SITE_URL}/blogs`,
        description: ROUTE_META['/blogs'].description,
        publisher: { '@type': 'Organization', name: 'AstroVakta', url: SITE_URL },
        blogPost: blogPosts.map((p) => ({
          '@type': 'BlogPosting',
          headline: p.title,
          url: `${SITE_URL}/blogs/${p.slug}`,
          datePublished: new Date(p.date).toISOString(),
          author: { '@type': 'Person', name: p.author },
        })),
      },
    }
  }

  const meta = ROUTE_META[pathname] || ROUTE_META[pathname.replace(/\/$/, '')]
  if (meta) return meta

  // Fallbacks (unknown paths fall back to home metadata; canonical keeps them deduped)
  return { title: HOME.title, description: HOME.description }
}

export default function SeoManager() {
  const location = useLocation()
  const pathname = location.pathname.replace(/\/+$/, '') || '/'
  const noindex = NOINDEX_ROUTES.has(pathname)
  const { title, description, type = 'website', jsonLd } = resolveMeta(pathname)

  useEffect(() => {
    const url = `${SITE_URL}${pathname === '/' ? '/' : pathname}`

    document.title = title

    upsertMeta('name', 'description', description)
    upsertMeta(
      'name',
      'robots',
      noindex
        ? 'noindex, nofollow'
        : 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'
    )
    upsertCanonical(url)

    upsertMeta('property', 'og:title', title)
    upsertMeta('property', 'og:description', description)
    upsertMeta('property', 'og:url', url)
    upsertMeta('property', 'og:type', type)
    upsertMeta('property', 'og:image', OG_IMAGE)

    upsertMeta('name', 'twitter:title', title)
    upsertMeta('name', 'twitter:description', description)
    upsertMeta('name', 'twitter:image', OG_IMAGE)

    setJsonLd('route-jsonld', jsonLd || null)
  }, [pathname, title, description, type, noindex, jsonLd])

  return null
}
