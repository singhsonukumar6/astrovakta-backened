import { Link } from 'react-router-dom'
import { Star, ExternalLink } from 'lucide-react'
import { useConfig } from '../lib/ConfigContext.jsx'

export default function Footer() {
  const { config } = useConfig()
  return (
    <footer
      style={{
        borderTop: '1px solid rgba(124,58,237,0.15)',
        padding: '48px 24px 32px',
        position: 'relative',
        zIndex: 1,
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          gap: 32,
        }}
      >
        <div style={{ maxWidth: 300 }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            {config.logo_url ? (
              <img src={config.logo_url} alt="logo" style={{ width: 22, height: 22, objectFit: 'contain' }} />
            ) : (
              <Star size={22} color="#7c3aed" fill="#7c3aed" />
            )}
            <span>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#0f172a' }}>Astro</span>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#d97706' }}>Vakta</span>
            </span>
          </Link>
          <p style={{ color: '#64748b', fontSize: 14, lineHeight: 1.7 }}>
            {config.footer_text || 'Create your complete astrology website and business — bookings, payments, WhatsApp, store, SEO — in a few clicks. Plus a 216+ endpoint astrology API for developers.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: 48, flexWrap: 'wrap' }}>
          <div>
            <h4 style={{ color: '#1e293b', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
              Product
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Link to="/pricing" style={{ color: '#64748b', fontSize: 14 }}>Pricing</Link>
              <Link to="/developer" style={{ color: '#64748b', fontSize: 14 }}>Developer Portal</Link>
              <Link to="/kundali-report" style={{ color: '#64748b', fontSize: 14 }}>Free Kundli Report</Link>
            </div>
          </div>
          <div>
            <h4 style={{ color: '#1e293b', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
              Developers
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Link to="/docs" style={{ color: '#64748b', fontSize: 14 }}>API Documentation</Link>
              <Link to="/sandbox" style={{ color: '#64748b', fontSize: 14 }}>API Sandbox</Link>
              <Link to="/blogs" style={{ color: '#64748b', fontSize: 14 }}>Blog</Link>
            </div>
          </div>
          <div>
            <h4 style={{ color: '#1e293b', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
              Company
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Link to="/about" style={{ color: '#64748b', fontSize: 14 }}>About</Link>
              <Link to="/contact" style={{ color: '#64748b', fontSize: 14 }}>Contact</Link>
            </div>
          </div>
          <div>
            <h4 style={{ color: '#1e293b', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
              Legal
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Link to="/privacy" style={{ color: '#64748b', fontSize: 14 }}>Privacy</Link>
              <Link to="/terms" style={{ color: '#64748b', fontSize: 14 }}>Terms</Link>
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          maxWidth: 1200,
          margin: '40px auto 0',
          paddingTop: 24,
          borderTop: '1px solid rgba(124,58,237,0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <p style={{ color: '#475569', fontSize: 13 }}>
          &copy; {new Date().getFullYear()} {config.site_title || 'AstroVakta'}. All rights reserved.
        </p>
        <div style={{ display: 'flex', gap: 16 }}>
          <a href="#" style={{ color: '#475569' }}><ExternalLink size={18} /></a>
          <a href="#" style={{ color: '#475569' }}><ExternalLink size={18} /></a>
        </div>
      </div>
    </footer>
  )
}
