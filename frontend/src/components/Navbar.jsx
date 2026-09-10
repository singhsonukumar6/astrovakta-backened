import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, LogIn, LayoutDashboard, Globe } from 'lucide-react'
import { useAuth } from '../lib/auth.jsx'
import { useConfig } from '../lib/ConfigContext.jsx'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isAuthenticated, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { config } = useConfig()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => setMobileOpen(false), [location])

  const links = [
    { to: '/', label: 'Home' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/developer', label: 'Developers' },
    { to: '/blogs', label: 'Blog' },
    { to: '/contact', label: 'Contact' },
  ]

  return (
    <motion.nav
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        padding: '0 24px', height: 72, display: 'flex', alignItems: 'center',
        justifyContent: 'center',
        background: scrolled ? 'rgba(255,255,255,0.85)' : 'transparent',
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(20px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(124,58,237,0.15)' : '1px solid transparent',
        transition: 'all 0.3s ease',
      }}
    >
      <div style={{ width: '100%', maxWidth: 1200, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {config.logo_url ? (
            <img src={config.logo_url} alt="logo" style={{ width: 26, height: 26, objectFit: 'contain' }} />
          ) : null}
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 0 }}>
              <span style={{ fontSize: 22, fontWeight: 800, color: '#0f172a' }}>Astro</span>
              <span style={{ fontSize: 22, fontWeight: 800, color: '#d97706' }}>Vakta</span>
            </div>
            <span style={{ fontSize: 10, color: '#64748b', fontWeight: 500, display: 'block', marginTop: -2 }}>
              {config.site_tagline && !location.pathname.startsWith('/developer') ? config.site_tagline : location.pathname.startsWith('/developer') ? 'for developers' : 'for astrologers'}
            </span>
          </div>
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }} className="nav-desktop">
          {links.map((l) => (
            <Link key={l.to} to={l.to}
              style={{
                color: location.pathname === l.to ? '#4f46e5' : '#475569',
                fontWeight: 500, fontSize: 15, transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => (e.target.style.color = '#1e293b')}
              onMouseLeave={(e) => (e.target.style.color = location.pathname === l.to ? '#4f46e5' : '#475569')}
            >{l.label}</Link>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }} className="nav-desktop">
          {isAuthenticated ? (
            <>
              <button onClick={() => navigate('/mysite')} className="btn-secondary" style={{ padding: '10px 18px', fontSize: 14 }}>
                <Globe size={15} /> My Website
              </button>
              <button onClick={() => navigate('/dashboard')} className="btn-primary" style={{ padding: '10px 20px', fontSize: 14 }}>
                <LayoutDashboard size={16} /> Dashboard
              </button>
              <button onClick={() => { logout(); navigate('/') }} className="btn-secondary" style={{ padding: '10px 18px', fontSize: 14 }}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary" style={{ padding: '10px 20px', fontSize: 14 }}>Log In</Link>
              <Link to="/register" className="btn-primary" style={{ padding: '10px 20px', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                <LogIn size={16} /> Sign Up
              </Link>
            </>
          )}
        </div>

        <button className="nav-mobile-btn" onClick={() => setMobileOpen(!mobileOpen)}
          style={{ display: 'none', background: 'none', border: 'none', color: '#1e293b' }}>
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            style={{
              position: 'absolute', top: 72, left: 0, right: 0,
              background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(20px)',
              borderBottom: '1px solid rgba(124,58,237,0.2)',
              padding: '16px 24px 24px', display: 'flex', flexDirection: 'column', gap: 12,
            }}>
            {links.map((l) => (
              <Link key={l.to} to={l.to} style={{
                color: location.pathname === l.to ? '#4f46e5' : '#475569',
                fontWeight: 500, fontSize: 16, padding: '8px 0',
              }}>{l.label}</Link>
            ))}
            <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap' }}>
              {isAuthenticated ? (
                <>
                  <button onClick={() => navigate('/mysite')} className="btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>
                    <Globe size={15} /> My Website
                  </button>
                  <button onClick={() => navigate('/dashboard')} className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
                    Dashboard
                  </button>
                  <button onClick={() => { logout(); navigate('/') }} className="btn-secondary" style={{ flex: '1 1 100%', justifyContent: 'center' }}>
                    Log Out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn-secondary" style={{ flex: 1, justifyContent: 'center', display: 'flex', alignItems: 'center', padding: '10px 20px' }}>Log In</Link>
                  <Link to="/register" className="btn-primary" style={{ flex: 1, justifyContent: 'center', display: 'flex', alignItems: 'center', padding: '10px 20px' }}>Sign Up</Link>
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
