import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useUser, useAuth as useClerkAuth, CLERK_ENABLED } from './clerk.jsx'
import api, { getMe } from './api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)
  const [clerkSyncing, setClerkSyncing] = useState(false)
  const { isLoaded: clerkLoaded, isSignedIn: clerkSignedIn } = useClerkAuth()
  const { user: clerkUser } = useUser()

  useEffect(() => {
    if (!clerkLoaded) return
    if (!clerkSignedIn) {
      // Clerk disabled (local/dev or key removed): email+password token auth
      // stays valid — only clear when Clerk is actually enabled and signed out.
      if (!CLERK_ENABLED) {
        // A stored token is being hydrated by the getMe effect below —
        // keep `loading` true until it settles so guards don't redirect early.
        if (!localStorage.getItem('token')) setLoading(false)
        return
      }
      setToken(null)
      setUser(null)
      localStorage.removeItem('token')
      setLoading(false)
      setClerkSyncing(false)
      return
    }

    const email = clerkUser?.primaryEmailAddress?.emailAddress
    const name = `${clerkUser?.firstName || ''} ${clerkUser?.lastName || ''}`.trim()
    const clerkId = clerkUser?.id

    if (token && user) {
      setLoading(false)
      setClerkSyncing(false)
      return
    }

    setClerkSyncing(true)
    api.post('/auth/clerk-sync', { clerk_id: clerkId, email, name })
      .then((res) => {
        const newToken = res.data?.token
        const newUser = res.data?.user
        if (newToken && newUser) {
          setToken(newToken)
          setUser(newUser)
          localStorage.setItem('token', newToken)
        }
      })
      .catch(() => {})
      .finally(() => {
        setLoading(false)
        setClerkSyncing(false)
      })
  }, [clerkLoaded, clerkSignedIn, clerkUser])

  useEffect(() => {
    if (!token || user) return
    let cancelled = false
    // Hydrating a stored session — hold `loading` until we know who this is.
    setLoading(true)
    getMe()
      .then((data) => {
        if (!cancelled) setUser(data.user || data)
      })
      .catch((err) => {
        // Invalid/expired session — drop the token so guards settle to
        // signed-out. Network errors keep the token (transient).
        if (!cancelled && err?.response?.status === 401) {
          setToken(null)
          localStorage.removeItem('token')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [token, user])

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
      value={{
        user, token, login, logout, loading, clerkSyncing,
        isAuthenticated: !!token && !!user,
        clerkSignedIn,
        refreshUser,
      }}
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
