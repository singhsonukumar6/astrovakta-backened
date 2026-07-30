import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api, { getMe } from './api.js'

const AuthContext = createContext(null)

let _hasClerk = null
export function hasClerk() {
  if (_hasClerk !== null) return _hasClerk
  const k = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
  _hasClerk = !!(k && !k.includes('placeholder') && k.length > 10)
  return _hasClerk
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)
  const [clerkSynced, setClerkSynced] = useState(false)

  useEffect(() => {
    if (!hasClerk()) return
    let cancelled = false

    async function syncWithBackend(clerkSession) {
      try {
        const email = clerkSession.user.primaryEmailAddress?.emailAddress
        const name = `${clerkSession.user.firstName || ''} ${clerkSession.user.lastName || ''}`.trim()
        const clerkId = clerkSession.user.id

        const res = await api.post('/auth/clerk-sync', { clerk_id: clerkId, email, name })
        const newToken = res.data?.token
        const newUser = res.data?.user

        if (!cancelled && newToken) {
          setToken(newToken)
          setUser(newUser)
          localStorage.setItem('token', newToken)
        }
      } catch {} finally {
        if (!cancelled) setClerkSynced(true)
      }
    }

    async function trySync() {
      try {
        const { Clerk } = await import('@clerk/clerk-react')
        const session = Clerk.session
        if (session) {
          await syncWithBackend(session)
          return
        }
        const unsub = Clerk.addListener((payload) => {
          if (payload.session) {
            syncWithBackend(payload.session)
            unsub()
          }
        })
      } catch {}
    }

    trySync().finally(() => {
      if (!cancelled) setClerkSynced(true)
    })

    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false
    if (token) {
      localStorage.setItem('token', token)
      getMe()
        .then((data) => {
          if (!cancelled) setUser(data.user || data)
        })
        .catch(() => {
          if (!cancelled) {
            setToken(null)
            setUser(null)
            localStorage.removeItem('token')
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
    } else {
      if (!hasClerk() || clerkSynced) {
        setLoading(false)
      }
    }
    return () => { cancelled = true }
  }, [token, clerkSynced])

  const login = useCallback((newToken, userData) => {
    setToken(newToken)
    setUser(userData)
    localStorage.setItem('token', newToken)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const data = await getMe()
      setUser(data.user || data)
    } catch {}
  }, [])

  return (
    <AuthContext.Provider
      value={{ user, token, login, logout, loading, isAuthenticated: !!token && !!user, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
