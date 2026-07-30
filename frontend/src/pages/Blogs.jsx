import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, useInView } from 'framer-motion'
import { ArrowRight, BookOpen, Clock, User } from 'lucide-react'
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

export default function Blogs() {
  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section">
        <FadeIn>
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
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 28, maxWidth: 1100, margin: '0 auto' }}>
          {blogPosts.map((post, i) => (
            <FadeIn key={post.slug} delay={i * 0.1}>
              <Link to={`/blogs/${post.slug}`}>
                <motion.div
                  whileHover={{ y: -4 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                  className="card-glow"
                  style={{
                    background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)', overflow: 'hidden', height: '100%', display: 'flex', flexDirection: 'column',
                  }}>
                  <div style={{
                    height: 180,
                    background: `linear-gradient(135deg, ${post.tagColor}20, ${post.tagColor}05)`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    borderBottom: `1px solid ${post.tagColor}20`,
                  }}>
                    <BookOpen size={48} color={post.tagColor} opacity={0.6} />
                  </div>
                  <div style={{ padding: 24, flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                      <span style={{
                        background: `${post.tagColor}18`, color: post.tagColor,
                        padding: '3px 10px', borderRadius: 6, fontSize: 11,
                        fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5,
                      }}>{post.tag}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#64748b', fontSize: 12 }}>
                        <Clock size={12} /> {post.readTime}
                      </div>
                    </div>
                    <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8, lineHeight: 1.4 }}>{post.title}</h2>
                    <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.6, marginBottom: 16, flex: 1 }}>{post.excerpt}</p>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#64748b', fontSize: 13 }}>
                        <User size={13} /> {post.author} · {post.date}
                      </div>
                      <span style={{ color: '#a78bfa', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                        Read <ArrowRight size={14} />
                      </span>
                    </div>
                  </div>
                </motion.div>
              </Link>
            </FadeIn>
          ))}
        </div>
      </section>
    </div>
  )
}
