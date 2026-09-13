import { useEffect, useState } from 'react'
import { firebaseEnabled, signInWithFirebase } from '../lib/firebase.js'
import api from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import { useNavigate, useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'

// Firebase Auth sign-in buttons (Google today; providers are added in
// signInWithFirebase). Hidden entirely until VITE_FIREBASE_* env vars exist.
export default function FirebaseSignIn() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [busy, setBusy] = useState(false)

  useEffect(() => { if (firebaseEnabled) { /* warm the SDK */ } }, [])

  const handle = async () => {
    setBusy(true)
    try {
      const fu = await signInWithFirebase('google')
      const data = await api.post('/auth/firebase', { idToken: await fu.getIdToken() }).then((r) => r.data)
      login(data.token, data.user)
      toast.success('Welcome!')
      navigate(location.state?.from || '/mysite', { replace: true })
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message || 'Sign-in failed')
    } finally { setBusy(false) }
  }

  if (!firebaseEnabled) return null
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '18px 0', color: '#94a3b8', fontSize: 12.5, fontWeight: 600 }}>
        <span style={{ flex: 1, height: 1, background: '#e2e8f0' }} /> OR <span style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
      </div>
      <button onClick={handle} disabled={busy}
        style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: '12px 14px', borderRadius: 999, border: '1px solid #e2e8f0', background: '#fff', fontWeight: 700, fontSize: 14, color: '#0f172a', cursor: 'pointer' }}>
        <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.3 6.1 29.4 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.6-.4-3.9z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.3 6.1 29.4 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C41.4 35.4 44 30.2 44 24c0-1.3-.1-2.6-.4-3.9z"/></svg>
        {busy ? 'Signing you in…' : 'Continue with Google (Firebase)'}
      </button>
    </>
  )
}
