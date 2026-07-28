import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, Star, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { login as apiLogin } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

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
        navigate('/dashboard')
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        paddingTop: 72,
      }}
    >
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
        className="login-left"
      >
        <div
          style={{
            position: 'absolute',
            width: 300,
            height: 300,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(124,58,237,0.2) 0%, transparent 70%)',
            animation: 'float 6s ease-in-out infinite',
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(236,72,153,0.15) 0%, transparent 70%)',
            animation: 'float 8s ease-in-out infinite reverse',
            top: '30%',
            left: '20%',
          }}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}
        >
          <Star size={80} color="#7c3aed" fill="rgba(124,58,237,0.3)" />
          <h2
            style={{
              fontSize: 28,
              fontWeight: 800,
              marginTop: 24,
              background: 'var(--gradient-primary)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Welcome to AstroVakta
          </h2>
          <p style={{ color: '#94a3b8', marginTop: 8, maxWidth: 300 }}>
            The universe awaits. Access the most powerful Vedic Astrology API.
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
          <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 8 }}>Log In</h1>
          <p style={{ color: '#94a3b8', marginBottom: 32 }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#a78bfa', fontWeight: 600 }}>
              Sign up
            </Link>
          </p>

          <form onSubmit={handleSubmit}>
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

            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <label style={{ fontSize: 14, color: '#94a3b8' }}>Password</label>
                <Link to="/forgot-password" style={{ fontSize: 13, color: '#a78bfa', fontWeight: 500, textDecoration: 'none' }}>
                  Forgot password?
                </Link>
              </div>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={18}
                  color="#64748b"
                  style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}
                />
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
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
              {loading ? 'Logging in...' : 'Log In'}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>
        </motion.div>
      </div>

      <style>{`
        @media (min-width: 769px) {
          .login-left { display: flex !important; }
        }
      `}</style>
    </div>
  )
}
