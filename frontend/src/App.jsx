import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import SeoManager from './components/SEO.jsx'
import Landing from './pages/Landing.jsx'
import Developer from './pages/Developer.jsx'
import Pricing from './pages/Pricing.jsx'
import Dashboard from './pages/Dashboard.jsx'
import MySite from './pages/MySite.jsx'
import TenantSite from './pages/TenantSite.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Sandbox from './pages/Sandbox.jsx'
import Admin from './pages/Admin.jsx'
import Docs from './pages/Docs.jsx'
import KundaliReport from './pages/KundaliReport.jsx'
import VerifyEmail from './pages/VerifyEmail.jsx'
import VerifyEmailPrompt from './pages/VerifyEmailPrompt.jsx'
import ForgotPassword from './pages/ForgotPassword.jsx'
import ResetPassword from './pages/ResetPassword.jsx'
import About from './pages/About.jsx'
import Contact from './pages/Contact.jsx'
import Privacy from './pages/Privacy.jsx'
import Terms from './pages/Terms.jsx'
import Blogs from './pages/Blogs.jsx'
import BlogPost from './pages/BlogPost.jsx'
import Starfield from './components/Starfield.jsx'
import { CLERK_ENABLED } from './lib/clerk.jsx'
import { resolveTenantHost } from './lib/tenant.js'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/developer" element={<Developer />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/mysite" element={<MySite />} />
      {/* Public tenant site (astrologer's branded website) */}
      <Route path="/s/:slug" element={<TenantSite />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/sandbox" element={<Sandbox />} />
      <Route path="/docs" element={<Docs />} />
      <Route path="/kundali-report" element={<KundaliReport />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/verify-email-prompt" element={<VerifyEmailPrompt />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/about" element={<About />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/blogs" element={<Blogs />} />
      <Route path="/blogs/:slug" element={<BlogPost />} />
      {/* Clerk handles auth when enabled; email+password pages otherwise. */}
      <Route path="/register" element={CLERK_ENABLED ? <Navigate to="/" replace /> : <Register />} />
      <Route path="/login" element={CLERK_ENABLED ? <Navigate to="/" replace /> : <Login />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  const { pathname } = useLocation()
  // Tenant sites are standalone brands — no platform navbar/footer/starfield.
  const isTenantSite = pathname.startsWith('/s/')

  if (isTenantSite) {
    return (
      <>
        <SeoManager />
        <AppRoutes />
      </>
    )
  }

  return (
    <>
      <SeoManager />
      <Starfield />
      <Navbar />
      <main style={{ flex: 1, position: 'relative', zIndex: 1 }}>
        <AppRoutes />
      </main>
      <Footer />
    </>
  )
}

// Rendered instead of the platform app when the browser is on a tenant host:
// pandit-rajesh.localhost (dev), pandit-rajesh.astrovakta.com (prod wildcard),
// or the astrologer's own custom domain.
export function TenantHostApp() {
  const tenant = resolveTenantHost(window.location.hostname)
  if (!tenant) return null
  return (
    <>
      <SeoManager />
      <TenantSite
        slug={tenant.type === 'slug' ? tenant.value : undefined}
        domain={tenant.type === 'domain' ? tenant.value : undefined}
      />
    </>
  )
}
