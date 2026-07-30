import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useUser, useAuth as useClerkAuth } from '@clerk/clerk-react'
import api, { getMe } from './api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)
  const { isLoaded: clerkLoaded, isSignedIn: clerkSignedIn } = useClerkAuth()
  const { user: clerkUser } = useUser()

  useEffect(() => {
    if (!clerkLoaded) return
    if (!clerkSignedIn) {
      setToken(null)
      setUser(null)
      localStorage.removeItem('token')
      setLoading(false)
      return
    }

    const email = clerkUser?.primaryEmailAddress?.emailAddress
    const name = `${clerkUser?.firstName || ''} ${clerkUser?.lastName || ''}`.trim()
    const clerkId = clerkUser?.id

    if (token && user) return

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
      .finally(() => setLoading(false))
  }, [clerkLoaded, clerkSignedIn, clerkUser])

  useEffect(() => {
    if (!token || user) return
    let cancelled = false
    localStorage.setItem('token', token)
    getMe()
      .then((data) => {
        if (!cancelled) setUser(data.user || data)
      })
      .catch(() => {})
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
