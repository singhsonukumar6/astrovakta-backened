import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, ArrowRight, Star, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { forgotPassword } from '../lib/api.js'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email) return toast.error('Please enter your email')
    setLoading(true)
    try {
      await forgotPassword(email)
      setSent(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72, padding: '72px 24px 40px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ width: '100%', maxWidth: 440 }}
      >
        {sent ? (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center' }}>
            <CheckCircle size={64} color="#7c3aed" style={{ marginBottom: 24 }} />
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12 }}>Check Your Email</h1>
            <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 8, lineHeight: 1.6 }}>
              If an account exists with <strong style={{ color: '#e2e8f0' }}>{email}</strong>, we've sent a password reset link.
            </p>
            <p style={{ color: '#64748b', fontSize: 14, marginBottom: 32 }}>
              Didn't receive it? Check your spam folder or try again.
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
              <button className="btn-secondary" onClick={() => { setSent(false); setEmail('') }} style={{ padding: '12px 24px' }}>
                Try Again
              </button>
              <Link to="/login" className="btn-primary" style={{ textDecoration: 'none', padding: '12px 24px', display: 'inline-flex' }}>
                Back to Login <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        ) : (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48 }}>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <Star size={40} color="#7c3aed" fill="rgba(124,58,237,0.3)" style={{ marginBottom: 16 }} />
              <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>Forgot Password?</h1>
              <p style={{ color: '#94a3b8', fontSize: 15 }}>
                Enter your email and we'll send you a reset link.
              </p>
            </div>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 24 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Email</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={18} color="#64748b" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="email"
                    className="input-field"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{ paddingLeft: 42 }}
                    autoFocus
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}
                style={{ width: '100%', justifyContent: 'center', padding: '14px 24px', opacity: loading ? 0.7 : 1 }}>
                {loading ? 'Sending...' : 'Send Reset Link'}
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>

            <p style={{ color: '#64748b', fontSize: 14, textAlign: 'center', marginTop: 24 }}>
              Remember your password?{' '}
              <Link to="/login" style={{ color: '#a78bfa', fontWeight: 600 }}>Log in</Link>
            </p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
