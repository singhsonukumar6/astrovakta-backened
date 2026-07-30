import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { SignedOut, SignInButton } from '@clerk/clerk-react'
import {
  LayoutDashboard,
  Key,
  BarChart3,
  User,
  LogOut,
  Plus,
  Copy,
  Trash2,
  Eye,
  EyeOff,
  X,
  Activity,
  TrendingUp,
  Zap,
  Shield,
  FileText,
  Bot,
  Send,
  CheckCircle2,
  Clock,
  XCircle,
  Download,
  Sparkles,
  Settings,
  Mail,
  ScrollText,
  LogIn,
  Gauge,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth.jsx'
import KundaliReport from './KundaliReport.jsx'
import {
  getKeys, createKey, revokeKey,
  listProviders, createProvider, deleteProvider, testProvider,
  getMyJobs, submitPdfJob,
  updateProfile, changePassword,
  resendVerification,
  getUsageStats,
} from '../lib/api.js'

const tabs = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'keys', label: 'API Keys', icon: Key },
  { id: 'ai', label: 'AI Providers', icon: Bot },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'kundali', label: 'Kundali Report', icon: ScrollText },
  { id: 'usage', label: 'Usage', icon: BarChart3 },
  { id: 'profile', label: 'Profile', icon: User },
]

const providerMeta = {
  openai: { name: 'OpenAI', color: '#22c55e', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  anthropic: { name: 'Anthropic', color: '#d97706', models: ['claude-sonnet-4-20250514', 'claude-3-haiku-20240307'] },
  groq: { name: 'Groq', color: '#f59e0b', models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'] },
  together: { name: 'Together AI', color: '#8b5cf6', models: ['meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo'] },
}

const jobStatusColors = {
  pending: { bg: 'rgba(245,158,11,0.15)', text: '#fbbf24', icon: Clock },
  processing: { bg: 'rgba(59,130,246,0.15)', text: '#60a5fa', icon: Settings },
  completed: { bg: 'rgba(34,197,94,0.15)', text: '#22c55e', icon: CheckCircle2 },
  failed: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444', icon: XCircle },
}

// ──────────── OVERVIEW TAB ────────────
function Overview({ user, keys }) {
  const [resending, setResending] = useState(false)
  const totalKeys = keys?.length || 0
  const activeKeys = keys?.filter((k) => k.is_active).length || 0

  const handleResendVerification = async () => {
    setResending(true)
    try {
      await resendVerification(user?.email)
      toast.success('Verification email sent! Check your inbox.')
    } catch {
      toast.error('Failed to send verification email')
    } finally {
      setResending(false)
    }
  }

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Welcome back, <span className="gradient-text">{user?.name || 'User'}</span>
      </h2>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>
        Here's an overview of your AstroVakta developer account.
      </p>

      {user && !user.email_verified && (
        <div className="glass" style={{
          borderRadius: 'var(--radius-lg)', padding: 16, marginBottom: 24,
          border: '1px solid rgba(245,158,11,0.3)', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Mail size={18} color="#fbbf24" />
            <span style={{ color: '#fbbf24', fontSize: 14, fontWeight: 500 }}>
              Please verify your email address.
            </span>
          </div>
          <button
            onClick={handleResendVerification}
            disabled={resending}
            className="btn-secondary"
            style={{ fontSize: 13, padding: '6px 14px' }}
          >
            {resending ? 'Sending...' : 'Resend Verification'}
          </button>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 32 }}>
        {[
          { label: 'API Keys', value: totalKeys, icon: Key, color: '#7c3aed' },
          { label: 'Active Keys', value: activeKeys, icon: Activity, color: '#22c55e' },
          { label: 'Monthly Limit', value: (user?.monthly_limit ?? 0).toLocaleString(), icon: TrendingUp, color: '#3b82f6' },
          { label: 'Current Plan', value: user?.plan || 'Free', icon: Zap, color: '#f59e0b' },
        ].map((s) => (
          <div key={s.label} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 16 }}>
              <span style={{ color: '#94a3b8', fontSize: 14 }}>{s.label}</span>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: `${s.color}20`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <s.icon size={18} color={s.color} />
              </div>
            </div>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{s.value}</div>
          </div>
        ))}
      </div>

      {user?.is_admin && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <Shield size={20} color="#fbbf24" />
          <span style={{ color: '#e2e8f0', fontSize: 14 }}>
            You have admin access.
            <a href="/admin" style={{ color: '#a78bfa', marginLeft: 8, fontWeight: 600, textDecoration: 'underline' }}>Open Admin Panel →</a>
          </span>
        </div>
      )}

      <style>{`
        @media (max-width: 640px) {
          .overview-verify { flex-direction: column !important; align-items: flex-start !important; }
        }
      `}</style>
    </div>
  )
}

// ──────────── API KEYS TAB ────────────
function APIKeys({ keys, onRefresh }) {
  const [showModal, setShowModal] = useState(false)
  const [newName, setNewName] = useState('')
  const [newTier, setNewTier] = useState('free')
  const [loading, setLoading] = useState(false)
  const [showKey, setShowKey] = useState({})

  const handleCreate = async () => {
    if (!newName) return toast.error('Enter a key name')
    setLoading(true)
    try {
      await createKey(newName, newTier)
      toast.success('API key created!')
      setShowModal(false)
      setNewName('')
      onRefresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create key')
    } finally { setLoading(false) }
  }

  const handleRevoke = async (keyId) => {
    if (!confirm('Revoke this key? This cannot be undone.')) return
    try {
      await revokeKey(keyId)
      toast.success('Key revoked')
      onRefresh()
    } catch { toast.error('Failed to revoke key') }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => toast.success('Copied!'),
      () => toast.error('Failed to copy'),
    )
  }

  const maskKey = (k, id) => showKey[id] ? k : k?.slice(0, 10) + '...' + k?.slice(-4)

  return (
    <div>
      <div className="tab-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>API Keys</h2>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Manage API keys for accessing the Vedic Astrology API.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)} style={{ fontSize: 14, flexShrink: 0 }}>
          <Plus size={16} /> New Key
        </button>
      </div>

      {keys?.length === 0 ? (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center' }}>
          <Key size={48} color="#475569" style={{ marginBottom: 16 }} />
          <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 24 }}>No API keys yet</p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Create Your First Key
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {keys?.map((k) => (
            <div key={k.id} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
              <div className="key-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>{k.name}</span>
                  <span className="badge" style={{ background: 'rgba(124,58,237,0.15)', color: '#a78bfa', textTransform: 'capitalize' }}>{k.tier}</span>
                  <span style={{ color: k.is_active ? '#22c55e' : '#ef4444', fontWeight: 500, fontSize: 13 }}>{k.is_active ? 'Active' : 'Revoked'}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ color: '#64748b', fontSize: 13 }}>{k.request_count || 0} requests</span>
                  {k.is_active && (
                    <button onClick={() => handleRevoke(k.id)} style={{ background: 'rgba(239,68,68,0.1)', border: 'none', borderRadius: 8, padding: '6px 12px', color: '#ef4444', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>Revoke</button>
                  )}
                </div>
              </div>
              <div className="key-value-row" style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(10,10,26,0.6)', borderRadius: 10, padding: '10px 14px' }}>
                <Key size={14} color="#64748b" />
                <code style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 13, color: '#e2e8f0', wordBreak: 'break-all', lineHeight: 1.5 }}>
                  {maskKey(k.key, k.id)}
                </code>
                <button onClick={() => setShowKey((p) => ({ ...p, [k.id]: !p[k.id] }))} style={{ background: 'rgba(100,116,139,0.1)', border: 'none', borderRadius: 6, padding: '6px 8px', color: '#94a3b8', cursor: 'pointer' }}>
                  {showKey[k.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <button onClick={() => copyToClipboard(k.key)} style={{ background: 'rgba(124,58,237,0.15)', border: 'none', borderRadius: 6, padding: '6px 10px', color: '#a78bfa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 600, flexShrink: 0 }}>
                  <Copy size={13} /> Copy
                </button>
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 10 }}>
                <span style={{ color: '#64748b', fontSize: 12 }}>Created: {k.created_at ? new Date(k.created_at).toLocaleDateString() : '-'}</span>
                {k.last_used_at && <span style={{ color: '#64748b', fontSize: 12 }}>Last used: {new Date(k.last_used_at).toLocaleString()}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200, padding: 24 }}
            onClick={() => setShowModal(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()} className="glass"
              style={{ borderRadius: 'var(--radius-lg)', padding: 32, width: '100%', maxWidth: 420, maxHeight: '90vh', overflowY: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <h3 style={{ fontSize: 20, fontWeight: 700 }}>Create API Key</h3>
                <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={20} /></button>
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Key Name</label>
                <input className="input-field" placeholder="e.g. My App Key" value={newName} onChange={(e) => setNewName(e.target.value)} />
              </div>
              <div style={{ marginBottom: 24 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Plan Tier</label>
                <select className="input-field" value={newTier} onChange={(e) => setNewTier(e.target.value)}>
                  <option value="free">Free (100 req/day)</option>
                  <option value="starter">Starter (1K req/day)</option>
                  <option value="pro">Pro (10K req/day)</option>
                </select>
              </div>
              <button className="btn-primary" onClick={handleCreate} disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
                {loading ? 'Creating...' : 'Create Key'}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 640px) {
          .tab-header { flex-direction: column !important; align-items: flex-start !important; gap: 12px !important; }
          .tab-header .btn-primary { width: 100% !important; justify-content: center !important; }
        }
      `}</style>
    </div>
  )
}

// ──────────── AI PROVIDERS TAB ────────────
function AIProvidersTab() {
  const [providers, setProviders] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ provider: 'openai', api_key: '', model: '' })
  const [testing, setTesting] = useState(null)

  const load = () => {
    listProviders().then((data) => {
      setProviders(Array.isArray(data) ? data : data.providers || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleAdd = async () => {
    if (!form.api_key) return toast.error('Enter an API key')
    try {
      await createProvider(form)
      toast.success('Provider added!')
      setShowModal(false)
      setForm({ provider: 'openai', api_key: '', model: '' })
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add provider')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this provider?')) return
    try {
      await deleteProvider(id)
      toast.success('Provider deleted')
      load()
    } catch { toast.error('Failed to delete') }
  }

  const handleTest = async (id) => {
    setTesting(id)
    try {
      const result = await testProvider(id)
      toast.success(result.message || 'Connection successful!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Connection failed')
    } finally { setTesting(null) }
  }

  if (loading) return <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading providers...</div>

  return (
    <div>
      <div className="tab-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>AI Providers</h2>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Configure your own AI API keys for the /ai/* endpoints. Your keys are encrypted at rest.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)} style={{ fontSize: 14, flexShrink: 0 }}>
          <Plus size={16} /> Add Provider
        </button>
      </div>

      {providers.length === 0 ? (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center' }}>
          <Bot size={48} color="#475569" style={{ marginBottom: 16 }} />
          <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 8 }}>No AI providers configured</p>
          <p style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>Add your own API key to enable AI-powered birth chart interpretations.</p>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Add Your First Provider
          </button>
        </div>
      ) : (
        <div className="provider-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {providers.map((p) => {
            const meta = providerMeta[p.provider] || { name: p.provider, color: '#7c3aed' }
            return (
              <div key={p.id} className="glass card-glow" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: `${meta.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Bot size={18} color={meta.color} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>{meta.name}</div>
                      <div style={{ fontSize: 12, color: '#64748b' }}>{p.model || 'Default model'}</div>
                    </div>
                  </div>
                  <span style={{ display: 'inline-block', padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: p.is_active ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: p.is_active ? '#22c55e' : '#ef4444' }}>
                    {p.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(10,10,26,0.6)', borderRadius: 8, padding: '8px 12px', marginBottom: 16 }}>
                  <Key size={12} color="#64748b" />
                  <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#94a3b8' }}>{p.masked_key || '••••••••'}</code>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-secondary" onClick={() => handleTest(p.id)} disabled={testing === p.id} style={{ flex: 1, justifyContent: 'center', padding: '8px 12px', fontSize: 12 }}>
                    {testing === p.id ? 'Testing...' : 'Test'}
                  </button>
                  <button onClick={() => handleDelete(p.id)} style={{ background: 'rgba(239,68,68,0.1)', border: 'none', borderRadius: 8, padding: '8px 12px', color: '#ef4444', cursor: 'pointer', fontSize: 12 }}>
                    Delete
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200, padding: 24 }}
            onClick={() => setShowModal(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()} className="glass"
              style={{ borderRadius: 'var(--radius-lg)', padding: 32, width: '100%', maxWidth: 460 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <h3 style={{ fontSize: 20, fontWeight: 700 }}>Add AI Provider</h3>
                <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={20} /></button>
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Provider</label>
                <select className="input-field" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value, model: '' })}>
                  {Object.entries(providerMeta).map(([k, v]) => (
                    <option key={k} value={k}>{v.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>API Key</label>
                <input className="input-field" type="password" placeholder="sk-..." value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
              </div>
              <div style={{ marginBottom: 24 }}>
                <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Model (optional)</label>
                <select className="input-field" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}>
                  <option value="">Default</option>
                  {(providerMeta[form.provider]?.models || []).map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <button className="btn-primary" onClick={handleAdd} style={{ width: '100%', justifyContent: 'center' }}>Add Provider</button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 640px) {
          .tab-header { flex-direction: column !important; align-items: flex-start !important; gap: 12px !important; }
          .tab-header .btn-primary { width: 100% !important; justify-content: center !important; }
          .provider-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

// ──────────── REPORTS TAB ────────────
function ReportsTab() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showSubmit, setShowSubmit] = useState(false)
  const [form, setForm] = useState({
    dateOfBirth: '1990-05-15', timeOfBirth: '14:30',
    latitude: 28.6139, longitude: 77.2090, timezone: 'Asia/Kolkata',
    reportTitle: 'Vedic Birth Chart Report',
    clientName: '',
  })
  const [submitting, setSubmitting] = useState(false)

  const load = () => {
    getMyJobs().then((data) => {
      setJobs(Array.isArray(data) ? data : data.jobs || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await submitPdfJob(form)
      toast.success('PDF job submitted!')
      setShowSubmit(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit job')
    } finally { setSubmitting(false) }
  }

  if (loading) return <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading reports...</div>

  return (
    <div>
      <div className="tab-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>PDF Reports</h2>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Generate and download branded Vedic birth chart reports.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowSubmit(true)} style={{ fontSize: 14, flexShrink: 0 }}>
          <FileText size={16} /> Generate Report
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center' }}>
          <FileText size={48} color="#475569" style={{ marginBottom: 16 }} />
          <p style={{ color: '#94a3b8', fontSize: 16, marginBottom: 24 }}>No reports yet</p>
          <button className="btn-primary" onClick={() => setShowSubmit(true)}>Generate Your First Report</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {jobs.map((j) => {
            const sc = jobStatusColors[j.status] || jobStatusColors.pending
            const StatusIcon = sc.icon
            return (
              <div key={j.id} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <FileText size={18} color="#ec4899" />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{j.job_type?.toUpperCase()} Report #{j.id}</div>
                      <div style={{ fontSize: 12, color: '#64748b' }}>
                        Created: {j.created_at ? new Date(j.created_at).toLocaleString() : '-'}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: sc.bg, color: sc.text }}>
                      <StatusIcon size={14} /> {j.status}
                    </span>
                    {j.status === 'completed' && (
                      <a href={`/jobs/${j.id}/download`} target="_blank" rel="noopener"
                        style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 8, background: 'rgba(34,197,94,0.15)', color: '#22c55e', fontWeight: 600, fontSize: 13, textDecoration: 'none' }}>
                        <Download size={14} /> Download
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <AnimatePresence>
        {showSubmit && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200, padding: 24 }}
            onClick={() => setShowSubmit(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()} className="glass"
              style={{ borderRadius: 'var(--radius-lg)', padding: 32, width: '100%', maxWidth: 480, maxHeight: '80vh', overflowY: 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <h3 style={{ fontSize: 20, fontWeight: 700 }}>Generate PDF Report</h3>
                <button onClick={() => setShowSubmit(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={20} /></button>
              </div>
              <div className="report-form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Birth Date</label>
                  <input className="input-field" type="date" value={form.dateOfBirth} onChange={(e) => setForm({ ...form, dateOfBirth: e.target.value })} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Birth Time</label>
                  <input className="input-field" type="time" value={form.timeOfBirth} onChange={(e) => setForm({ ...form, timeOfBirth: e.target.value })} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Latitude</label>
                  <input className="input-field" type="number" step="0.0001" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) || 0 })} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Longitude</label>
                  <input className="input-field" type="number" step="0.0001" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) || 0 })} />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Timezone</label>
                  <input className="input-field" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Client Name (optional)</label>
                  <input className="input-field" value={form.clientName} onChange={(e) => setForm({ ...form, clientName: e.target.value })} placeholder="e.g. Ravi Kumar" />
                </div>
              </div>
              <button className="btn-primary" onClick={handleSubmit} disabled={submitting} style={{ width: '100%', justifyContent: 'center', marginTop: 24 }}>
                {submitting ? 'Submitting...' : 'Submit PDF Job'}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 640px) {
          .tab-header { flex-direction: column !important; align-items: flex-start !important; gap: 12px !important; }
          .tab-header .btn-primary { width: 100% !important; justify-content: center !important; }
          .report-form-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

// ──────────── USAGE TAB ────────────
function UsagePanel({ keys }) {
  const [usage, setUsage] = useState(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()

  useEffect(() => {
    const activeKey = keys?.find((k) => k.is_active)
    if (activeKey) {
      getUsageStats(activeKey.id).then((data) => {
        setUsage(data)
      }).catch(() => {}).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [keys])

  if (loading) return <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading usage...</div>

  const monthlyLimit = usage?.monthly_limit || user?.monthly_limit || 0
  const used = usage?.requests_this_month || 0
  const pct = monthlyLimit > 0 ? Math.min(100, (used / monthlyLimit) * 100) : 0
  const remaining = Math.max(0, monthlyLimit - used)
  const pctColor = pct > 80 ? '#ef4444' : pct > 60 ? '#f59e0b' : '#22c55e'

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Usage Monitor</h2>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>Track your monthly API usage and limits.</p>

      {!keys?.length && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 40, textAlign: 'center', marginBottom: 24 }}>
          <Activity size={40} color="#64748b" style={{ marginBottom: 16 }} />
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>No API Keys Yet</h3>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Create an API key from the API Keys tab to start tracking usage.</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Used This Month', value: used.toLocaleString(), icon: TrendingUp, color: '#7c3aed', bg: 'rgba(124,58,237,0.08)' },
          { label: 'Monthly Limit', value: monthlyLimit.toLocaleString(), icon: Gauge, color: '#3b82f6', bg: 'rgba(59,130,246,0.08)' },
          { label: 'Remaining', value: remaining.toLocaleString(), icon: Zap, color: '#22c55e', bg: 'rgba(34,197,94,0.08)' },
          { label: 'Today', value: (usage?.requests_today || 0).toLocaleString(), icon: Clock, color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
        ].map((stat) => (
          <div key={stat.label} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: stat.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <stat.icon size={16} color={stat.color} />
              </div>
              <span style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>{stat.label}</span>
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, lineHeight: 1 }}>{stat.value}</div>
          </div>
        ))}
      </div>

      {monthlyLimit > 0 && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: '#94a3b8', marginBottom: 16 }}>Monthly Progress</h3>
          <div style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 13, color: '#cbd5e1' }}>{used.toLocaleString()} / {monthlyLimit.toLocaleString()} calls</span>
              <span style={{ fontSize: 13, color: pctColor, fontWeight: 700 }}>{pct.toFixed(0)}%</span>
            </div>
            <div style={{ height: 12, background: 'rgba(124,58,237,0.08)', borderRadius: 6, overflow: 'hidden' }}>
              <div style={{
                height: '100%', width: `${pct}%`,
                background: `linear-gradient(to right, ${pctColor}, ${pctColor}cc)`,
                borderRadius: 6, transition: 'width 0.5s ease',
              }} />
            </div>
          </div>
          {pct >= 80 && (
            <p style={{ color: '#ef4444', fontSize: 13, marginTop: 12 }}>
              You're approaching your monthly limit. Consider upgrading your plan.
            </p>
          )}
        </div>
      )}

      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
        <h3 style={{ fontSize: 14, color: '#94a3b8', marginBottom: 16 }}>Endpoint Breakdown</h3>
        {!usage?.top_endpoints?.length ? (
          <p style={{ color: '#475569', textAlign: 'center', padding: 40 }}>
            {keys?.length ? 'No usage data yet — make some API calls!' : 'Create an API key and start making requests.'}
          </p>
        ) : (
          usage.top_endpoints.slice(0, 8).map((ep) => {
            const maxHits = usage.top_endpoints[0]?.hits || 1
            const epPct = (ep.hits / maxHits) * 100
            return (
              <div key={ep.endpoint} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#cbd5e1', maxWidth: '70%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {ep.endpoint}
                  </span>
                  <span style={{ fontSize: 12, color: '#94a3b8' }}>{ep.hits}</span>
                </div>
                <div style={{ height: 6, background: 'rgba(124,58,237,0.08)', borderRadius: 3 }}>
                  <div style={{ height: '100%', width: `${epPct}%`, background: 'var(--gradient-primary)', borderRadius: 3, transition: 'width 0.3s ease' }} />
                </div>
              </div>
            )
          })
        )}
      </div>

      <style>{`
        @media (max-width: 640px) {
          .usage-grid { grid-template-columns: repeat(2, 1fr) !important; }
        }
      `}</style>
    </div>
  )
}

// ──────────── PROFILE TAB ────────────
function Profile({ user, onUserUpdate }) {
  const [editing, setEditing] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [name, setName] = useState(user?.name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setName(user?.name || '')
    setEmail(user?.email || '')
  }, [user])

  const handleProfileSave = async () => {
    if (!name.trim()) return toast.error('Name is required')
    if (!email.trim()) return toast.error('Email is required')
    setSaving(true)
    try {
      const updated = await updateProfile({ name: name.trim(), email: email.trim() })
      onUserUpdate(updated)
      setEditing(false)
      toast.success('Profile updated!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update profile')
    } finally { setSaving(false) }
  }

  const handlePasswordChange = async () => {
    if (!currentPassword) return toast.error('Enter current password')
    if (!newPassword) return toast.error('Enter new password')
    if (newPassword.length < 6) return toast.error('Password must be at least 6 characters')
    if (newPassword !== confirmPassword) return toast.error('Passwords do not match')
    setSaving(true)
    try {
      await changePassword(currentPassword, newPassword)
      toast.success('Password changed!')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setShowPassword(false)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password')
    } finally { setSaving(false) }
  }

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Profile</h2>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>Manage your account details and password.</p>

      {/* Profile Info */}
      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 32, maxWidth: 500, marginBottom: 24, width: '100%' }}>
        <div className="profile-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Account Details</h3>
          {!editing ? (
            <button className="btn-secondary" onClick={() => setEditing(true)} style={{ fontSize: 13, padding: '8px 16px' }}>
              Edit Profile
            </button>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-secondary" onClick={() => { setEditing(false); setName(user?.name || ''); setEmail(user?.email || '') }} style={{ fontSize: 13, padding: '8px 16px' }}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleProfileSave} disabled={saving} style={{ fontSize: 13, padding: '8px 16px' }}>
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Name</label>
          <input className="input-field" value={name} onChange={(e) => setName(e.target.value)} readOnly={!editing} style={{ opacity: editing ? 1 : 0.7 }} />
        </div>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Email</label>
          <input className="input-field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} readOnly={!editing} style={{ opacity: editing ? 1 : 0.7 }} />
        </div>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Plan</label>
          <span className="badge" style={{ background: 'rgba(124,58,237,0.15)', color: '#a78bfa', textTransform: 'capitalize', fontSize: 14, padding: '6px 14px' }}>
            {user?.plan || 'Free'}
          </span>
        </div>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Email Status</label>
          {user?.email_verified ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 12, fontSize: 13, fontWeight: 600, background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
              <CheckCircle2 size={14} /> Verified
            </span>
          ) : (
            <button
              className="btn-secondary"
              onClick={async () => {
                try {
                  await resendVerification(user?.email)
                  toast.success('Verification email sent!')
                } catch { toast.error('Failed to send') }
              }}
              style={{ fontSize: 13, padding: '6px 14px' }}
            >
              <Mail size={14} /> Verify Email
            </button>
          )}
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Member Since</label>
          <input className="input-field" value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'} readOnly />
        </div>
      </div>

      {/* Password Change */}
      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 32, maxWidth: 500, width: '100%' }}>
        <div className="profile-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Change Password</h3>
          {!showPassword ? (
            <button className="btn-secondary" onClick={() => setShowPassword(true)} style={{ fontSize: 13, padding: '8px 16px' }}>
              Change Password
            </button>
          ) : (
            <button className="btn-secondary" onClick={() => { setShowPassword(false); setCurrentPassword(''); setNewPassword(''); setConfirmPassword('') }} style={{ fontSize: 13, padding: '8px 16px' }}>
              Cancel
            </button>
          )}
        </div>

        {showPassword && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Current Password</label>
              <input className="input-field" type="password" placeholder="Enter current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>New Password</label>
              <input className="input-field" type="password" placeholder="Min 6 characters" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Confirm New Password</label>
              <input className="input-field" type="password" placeholder="Re-enter new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
            </div>
            <button className="btn-primary" onClick={handlePasswordChange} disabled={saving} style={{ width: '100%', justifyContent: 'center' }}>
              {saving ? 'Updating...' : 'Update Password'}
            </button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

// ──────────── MAIN DASHBOARD ────────────
export default function Dashboard() {
  const { user, logout, isAuthenticated, loading: authLoading, clerkSyncing, clerkSignedIn } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [keys, setKeys] = useState([])
  const [localUser, setLocalUser] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    setLocalUser(user)
  }, [user])

  useEffect(() => {
    if (!authLoading && !clerkSignedIn) navigate('/')
  }, [authLoading, clerkSignedIn, navigate])

  useEffect(() => {
    setActiveTab('overview')
  }, [location.key])

  useEffect(() => {
    if (isAuthenticated && user && !user.email_verified && !clerkSignedIn) {
      navigate('/verify-email-prompt', { state: { email: user.email } })
    }
  }, [isAuthenticated, user, clerkSignedIn, navigate])

  useEffect(() => {
    if (isAuthenticated) {
      getKeys().then((data) => setKeys(Array.isArray(data) ? data : data.keys || [])).catch(() => {})
    }
  }, [isAuthenticated])

  useEffect(() => {
    setSidebarOpen(false)
  }, [activeTab])

  const refreshKeys = () => {
    getKeys().then((data) => setKeys(Array.isArray(data) ? data : data.keys || [])).catch(() => {})
  }

  const handleUserUpdate = (updated) => {
    setLocalUser(updated)
  }

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72 }}>
        <div className="gradient-text" style={{ fontSize: 18, fontWeight: 600 }}>Loading...</div>
      </div>
    )
  }

  if (!clerkSignedIn) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72, flexDirection: 'column', gap: 20 }}>
        <Shield size={48} color="#64748b" />
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Access Required</h2>
        <p style={{ color: '#94a3b8', fontSize: 15, maxWidth: 360, textAlign: 'center' }}>
          You need to sign in to access the dashboard.
        </p>
        <SignedOut>
          <SignInButton mode="modal">
            <button className="btn-primary" style={{ padding: '14px 32px', fontSize: 16 }}>
              <LogIn size={18} /> Sign In
            </button>
          </SignInButton>
        </SignedOut>
      </div>
    )
  }

  const displayUser = localUser || user

  return (
    <div style={{ minHeight: '100vh', paddingTop: 72 }}>
      {/* Desktop sidebar */}
      <aside className="dash-sidebar" style={{
        width: 240, borderRight: '1px solid var(--border-color)',
        padding: '24px 12px', display: 'flex', flexDirection: 'column',
        position: 'fixed', top: 72, left: 0, bottom: 0, zIndex: 40,
      }}>
        <div style={{ flex: 1 }}>
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 14px', borderRadius: 10, border: 'none',
                background: activeTab === tab.id ? 'rgba(124,58,237,0.15)' : 'transparent',
                color: activeTab === tab.id ? '#a78bfa' : '#94a3b8',
                fontSize: 14, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s',
                marginBottom: 4, textAlign: 'left',
              }}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>
        {user?.is_admin && (
          <button onClick={() => navigate('/admin')}
            style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
              borderRadius: 10, border: '1px solid rgba(245,158,11,0.3)',
              background: 'rgba(245,158,11,0.08)', color: '#fbbf24', fontSize: 13,
              fontWeight: 600, cursor: 'pointer', textAlign: 'left', marginBottom: 4,
            }}
          >
            <Shield size={16} /> Admin Panel
          </button>
        )}
        <button onClick={() => { logout(); navigate('/'); }}
          style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, border: 'none', background: 'transparent', color: '#94a3b8', fontSize: 14, cursor: 'pointer', textAlign: 'left' }}>
          <LogOut size={18} /> Log Out
        </button>
      </aside>

      {/* Mobile bottom tab bar */}
      <nav className="dash-bottombar">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? 'active' : ''}
          >
            <tab.icon size={20} />
            <span>{tab.label}</span>
          </button>
        ))}
        {user?.is_admin && (
          <button onClick={() => navigate('/admin')}>
            <Shield size={20} />
            <span>Admin</span>
          </button>
        )}
        <button onClick={() => { logout(); navigate('/'); }}>
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </nav>

      <main className="dash-main" style={{ padding: 32, overflow: 'auto' }}>
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
            {activeTab === 'overview' && <Overview user={displayUser} keys={keys} />}
            {activeTab === 'keys' && <APIKeys keys={keys} onRefresh={refreshKeys} />}
            {activeTab === 'ai' && <AIProvidersTab />}
            {activeTab === 'reports' && <ReportsTab />}
            {activeTab === 'kundali' && <KundaliReport />}
            {activeTab === 'usage' && <UsagePanel keys={keys} />}
            {activeTab === 'profile' && <Profile user={displayUser} onUserUpdate={handleUserUpdate} />}
          </motion.div>
        </AnimatePresence>
      </main>

      <style>{`
        .dash-main { margin-left: 240px; }
        .dash-bottombar { display: none; }

        @media (max-width: 768px) {
          .dash-sidebar { display: none !important; }
          .dash-main { margin-left: 0 !important; padding: 20px 16px !important; padding-bottom: 90px !important; }
          .dash-bottombar {
            display: flex !important;
            position: fixed; bottom: 0; left: 0; right: 0;
            background: rgba(10,10,26,0.95); backdrop-filter: blur(12px);
            border-top: 1px solid var(--border-color);
            z-index: 50; padding: 6px 8px;
            justify-content: space-around;
          }
          .dash-bottombar button {
            display: flex; flex-direction: column; align-items: center; gap: 3px;
            padding: 6px 4px; border: none; background: none;
            color: #64748b; font-size: 10px; cursor: pointer; border-radius: 8px;
            min-width: 0; flex: 1;
          }
          .dash-bottombar button.active { color: #a78bfa; background: rgba(124,58,237,0.1); }
          .dash-bottombar button svg { flex-shrink: 0; }
        }

        @media (max-width: 480px) {
          .dash-main { padding: 16px 12px !important; padding-bottom: 90px !important; }
        }
      `}</style>
    </div>
  )
}
