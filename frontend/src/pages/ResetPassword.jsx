import { useState } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, ArrowRight, Star, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { resetPassword } from '../lib/api.js'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const token = searchParams.get('token')

  if (!token) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72, padding: '72px 24px 40px' }}>
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center', maxWidth: 440 }}>
          <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 12 }}>Invalid Reset Link</h1>
          <p style={{ color: '#94a3b8', marginBottom: 24 }}>This password reset link is invalid or missing a token.</p>
          <Link to="/forgot-password" className="btn-primary" style={{ textDecoration: 'none', padding: '12px 24px', display: 'inline-flex' }}>
            Request New Link <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!password) return toast.error('Please enter a new password')
    if (password.length < 6) return toast.error('Password must be at least 6 characters')
    if (password !== confirmPassword) return toast.error('Passwords do not match')
    setLoading(true)
    try {
      await resetPassword(token, password)
      setDone(true)
      toast.success('Password reset successful!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Reset link expired or invalid')
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
        {done ? (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center' }}>
            <CheckCircle size={64} color="#22c55e" style={{ marginBottom: 24 }} />
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12, color: '#22c55e' }}>Password Reset!</h1>
            <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 32 }}>Your password has been updated successfully.</p>
            <button className="btn-primary" onClick={() => navigate('/login')} style={{ padding: '14px 32px' }}>
              Log In Now <ArrowRight size={18} />
            </button>
          </div>
        ) : (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48 }}>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <Star size={40} color="#7c3aed" fill="rgba(124,58,237,0.3)" style={{ marginBottom: 16 }} />
              <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>Reset Password</h1>
              <p style={{ color: '#94a3b8', fontSize: 15 }}>Enter your new password below.</p>
            </div>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>New Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} color="#64748b" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="password"
                    className="input-field"
                    placeholder="At least 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ paddingLeft: 42 }}
                    autoFocus
                  />
                </div>
              </div>

              <div style={{ marginBottom: 32 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Confirm Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} color="#64748b" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="password"
                    className="input-field"
                    placeholder="Re-enter new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ paddingLeft: 42 }}
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}
                style={{ width: '100%', justifyContent: 'center', padding: '14px 24px', opacity: loading ? 0.7 : 1 }}>
                {loading ? 'Resetting...' : 'Reset Password'}
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>
          </div>
        )}
      </motion.div>
    </div>
  )
}
