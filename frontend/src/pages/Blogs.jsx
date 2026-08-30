import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, BookOpen, Clock, User, Image as ImageIcon } from 'lucide-react'
import { getBlogs } from '../lib/api.js'

export default function Blogs() {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    getBlogs({ page: 1, per_page: 30 })
      .then((data) => setPosts(data.blogs || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const tagColor = (tag) => {
    const colors = ['#7c3aed', '#3b82f6', '#ec4899', '#8b5cf6', '#f59e0b']
    let hash = 0
    for (let i = 0; i < (tag || 'x').length; i++) hash = tag.charCodeAt(i) + ((hash << 5) - hash)
    return colors[Math.abs(hash) % colors.length]
  }

  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, justifyContent: 'center' }}>
          <BookOpen size={24} color="#7c3aed" />
          <p style={{ color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, fontWeight: 600 }}>Blog</p>
        </div>
        <h1 style={{ fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 900, textAlign: 'center', marginBottom: 16, letterSpacing: '-1px' }}>
          Insights & <span className="gradient-text">Guides</span>
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 18, textAlign: 'center', maxWidth: 500, margin: '0 auto 60px', lineHeight: 1.8 }}>
          Tutorials, technical deep-dives, and best practices for building astrology applications.
        </p>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>Loading posts...</div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#ef4444' }}>Failed to load blog posts.</div>
        ) : posts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
            <BookOpen size={48} color="#475569" style={{ margin: '0 auto 16px' }} />
            <p>No blog posts published yet.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 28, maxWidth: 1100, margin: '0 auto' }}>
            {posts.map((post, i) => {
              const color = tagColor(post.tag)
              return (
                <Link to={`/blogs/${post.slug}`} key={post.slug || i} style={{ textDecoration: 'none' }}>
                  <motion.div
                    whileHover={{ y: -4 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                    className="card-glow"
                    style={{
                      background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-lg)', overflow: 'hidden', height: '100%', display: 'flex', flexDirection: 'column',
                    }}>
                    <div style={{
                      height: 180, overflow: 'hidden',
                      background: post.cover_image ? `linear-gradient(135deg, ${color}20, ${color}05)` : `linear-gradient(135deg, ${color}20, ${color}05)`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      borderBottom: `1px solid ${color}20`,
                    }}>
                      {post.cover_image ? (
                        <img src={post.cover_image} alt={post.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.style.display = 'none' }} />
                      ) : (
                        <BookOpen size={48} color={color} opacity={0.6} />
                      )}
                    </div>
                    <div style={{ padding: 24, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                        {post.tag && (
                          <span style={{
                            background: `${color}18`, color,
                            padding: '3px 10px', borderRadius: 6, fontSize: 11,
                            fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5,
                          }}>{post.tag}</span>
                        )}
                        {post.read_time && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#64748b', fontSize: 12 }}>
                            <Clock size={12} /> {post.read_time}
                          </div>
                        )}
                      </div>
                      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8, lineHeight: 1.4, color: '#e2e8f0' }}>{post.title}</h2>
                      <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.6, marginBottom: 16, flex: 1 }}>{post.excerpt}</p>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#64748b', fontSize: 13 }}>
                          <User size={13} /> {post.author} · {post.created_at ? new Date(post.created_at).toLocaleDateString() : ''}
                        </div>
                        <span style={{ color: '#a78bfa', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                          Read <ArrowRight size={14} />
                        </span>
                      </div>
                    </div>
                  </motion.div>
                </Link>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
