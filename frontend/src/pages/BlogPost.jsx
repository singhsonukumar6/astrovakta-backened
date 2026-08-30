import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Clock, User, Calendar, BookOpen, Image as ImageIcon } from 'lucide-react'
import { getBlog } from '../lib/api.js'

const tagColor = (tag) => {
  const colors = ['#7c3aed', '#3b82f6', '#ec4899', '#8b5cf6', '#f59e0b']
  let hash = 0
  for (let i = 0; i < (tag || 'x').length; i++) hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

export default function BlogPost() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getBlog(slug)
      .then(setPost)
      .catch(() => setPost(null))
      .finally(() => setLoading(false))
  }, [slug])

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
