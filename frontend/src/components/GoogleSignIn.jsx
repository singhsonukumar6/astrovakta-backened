import { useEffect, useRef } from 'react'
import api from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import { useNavigate, useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

// Google Identity Services button — posts the ID token to /auth/google and
// signs the user in. Renders nothing when VITE_GOOGLE_CLIENT_ID is unset.
export default function GoogleSignIn({ label = 'continue_with' }) {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const btnRef = useRef(null)

  useEffect(() => {
    if (!CLIENT_ID) return
    const handle = async (resp) => {
      try {
        const data = await api.post('/auth/google', { credential: resp.credential }).then((r) => r.data)
        login(data.token, data.user)
        toast.success('Welcome!')
        navigate(location.state?.from || '/mysite', { replace: true })
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Google sign-in failed')
      }
    }
    const init = () => {
      if (!window.google?.accounts?.id) return false
      window.google.accounts.id.initialize({ client_id: CLIENT_ID, callback: handle })
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: 'outline', size: 'large', width: 380, text: label, shape: 'pill',
      })
      return true
    }
    if (window.google?.accounts?.id) { init(); return }
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = init
    document.head.appendChild(s)
  }, [CLIENT_ID, label])

  if (!CLIENT_ID) return null
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '18px 0', color: '#94a3b8', fontSize: 12.5, fontWeight: 600 }}>
        <span style={{ flex: 1, height: 1, background: '#e2e8f0' }} /> OR <span style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
      </div>
      <div ref={btnRef} style={{ display: 'flex', justifyContent: 'center', minHeight: 44 }} />
    </>
  )
}
