import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Star, Menu, X, LogIn, LayoutDashboard } from 'lucide-react'
import { useAuth } from '../lib/auth.jsx'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => setMobileOpen(false), [location])

  const links = [
    { to: '/', label: 'Home' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/kundali-report', label: 'Kundali Report' },
    { to: '/docs', label: 'Docs' },
    { to: '/sandbox', label: 'Sandbox' },
  ]

  return (
    <motion.nav
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        padding: '0 24px',
        height: 72,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: scrolled ? 'rgba(10,10,26,0.85)' : 'transparent',
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(20px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(124,58,237,0.15)' : '1px solid transparent',
        transition: 'all 0.3s ease',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 1200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Star size={28} color="#7c3aed" fill="#7c3aed" />
          <span
            style={{
              fontSize: 22,
              fontWeight: 800,
              background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AstroVakta
          </span>
        </Link>

        {/* Desktop links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }} className="nav-desktop">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              style={{
                color: location.pathname === l.to ? '#a78bfa' : '#94a3b8',
                fontWeight: 500,
                fontSize: 15,
                transition: 'color 0.2s',
                position: 'relative',
              }}
              onMouseEnter={(e) => (e.target.style.color = '#e2e8f0')}
              onMouseLeave={(e) =>
                (e.target.style.color = location.pathname === l.to ? '#a78bfa' : '#94a3b8')
              }
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }} className="nav-desktop">
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary"
              style={{ padding: '10px 20px', fontSize: 14 }}
            >
              <LayoutDashboard size={16} />
              Dashboard
            </button>
          ) : (
            <>
              <button
                onClick={() => navigate('/login')}
                className="btn-secondary"
                style={{ padding: '10px 20px', fontSize: 14 }}
              >
                Log In
              </button>
              <button
                onClick={() => navigate('/register')}
                className="btn-primary"
                style={{ padding: '10px 20px', fontSize: 14 }}
              >
                <LogIn size={16} />
                Sign Up
              </button>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="nav-mobile-btn"
          onClick={() => setMobileOpen(!mobileOpen)}
          style={{
            display: 'none',
            background: 'none',
            border: 'none',
            color: '#e2e8f0',
          }}
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            style={{
              position: 'absolute',
              top: 72,
              left: 0,
              right: 0,
              background: 'rgba(10,10,26,0.95)',
              backdropFilter: 'blur(20px)',
              borderBottom: '1px solid rgba(124,58,237,0.2)',
              padding: '16px 24px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                style={{
                  color: location.pathname === l.to ? '#a78bfa' : '#94a3b8',
                  fontWeight: 500,
                  fontSize: 16,
                  padding: '8px 0',
                }}
              >
                {l.label}
              </Link>
            ))}
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="btn-primary"
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  Dashboard
                </button>
              ) : (
                <>
                  <button
                    onClick={() => navigate('/login')}
                    className="btn-secondary"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    Log In
                  </button>
                  <button
                    onClick={() => navigate('/register')}
                    className="btn-primary"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 768px) {
          .nav-desktop { display: none !important; }
          .nav-mobile-btn { display: flex !important; }
        }
      `}</style>
    </motion.nav>
  )
}
