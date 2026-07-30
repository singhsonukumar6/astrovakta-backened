import { useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import { MessageCircle, Mail, MapPin, Phone, Send, Clock, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'

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

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
  const [sent, setSent] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    const msg = `Hi AstroVakta,%0A%0AName: ${form.name}%0AEmail: ${form.email}%0ASubject: ${form.subject}%0A%0A${form.message}`
    window.open(`https://wa.me/916239402519?text=${msg}`, '_blank')
    setSent(true)
  }

  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Get In Touch</p>
          <h1 style={{ fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 900, textAlign: 'center', marginBottom: 20, letterSpacing: '-1px' }}>
            Let's <span className="gradient-text">Talk</span>
          </h1>
          <p style={{ color: '#94a3b8', fontSize: 18, textAlign: 'center', maxWidth: 500, margin: '0 auto 60px', lineHeight: 1.8 }}>
            Have a question about the API, custom development, or enterprise plans? We'd love to hear from you.
          </p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 48, maxWidth: 1000, margin: '0 auto' }}>
          <FadeIn delay={0.1}>
            <div>
              <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>
                Send Us a <span className="gradient-text">Message</span>
              </h2>

              {sent ? (
                <div style={{
                  background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)',
                  borderRadius: 'var(--radius-lg)', padding: 32, textAlign: 'center',
                }}>
                  <Zap size={40} color="#22c55e" style={{ marginBottom: 16 }} />
                  <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Message Sent!</h3>
                  <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.6 }}>
                    We've redirected you to WhatsApp. We typically respond within a few hours during business hours.
                  </p>
                  <button onClick={() => setSent(false)} style={{
                    marginTop: 20, padding: '10px 24px', borderRadius: 10,
                    background: 'var(--gradient-primary)', color: '#fff',
                    fontWeight: 600, fontSize: 14, cursor: 'pointer', border: 'none',
                  }}>Send Another Message</button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <input className="input-field" placeholder="Your Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
                  <input className="input-field" type="email" placeholder="Your Email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
                  <input className="input-field" placeholder="Subject" value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })} required />
                  <textarea
                    className="input-field"
                    placeholder="Your Message"
                    rows={5}
                    value={form.message}
                    onChange={e => setForm({ ...form, message: e.target.value })}
                    required
                    style={{ resize: 'vertical', minHeight: 120 }}
                  />
                  <button type="submit" className="btn-primary" style={{ justifyContent: 'center', padding: '14px 0', fontSize: 16 }}>
                    <Send size={18} /> Send via WhatsApp
                  </button>
                </form>
              )}
            </div>
          </FadeIn>

          <FadeIn delay={0.2}>
            <div>
              <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>
                Other Ways to <span className="gradient-text">Reach Us</span>
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {[
                  { icon: MessageCircle, label: 'WhatsApp', value: '+91 62394 02519', href: 'https://wa.me/916239402519', color: '#25D366' },
                  { icon: Mail, label: 'Email', value: 'hello@astrovakta.com', href: 'mailto:hello@astrovakta.com', color: '#7c3aed' },
                  { icon: MapPin, label: 'Location', value: 'Bangalore, India', href: null, color: '#ef4444' },
                  { icon: Clock, label: 'Response Time', value: 'Within 24 hours (Mon-Fri)', href: null, color: '#f59e0b' },
                ].map((item, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 16, padding: '16px 20px',
                    background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                  }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 12,
                      background: `${item.color}18`, display: 'flex',
                      alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      <item.icon size={20} color={item.color} />
                    </div>
                    <div>
                      <p style={{ color: '#64748b', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>{item.label}</p>
                      {item.href ? (
                        <a href={item.href} target="_blank" rel="noopener noreferrer" style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 600 }}>
                          {item.value}
                        </a>
                      ) : (
                        <p style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 600 }}>{item.value}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 40, padding: 24, background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)' }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>Quick Links</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
                  <Link to="/docs" style={{ color: '#a78bfa', fontSize: 14 }}>API Documentation</Link>
                  <Link to="/pricing" style={{ color: '#a78bfa', fontSize: 14 }}>Pricing Plans</Link>
                  <Link to="/sandbox" style={{ color: '#a78bfa', fontSize: 14 }}>API Sandbox</Link>
                  <Link to="/blogs" style={{ color: '#a78bfa', fontSize: 14 }}>Blog & Guides</Link>
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>
    </div>
  )
}
