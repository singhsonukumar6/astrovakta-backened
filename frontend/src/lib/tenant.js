// Tenant host resolution — maps the browser hostname to a tenant site.
//
//   pandit-rajesh.localhost:4188      → tenant by slug (local dev; browsers
//                                       resolve *.localhost to 127.0.0.1)
//   pandit-rajesh.astrovakta.com      → tenant by slug (prod wildcard subdomain)
//   astrovakra.com / www.astrovakra…  → tenant by custom domain
//   localhost / www.astrovakta.com …  → the AstroVakta platform itself

const PLATFORM_HOSTS = new Set([
  'localhost',
  '127.0.0.1',
  'astrovakta.com',
  'www.astrovakta.com',
  'dev.astrovakta.com',
  'api.astrovakta.com',
  'sites.astrovakta.com',
])

const IPV4_RE = /^\d{1,3}(\.\d{1,3}){3}$/

// Returns { type: 'slug', value } | { type: 'domain', value } | null (platform).
export function resolveTenantHost(hostname) {
  const h = (hostname || '').toLowerCase()

  // Local dev tenant subdomains: pandit-rajesh.localhost
  if (h.endsWith('.localhost')) {
    const slug = h.slice(0, -'.localhost'.length)
    if (slug && !slug.includes('.')) return { type: 'slug', value: slug }
    return null
  }

  if (PLATFORM_HOSTS.has(h) || IPV4_RE.test(h) || !h.includes('.')) return null

  // Prod wildcard: pandit-rajesh.astrovakta.com
  if (h.endsWith('.astrovakta.com')) {
    const slug = h.slice(0, -'.astrovakta.com'.length)
    if (slug && !slug.includes('.')) return { type: 'slug', value: slug }
    return null
  }

  // Any other real domain is a tenant's custom domain.
  return { type: 'domain', value: h.replace(/^www\./, '') }
}

export function isTenantHost() {
  return typeof window !== 'undefined' && resolveTenantHost(window.location.hostname) !== null
}

// Public URL of a tenant site (used for "View site" links and copy).
export function tenantSiteUrl(slug) {
  if (typeof window === 'undefined') return `https://${slug}.astrovakta.com`
  const { protocol, hostname, port } = window.location
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.endsWith('.localhost')
  if (isLocal) return `${protocol}//${slug}.localhost${port ? `:${port}` : ''}`
  return `https://${slug}.astrovakta.com`
}

// Display form of the free subdomain (prod naming).
export function tenantSubdomainLabel(slug) {
  return `${slug}.astrovakta.com`
}
