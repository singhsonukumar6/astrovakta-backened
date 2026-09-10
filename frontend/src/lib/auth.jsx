import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getMe } from './api.js'

const AuthContext = createContext(null)

/**
 * Email + password JWT auth. The token lives in localStorage; sessions are
 * hydrated on load via getMe() and dropped on a hard 401 (network errors keep
 * the token — they're transient).
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token || user) {
      if (!token) setLoading(false)
      return
    }
    let cancelled = false
    // Hydrating a stored session — hold `loading` until we know who this is.
    setLoading(true)
    getMe()
      .then((data) => {
        if (!cancelled) setUser(data.user || data)
      })
      .catch((err) => {
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
        user, token, login, logout, loading,
        isAuthenticated: !!token && !!user,
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
