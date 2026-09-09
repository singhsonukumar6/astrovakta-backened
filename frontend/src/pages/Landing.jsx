import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useInView, useScroll, useTransform } from 'framer-motion'
import { useConfig } from '../lib/ConfigContext.jsx'
import {
  Sparkles, Globe, CalendarCheck, MessageCircle, Camera, ShoppingCart,
  Search, Check, ArrowRight, Star, Users, TrendingUp, Zap,
  MonitorSmartphone, HelpCircle, Globe2, BadgeCheck, ChevronRight,
  Store, Megaphone, BarChart3, Wand2, ChevronDown, Code2,
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
        background: 'radial-gradient(circle, rgba(79,70,229,0.10) 0%, rgba(124,58,237,0.05) 40%, transparent 70%)',
        filter: 'blur(40px)',
      }}
    />
  )
}

/* ── Mock browser: the branded website an astrologer gets in a few clicks ── */
function WebsiteMockup() {
  const [activeStep, setActiveStep] = useState(0)
  const steps = ['Your Website', 'Your Domain', 'Your Business']
  useEffect(() => {
    const t = setInterval(() => setActiveStep((s) => (s + 1) % steps.length), 2600)
    return () => clearInterval(t)
  }, [steps.length])

  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.7 }}
      style={{
        marginTop: 56, maxWidth: 680, width: '100%', margin: '56px auto 0', position: 'relative',
        background: '#ffffff', border: '1px solid rgba(124,58,237,0.25)',
        borderRadius: 16, overflow: 'hidden',
        boxShadow: '0 30px 80px rgba(15,23,42,0.12), 0 0 60px rgba(124,58,237,0.08)',
      }}>
      {/* browser chrome */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 16px', borderBottom: '1px solid rgba(124,58,237,0.12)' }}>
        <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#ef4444' }} />
        <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#d97706' }} />
        <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#16a34a' }} />
        <div style={{
          marginLeft: 10, flex: 1, display: 'flex', alignItems: 'center', gap: 6,
          background: 'rgba(124,58,237,0.08)', borderRadius: 8, padding: '5px 12px',
          fontSize: 12, color: '#475569', fontFamily: 'var(--font-mono)',
        }}>
          <Check size={12} color="#16a34a" />
          {activeStep === 0 ? 'astrovakra.example.com' : activeStep === 1 ? 'www.astrovakra.com' : 'book.astrovakra.com'}
        </div>
      </div>

      {/* fake site content */}
      <div style={{ padding: '22px 26px 26px', minHeight: 300 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 22, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Star size={16} color="#fff" />
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 800, color: '#0f172a' }}>AstroVakra</div>
              <div style={{ fontSize: 9, color: '#64748b' }}>Vedic Astrology · Since 1998</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 14, fontSize: 11, color: '#475569' }}>
            <span>Home</span><span>Services</span><span>Book</span><span>Shop</span><span>Blog</span>
          </div>
        </div>

        <AnimatePresenceStep activeStep={activeStep} />

        <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
          <div style={{ flex: 1, background: 'var(--gradient-primary)', borderRadius: 8, padding: '8px 0', fontSize: 11, fontWeight: 700, color: '#fff', textAlign: 'center' }}>Book Consultation</div>
          <div style={{ flex: 1, border: '1px solid rgba(124,58,237,0.3)', borderRadius: 8, padding: '8px 0', fontSize: 11, fontWeight: 600, color: '#1e293b', textAlign: 'center' }}>Free Kundli</div>
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          {[CalendarCheck, MessageCircle, Camera, ShoppingCart, Search].map((Icon, i) => (
            <motion.div key={i}
              animate={{ opacity: [0.35, 1, 0.35] }}
              transition={{ duration: 2.4, repeat: Infinity, delay: i * 0.3 }}
              style={{
                flex: 1, border: '1px solid rgba(124,58,237,0.2)', borderRadius: 8,
                padding: '7px 0', display: 'flex', justifyContent: 'center', background: 'rgba(124,58,237,0.05)',
              }}>
              <Icon size={14} color="#4f46e5" />
            </motion.div>
          ))}
        </div>
      </div>

      {/* step labels */}
      <div style={{
        position: 'absolute', bottom: -14, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', gap: 4, background: '#ffffff', border: '1px solid rgba(124,58,237,0.25)',
        borderRadius: 20, padding: '4px 6px',
      }}>
        {steps.map((_, i) => (
          <div key={i} style={{
            width: i === activeStep ? 22 : 8, height: 8, borderRadius: 4,
            background: i === activeStep ? '#4f46e5' : 'rgba(124,58,237,0.3)',
            transition: 'all 0.4s ease',
          }} />
        ))}
      </div>
    </motion.div>
  )
}

function AnimatePresenceStep({ activeStep }) {
  const contents = [
    {
      title: 'Pandit Rajesh Vakra',
      subtitle: 'Vedic Astrologer · 25,000+ consultations',
      body: 'Get your complete Vedic kundli, career & marriage guidance, dosha remedies — online and in person.',
      badge: 'Your website is live in minutes',
    },
    {
      title: 'www.astrovakra.com',
      subtitle: 'Your own domain, your own brand',
      body: 'Connect any domain you own in one click. Free SSL, automatic HTTPS, lightning-fast global hosting.',
      badge: 'Your domain — live',
    },
    {
      title: 'Your complete business',
      subtitle: 'Bookings · Payments · WhatsApp · Social',
      body: 'Appointments with reminders, online payments, WhatsApp alerts, Instagram posts, products store — all in one dashboard.',
      badge: 'Everything managed for you',
    },
  ]
  const c = contents[activeStep]
  return (
    <motion.div
      key={activeStep}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 12px', borderRadius: 16,
        background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.3)',
        fontSize: 10, fontWeight: 700, color: '#16a34a', marginBottom: 14,
      }}>
        <BadgeCheck size={12} /> {c.badge}
      </div>
      <h3 style={{ fontSize: 24, fontWeight: 900, color: '#0f172a', marginBottom: 4, letterSpacing: '-0.5px' }}>{c.title}</h3>
      <p style={{ fontSize: 12, color: '#4f46e5', fontWeight: 600, marginBottom: 10 }}>{c.subtitle}</p>
      <p style={{ fontSize: 13, color: '#475569', lineHeight: 1.7, maxWidth: 440 }}>{c.body}</p>
    </motion.div>
  )
}

/* ── Phone mockup showing the booking + WhatsApp flow ── */
function PhoneMockup({ floating = false }) {
  return (
    <div style={{
      width: '100%', maxWidth: 250, borderRadius: 28, border: '1px solid rgba(124,58,237,0.3)',
      background: 'linear-gradient(180deg, #ffffff, #f8fafc)',
      padding: 12, boxShadow: '0 24px 60px rgba(15,23,42,0.12)',
      position: floating ? 'absolute' : 'relative',
      right: floating ? 0 : undefined, bottom: floating ? 24 : undefined,
      zIndex: floating ? 2 : undefined,
    }}>
      <div style={{ background: '#ffffff', borderRadius: 18, overflow: 'hidden', border: '1px solid rgba(124,58,237,0.15)' }}>
        {/* notch */}
        <div style={{ display: 'flex', justifyContent: 'center', padding: '6px 0' }}>
          <div style={{ width: 60, height: 4, borderRadius: 4, background: 'rgba(124,58,237,0.4)' }} />
        </div>
        <div style={{ padding: '4px 12px 14px' }}>
          <div style={{ fontSize: 10, color: '#64748b', marginBottom: 8 }}>Today · 3 slots left</div>
          {[['Mon', '09:00 AM', true], ['Mon', '11:30 AM', false], ['Mon', '04:00 PM', true]].map(([d, t, free], i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              border: `1px solid ${free ? 'rgba(34,197,94,0.25)' : 'rgba(124,58,237,0.15)'}`,
              borderRadius: 10, padding: '7px 10px', marginBottom: 6,
              background: free ? 'rgba(34,197,94,0.06)' : 'transparent',
            }}>
              <span style={{ fontSize: 11, color: '#334155' }}>{t}</span>
              <span style={{ fontSize: 9, fontWeight: 700, color: free ? '#16a34a' : '#64748b' }}>
                {free ? 'Book' : 'Full'}
              </span>
            </div>
          ))}
          <div style={{
            marginTop: 8, background: 'var(--gradient-primary)', borderRadius: 10,
            padding: '8px 0', textAlign: 'center', fontSize: 11, fontWeight: 700, color: '#fff',
          }}>Confirm · ₹499</div>
          <div style={{
            marginTop: 10, display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(37,211,102,0.1)', border: '1px solid rgba(37,211,102,0.3)',
            borderRadius: 10, padding: '7px 10px',
          }}>
            <MessageCircle size={13} color="#25D366" />
            <div>
              <div style={{ fontSize: 9, color: '#25D366', fontWeight: 700 }}>WhatsApp reminder sent</div>
              <div style={{ fontSize: 8, color: '#475569' }}>Your slot is confirmed for Mon 09:00</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Landing() {
  const { scrollYProgress } = useScroll()
  const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -80])
  const [openFaq, setOpenFaq] = useState(null)
  const { config } = useConfig()

  return (
    <div style={{ overflow: 'hidden' }}>

      {/* ═══════════ HERO ═══════════ */}
      <section style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center',
        justifyContent: 'center', textAlign: 'center',
        padding: '140px 24px 100px', position: 'relative',
      }}>
        <GlowOrb />

        <motion.div style={{ y: heroY, maxWidth: 900, position: 'relative', zIndex: 1 }}>
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '8px 18px', borderRadius: 24,
              background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.25)',
              marginBottom: 32, fontSize: 13, color: '#4f46e5', fontWeight: 600,
            }}>
            <Wand2 size={14} /> No coding · No designers · No agencies
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            style={{
              fontSize: 'clamp(38px, 6.5vw, 72px)', fontWeight: 900,
              lineHeight: 1.08, marginBottom: 24, letterSpacing: '-1.5px',
              color: '#0f172a',
            }}>
            Your Complete Astrology Business,
            <span className="gradient-text" style={{ display: 'block' }}>Live in a Few Clicks</span>
          </motion.h1>

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            style={{
              fontSize: 'clamp(16px, 2vw, 20px)', color: '#475569',
              maxWidth: 660, margin: '0 auto 44px', lineHeight: 1.75,
            }}>
            AstroVakta gives every astrologer a beautiful branded website with your own domain —
            plus appointment booking, WhatsApp alerts, online payments, social media management,
            an online store, and complete SEO. <strong style={{ color: '#1e293b' }}>Built for astrologers, not programmers.</strong>
          </motion.p>

          <motion.div id="start-free" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/mysite">
              <button className="btn-primary" style={{ padding: '16px 40px', fontSize: 16 }}>
                <Sparkles size={18} /> Create Your Website — Free
              </button>
            </Link>
            <Link to="/pricing">
              <button className="btn-secondary" style={{ padding: '16px 40px', fontSize: 16 }}>
                See Plans <ArrowRight size={18} />
              </button>
            </Link>
          </motion.div>

          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
            style={{ color: '#64748b', fontSize: 13, marginTop: 16 }}>
            Free subdomain included · Connect your own domain anytime · No credit card required
          </motion.p>

          <WebsiteMockup />
        </motion.div>
      </section>

      {/* ═══════════ STATS BAR ═══════════ */}
      <section style={{ padding: '48px 24px', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 32, maxWidth: 1000, margin: '0 auto' }}>
          {[
            { v: 216, s: '+', l: 'Astrology Calculations' },
            { v: 9, s: '', l: 'Indian Languages' },
            { v: 30, s: 's', l: 'Website Setup Time' },
            { v: 100, s: '%', l: 'Mobile Responsive' },
            { v: 24, s: '/7', l: 'Hosting & Security' },
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

      {/* ═══════════ THE PROBLEM ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>The Old Way</p>
          <h2 className="section-title">Building Your Online Presence <span className="gradient-text">Shouldn't Be This Hard</span></h2>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24, maxWidth: 1000, margin: '0 auto' }}>
          <FadeIn>
            <div style={{
              background: 'var(--bg-card)', border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
            }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#dc2626', marginBottom: 20 }}>❌ The DIY / Agency Route</h3>
              {[
                'Hire a web agency: ₹30,000–₹2,00,000 + weeks of back-and-forth',
                'A developer for the booking system: another ₹50,000+',
                'Separate tools for WhatsApp, Instagram, payments, SEO — all stitched together',
                'Every small change needs another call, another invoice',
                'Hosting, SSL, backups, speed — your problem forever',
              ].map((item) => (
                <div key={item} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 0', fontSize: 14, color: '#475569', lineHeight: 1.6 }}>
                  <span style={{ color: '#ef4444', fontWeight: 700, flexShrink: 0 }}>✗</span> {item}
                </div>
              ))}
            </div>
          </FadeIn>
          <FadeIn delay={0.12}>
            <div style={{
              background: 'var(--bg-card)', border: '1px solid rgba(34,197,94,0.25)',
              borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
              boxShadow: '0 0 40px rgba(34,197,94,0.06)',
            }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#4ade80', marginBottom: 20 }}>✓ The AstroVakta Way</h3>
              {[
                'Sign up, pick a template, add your name & photo — site is live in ~30 seconds',
                'Booking, payments, WhatsApp, store, SEO: built in from day one',
                'Connect your own domain in one click — free SSL included',
                'Change anything yourself: text, colors, services, prices — no developer',
                'Hosting, security, speed, backups: all handled for you',
              ].map((item) => (
                <div key={item} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 0', fontSize: 14, color: '#334155', lineHeight: 1.6 }}>
                  <Check size={16} color="#16a34a" style={{ flexShrink: 0, marginTop: 3 }} /> {item}
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════ EVERYTHING YOU GET ═══════════ */}
      <section className="section" id="features">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Everything You Get</p>
          <h2 className="section-title">A Complete Business, <span className="gradient-text">Not Just a Website</span></h2>
          <p className="section-subtitle">
            Everything an astrology practice needs online — one platform, one dashboard, one bill.
          </p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
          {[
            { icon: Globe, title: 'Branded Website + Your Own Domain', desc: 'A gorgeous mobile-first website with your name, photo, services and testimonials. Start on a free subdomain, connect your own domain in one click — free SSL and HTTPS included.', color: '#7c3aed' },
            { icon: CalendarCheck, title: 'Appointment Booking', desc: 'Your clients see real-time availability and book consultations in 60 seconds. Automatic confirmations, reminders before every appointment, and rescheduling without phone tag.', color: '#2563eb' },
            { icon: MessageCircle, title: 'WhatsApp Alerts', desc: 'Every booking, payment and reminder automatically reaches your clients on WhatsApp — the channel Indians actually read. No-shows drop dramatically.', color: '#16a34a' },
            { icon: Search, title: 'Complete SEO, Done For You', desc: 'Google-optimized pages out of the box: meta tags, sitemap, fast loading, structured data. Clients searching "astrologer near me" or "kundli online" find you.', color: '#d97706' },
            { icon: ShoppingCart, title: 'Online Store (Ecommerce)', desc: 'Sell gemstones, rudraksha, puja items and reports online with built-in payments and inventory. Your products, your prices, your margins.', color: '#db2777' },
            { icon: Camera, title: 'Instagram & Social Management', desc: 'Auto-publish daily horoscopes, festival posts and reels to Instagram and other social networks — a steady content calendar that grows your following.', color: '#7c3aed' },
            { icon: Sparkles, title: 'Free Kundli & Astrology Tools', desc: 'Give visitors free kundli, matching, panchang and daily horoscope tools powered by our 216+ endpoint engine. Free tools = more traffic, more leads.', color: '#06b6d4' },
            { icon: Store, title: 'Payments & Orders', desc: 'Accept UPI, cards and netbanking for consultations, reports and products. Track every order, invoice and payment in one place.', color: '#10b981' },
            { icon: BarChart3, title: 'Client & Business Dashboard', desc: 'See appointments, revenue, top services and website visitors at a glance. Understand your business like never before.', color: '#4f46e5' },
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
                <p style={{ color: '#475569', fontSize: 14, lineHeight: 1.7 }}>{f.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ HOW IT WORKS ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }} id="how-it-works">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>How It Works</p>
          <h2 className="section-title">Live in <span className="gradient-text">3 Simple Steps</span></h2>
          <p className="section-subtitle">No coding. No designers. No waiting.</p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 32, maxWidth: 1000, margin: '0 auto' }}>
          {[
            { n: '01', title: 'Sign Up & Pick Your Style', desc: 'Create your free account and choose from beautiful astrology templates. Add your name, photo, services and prices — a simple form, like filling a WhatsApp profile.', icon: Wand2 },
            { n: '02', title: 'Your Site Goes Live Instantly', desc: 'You get a free subdomain (you.astrovakta.com) immediately. Add your domain — astrovakra.com — whenever you\'re ready with one click. SSL and hosting are on us.', icon: Globe2 },
            { n: '03', title: 'Run Your Entire Business', desc: 'Accept bookings, get paid, chat on WhatsApp, publish to Instagram, sell products — all from one simple dashboard on your phone or laptop.', icon: TrendingUp },
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
                  <s.icon size={26} color="#4f46e5" />
                </div>
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>{s.title}</h3>
                <p style={{ color: '#475569', fontSize: 15, lineHeight: 1.7 }}>{s.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.2}>
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Link to="/mysite">
              <button className="btn-primary" style={{ padding: '14px 36px', fontSize: 15 }}>
                <Zap size={18} /> Start Step 1 Now — Free
              </button>
            </Link>
          </div>
        </FadeIn>
      </section>

      {/* ═══════════ BOOKING + WHATSAPP SHOWCASE ═══════════ */}
      <section className="section">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 64, alignItems: 'center', maxWidth: 1000, margin: '0 auto' }}>
          <FadeIn direction="right">
            <p style={{ color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Bookings & WhatsApp</p>
            <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 20, letterSpacing: '-0.5px', lineHeight: 1.15 }}>
              Clients Book in Seconds.<br /><span className="gradient-text">You Never Miss One.</span>
            </h2>
            <p style={{ color: '#475569', fontSize: 16, lineHeight: 1.8, marginBottom: 28 }}>
              Share one link — on Instagram, WhatsApp, or your visiting card. Your clients pick a slot,
              pay online if you want, and everything else is automatic.
            </p>
            {[
              'Real-time availability — no double bookings, ever',
              'Instant WhatsApp confirmation when a slot is booked',
              'Automatic reminders 24 hours and 1 hour before',
              'Payments collected at booking — no-shows eliminated',
              'Daily summary of tomorrow\'s appointments on WhatsApp',
            ].map((item) => (
              <div key={item} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '7px 0', fontSize: 15, color: '#334155' }}>
                <Check size={17} color="#16a34a" style={{ flexShrink: 0 }} /> {item}
              </div>
            ))}
          </FadeIn>
          <FadeIn direction="left" delay={0.15}>
            <div style={{ display: 'flex', justifyContent: 'center', position: 'relative', minHeight: 380 }}>
              <PhoneMockup />
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ═══════════ SEO + SOCIAL SHOWCASE ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 64, alignItems: 'center', maxWidth: 1000, margin: '0 auto' }}>
          <FadeIn direction="right" delay={0.15}>
            <div style={{ position: 'relative', minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {/* Google search result mock */}
              <div style={{
                width: '100%', maxWidth: 420, background: '#fff', borderRadius: 12,
                padding: '20px 22px', fontFamily: 'Arial, sans-serif',
                boxShadow: '0 24px 60px rgba(15,23,42,0.14)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'linear-gradient(135deg,#7c3aed,#db2777)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: '#fff', fontWeight: 700 }}>A</div>
                  <div>
                    <div style={{ fontSize: 13, color: '#202124' }}>AstroVakra</div>
                    <div style={{ fontSize: 11, color: '#5f6368' }}>https://astrovakra.com</div>
                  </div>
                </div>
                <div style={{ fontSize: 17, color: '#1a0dab', marginBottom: 4, fontWeight: 500 }}>Best Astrologer in Jaipur — Kundli, Match...</div>
                <div style={{ fontSize: 12, color: '#4d5156', lineHeight: 1.6 }}>
                  Pandit Rajesh Vakra — 25,000+ consultations. Online kundli, matching & consultation.
                  Book on WhatsApp. ⭐ 4.9 (312 reviews)…
                </div>
                <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                  {['★ 4.9 rating', '300+ reviews', 'Accepts online booking'].map((b) => (
                    <span key={b} style={{ fontSize: 9, background: '#f1f3f4', color: '#3c4043', borderRadius: 10, padding: '3px 8px', fontWeight: 600 }}>{b}</span>
                  ))}
                </div>
              </div>
            </div>
          </FadeIn>
          <FadeIn direction="left">
            <p style={{ color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>SEO & Social Media</p>
            <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 20, letterSpacing: '-0.5px', lineHeight: 1.15 }}>
              Get Found on Google.<br /><span className="gradient-text">Stay Famous on Instagram.</span>
            </h2>
            <p style={{ color: '#475569', fontSize: 16, lineHeight: 1.8, marginBottom: 28 }}>
              When someone searches "astrologer in <em>your city</em>" or "online kundli", your website is
              technically perfect for Google — automatically. Meanwhile your social feeds stay active
              without you lifting a finger.
            </p>
            {[
              { icon: Search, text: 'Google-optimized pages, sitemap, schema markup — all automatic' },
              { icon: Megaphone, text: 'Auto-post daily horoscopes & festival greetings to Instagram' },
              { icon: MonitorSmartphone, text: 'Perfect score on Google PageSpeed — site loads instantly' },
              { icon: Globe, text: 'Built-in Hindi + 8 regional languages for wider reach' },
            ].map((item) => (
              <div key={item.text} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '8px 0', fontSize: 15, color: '#334155' }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(124,58,237,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <item.icon size={16} color="#4f46e5" />
                </div>
                {item.text}
              </div>
            ))}
          </FadeIn>
        </div>
      </section>

      {/* ═══════════ WHAT'S INSIDE YOUR WEBSITE ═══════════ */}
      <section className="section">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Powered by AstroVakta</p>
          <h2 className="section-title">Your Site Includes <span className="gradient-text">Every Astrology Tool</span></h2>
          <p className="section-subtitle">
            The same engine behind our 216+ endpoint professional API runs your website's tools — the most complete Vedic astrology platform in India.
          </p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20, maxWidth: 1100, margin: '0 auto' }}>
          {[
            { cat: 'Kundli & Charts', items: ['Full Kundli (Birth Chart)', 'North & South Indian styles', 'Divisional Charts (D1–D60)', 'Online PDF Kundli download'], color: '#7c3aed' },
            { cat: 'Matching', items: ['Kundali Milan (Guna)', 'Mangal Dosha check', 'Nadi Dosha analysis', 'Marriage compatibility report'], color: '#db2777' },
            { cat: 'Daily Content', items: ['Daily horoscope (raashi fal)', 'Panchang & festivals', 'Muhurat timings', 'Today\'s lucky color & number'], color: '#d97706' },
            { cat: 'Advanced Tools', items: ['Vimshottari Dasha', 'Sade Sati calculator', 'Gemstone & Rudraksha advisor', 'Lal Kitab remedies'], color: '#06b6d4' },
          ].map((g, i) => (
            <FadeIn key={g.cat} delay={i * 0.06}>
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 24, height: '100%',
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: g.color, textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 14 }}>{g.cat}</div>
                {g.items.map((item) => (
                  <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '5px 0', fontSize: 13, color: '#334155' }}>
                    <ChevronRight size={13} color={g.color} style={{ flexShrink: 0 }} />
                    {item}
                  </div>
                ))}
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.15}>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 14, marginTop: 32 }}>
            Want the raw API behind these tools instead?{' '}
            <Link to="/developer" style={{ color: '#4f46e5', fontWeight: 600 }}>
              Visit our developer portal <ArrowRight size={13} style={{ display: 'inline', verticalAlign: 'middle' }} />
            </Link>
          </p>
        </FadeIn>
      </section>

      {/* ═══════════ FOR EVERY KIND OF ASTROLOGER ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Built For You</p>
          <h2 className="section-title">For Every Kind of <span className="gradient-text">Astrology Practice</span></h2>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24, maxWidth: 1100, margin: '0 auto' }}>
          {[
            { icon: Star, title: 'Independent Astrologers', desc: 'Take your practice online without depending on marketplaces that take 40–60% commission. Your clients, your brand, your pricing.', color: '#7c3aed' },
            { icon: Users, title: 'Astrology Centers', desc: 'Multiple astrologers, one branded website. Manage everyone\'s calendars, services and payouts from a single dashboard.', color: '#2563eb' },
            { icon: Store, title: 'Gemstone & Puja Sellers', desc: 'Sell online with a full ecommerce store — catalog, cart, payments, orders — plus astrology content that attracts buyers.', color: '#db2777' },
            { icon: TrendingUp, title: 'Content Creators', desc: 'Growing on Instagram or YouTube? Convert followers into paying clients with a professional booking site.', color: '#10b981' },
          ].map((u, i) => (
            <FadeIn key={u.title} delay={i * 0.08}>
              <motion.div whileHover={{ y: -4 }} className="card-glow" style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
              }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14,
                  background: `${u.color}18`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 16,
                }}>
                  <u.icon size={24} color={u.color} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{u.title}</h3>
                <p style={{ color: '#475569', fontSize: 14, lineHeight: 1.7 }}>{u.desc}</p>
              </motion.div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ TESTIMONIALS ═══════════ */}
      <section className="section">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>Testimonials</p>
          <h2 className="section-title">Astrologers <span className="gradient-text">Love AstroVakta</span></h2>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24, maxWidth: 1000, margin: '48px auto 0' }}>
          {[
            { quote: "I used to pay an agency ₹8,000 every time I wanted to change a price on my website. Now I do it myself in 30 seconds. Bookings doubled in 3 months.", name: 'Pandit Rajesh S.', role: 'Vedic Astrologer, Jaipur', stat: '2x bookings in 3 months' },
            { quote: "The WhatsApp reminders alone are worth it. Earlier 3–4 clients out of 10 wouldn't show up. Now almost everyone arrives on time with payment already done.", name: 'Sunita M.', role: 'Tarot & Vedic Astrologer, Pune', stat: 'No-shows down 80%' },
            { quote: "Clients from Instagram used to DM and ask a hundred questions. Now my link has prices, slots and instant booking. I just wake up to confirmed appointments.", name: 'Acharya Vikram', role: 'Astro-content creator, 180k followers', stat: 'Zero DM back-and-forth' },
          ].map((t, i) => (
            <FadeIn key={i} delay={i * 0.12}>
              <div className="card-glow" style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 28, height: '100%',
              }}>
                <div style={{ display: 'flex', gap: 2, marginBottom: 14 }}>
                  {Array.from({ length: 5 }, (_, j) => (
                    <Star key={j} size={16} fill="#d97706" color="#d97706" />
                  ))}
                </div>
                <p style={{ color: '#334155', fontSize: 15, lineHeight: 1.7, marginBottom: 16, fontStyle: 'italic' }}>"{t.quote}"</p>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px',
                  borderRadius: 16, background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)',
                  fontSize: 11, fontWeight: 700, color: '#16a34a', marginBottom: 18,
                }}>
                  <TrendingUp size={12} /> {t.stat}
                </div>
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
        <FadeIn delay={0.2}>
          <p style={{ textAlign: 'center', color: '#475569', fontSize: 12, marginTop: 24, fontStyle: 'italic' }}>
            Early-access feedback from our pilot astrologers.
          </p>
        </FadeIn>
      </section>

      {/* ═══════════ FAQ ═══════════ */}
      <section className="section" style={{ background: 'var(--bg-secondary)' }} id="faq">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>FAQ</p>
          <h2 className="section-title">Frequently <span className="gradient-text">Asked Questions</span></h2>
        </FadeIn>

        <div style={{ maxWidth: 800, margin: '48px auto 0' }}>
          {[
            { q: 'I am not technical at all. Can I really do this myself?', a: 'Yes — that is exactly who we built this for. If you can use WhatsApp, you can use AstroVakta. You fill simple forms (your name, photo, services, prices) and pick a design. Everything else — hosting, security, speed, backups — is handled automatically. And if you ever get stuck, our support chat in Hindi and English is one tap away.' },
            { q: 'Do I really get my own domain?', a: 'Yes. You start immediately on a free subdomain (yourname.astrovakta.com). When you\'re ready, connect your own domain — like astrovakra.com — in one click from your dashboard. If you don\'t own a domain yet, we\'ll help you buy one and connect it. Free SSL (the padlock icon) is included automatically.' },
            { q: 'Will my website show up on Google?', a: 'Yes — your site is built SEO-first: proper page titles, meta descriptions, sitemap, structured data (star ratings, business info) and near-perfect Google PageSpeed scores. Clients searching for "astrologer near me", "online kundli" and similar phrases will find you. You can also add your Google Business Profile for local search.' },
            { q: 'How do bookings and WhatsApp alerts work?', a: 'You set your working hours and services. Clients see only your free slots, book, and (optionally) pay online. They instantly get a WhatsApp confirmation, then automatic reminders before the appointment. You get a daily summary of the next day\'s bookings. No app to install, no manual follow-ups.' },
            { q: 'Can I sell gemstones and other products on my site?', a: 'Yes — every plan includes a full online store: product catalog with photos, prices, cart, UPI/card/netbanking payments and order tracking. Gemstones, rudraksha, puja kits, reports — whatever you sell, you can list it in minutes.' },
            { q: 'How does the Instagram / social media feature work?', a: 'Our engine auto-generates daily horoscope posts, festival greetings and panchang updates in your branding. You approve them (or let them auto-publish on a schedule you choose) and they go out to your Instagram and other connected social accounts — so your profile stays active and professional even when you\'re busy with consultations.' },
            { q: 'What do I need to get started?', a: 'Just your phone. Sign up free, fill in your details, pick a template — your site is live in about 30 seconds. You can add your photo, services, pricing, domain, and products whenever you like. No documents, no developer, no credit card to start.' },
            { q: 'Can the free tools like kundli really be free on my site?', a: 'Yes. Your website includes unlimited free kundli, matching, panchang and daily horoscope tools powered by our astrology engine (the same one behind our professional API with 216+ endpoints). Free tools bring visitors from Google — visitors become clients.' },
            { q: 'I am a developer and want the API instead. Where do I go?', a: 'We built a whole portal just for you: 216+ REST endpoints, an interactive sandbox, and complete documentation with free API calls every month. Visit our developer portal at astrovakta.com/developer.' },
          ].map((faq, i) => (
            <FadeIn key={i} delay={i * 0.05}>
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', marginBottom: 14, overflow: 'hidden',
              }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: '100%', display: 'flex', gap: 12, alignItems: 'center',
                    padding: '20px 24px', textAlign: 'left', background: 'transparent',
                    color: 'inherit',
                  }}>
                  <HelpCircle size={20} color="#7c3aed" style={{ flexShrink: 0 }} />
                  <span style={{ fontSize: 16, fontWeight: 600, flex: 1 }}>{faq.q}</span>
                  <ChevronDown size={18} color="#64748b" style={{
                    transform: openFaq === i ? 'rotate(180deg)' : 'none',
                    transition: 'transform 0.3s ease', flexShrink: 0,
                  }} />
                </button>
                <motion.div
                  initial={false}
                  animate={{ height: openFaq === i ? 'auto' : 0, opacity: openFaq === i ? 1 : 0 }}
                  transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  style={{ overflow: 'hidden' }}>
                  <p style={{ color: '#475569', fontSize: 14, lineHeight: 1.75, padding: '0 24px 22px 56px' }}>{faq.a}</p>
                </motion.div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ═══════════ FINAL CTA ═══════════ */}
      <section className="section" style={{ textAlign: 'center' }}>
        <FadeIn>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, marginBottom: 20 }}>
            Your Clients Are Already<br />Searching for You <span className="gradient-text">Online</span>
          </h2>
          <p style={{ color: '#475569', fontSize: 18, maxWidth: 520, margin: '0 auto 40px', lineHeight: 1.7 }}>
            Create your complete astrology website and business system today. Free to start, live in minutes.
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/mysite">
              <button className="btn-primary" style={{ padding: '18px 48px', fontSize: 18 }}>
                Create Your Website — Free <Sparkles size={20} />
              </button>
            </Link>
            <a href="https://wa.me/916239402519?text=Hi%20AstroVakta%2C%20I%20am%20an%20astrologer%20and%20want%20my%20own%20website" target="_blank" rel="noopener noreferrer">
              <button className="btn-secondary" style={{ padding: '18px 48px', fontSize: 18 }}>
                <MessageCircle size={18} /> Talk to Us on WhatsApp
              </button>
            </a>
          </div>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 20 }}>
            Are you a developer?{' '}
            <Link to="/developer" style={{ color: '#4f46e5', fontWeight: 600 }}>
              Explore the AstroVakta API <Code2 size={13} style={{ display: 'inline', verticalAlign: 'middle' }} />
            </Link>
          </p>
        </FadeIn>
      </section>

      {/* ═══════════ WHATSAPP FLOATING BUTTON ═══════════ */}
      <a
        href="https://wa.me/916239402519?text=Hi%20AstroVakta%2C%20I%20have%20a%20question%20about%20creating%20my%20astrology%20website"
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
        onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.1)')}
        onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
      >
        <MessageCircle size={28} color="#fff" />
      </a>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        style={{
          position: 'fixed', bottom: 24, right: 92, zIndex: 1000,
          color: '#475569', fontSize: 12, fontWeight: 500,
          background: 'rgba(255,255,255,0.85)', padding: '8px 14px',
          borderRadius: 20, border: '1px solid rgba(124,58,237,0.15)',
          backdropFilter: 'blur(10px)',
        }}>
        Chat with us
      </motion.p>
    </div>
  )
}
