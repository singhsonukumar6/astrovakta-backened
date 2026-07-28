import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MailCheck, Send, LogOut, Star } from 'lucide-react'
import toast from 'react-hot-toast'
import { resendVerification } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

export default function VerifyEmailPrompt() {
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const email = location.state?.email || ''

  const handleResend = async () => {
    if (!email) return toast.error('No email found. Please log in again.')
    setSending(true)
    try {
      await resendVerification(email)
      setSent(true)
      toast.success('Verification email sent!')
    } catch (err) {
      toast.error('Failed to send email. Please try again.')
    } finally {
      setSending(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ width: '100%', maxWidth: 480, textAlign: 'center' }}
      >
        <div style={{
          width: 88, height: 88, borderRadius: '50%',
          background: 'linear-gradient(135deg, rgba(251,191,36,0.15), rgba(251,146,60,0.1))',
          border: '1px solid rgba(251,191,36,0.25)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 32px',
        }}>
          <MailCheck size={42} color="#fbbf24" />
        </div>

        <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12 }}>
          Verify your email
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, lineHeight: 1.6, marginBottom: 8 }}>
          Your account is not yet verified. Please check your inbox and click the
          verification link we sent you.
        </p>
        {email && (
          <p style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 14, marginBottom: 32 }}>
            {email}
          </p>
        )}

        <div style={{
          background: 'rgba(251,191,36,0.05)',
          border: '1px solid rgba(251,191,36,0.15)',
          borderRadius: 12,
          padding: '20px 24px',
          marginBottom: 28,
          textAlign: 'left',
        }}>
          <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.6, margin: 0 }}>
            <strong style={{ color: '#fbbf24' }}>Didn't receive the email?</strong><br />
            Check your spam/junk folder, or click the button below to resend.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <button
            onClick={handleResend}
            disabled={sending || sent}
            className="btn-primary"
            style={{
              width: '100%', justifyContent: 'center', padding: '14px 24px',
              opacity: sending || sent ? 0.7 : 1,
            }}
          >
            {sent ? (
              <>✓ Email Sent</>
            ) : sending ? (
              'Sending...'
            ) : (
              <><Send size={18} /> Resend Verification Email</>
            )}
          </button>

          <button
            onClick={handleLogout}
            style={{
              background: 'none', border: '1px solid rgba(148,163,184,0.2)',
              color: '#94a3b8', padding: '12px 24px', borderRadius: 10,
              cursor: 'pointer', fontSize: 14, fontWeight: 500,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            <LogOut size={16} /> Log out and use a different account
          </button>
        </div>

        <p style={{ color: '#475569', fontSize: 12, marginTop: 24 }}>
          Need help? <a href="mailto:support@astrovakta.com" style={{ color: '#a78bfa' }}>Contact Support</a>
        </p>
      </motion.div>
    </div>
  )
}
