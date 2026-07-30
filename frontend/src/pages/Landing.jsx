import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useInView, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import { SignUpOrRegister, ClerkSignedOut } from '../components/AuthButton.jsx'
import {
  Sparkles, BookOpen, Heart, Sun, Shield, Brain, Code, Zap, Globe,
  Clock, Cpu, TrendingUp, Star, Check, X as XIcon, ChevronRight,
  Terminal, Layers, BarChart3, Moon, Compass, Gem,
  ArrowRight, Play, Rocket, FileText, Bot, Lock, Gauge, Key,
  MessageCircle, DollarSign, IndianRupee, MonitorSmartphone, Palette, Server,
  ShoppingCart, Users, CreditCard,
} from 'lucide-react'

function FadeIn({ children, delay = 0, direction = 'up', className = '', style = {} }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })
  const map = { up: [50, 0], down: [-50, 0], left: [50, 0], right: [-50, 0] }
  const [x, y] = map[direction] || [0, 50]
  return (
    <motion.div ref={ref} className={className} style={style}
      initial={{ opacity: 0, y, x }}
      animate={isInView ? { opacity: 1, y: 0, x: 0 } : {}}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}>
      {children}
    </motion.div>
  )
}

function AnimatedCounter({ target, suffix = '' }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!isInView) return
    const start = performance.now()
    const step = (now) => {
      const p = Math.min((now - start) / 2000, 1)
      setCount(Math.floor((1 - Math.pow(1 - p, 3)) * target))
      if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [isInView, target])
  return <span ref={ref}>{count}{suffix}</span>
}

function GlowOrb() {
  return (
    <motion.div
      animate={{ scale: [1, 1.15, 1], rotate: [0, 180, 360] }}
      transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
      style={{
        position: 'absolute', top: '10%', left: '50%', transform: 'translate(-50%,0)',
        width: 700, height: 700, borderRadius: '50%', pointerEvents: 'none',
        background: 'radial-gradient(circle, rgba(124,58,237,0.18) 0%, rgba(99,102,241,0.08) 40%, transparent 70%)',
        filter: 'blur(40px)',
      }}
    />
  )
}

function GridDots() {
  const dots = useRef(Array.from({ length: 60 }, (_, i) => ({
    x: Math.random() * 100, y: Math.random() * 100,
    delay: Math.random() * 3, size: Math.random() * 2 + 1,
  })))
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {dots.current.map((d, i) => (
        <motion.div key={i}
          animate={{ opacity: [0.1, 0.5, 0.1] }}
          transition={{ duration: 3 + Math.random() * 2, repeat: Infinity, delay: d.delay }}
          style={{
            position: 'absolute', left: `${d.x}%`, top: `${d.y}%`,
            width: d.size, height: d.size, borderRadius: '50%',
            background: 'rgba(124,58,237,0.6)',
          }}
        />
      ))}
    </div>
  )
}

function FloatingIcon({ icon: Icon, top, left, delay = 0, size = 40, color = '#7c3aed' }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.5 }}
      style={{
        position: 'absolute', top, left,
        width: size, height: size, borderRadius: 12,
        background: `${color}18`, border: `1px solid ${color}30`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 3 + delay, repeat: Infinity, ease: 'easeInOut' }}
      >
        <Icon size={size * 0.5} color={color} />
      </motion.div>
    </motion.div>
  )
}

const EXCHANGE_RATE = 83

export default function Landing() {
  const { scrollYProgress } = useScroll()
  const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -80])
  const [currency, setCurrency] = useState('usd')

  return (
    <div style={{ overflow: 'hidden' }}>

      {/* ═══════════ HERO ═══════════ */}
      <section style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center',
        justifyContent: 'center', textAlign: 'center',
        padding: '140px 24px 100px', position: 'relative',
      }}>
        <GlowOrb />
        <GridDots />

        <motion.div style={{ y: heroY, maxWidth: 900, position: 'relative', zIndex: 1 }}>
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '8px 18px', borderRadius: 24,
              background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.25)',
              marginBottom: 32, fontSize: 13, color: '#a78bfa', fontWeight: 600,
            }}>
            <Zap size={14} /> 180+ Endpoints {'\u00B7'} AI-Powered {'\u00B7'} Sidereal Engine
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            style={{
              fontSize: 'clamp(40px, 7vw, 80px)', fontWeight: 900,
              lineHeight: 1.05, marginBottom: 28, letterSpacing: '-1.5px',
            }}>
            <span style={{ color: '#ffffff' }}>Astro</span>
            <span style={{ color: '#eab308' }}>Vakta</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.45 }}
            style={{ color: '#64748b', fontSize: 15, fontWeight: 500, marginBottom: 8 }}
          >for developers</motion.p>

          <motion.h2 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            style={{
              fontSize: 'clamp(18px, 2.5vw, 28px)', fontWeight: 600,
              color: '#94a3b8', marginBottom: 16, lineHeight: 1.4,
            }}>
            The Vedic Astrology API for Modern Developers
          </motion.h2>

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.55 }}
            style={{
              fontSize: 'clamp(15px, 1.8vw, 18px)', color: '#94a3b8',
              maxWidth: 640, margin: '0 auto 44px', lineHeight: 1.75,
            }}>
            Birth charts, horoscopes, doshas, compatibility, panchang, divisional charts,
            PDF reports, and AI interpretations {'\u2014'} a complete sidereal astrology engine behind a single REST API.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <ClerkSignedOut>
              <SignUpOrRegister mode="modal">
                <button className="btn-primary" style={{ padding: '16px 40px', fontSize: 16 }}>
                  <Rocket size={18} /> Try for Free
                </button>
              </SignUpOrRegister>
            </ClerkSignedOut>
            <Link to="/docs">
              <button className="btn-secondary" style={{ padding: '16px 40px', fontSize: 16 }}>
                <BookOpen size={18} /> API Docs
              </button>
            </Link>
            <Link to="/sandbox">
              <button className="btn-secondary" style={{ padding: '16px 40px', fontSize: 16 }}>
                <Play size={18} /> Try Sandbox
              </button>
            </Link>
          </motion.div>

          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
            style={{ color: '#64748b', fontSize: 13, marginTop: 16 }}>
            No credit card required · 100 API calls per month free
          </motion.p>

          {/* code peek */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.9 }}
            style={{
              marginTop: 56, background: '#0a0a1f', border: '1px solid rgba(124,58,237,0.2)',
              borderRadius: 16, overflow: 'hidden', maxWidth: 680, margin: '56px auto 0',
            }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 16px', borderBottom: '1px solid rgba(124,58,237,0.12)' }}>
              <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#ef4444' }} />
              <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#eab308' }} />
              <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#22c55e' }} />
              <span style={{ marginLeft: 10, fontSize: 12, color: '#475569' }}>birth-chart.sh</span>
            </div>
            <pre style={{ padding: '20px 24px', fontSize: 13, lineHeight: 1.9, fontFamily: 'var(--font-mono)', color: '#e2e8f0', overflow: 'auto', textAlign: 'left' }}>
              <code>{`# Get your birth chart in one request
`}<span style={{color:'#a78bfa'}}>curl</span>{` `}<span style={{color:'#22c55e'}}>-X POST</span>{` `}<span style={{color:'#fbbf24'}}>"http://localhost:5000/chart/birth-chart"</span>{` \\
  `}<span style={{color:'#a78bfa'}}>-H</span>{` `}<span style={{color:'#fbbf24'}}>"X-API-Key: avk_live_xxx"</span>{` \\
  `}<span style={{color:'#a78bfa'}}>-d</span>{` `}<span style={{color:'#fbbf24'}}>{'{"dateOfBirth":"1990-05-15","timeOfBirth":"14:30","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}'}</span>{``}</code>
            </pre>
          </motion.div>
        </motion.div>
      </section>

      {/* ═══════════ STATS BAR ═══════════ */}
      <section style={{ padding: '48px 24px', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 32, maxWidth: 1000, margin: '0 auto' }}>
          {[
            { v: 180, s: '+', l: 'API Endpoints' },
            { v: 16, s: '', l: 'Vedic Chart Types' },
            { v: 8, s: '', l: 'Divisional Charts' },
            { v: 4, s: '', l: 'AI Providers' },
            { v: 99, s: '.9%', l: 'Uptime SLA' },
          ].map((s) => (
            <FadeIn key={s.l}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 40, fontWeight: 900, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', lineHeight: 1.2 }}>
                  <AnimatedCounter target={s.v} suffix={s.s} />
                </div>
                <p style={{ color: '#64748b', fontSize: 13, marginTop: 6, fontWeight: 500 }}>{s.l}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ FEATURES ═══════════ */}
      <section className="section" id="features">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Features</p>
          <h2 className="section-title">Everything You Need to <span className="gradient-text">Build</span></h2>
          <p className="section-subtitle">From birth charts to AI-powered insights, our API covers every aspect of Vedic astrology.</p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
          {[
            { icon: Compass, title: 'Birth Charts (Kundli)', desc: 'Generate accurate D1 Rasi charts with all 9 Vedic planets, house placements, dignities, nakshatras, and combustion status.', color: '#7c3aed' },
            { icon: Layers, title: 'Divisional Charts (Vargas)', desc: 'D1 through D60 divisional charts \u2014 Navamsa, Hora, Drekkana, Dashamamsa and more for fine-grained life-area analysis.', color: '#6366f1' },
            { icon: Moon, title: 'Daily Horoscopes', desc: 'Daily, weekly, monthly & yearly horoscopes generated from real-time transits over the natal chart.', color: '#3b82f6' },
            { icon: Heart, title: 'Compatibility (Milan)', desc: 'Ashtakoot gun milan, Nadi dosha, Bhakoot dosha, and Gana matching for matrimonial analysis.', color: '#ec4899' },
            { icon: Shield, title: 'Dosha Analysis', desc: 'Mangal, Kaal Sarp, Sade Sati, Pitra, Shani doshas with severity ratings and personalized remedies.', color: '#ef4444' },
            { icon: Brain, title: 'AI Interpretations', desc: 'Bring your own OpenAI, Claude, Groq, or Together key. AI reads your chart context and gives natural-language predictions.', color: '#8b5cf6' },
            { icon: Clock, title: 'Panchang & Muhurat', desc: 'Full Panchang \u2014 Tithi, Nakshatra, Yoga, Karana, Vara \u2014 plus auspicious muhurat windows for events.', color: '#f59e0b' },
            { icon: Gem, title: 'Gemstone & Rudraksha', desc: 'Personalized gemstone and rudraksha recommendations based on ascendant lord, afflictions, and yoga positions.', color: '#10b981' },
            { icon: FileText, title: 'PDF Report Generation', desc: 'Branded 22-section PDF reports with cover page, charts, predictions, remedies, and downloadable output.', color: '#06b6d4' },
            { icon: Terminal, title: 'Developer Sandbox', desc: 'Interactive API playground in the browser \u2014 try every endpoint with your API key before writing a single line of code.', color: '#64748b' },
            { icon: Lock, title: 'API Key Auth & Tiers', desc: 'AES-encrypted key storage, rate limiting by tier (Free / Starter / Pro / Enterprise), and usage analytics.', color: '#a78bfa' },
            { icon: Bot, title: 'Multi-Provider AI', desc: 'OpenAI, Anthropic, Groq, Together \u2014 configure multiple providers, test connectivity, and switch seamlessly.', color: '#f472b6' },
          ].map((f, i) => (
            <FadeIn key={f.title} delay={i * 0.05}>
              <div className="card-glow" style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
              }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: `${f.color}18`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 18,
                }}>
                  <f.icon size={22} color={f.color} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{f.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7 }}>{f.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ ANIMATED SHOWCASE ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>What We Offer</p>
          <h2 className="section-title">See <span className="gradient-text">AstroVakta</span> in Action</h2>
          <p className="section-subtitle">A visual tour of what you can build with our API.</p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 24 }}>
          {[
            {
              title: 'Birth Chart Visualization',
              desc: 'Generate beautiful North Indian, South Indian, and East Indian style charts. Full D1-D60 divisional chart support with SVG output.',
              color: '#7c3aed',
              items: ['North Indian Diamond', 'South Indian Grid', 'East Indian Style', 'Moon Chart', 'Navamsa D9', 'Sudarshana Chakra'],
            },
            {
              title: 'Horoscope & Predictions',
              desc: 'Daily, weekly, monthly, and yearly horoscopes. Transit analysis, dasha predictions, and personalized AI readings.',
              color: '#3b82f6',
              items: ['Daily Horoscope', 'Weekly Forecast', 'Yearly Predictions', 'Vimshottari Dasha', 'Transit Analysis', 'AI Chat'],
            },
            {
              title: 'Compatibility & Analysis',
              desc: 'Ashtakoot Guna Milan, dosha detection, yoga analysis, and gemstone recommendations with detailed reports.',
              color: '#ec4899',
              items: ['Guna Milan', 'Mangal Dosha', 'Kaal Sarp Dosha', 'Sade Sati', 'Gemstone Advisor', 'Rudraksha Guide'],
            },
          ].map((showcase, i) => (
            <FadeIn key={showcase.title} delay={i * 0.12}>
              <motion.div
                whileHover={{ y: -6 }}
                transition={{ type: 'spring', stiffness: 200 }}
                className="card-glow"
                style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
                }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14,
                  background: `${showcase.color}18`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 16,
                }}>
                  <Star size={24} color={showcase.color} />
                </div>
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>{showcase.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7, marginBottom: 20 }}>{showcase.desc}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {showcase.items.map((item) => (
                    <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#cbd5e1' }}>
                      <Check size={14} color="#22c55e" />
                      {item}
                    </div>
                  ))}
                </div>
              </motion.div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ CUSTOM ASTROLOGER WEBSITE ═══════════ */}
      <section className="section" id="custom-websites">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Custom Development</p>
          <h2 className="section-title">We Build Your <span className="gradient-text">Astrologer Website</span></h2>
          <p className="section-subtitle">Want a fully custom astrology website for your brand? We handle everything from design to deployment.</p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24, marginBottom: 48 }}>
          {[
            { icon: MonitorSmartphone, title: 'Responsive Design', desc: 'Beautiful, mobile-first websites optimized for all devices. Stunning UI/UX tailored to your brand.' },
            { icon: Palette, title: 'White-Label Branding', desc: 'Your logo, your colors, your domain. Fully branded astrology platform under your name.' },
            { icon: Server, title: 'API Integration', desc: 'We integrate the full AstroVakta API stack — birth charts, horoscopes, compatibility, and more.' },
            { icon: ShoppingCart, title: 'Payment Gateway', desc: 'Integrated Stripe/Razorpay for consultation bookings, report sales, and subscription plans.' },
            { icon: Users, title: 'User Dashboard', desc: 'Client management, booking calendar, report history. Everything your customers need.' },
            { icon: CreditCard, title: 'Monetization Ready', desc: 'Sell PDF reports, consultation slots, and premium content. We set up the revenue pipeline.' },
          ].map((f, i) => (
            <FadeIn key={f.title} delay={i * 0.06}>
              <motion.div whileHover={{ y: -4 }} className="card-glow"
                style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)', padding: 24, height: '100%',
                }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: 'rgba(234,179,8,0.12)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 16,
                }}>
                  <f.icon size={22} color="#eab308" />
                </div>
                <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 8 }}>{f.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.6 }}>{f.desc}</p>
              </motion.div>
            </FadeIn>
          ))}
        </div>

        {/* Custom Website Pricing */}
        <FadeIn>
          <h3 style={{ textAlign: 'center', fontSize: 24, fontWeight: 700, marginBottom: 32 }}>
            Custom Website <span className="gradient-text">Packages</span>
          </h3>
        </FadeIn>

        {/* Currency Toggle */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center',
            background: 'var(--bg-card)', borderRadius: 12,
            border: '1px solid var(--border-color)', padding: 4,
          }}>
            <button
              onClick={() => setCurrency('inr')}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '10px 20px', borderRadius: 10,
                border: 'none', background: currency === 'inr' ? 'var(--gradient-primary)' : 'transparent',
                color: currency === 'inr' ? '#fff' : '#94a3b8',
                fontWeight: 600, fontSize: 14, cursor: 'pointer',
              }}>
              <IndianRupee size={16} /> INR
            </button>
            <button
              onClick={() => setCurrency('usd')}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '10px 20px', borderRadius: 10,
                border: 'none', background: currency === 'usd' ? 'var(--gradient-primary)' : 'transparent',
                color: currency === 'usd' ? '#fff' : '#94a3b8',
                fontWeight: 600, fontSize: 14, cursor: 'pointer',
              }}>
              <DollarSign size={16} /> USD
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24, maxWidth: 960, margin: '0 auto' }}>
          {[
            {
              name: 'Starter Site', color: '#64748b',
              usd: 499, inr: 24999,
              features: ['5 Pages (Home, About, Services, Contact, Blog)', 'Mobile Responsive Design', 'Basic Astrology API Integration', 'Contact Form', 'WhatsApp Button', '1 Month Support'],
            },
            {
              name: 'Professional', color: '#7c3aed',
              usd: 1499, inr: 79999,
              features: ['10 Pages with Custom Design', 'Full API Integration (Charts, Horoscopes, AI)', 'Payment Gateway (Stripe/Razorpay)', 'User Login & Dashboard', 'Report Generation System', '3 Months Support', 'SEO Optimization'],
              highlight: true,
            },
            {
              name: 'Enterprise', color: '#eab308',
              usd: 4999, inr: 249999,
              features: ['Unlimited Pages', 'Custom Brand Identity', 'Full API Stack + Custom Endpoints', 'Multi-Payment Gateway', 'Advanced User Portal', 'Admin Dashboard', 'White-Label Mobile App (PWA)', '12 Months Premium Support', 'Priority Updates'],
            },
          ].map((p, i) => (
            <FadeIn key={p.name} delay={i * 0.1}>
              <div style={{
                background: 'var(--bg-card)',
                border: `1px solid ${p.highlight ? 'var(--accent-purple)' : 'var(--border-color)'}`,
                borderRadius: 'var(--radius-lg)', padding: 32, height: '100%',
                position: 'relative', overflow: 'hidden',
                boxShadow: p.highlight ? '0 0 60px rgba(124,58,237,0.12)' : 'none',
              }}>
                {p.highlight && (
                  <div style={{
                    position: 'absolute', top: 16, right: -28,
                    background: 'var(--gradient-primary)', color: '#fff',
                    fontSize: 10, fontWeight: 700, padding: '4px 36px',
                    transform: 'rotate(45deg)', textTransform: 'uppercase', letterSpacing: 1,
                  }}>Popular</div>
                )}
                <div style={{ fontSize: 13, fontWeight: 700, color: p.color, textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 16 }}>{p.name}</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 24 }}>
                  <span style={{ fontSize: 40, fontWeight: 900 }}>
                    {currency === 'usd' ? `$${p.usd.toLocaleString()}` : `₹${p.inr.toLocaleString()}`}
                  </span>
                  <span style={{ color: '#64748b', fontSize: 14 }}>one-time</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 28, flex: 1 }}>
                  {p.features.map((f) => (
                    <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: '#cbd5e1', lineHeight: 1.5 }}>
                      <Check size={15} color="#22c55e" style={{ flexShrink: 0, marginTop: 2 }} />
                      {f}
                    </div>
                  ))}
                </div>
                <a
                  href="https://wa.me/916239402519?text=Hi%20AstroVakta%2C%20I%20am%20interested%20in%20the%20custom%20website%20package"
                  target="_blank" rel="noopener noreferrer"
                >
                  <button style={{
                    width: '100%', padding: '14px 0', borderRadius: 12,
                    border: p.highlight ? 'none' : '1px solid var(--border-color)',
                    background: p.highlight ? 'var(--gradient-primary)' : 'transparent',
                    color: p.highlight ? '#fff' : '#e2e8f0',
                    fontWeight: 600, fontSize: 14, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}>
                    <MessageCircle size={16} /> Discuss on WhatsApp
                  </button>
                </a>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ HOW IT WORKS ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>How It Works</p>
          <h2 className="section-title">Three Steps to <span className="gradient-text">Cosmic Data</span></h2>
          <p className="section-subtitle">Get from zero to a working birth chart integration in under 5 minutes.</p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 32, maxWidth: 1000, margin: '0 auto' }}>
          {[
            { n: '01', title: 'Sign Up & Get Key', desc: 'Create a free account. You instantly get an API key with 100 calls/month \u2014 no credit card.', icon: Key },
            { n: '02', title: 'Call the API', desc: 'Send birth details (date, time, place) to any endpoint. Get charts, predictions, or AI readings in JSON.', icon: Terminal },
            { n: '03', title: 'Build Your App', desc: 'Integrate into astrology apps, SaaS platforms, wellness products, or research tools. Ship fast.', icon: Rocket },
          ].map((s, i) => (
            <FadeIn key={s.n} delay={i * 0.15}>
              <div style={{ textAlign: 'center', padding: '32px 20px' }}>
                <div style={{
                  fontSize: 48, fontWeight: 900, background: 'var(--gradient-primary)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                  lineHeight: 1, marginBottom: 20, opacity: 0.2,
                }}>{s.n}</div>
                <div style={{
                  width: 56, height: 56, borderRadius: 16,
                  background: 'rgba(124,58,237,0.12)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px',
                }}>
                  <s.icon size={26} color="#a78bfa" />
                </div>
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>{s.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: 15, lineHeight: 1.7 }}>{s.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ PRICING ═══════════ */}
      <section className="section" id="api-pricing">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>API Pricing</p>
          <h2 className="section-title">Start <span className="gradient-text">Free</span>, Scale When Ready</h2>
          <p className="section-subtitle">No credit card required. Upgrade when you need more.</p>
        </FadeIn>

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center',
            background: 'var(--bg-card)', borderRadius: 12,
            border: '1px solid var(--border-color)', padding: 4,
          }}>
            <button
              onClick={() => setCurrency('inr')}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '10px 20px', borderRadius: 10,
                border: 'none', background: currency === 'inr' ? 'var(--gradient-primary)' : 'transparent',
                color: currency === 'inr' ? '#fff' : '#94a3b8',
                fontWeight: 600, fontSize: 14, cursor: 'pointer',
              }}>
              <IndianRupee size={16} /> INR
            </button>
            <button
              onClick={() => setCurrency('usd')}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '10px 20px', borderRadius: 10,
                border: 'none', background: currency === 'usd' ? 'var(--gradient-primary)' : 'transparent',
                color: currency === 'usd' ? '#fff' : '#94a3b8',
                fontWeight: 600, fontSize: 14, cursor: 'pointer',
              }}>
              <DollarSign size={16} /> USD
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24, maxWidth: 960, margin: '0 auto' }}>
          {[
            {
              name: 'Free', usdPrice: 0, inrPrice: 0,
              limit: '500 calls/month',
              color: '#64748b',
              features: ['All 180+ endpoints', 'Birth charts & predictions', 'Divisional charts', 'AI chat (BYO key)', 'Community support'],
              cta: 'Get Started Free',
              highlight: false,
            },
            {
              name: 'Starter', usdPrice: 29, inrPrice: 1499,
              limit: '5,000 calls/month',
              color: '#3b82f6',
              features: ['Everything in Free', 'PDF report generation', 'Email support', 'Usage analytics', '1 API key'],
              cta: 'Start Free Trial',
              highlight: false,
            },
            {
              name: 'Pro', usdPrice: 99, inrPrice: 4999,
              limit: '50,000 calls/month',
              color: '#7c3aed',
              features: ['Everything in Starter', 'Priority support', '99.9% SLA', '10 API keys', 'Custom rate limits'],
              cta: 'Start Free Trial',
              highlight: true,
            },
            {
              name: 'Enterprise', usdPrice: null, inrPrice: null,
              limit: 'Unlimited calls',
              color: '#f59e0b',
              features: ['Everything in Pro', 'Dedicated infrastructure', 'Custom SLA', 'Phone support', 'On-premise deployment', 'Unlimited API keys'],
              cta: 'Contact Sales',
              highlight: false,
            },
          ].map((p, i) => (
            <FadeIn key={p.name} delay={i * 0.1}>
              <div style={{
                background: 'var(--bg-card)',
                border: `1px solid ${p.highlight ? 'var(--accent-purple)' : 'var(--border-color)'}`,
                borderRadius: 'var(--radius-lg)', padding: 32, height: '100%',
                position: 'relative', overflow: 'hidden',
                boxShadow: p.highlight ? '0 0 60px rgba(124,58,237,0.12)' : 'none',
              }}>
                {p.highlight && (
                  <div style={{
                    position: 'absolute', top: 16, right: -28,
                    background: 'var(--gradient-primary)', color: '#fff',
                    fontSize: 10, fontWeight: 700, padding: '4px 36px',
                    transform: 'rotate(45deg)', textTransform: 'uppercase', letterSpacing: 1,
                  }}>Popular</div>
                )}
                <div style={{ fontSize: 13, fontWeight: 700, color: p.color, textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 16 }}>{p.name}</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 8 }}>
                  <span style={{ fontSize: 44, fontWeight: 900 }}>
                    {p.usdPrice !== null
                      ? (currency === 'usd' ? `$${p.usdPrice}` : `₹${p.inrPrice}`)
                      : 'Custom'}
                  </span>
                  {p.usdPrice !== null && <span style={{ color: '#64748b', fontSize: 15 }}>/month</span>}
                </div>
                <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 24 }}>{p.limit}</p>
                {p.cta === 'Contact Sales' ? (
                  <a href="https://wa.me/916239402519?text=Hi%20AstroVakta%2C%20I%20am%20interested%20in%20the%20Enterprise%20plan" target="_blank" rel="noopener noreferrer">
                    <button style={{
                      width: '100%', padding: '12px 0', borderRadius: 12,
                      border: '1px solid var(--border-color)',
                      background: 'transparent', color: '#e2e8f0',
                      fontWeight: 600, fontSize: 14, cursor: 'pointer', marginBottom: 24,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    }}>
                      <MessageCircle size={16} /> {p.cta}
                    </button>
                  </a>
                ) : p.name === 'Free' ? (
                  <ClerkSignedOut>
                    <SignUpOrRegister mode="modal">
                      <button style={{
                        width: '100%', padding: '12px 0', borderRadius: 12,
                        border: p.highlight ? 'none' : '1px solid var(--border-color)',
                        background: p.highlight ? 'var(--gradient-primary)' : 'transparent',
                        color: p.highlight ? '#fff' : '#e2e8f0',
                        fontWeight: 600, fontSize: 14, cursor: 'pointer', marginBottom: 24,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                      }}>
                        {p.cta} <ArrowRight size={16} />
                      </button>
                    </SignUpOrRegister>
                  </ClerkSignedOut>
                ) : (
                  <Link to="/register">
                    <button style={{
                      width: '100%', padding: '12px 0', borderRadius: 12,
                      border: p.highlight ? 'none' : '1px solid var(--border-color)',
                      background: p.highlight ? 'var(--gradient-primary)' : 'transparent',
                      color: p.highlight ? '#fff' : '#e2e8f0',
                      fontWeight: 600, fontSize: 14, cursor: 'pointer', marginBottom: 24,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    }}>
                      {p.cta} <ArrowRight size={16} />
                    </button>
                  </Link>
                )}
                {p.features.map((feat) => (
                  <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', fontSize: 13, color: '#cbd5e1' }}>
                    <Check size={15} color="#22c55e" style={{ flexShrink: 0 }} />
                    {feat}
                  </div>
                ))}
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ API ENDPOINTS SHOWCASE ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>API Endpoints</p>
          <h2 className="section-title">Powerful & <span className="gradient-text">Comprehensive</span></h2>
          <p className="section-subtitle">Every aspect of Vedic astrology exposed through clean REST endpoints.</p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, maxWidth: 1100, margin: '0 auto' }}>
          {[
            { cat: 'Charts', items: ['Birth Chart', 'Navamsa (D9)', 'Hora (D2)', 'Sudarshana Chakra', 'Divisional D1-D60', 'Bhava Chalit', 'East / Grid / Moon'], color: '#7c3aed' },
            { cat: 'Predictions', items: ['Daily Horoscope', 'Weekly / Monthly', 'Yearly Forecast', 'Transit Analysis', 'Business Prediction', 'Education Prediction'], color: '#3b82f6' },
            { cat: 'Timing', items: ['Vimshottari Dasha', 'Chara Dasha', 'Yogini Dasha', 'Panchang', 'Muhurat', 'Varshaphal'], color: '#f59e0b' },
            { cat: 'Analysis', items: ['Compatibility', 'Dosha Detection', 'Yoga Detection', 'Shadbala', 'Ashtakavarga', 'Numerology'], color: '#ec4899' },
            { cat: 'AI & Reports', items: ['AI Chat', 'AI Interpretation', 'AI Horoscope Gen', 'PDF Reports', 'Gemstone Advisor', 'Career Analysis'], color: '#8b5cf6' },
            { cat: 'Infrastructure', items: ['JWT Auth', 'API Key Management', 'Rate Limiting', 'Admin Panel', 'Job Queue', 'Usage Analytics'], color: '#10b981' },
          ].map((g, i) => (
            <FadeIn key={g.cat} delay={i * 0.06}>
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 24, height: '100%',
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: g.color, textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 14 }}>{g.cat}</div>
                {g.items.map((item) => (
                  <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '5px 0', fontSize: 13, color: '#cbd5e1' }}>
                    <ChevronRight size={13} color={g.color} style={{ flexShrink: 0 }} />
                    {item}
                  </div>
                ))}
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ TESTIMONIALS ═══════════ */}
      <section className="section">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Testimonials</p>
          <h2 className="section-title">Loved by <span className="gradient-text">Developers</span></h2>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24, maxWidth: 1000, margin: '48px auto 0' }}>
          {[
            { quote: "AstroVakta replaced three separate APIs we were stitching together. The divisional charts alone saved us months of development.", name: 'Priya S.', role: 'CTO, ZodiacApp' },
            { quote: "The BYO AI provider feature is genius. We use Claude for detailed readings and Groq for quick summaries \u2014 all through one API.", name: 'Arjun M.', role: 'Founder, JyotishAI' },
            { quote: "Most astrology APIs give you raw data. AstroVakta gives you charts, predictions, AND PDF reports. It's a complete platform.", name: 'Sarah K.', role: 'Lead Dev, CosmicTech' },
          ].map((t, i) => (
            <FadeIn key={i} delay={i * 0.12}>
              <div className="card-glow" style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
              }}>
                <div style={{ display: 'flex', gap: 2, marginBottom: 16 }}>
                  {Array.from({ length: 5 }, (_, j) => (
                    <Star key={j} size={16} fill="#fbbf24" color="#fbbf24" />
                  ))}
                </div>
                <p style={{ color: '#cbd5e1', fontSize: 15, lineHeight: 1.7, marginBottom: 20, fontStyle: 'italic' }}>"{t.quote}"</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: 'var(--gradient-primary)', display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    fontSize: 16, fontWeight: 700, color: '#fff',
                  }}>{t.name[0]}</div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{t.name}</div>
                    <div style={{ color: '#64748b', fontSize: 12 }}>{t.role}</div>
                  </div>
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ COMPARISON TABLE ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Why AstroVakta</p>
          <h2 className="section-title">Compare with <span className="gradient-text">Alternatives</span></h2>
          <p className="section-subtitle">See how AstroVakta stacks up against popular astrology API providers.</p>
        </FadeIn>

        <FadeIn delay={0.15}>
          <div style={{ overflowX: 'auto', maxWidth: 1000, margin: '0 auto' }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, fontSize: 14 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '16px 20px', color: '#64748b', fontWeight: 600, fontSize: 13, textTransform: 'uppercase', letterSpacing: 0.5, borderBottom: '2px solid var(--border-color)', minWidth: 200 }}>Feature</th>
                  {['AstroVakta', 'AstroYogi API', 'Prokerala', 'ClickAstro'].map((name, i) => (
                    <th key={name} style={{
                      textAlign: 'center', padding: '16px 20px', fontWeight: 700,
                      fontSize: i === 0 ? 15 : 14, color: i === 0 ? '#a78bfa' : '#94a3b8',
                      borderBottom: `2px solid ${i === 0 ? 'var(--accent-purple)' : 'var(--border-color)'}`,
                      background: i === 0 ? 'rgba(124,58,237,0.05)' : 'transparent',
                    }}>
                      {i === 0 && <span style={{ display: 'inline-block', background: 'var(--gradient-primary)', color: '#fff', fontSize: 10, padding: '2px 8px', borderRadius: 8, fontWeight: 700, marginRight: 8, verticalAlign: 'middle' }}>US</span>}
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { f: 'Free Tier', a: '500 calls/month', b: 'Limited trial', c: '50 req/day', d: 'Paid only' },
                  { f: 'Total Endpoints', a: '180+', b: '~40', c: '~60', d: '~30' },
                  { f: 'Sidereal Engine', a: 'Swiss Ephemeris', b: 'Proprietary', c: 'Swiss Ephemeris', d: 'Proprietary' },
                  { f: 'Divisional Charts (D1-D60)', a: true, b: 'Partial', c: 'D9 only', d: false },
                  { f: 'Navamsa / Hora SVG', a: true, b: false, c: false, d: false },
                  { f: 'Sudarshana Chakra', a: true, b: false, c: false, d: false },
                  { f: 'AI Interpretations', a: 'BYO Key (4 providers)', b: 'Built-in (limited)', c: false, d: 'Built-in (basic)' },
                  { f: 'PDF Report Generation', a: '22-section branded', b: 'Basic PDF', c: false, d: 'Basic PDF' },
                  { f: 'Compatibility (Milan)', a: true, b: true, c: true, d: true },
                  { f: 'Dosha Analysis', a: '12+ doshas', b: '~5', c: '~6', d: '~4' },
                  { f: 'Panchang & Muhurat', a: true, b: true, c: true, d: 'Partial' },
                  { f: 'Vimshottari Dasha (4 levels)', a: true, b: '2 levels', c: '2 levels', d: '2 levels' },
                  { f: 'Developer Sandbox', a: true, b: false, c: false, d: false },
                  { f: 'Admin Panel & Analytics', a: true, b: false, c: false, d: false },
                  { f: 'Background Job Queue', a: 'Redis + Celery', b: 'Sync only', c: 'Sync only', d: 'Sync only' },
                  { f: 'OpenAPI / Swagger', a: true, b: false, c: 'Partial', d: false },
                  { f: 'AES Encrypted Keys', a: true, b: 'N/A', c: 'N/A', d: 'N/A' },
                  { f: 'Self-Hostable', a: true, b: false, c: false, d: false },
                  { f: 'Pricing (Pro)', a: '$29/mo', b: '$49/mo', c: '$39/mo', d: '$45/mo' },
                ].map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(124,58,237,0.08)' }}>
                    <td style={{ padding: '13px 20px', color: '#e2e8f0', fontWeight: 500, fontSize: 13 }}>{row.f}</td>
                    {[row.a, row.b, row.c, row.d].map((val, j) => (
                      <td key={j} style={{
                        textAlign: 'center', padding: '13px 16px', fontSize: 13,
                        color: j === 0 ? '#e2e8f0' : '#94a3b8',
                        fontWeight: j === 0 ? 600 : 400,
                        background: j === 0 ? 'rgba(124,58,237,0.04)' : 'transparent',
                      }}>
                        {val === true ? (
                          <span style={{ color: '#22c55e', fontWeight: 700 }}><Check size={16} style={{ display: 'inline' }} /></span>
                        ) : val === false ? (
                          <span style={{ color: '#475569' }}><XIcon size={16} style={{ display: 'inline' }} /></span>
                        ) : (
                          <span>{val}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </FadeIn>
      </section>

      {/* ═══════════ FINAL CTA ═══════════ */}
      <section className="section" style={{ textAlign: 'center' }}>
        <FadeIn>
          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, marginBottom: 24,
          }}>
            Start Building for <span className="gradient-text">Free</span>
          </h2>
          <p style={{ color: '#94a3b8', fontSize: 18, maxWidth: 500, margin: '0 auto 40px', lineHeight: 1.7 }}>
            No credit card required. 500 free API calls per month. Full access to all endpoints.
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <ClerkSignedOut>
              <SignUpOrRegister mode="modal">
                <button className="btn-primary" style={{ padding: '18px 48px', fontSize: 18 }}>
                  Get Your API Key <Sparkles size={20} />
                </button>
              </SignUpOrRegister>
            </ClerkSignedOut>
            <Link to="/sandbox">
              <button className="btn-secondary" style={{ padding: '18px 48px', fontSize: 18 }}>
                <Play size={18} /> Try the Sandbox
              </button>
            </Link>
          </div>
        </FadeIn>
      </section>

      {/* ═══════════ WHATSAPP FLOATING BUTTON ═══════════ */}
      <a
        href="https://wa.me/916239402519?text=Hi%20AstroVakta%2C%20I%20have%20a%20question"
        target="_blank"
        rel="noopener noreferrer"
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 1000,
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: '#25D366',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 20px rgba(37,211,102,0.4)',
          transition: 'transform 0.2s',
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
      >
        <MessageCircle size={28} color="#fff" />
      </a>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        style={{
          position: 'fixed', bottom: 24, right: 92, zIndex: 1000,
          color: '#94a3b8', fontSize: 12, fontWeight: 500,
          background: 'rgba(10,10,26,0.85)', padding: '8px 14px',
          borderRadius: 20, border: '1px solid rgba(124,58,237,0.15)',
          backdropFilter: 'blur(10px)',
        }}>
        Chat with us
      </motion.p>
    </div>
  )
}
