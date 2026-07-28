import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, User, Star, ArrowRight, MailCheck, LogIn } from 'lucide-react'
import toast from 'react-hot-toast'
import { register as apiRegister } from '../lib/api.js'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [registered, setRegistered] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name || !email || !password) return toast.error('Please fill all fields')
    if (password.length < 6) return toast.error('Password must be at least 6 characters')
    setLoading(true)
    try {
      const data = await apiRegister(email, name, password)
      if (data.email_sent) {
        toast.success('Account created! Check your email for the verification link.')
      } else {
        toast.error('Account created but email could not be sent. Please contact support or try again later.')
      }
      setRegistered(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', paddingTop: 72 }}>
      {/* Left decorative panel */}
      <div
        style={{
          flex: 1,
          display: 'none',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #0a0a1a 0%, #1a1040 50%, #0a0a1a 100%)',
          position: 'relative',
          overflow: 'hidden',
        }}
        className="register-left"
      >
        <div
          style={{
            position: 'absolute',
            width: 300,
            height: 300,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)',
            animation: 'float 6s ease-in-out infinite',
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)',
            animation: 'float 8s ease-in-out infinite reverse',
            top: '25%',
            right: '20%',
          }}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}
        >
          <Star size={80} color="#6366f1" fill="rgba(99,102,241,0.3)" />
          <h2
            style={{
              fontSize: 28,
              fontWeight: 800,
              marginTop: 24,
              background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Join AstroVakta
          </h2>
          <p style={{ color: '#94a3b8', marginTop: 8, maxWidth: 300 }}>
            Start building with the cosmos. Free tier included.
          </p>
        </motion.div>
      </div>

      {/* Right form panel */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 24px',
        }}
      >
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          style={{ width: '100%', maxWidth: 420 }}
        >
          <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 8 }}>Create Account</h1>
          {!registered && (
            <p style={{ color: '#94a3b8', marginBottom: 32 }}>
              Already have an account?{' '}
              <Link to="/login" style={{ color: '#a78bfa', fontWeight: 600 }}>
                Log in
              </Link>
            </p>
          )}

          {registered ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <div style={{
                background: 'linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.05))',
                border: '1px solid rgba(34,197,94,0.3)',
                borderRadius: 16,
                padding: '40px 32px',
                textAlign: 'center',
              }}>
                <div style={{
                  width: 72, height: 72, borderRadius: '50%',
                  background: 'rgba(34,197,94,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 24px',
                }}>
                  <MailCheck size={36} color="#22c55e" />
                </div>
                <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>
                  Check your email
                </h2>
                <p style={{ color: '#94a3b8', fontSize: 15, lineHeight: 1.6, marginBottom: 8 }}>
                  We sent a verification link to:
                </p>
                <p style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 15, marginBottom: 24 }}>
                  {email}
                </p>
                <p style={{ color: '#64748b', fontSize: 13, lineHeight: 1.6, marginBottom: 32 }}>
                  Click the link in the email to verify your account.
                  The link expires in 24 hours.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <button
                    onClick={() => navigate('/login')}
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center', padding: '14px 24px' }}
                  >
                    <LogIn size={18} />
                    Go to Login
                  </button>
                  <button
                    onClick={() => { setRegistered(false); setName(''); setEmail(''); setPassword('') }}
                    style={{
                      background: 'none', border: '1px solid rgba(148,163,184,0.2)',
                      color: '#94a3b8', padding: '12px 24px', borderRadius: 10,
                      cursor: 'pointer', fontSize: 14, fontWeight: 500,
                    }}
                  >
                    Register with a different email
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>
                  Name
                </label>
                <div style={{ position: 'relative' }}>
                  <User
                    size={18}
                    color="#64748b"
                    style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}
                  />
                  <input
                    type="text"
                    className="input-field"
                    placeholder="Your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    style={{ paddingLeft: 42 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>
                  Email
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail
                    size={18}
                    color="#64748b"
                    style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}
                  />
                  <input
                    type="email"
                    className="input-field"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{ paddingLeft: 42 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 32 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock
                    size={18}
                    color="#64748b"
                    style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}
                  />
                  <input
                    type="password"
                    className="input-field"
                    placeholder="At least 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ paddingLeft: 42 }}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  padding: '14px 24px',
                  opacity: loading ? 0.7 : 1,
                }}
              >
                {loading ? 'Creating account...' : 'Create Account'}
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>
          )}
        </motion.div>
      </div>

      <style>{`
        @media (min-width: 769px) {
          .register-left { display: flex !important; }
        }
      `}</style>
    </div>
  )
}
