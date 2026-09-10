import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, User, ArrowRight, Eye, EyeOff, Check, Globe, CalendarCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { register as apiRegister } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [registered, setRegistered] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const passChecks = [
    { ok: password.length >= 6, label: 'At least 6 characters' },
    { ok: /[A-Za-z]/.test(password) && /\d/.test(password), label: 'A letter and a number' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name || !email || !password) return toast.error('Please fill all fields')
    if (password.length < 6) return toast.error('Password must be at least 6 characters')
    setLoading(true)
    try {
      const data = await apiRegister(email, name, password)
      if (data.user?.email_verified) {
        // Email delivery unavailable → backend auto-verified. Sign straight in.
        login(data.token, data.user)
        toast.success('Welcome to AstroVakta! Let\'s create your website.')
        navigate('/mysite')
      } else if (data.email_sent) {
        toast.success('Account created! Check your email for the verification link.')
        setRegistered(true)
      } else {
        toast.error('Account created but email could not be sent. Please try again later.')
        setRegistered(true)
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.error || 'Registration failed')
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
            background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)',
            fontSize: 12, fontWeight: 700, color: '#16a34a', marginBottom: 28,
          }}>
            <Check size={13} /> Free forever · No credit card
          </div>
          <h2 style={{ fontSize: 38, fontWeight: 900, lineHeight: 1.15, letterSpacing: '-0.5px', marginBottom: 16, color: '#0f172a' }}>
            Launch your astrology website{' '}
            <span className="gradient-text">today.</span>
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 32 }}>
            {[
              { icon: Globe, title: 'Your own branded website', text: 'Free subdomain instantly, connect your own domain anytime' },
              { icon: CalendarCheck, title: 'Bookings that fill themselves', text: 'Real-time slots, WhatsApp confirmations & reminders' },
            ].map((f, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.15 }}
                style={{ display: 'flex', gap: 14, padding: '16px 18px', background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(79,70,229,0.15)', borderRadius: 14 }}>
                <div style={{ width: 38, height: 38, borderRadius: 10, background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <f.icon size={18} color="#fff" />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 14, color: '#0f172a', marginBottom: 2 }}>{f.title}</div>
                  <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.5 }}>{f.text}</div>
                </div>
              </motion.div>
            ))}
          </div>
          <p style={{ fontSize: 13, color: '#64748b', fontStyle: 'italic' }}>
            “I had my website with bookings live the same evening. Clients find me on Google now.”
            <span style={{ display: 'block', fontWeight: 700, fontStyle: 'normal', marginTop: 6, color: '#475569' }}>— Pandit Rajesh S., Vedic Astrologer</span>
          </p>
        </motion.div>
      </div>

      {/* Right form panel */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}
          style={{ width: '100%', maxWidth: 420 }}>
          {registered ? (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div style={{
                background: 'linear-gradient(135deg, rgba(34,197,94,0.08), rgba(34,197,94,0.03))',
                border: '1px solid rgba(34,197,94,0.3)', borderRadius: 18, padding: '40px 32px', textAlign: 'center',
              }}>
                <div style={{
                  width: 72, height: 72, borderRadius: '50%', background: 'rgba(34,197,94,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px',
                }}>
                  <Mail size={34} color="#16a34a" />
                </div>
                <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 10, color: '#0f172a' }}>Check your email</h2>
                <p style={{ color: '#475569', fontSize: 14, lineHeight: 1.7, marginBottom: 6 }}>
                  We sent a verification link to
                </p>
                <p style={{ color: '#0f172a', fontWeight: 700, fontSize: 15, marginBottom: 20 }}>{email}</p>
                <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 28 }}>
                  Click the link to verify your account — the link expires in 24 hours.
                </p>
                <button onClick={() => navigate('/login')} className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center', padding: '13px 24px' }}>
                  Go to Login <ArrowRight size={16} />
                </button>
                <button onClick={() => { setRegistered(false); setName(''); setEmail(''); setPassword('') }}
                  style={{
                    background: 'none', border: 'none', color: '#64748b', padding: '12px 24px',
                    cursor: 'pointer', fontSize: 13, fontWeight: 600, marginTop: 6,
                  }}>
                  Register with a different email
                </button>
              </div>
            </motion.div>
          ) : (
            <>
              <div style={{ marginBottom: 30 }}>
                <h1 style={{ fontSize: 30, fontWeight: 800, letterSpacing: '-0.5px', marginBottom: 10, color: '#0f172a' }}>
                  Create your account
                </h1>
                <p style={{ color: '#475569', fontSize: 15 }}>
                  Already have an account?{' '}
                  <Link to="/login" style={{ color: '#4f46e5', fontWeight: 700, textDecoration: 'none' }}>
                    Log in →
                  </Link>
                </p>
              </div>

              <form onSubmit={handleSubmit}>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#334155', marginBottom: 7 }}>Your name</label>
                <div style={{ position: 'relative', marginBottom: 18 }}>
                  <User size={17} color="#94a3b8" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                  <input type="text" className="input-field" placeholder="Pandit Rajesh Sharma"
                    value={name} onChange={(e) => setName(e.target.value)} style={{ paddingLeft: 42 }} />
                </div>

                <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#334155', marginBottom: 7 }}>Email</label>
                <div style={{ position: 'relative', marginBottom: 18 }}>
                  <Mail size={17} color="#94a3b8" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                  <input type="email" className="input-field" placeholder="you@example.com"
                    value={email} onChange={(e) => setEmail(e.target.value)} style={{ paddingLeft: 42 }} />
                </div>

                <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#334155', marginBottom: 7 }}>Password</label>
                <div style={{ position: 'relative', marginBottom: 12 }}>
                  <Lock size={17} color="#94a3b8" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                  <input type={showPass ? 'text' : 'password'} className="input-field" placeholder="Create a password"
                    value={password} onChange={(e) => setPassword(e.target.value)} style={{ paddingLeft: 42, paddingRight: 44 }} />
                  <button type="button" onClick={() => setShowPass((s) => !s)}
                    style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex' }}>
                    {showPass ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>

                <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
                  {passChecks.map((c) => (
                    <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: c.ok ? '#16a34a' : '#94a3b8', fontWeight: 600 }}>
                      <div style={{
                        width: 16, height: 16, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: c.ok ? 'rgba(34,197,94,0.15)' : 'rgba(148,163,184,0.15)',
                      }}>
                        <Check size={10} strokeWidth={3} />
                      </div>
                      {c.label}
                    </div>
                  ))}
                </div>

                <button type="submit" className="btn-primary" disabled={loading}
                  style={{ width: '100%', justifyContent: 'center', padding: '14px 24px', fontSize: 15, opacity: loading ? 0.7 : 1 }}>
                  {loading ? 'Creating your account…' : 'Create Free Account'}
                  {!loading && <ArrowRight size={17} />}
                </button>
              </form>

              <p style={{ textAlign: 'center', color: '#94a3b8', fontSize: 12, marginTop: 24, lineHeight: 1.6 }}>
                Free forever plan · No credit card required ·{' '}
                <Link to="/terms" style={{ color: 'inherit' }}>Terms</Link>
              </p>
            </>
          )}
        </motion.div>
      </div>

      <style>{`
        @media (min-width: 901px) { .auth-left { display: flex !important; } }
      `}</style>
    </div>
  )
}
