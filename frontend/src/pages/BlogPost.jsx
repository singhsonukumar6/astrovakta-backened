import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Clock, User, Calendar, BookOpen, Image as ImageIcon } from 'lucide-react'
import { getBlog } from '../lib/api.js'
import { SITE_URL, OG_IMAGE } from '../components/SEO.jsx'
import blogData from './blogData.js'

const tagColor = (tag) => {
  const colors = ['#7c3aed', '#3b82f6', '#ec4899', '#8b5cf6', '#f59e0b']
  let hash = 0
  for (let i = 0; i < (tag || 'x').length; i++) hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

// Bundled fallback post, same shape the API returns (used when the API has none).
const FALLBACK_BY_SLUG = Object.fromEntries(
  blogData.map((p) => [
    p.slug,
    {
      slug: p.slug,
      title: p.title,
      excerpt: p.excerpt,
      tag: p.tag,
      read_time: p.readTime,
      author: p.author,
      cover_image: null,
      created_at: p.date,
      body: p.body
        .map((b) =>
          b.type === 'h2'
            ? `<h2>${b.text}</h2>`
            : b.type === 'pre'
              ? `<pre><code>${b.text.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</code></pre>`
              : `<p>${b.text}</p>`,
        )
        .join('\n'),
    },
  ]),
)

function upsertMeta(attr, key, content) {
  if (content == null) return
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function toIsoDate(value) {
  if (!value) return null
  if (/^\d{4}-\d{2}-\d{2}/.test(value)) return value
  const parsed = new Date(value)
  return isNaN(parsed) ? null : parsed.toISOString()
}

// Per-post SEO: title, description, canonical, OG/Twitter tags and Article JSON-LD.
function applyPostSeo(post, slug) {
  const url = `${SITE_URL}/blogs/${slug}`
  const title = `${post.title} | AstroVakta Blog`
  const description = (post.excerpt || 'AstroVakta developer blog').slice(0, 300)

  document.title = title
  upsertMeta('name', 'description', description)
  upsertMeta('name', 'robots', 'index, follow, max-image-preview:large, max-snippet:-1')

  let canonical = document.head.querySelector('link[rel="canonical"]')
  if (!canonical) {
    canonical = document.createElement('link')
    canonical.setAttribute('rel', 'canonical')
    document.head.appendChild(canonical)
  }
  canonical.setAttribute('href', url)

  const image = post.cover_image || OG_IMAGE
  upsertMeta('property', 'og:title', title)
  upsertMeta('property', 'og:description', description)
  upsertMeta('property', 'og:url', url)
  upsertMeta('property', 'og:type', 'article')
  upsertMeta('property', 'og:image', image)
  upsertMeta('name', 'twitter:card', 'summary_large_image')
  upsertMeta('name', 'twitter:title', title)
  upsertMeta('name', 'twitter:description', description)
  upsertMeta('name', 'twitter:image', image)

  const published = toIsoDate(post.created_at)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description,
    url,
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
    image: [image],
    author: { '@type': 'Person', name: post.author || 'AstroVakta' },
    publisher: { '@type': 'Organization', name: 'AstroVakta', url: SITE_URL },
    ...(published ? { datePublished: published, dateModified: published } : {}),
  }
  let script = document.getElementById('blogpost-jsonld')
  if (!script) {
    script = document.createElement('script')
    script.type = 'application/ld+json'
    script.id = 'blogpost-jsonld'
    document.head.appendChild(script)
  }
  script.textContent = JSON.stringify(jsonLd)
}

export default function BlogPost() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getBlog(slug)
      .then((data) => {
        setPost(data || FALLBACK_BY_SLUG[slug] || null)
      })
      .catch(() => setPost(FALLBACK_BY_SLUG[slug] || null))
      .finally(() => setLoading(false))
  }, [slug])

  useEffect(() => {
    if (post) applyPostSeo(post, slug)
  }, [post, slug])

  if (loading) {
    return (
      <div style={{ paddingTop: 140, textAlign: 'center', color: '#64748b' }}>
        <BookOpen size={48} color="#475569" style={{ margin: '0 auto 16px' }} />
        <p>Loading post...</p>
      </div>
    )
  }

  if (!post) {
    return (
      <div style={{ paddingTop: 140, textAlign: 'center' }}>
        <BookOpen size={48} color="#64748b" style={{ margin: '0 auto 16px' }} />
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12 }}>Post Not Found</h1>
        <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 32 }}>The blog post you're looking for doesn't exist or isn't published yet.</p>
        <Link to="/blogs" className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <ArrowLeft size={16} /> Back to Blog
        </Link>
      </div>
    )
  }

  const color = tagColor(post.tag)

  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section" style={{ maxWidth: 800, margin: '0 auto' }}>
        <Link to="/blogs" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: 14, marginBottom: 32 }}>
          <ArrowLeft size={14} /> Back to all posts
        </Link>

        {post.cover_image && (
          <img
            src={post.cover_image}
            alt={post.title}
            style={{ width: '100%', maxHeight: 420, objectFit: 'cover', borderRadius: 'var(--radius-lg)', marginBottom: 32, border: '1px solid var(--border-color)' }}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          {post.tag && (
            <span style={{ background: `${color}18`, color, padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {post.tag}
            </span>
          )}
          {post.read_time && (
            <span style={{ color: '#64748b', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={13} /> {post.read_time}
            </span>
          )}
        </div>

        <h1 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 900, marginBottom: 16, lineHeight: 1.2, letterSpacing: '-0.5px' }}>
          {post.title}
        </h1>
        {post.excerpt && (
          <p style={{ color: '#94a3b8', fontSize: 16, lineHeight: 1.7, marginBottom: 32 }}>{post.excerpt}</p>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 16, paddingBottom: 32, borderBottom: '1px solid var(--border-color)', marginBottom: 32 }}>
          <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#fff' }}>
            {(post.author || 'A')[0]}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, display: 'flex', alignItems: 'center', gap: 4 }}>
              <User size={13} /> {post.author}
            </div>
            <div style={{ color: '#64748b', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
              <Calendar size={13} /> {post.created_at ? new Date(post.created_at).toLocaleDateString() : ''}
            </div>
          </div>
        </div>

        {/* Rich text body rendered from stored HTML */}
        <div
          className="blog-prose"
          style={{
            color: '#cbd5e1', fontSize: 16, lineHeight: 1.85, wordBreak: 'break-word',
          }}
          dangerouslySetInnerHTML={{ __html: post.body || '' }}
        />
      </section>
    </div>
  )
}
