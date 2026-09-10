import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'
import { CreateSiteWizard } from '../components/CreateSiteWizard.jsx'

// First-run flow: users without a website land here from /mysite and are
// sent back to the dashboard the moment their site is created.
export default function Onboarding() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f1f5f9' }}>
        <div className="gradient-text" style={{ fontSize: 18, fontWeight: 600 }}>Loading…</div>
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9', padding: '48px 20px 90px' }}>
      <style>{`
        .wiz-step-in { animation: wizStepIn 0.22s ease; }
        @keyframes wizStepIn { from { opacity: 0; transform: translateX(16px); } to { opacity: 1; transform: none; } }
      `}</style>
      <div style={{ maxWidth: 880, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 18 }}>
          <h1 style={{ fontSize: 34, fontWeight: 800, marginBottom: 10 }}>Create your website</h1>
          <p style={{ color: '#475569', fontSize: 16 }}>Live in under a minute — no coding, no design skills.</p>
        </div>
        <CreateSiteWizard onCreated={() => navigate('/mysite', { replace: true })} />
      </div>
    </div>
  )
}
