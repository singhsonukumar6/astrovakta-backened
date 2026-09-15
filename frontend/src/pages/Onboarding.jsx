import { Navigate, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, CalendarCheck, Star, Store, Globe, ArrowRight } from 'lucide-react'
import { useAuth } from '../lib/auth.jsx'
import { CreateSiteWizard } from '../components/CreateSiteWizard.jsx'

// First-run flow: users without a website land here from /mysite (both
// after login and signup) and are sent to the dashboard once created.
export default function Onboarding() {
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const navigate = useNavigate()

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0b0b1e' }}>
        <div className="gradient-text" style={{ fontSize: 18, fontWeight: 600 }}>Loading…</div>
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />

  const firstName = (user?.name || user?.email || 'there').split(' ')[0].split('@')[0]

  return (
    <div style={{ minHeight: '100vh', background: '#0b0b1e', color: '#f1f0ff', position: 'relative', overflow: 'hidden' }}>
      {/* ambient glows */}
      <div style={{ position: 'absolute', width: 560, height: 560, borderRadius: '50%', top: -200, left: -140, background: 'radial-gradient(circle, rgba(124,58,237,0.28) 0%, transparent 70%)' }} />
      <div style={{ position: 'absolute', width: 460, height: 460, borderRadius: '50%', bottom: -180, right: -120, background: 'radial-gradient(circle, rgba(234,179,8,0.15) 0%, transparent 70%)' }} />
      {/* starfield dots */}
      <div style={{ position: 'absolute', inset: 0, opacity: 0.5, backgroundImage: 'radial-gradient(1.5px 1.5px at 20% 30%, #fff 50%, transparent 51%), radial-gradient(1px 1px at 70% 20%, #c7d2fe 50%, transparent 51%), radial-gradient(1.5px 1.5px at 85% 65%, #fff 50%, transparent 51%), radial-gradient(1px 1px at 40% 80%, #e9d5ff 50%, transparent 51%), radial-gradient(1px 1px at 10% 60%, #fff 50%, transparent 51%)' }} />

      <div style={{ position: 'relative', maxWidth: 980, margin: '0 auto', padding: '46px 20px 90px' }}>
        {/* welcome hero */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          style={{ textAlign: 'center', marginBottom: 34 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px', borderRadius: 999, background: 'rgba(124,58,237,0.18)', border: '1px solid rgba(124,58,237,0.4)', fontSize: 12.5, fontWeight: 700, color: '#c4b5fd', marginBottom: 20 }}>
            <Sparkles size={13} /> Welcome to AstroVakta
          </div>
          <h1 style={{ fontSize: 'clamp(30px, 5vw, 44px)', fontWeight: 900, letterSpacing: '-1px', margin: '0 0 12px', lineHeight: 1.15 }}>
            Namaste, {firstName} 👋<br />
            <span style={{ background: 'linear-gradient(135deg, #a78bfa, #fbbf24)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Let's build your website.
            </span>
          </h1>
          <p style={{ color: 'rgba(241,240,255,0.65)', fontSize: 15.5, maxWidth: 520, margin: '0 auto', lineHeight: 1.8 }}>
            Three quick steps and your astrology practice is online — bookings, store, free kundli tools and your own domain.
          </p>

          {/* benefit strip */}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap', marginTop: 22 }}>
            {[
              [CalendarCheck, 'Bookings & WhatsApp alerts'],
              [Store, 'Your own remedies store'],
              [Star, 'Free kundli tools for visitors'],
              [Globe, 'Custom domain support'],
            ].map(([Icon, label], i) => (
              <motion.span key={label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + i * 0.08 }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 600, color: 'rgba(241,240,255,0.8)', padding: '7px 13px', borderRadius: 999, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
                <Icon size={13} color="#fbbf24" /> {label}
              </motion.span>
            ))}
          </div>
        </motion.div>

        {/* the wizard card — styled to float on the dark hero */}
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }}>
          <OnboardingWizard onDone={() => navigate('/mysite', { replace: true })} />
        </motion.div>

        <div style={{ textAlign: 'center', marginTop: 26 }}>
          <button onClick={() => navigate('/mysite')} style={{ background: 'none', border: 'none', color: 'rgba(241,240,255,0.45)', fontSize: 13, cursor: 'pointer', textDecoration: 'underline' }}>
            Skip for now — explore the dashboard first
          </button>
        </div>
      </div>
    </div>
  )
}

/* Wizard wrapper: keeps the stepper chrome here so CreateSiteWizard stays
   reusable, and shows a success celebration before redirecting. */
import { useState } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { tenantSiteUrl } from '../lib/tenant.js'

function OnboardingWizard({ onDone }) {
  const [created, setCreated] = useState(null)

  if (created) {
    return (
      <div style={{ background: '#fff', borderRadius: 22, padding: '44px 30px', textAlign: 'center', color: '#0f172a', boxShadow: '0 30px 80px rgba(0,0,0,0.45)' }}>
        <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 260, damping: 18 }}>
          <CheckCircle2 size={64} color="#16a34a" style={{ marginBottom: 12 }} />
        </motion.div>
        <h2 style={{ fontSize: 26, fontWeight: 900, margin: '0 0 8px' }}>Your website is ready! 🎉</h2>
        <p style={{ color: '#64748b', fontSize: 14.5, marginBottom: 22, lineHeight: 1.7 }}>
          <b>{created.name}</b> is live at <b>{created.slug}.astrovakta.com</b>.<br />
          Next: add your services and share your link.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href={tenantSiteUrl(created.slug)} target="_blank" rel="noopener noreferrer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '12px 22px', borderRadius: 12, border: '1.5px solid #e2e8f0', color: '#0f172a', fontWeight: 700, fontSize: 14, textDecoration: 'none' }}>
            View my website <ArrowRight size={15} />
          </a>
          <button onClick={onDone}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '12px 24px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer' }}>
            Go to dashboard →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ background: '#fff', borderRadius: 22, padding: '30px 28px', color: '#0f172a', boxShadow: '0 30px 80px rgba(0,0,0,0.45)' }}>
      <CreateSiteWizard onCreated={(site) => setCreated(site)} />
    </div>
  )
}
