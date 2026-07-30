import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Star, Zap, Globe, Shield, Target, Users } from 'lucide-react'

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

export default function About() {
  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section">
        <FadeIn>
          <p style={{ textAlign: 'center', color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, marginBottom: 12, fontWeight: 600 }}>About Us</p>
          <h1 style={{ fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 900, textAlign: 'center', marginBottom: 20, letterSpacing: '-1px' }}>
            Powering the Future of <span className="gradient-text">Vedic Astrology</span>
          </h1>
          <p style={{ color: '#94a3b8', fontSize: 18, textAlign: 'center', maxWidth: 700, margin: '0 auto 60px', lineHeight: 1.8 }}>
            AstroVakta started with a simple idea: make accurate Vedic astrology accessible to every developer.
            What began as an internal tool is now a comprehensive API platform serving thousands of requests daily.
          </p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 24, maxWidth: 1000, margin: '0 auto 80px' }}>
          {[
            { icon: Target, title: 'Our Mission', desc: 'To democratize Vedic astrology by providing the most accurate, developer-friendly API on the planet. We believe astrology should be accessible, programmable, and infinitely scalable.', color: '#7c3aed' },
            { icon: Globe, title: 'Our Reach', desc: 'Developers across 15+ countries use AstroVakta to build astrology apps, matrimony platforms, wellness tools, and research platforms. Every request is powered by Swiss Ephemeris precision.', color: '#3b82f6' },
            { icon: Shield, title: 'Our Promise', desc: 'Enterprise-grade security with AES-256 encryption, 99.9% uptime SLA, and a commitment to never log or mine your data. Your API keys and user data are always yours.', color: '#10b981' },
          ].map((v, i) => (
            <FadeIn key={v.title} delay={i * 0.1}>
              <div className="card-glow" style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 32, height: '100%',
              }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14,
                  background: `${v.color}18`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 20,
                }}>
                  <v.icon size={24} color={v.color} />
                </div>
                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 10 }}>{v.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7 }}>{v.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.2}>
          <h2 style={{ fontSize: 28, fontWeight: 800, textAlign: 'center', marginBottom: 48 }}>
            The <span className="gradient-text">Numbers</span> Speak
          </h2>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 32, maxWidth: 900, margin: '0 auto' }}>
          {[
            { n: '180+', l: 'API Endpoints' },
            { n: '16', l: 'Chart Types' },
            { n: '15+', l: 'Countries Served' },
            { n: '99.9%', l: 'Uptime SLA' },
          ].map((stat, i) => (
            <FadeIn key={stat.l} delay={i * 0.1}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 44, fontWeight: 900, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', lineHeight: 1.2 }}>
                  {stat.n}
                </div>
                <p style={{ color: '#64748b', fontSize: 14, marginTop: 8, fontWeight: 500 }}>{stat.l}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      <section className="section" style={{ background: 'var(--bg-secondary)' }}>
        <FadeIn>
          <h2 style={{ fontSize: 28, fontWeight: 800, textAlign: 'center', marginBottom: 16 }}>
            Meet the <span className="gradient-text">Team</span>
          </h2>
          <p style={{ color: '#94a3b8', fontSize: 16, textAlign: 'center', maxWidth: 500, margin: '0 auto 48px' }}>
            A small team of engineers and astrologers passionate about blending ancient wisdom with modern technology.
          </p>
        </FadeIn>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24, maxWidth: 900, margin: '0 auto' }}>
          {[
            { name: 'Rohan Sharma', role: 'Founder & Lead Engineer', desc: 'Full-stack developer with 8 years of experience. Built AstroVakta from ground up with a passion for Vedic astrology.' },
            { name: 'Dr. Ananya Gupta', role: 'Astrology Advisor', desc: 'PhD in Vedic Astrology. Ensures every calculation, yoga, and remedy meets traditional standards.' },
            { name: 'Vikram Patel', role: 'AI & ML Engineer', desc: 'Specializes in LLM integration. Built the multi-provider AI pipeline that powers intelligent chart interpretations.' },
          ].map((member, i) => (
            <FadeIn key={member.name} delay={i * 0.1}>
              <div className="card-glow" style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)', padding: 32, textAlign: 'center', height: '100%',
              }}>
                <div style={{
                  width: 72, height: 72, borderRadius: '50%',
                  background: 'var(--gradient-primary)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px',
                  fontSize: 28, fontWeight: 700, color: '#fff',
                }}>{member.name[0]}</div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>{member.name}</h3>
                <p style={{ color: '#a78bfa', fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{member.role}</p>
                <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.6 }}>{member.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>
    </div>
  )
}
