import { useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, useInView } from 'framer-motion'
import { ArrowLeft, Clock, User, Calendar, BookOpen } from 'lucide-react'
import blogPosts from './blogData.js'

function FadeIn({ children, delay = 0 }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}>
      {children}
    </motion.div>
  )
}

export default function BlogPost() {
  const { slug } = useParams()
  const post = blogPosts.find(p => p.slug === slug)

  if (!post) {
    return (
      <div style={{ paddingTop: 140, textAlign: 'center' }}>
        <BookOpen size={48} color="#64748b" style={{ margin: '0 auto 16px' }} />
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12 }}>Post Not Found</h1>
        <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 32 }}>The blog post you're looking for doesn't exist.</p>
        <Link to="/blogs" className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <ArrowLeft size={16} /> Back to Blog
        </Link>
      </div>
    )
  }

  const renderBody = (block, i) => {
    switch (block.type) {
      case 'h2':
        return <h2 key={i} style={{ fontSize: 24, fontWeight: 700, marginTop: 40, marginBottom: 14 }}>{block.text}</h2>
      case 'p':
        return <p key={i} style={{ color: '#94a3b8', fontSize: 16, lineHeight: 1.85, marginBottom: 18 }}>{block.text}</p>
      case 'pre':
        return (
          <pre key={i} style={{
            background: '#0a0a1f', border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius)', padding: '20px 24px', fontSize: 13,
            lineHeight: 1.8, fontFamily: 'var(--font-mono)', color: '#e2e8f0',
            overflow: 'auto', marginBottom: 20,
          }}>{block.text}</pre>
        )
      default:
        return null
    }
  }

  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section" style={{ maxWidth: 800, margin: '0 auto' }}>
        <FadeIn>
          <Link to="/blogs" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            color: '#94a3b8', fontSize: 14, marginBottom: 32,
          }}>
            <ArrowLeft size={14} /> Back to all posts
          </Link>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <span style={{
              background: `${post.tagColor}18`, color: post.tagColor,
              padding: '4px 12px', borderRadius: 6, fontSize: 12,
              fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5,
            }}>{post.tag}</span>
            <span style={{ color: '#64748b', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={13} /> {post.readTime}
            </span>
          </div>

          <h1 style={{ fontSize: 'clamp(28px, 4vw, 42px)', fontWeight: 900, marginBottom: 16, lineHeight: 1.2, letterSpacing: '-0.5px' }}>
            {post.title}
          </h1>
          <p style={{ color: '#94a3b8', fontSize: 16, lineHeight: 1.7, marginBottom: 32 }}>{post.excerpt}</p>

          <div style={{
            display: 'flex', alignItems: 'center', gap: 16, paddingBottom: 32,
            borderBottom: '1px solid var(--border-color)', marginBottom: 32,
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: '50%',
              background: 'var(--gradient-primary)', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              fontSize: 18, fontWeight: 700, color: '#fff',
            }}>{post.author[0]}</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15, display: 'flex', alignItems: 'center', gap: 4 }}>
                <User size={13} /> {post.author}
              </div>
              <div style={{ color: '#64748b', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                <Calendar size={13} /> {post.date}
              </div>
            </div>
          </div>

          {post.body.map((block, i) => renderBody(block, i))}
        </FadeIn>
      </section>
    </div>
  )
}
