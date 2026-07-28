import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Mail, ArrowRight } from 'lucide-react'
import { verifyEmail } from '../lib/api.js'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setStatus('error')
      setMessage('No verification token provided.')
      return
    }
    verifyEmail(token)
      .then((data) => {
        setStatus('success')
        setMessage(data.detail || 'Email verified successfully!')
      })
      .catch((err) => {
        setStatus('error')
        setMessage(err.response?.data?.detail || 'Invalid or expired verification link.')
      })
  }, [searchParams])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72, padding: '72px 24px 40px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ width: '100%', maxWidth: 440, textAlign: 'center' }}
      >
        {status === 'loading' && (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48 }}>
            <div className="gradient-text" style={{ fontSize: 18 }}>Verifying your email...</div>
          </div>
        )}

        {status === 'success' && (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48 }}>
            <CheckCircle size={64} color="#22c55e" style={{ marginBottom: 24 }} />
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12, color: '#22c55e' }}>Email Verified!</h1>
            <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 32, lineHeight: 1.6 }}>{message}</p>
            <Link to="/login" className="btn-primary" style={{ display: 'inline-flex', textDecoration: 'none' }}>
              Continue to Login <ArrowRight size={18} />
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48 }}>
            <XCircle size={64} color="#ef4444" style={{ marginBottom: 24 }} />
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12, color: '#ef4444' }}>Verification Failed</h1>
            <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 32, lineHeight: 1.6 }}>{message}</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
              <Link to="/login" className="btn-secondary" style={{ textDecoration: 'none', padding: '12px 24px' }}>
                Go to Login
              </Link>
              <Link to="/register" className="btn-primary" style={{ textDecoration: 'none', padding: '12px 24px' }}>
                <Mail size={16} /> Register Again
              </Link>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}
