import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, ArrowRight, Eye, EyeOff, Sparkles, CalendarCheck, Star } from 'lucide-react'
import toast from 'react-hot-toast'
import { login as apiLogin } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/mysite'

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !password) return toast.error('Please fill all fields')
    setLoading(true)
    try {
      const data = await apiLogin(email, password)
      login(data.token, data.user)
      if (!data.user.email_verified) {
        toast('Please verify your email before continuing.', { icon: '📧' })
        navigate('/verify-email-prompt', { state: { email: data.user.email } })
      } else {
        toast.success('Welcome back!')
        navigate(from)
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', paddingTop: 72 }}>
      {/* Left brand panel */}
      <div
        className="auth-left"
        style={{
          flex: 1, display: 'none', flexDirection: 'column', justifyContent: 'center',
          padding: '64px', position: 'relative', overflow: 'hidden',
          background: 'linear-gradient(160deg, #eef2ff 0%, #f8fafc 45%, #fdf2f8 100%)',
        }}
      >
        <div style={{
          position: 'absolute', width: 420, height: 420, borderRadius: '50%', top: -120, right: -80,
          background: 'radial-gradient(circle, rgba(79,70,229,0.14) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', width: 320, height: 320, borderRadius: '50%', bottom: -100, left: -60,
          background: 'radial-gradient(circle, rgba(217,119,6,0.12) 0%, transparent 70%)',
        }} />
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
          style={{ position: 'relative', maxWidth: 420 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 20,
            background: 'rgba(79,70,229,0.08)', border: '1px solid rgba(79,70,229,0.2)',
            fontSize: 12, fontWeight: 700, color: '#4f46e5', marginBottom: 28,
          }}>
            <Sparkles size={13} /> India's astrology business platform
          </div>
          <h2 style={{ fontSize: 38, fontWeight: 900, lineHeight: 1.15, letterSpacing: '-0.5px', marginBottom: 16, color: '#0f172a' }}>
            Your complete astrology practice,{' '}
            <span className="gradient-text">online in minutes.</span>
          </h2>
          <p style={{ color: '#475569', fontSize: 15, lineHeight: 1.8, marginBottom: 36 }}>
            Branded website, bookings with WhatsApp alerts, free kundli tools for your visitors,
            and your own store — all in one dashboard.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { icon: CalendarCheck, text: 'Appointments & reminders — automatic' },
              { icon: Star, text: 'Free kundli & panchang tools on your site' },
              { icon: Sparkles, text: '8 professional themes, your own domain' },
            ].map((f, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.12 }}
                style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 14, color: '#334155', fontWeight: 500 }}>
                <div style={{ width: 34, height: 34, borderRadius: 10, background: '#fff', border: '1px solid rgba(79,70,229,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <f.icon size={16} color="#4f46e5" />
                </div>
                {f.text}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right form panel */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}
          style={{ width: '100%', maxWidth: 420 }}>
          <div style={{ marginBottom: 32 }}>
            <h1 style={{ fontSize: 30, fontWeight: 800, letterSpacing: '-0.5px', marginBottom: 10, color: '#0f172a' }}>
              Welcome back
            </h1>
            <p style={{ color: '#475569', fontSize: 15 }}>
              New to AstroVakta?{' '}
              <Link to="/register" style={{ color: '#4f46e5', fontWeight: 700, textDecoration: 'none' }}>
                Create your free account →
              </Link>
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#334155', marginBottom: 7 }}>Email</label>
            <div style={{ position: 'relative', marginBottom: 18 }}>
              <Mail size={17} color="#94a3b8" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="email" className="input-field" placeholder="you@example.com"
                value={email} onChange={(e) => setEmail(e.target.value)} style={{ paddingLeft: 42 }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }}>
              <label style={{ fontSize: 13, fontWeight: 700, color: '#334155' }}>Password</label>
              <Link to="/forgot-password" style={{ fontSize: 13, color: '#4f46e5', fontWeight: 600, textDecoration: 'none' }}>
                Forgot password?
              </Link>
            </div>
            <div style={{ position: 'relative', marginBottom: 24 }}>
              <Lock size={17} color="#94a3b8" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type={showPass ? 'text' : 'password'} className="input-field" placeholder="Your password"
                value={password} onChange={(e) => setPassword(e.target.value)} style={{ paddingLeft: 42, paddingRight: 44 }}
              />
              <button type="button" onClick={() => setShowPass((s) => !s)}
                style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex' }}>
                {showPass ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>

            <button
              type="submit" className="btn-primary" disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '14px 24px', fontSize: 15, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? 'Signing in…' : 'Sign In'}
              {!loading && <ArrowRight size={17} />}
            </button>
          </form>

          <p style={{ textAlign: 'center', color: '#94a3b8', fontSize: 12, marginTop: 24, lineHeight: 1.6 }}>
            By continuing you agree to our{' '}
            <Link to="/terms" style={{ color: 'inherit' }}>Terms</Link> and{' '}
            <Link to="/privacy" style={{ color: 'inherit' }}>Privacy Policy</Link>.
          </p>
        </motion.div>
      </div>

      <style>{`
        @media (min-width: 901px) { .auth-left { display: flex !important; } }
      `}</style>
    </div>
  )
}
