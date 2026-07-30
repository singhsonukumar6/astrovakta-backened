import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield,
  Users,
  Key,
  Activity,
  BarChart3,
  Briefcase,
  Search,
  ChevronLeft,
  ChevronRight,
  Trash2,
  ToggleLeft,
  ToggleRight,
  RefreshCw,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  ExternalLink,
  User,
  Terminal,
  Plus,
  Eye,
  EyeOff,
  Copy,
  Lock,
  Unlock,
  X,
  Send,
  Globe,
  ArrowRight,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth.jsx'
import {
  adminGetUsers,
  adminUpdatePlan,
  adminToggleAdmin,
  adminDeleteUser,
  adminGetKeys,
  adminRevokeKey,
  adminUpdateKeyTier,
  adminGetStats,
  adminGetJobs,
  updateProfile,
  changePassword,
  adminResetPassword,
  adminCreateKeyForUser,
  adminGetUserUsage,
  adminGetUsageDaily,
  adminGetUsageByUser,
  adminGetUsageEndpoints,
  adminSetMonthlyLimit,
  getKeys,
} from '../lib/api.js'
import api from '../lib/api.js'

const tabs = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'keys', label: 'API Keys', icon: Key },
  { id: 'jobs', label: 'Jobs', icon: Briefcase },
  { id: 'usage', label: 'Analytics', icon: Activity },
  { id: 'sandbox', label: 'Sandbox', icon: Terminal },
  { id: 'profile', label: 'Profile', icon: User },
]

const planColors = {
  free: { bg: 'rgba(100,116,139,0.15)', text: '#94a3b8' },
  starter: { bg: 'rgba(59,130,246,0.15)', text: '#60a5fa' },
  pro: { bg: 'rgba(124,58,237,0.15)', text: '#a78bfa' },
  enterprise: { bg: 'rgba(245,158,11,0.15)', text: '#fbbf24' },
}

const statusColors = {
  pending: { bg: 'rgba(245,158,11,0.15)', text: '#fbbf24', icon: Clock },
  processing: { bg: 'rgba(59,130,246,0.15)', text: '#60a5fa', icon: RefreshCw },
  completed: { bg: 'rgba(34,197,94,0.15)', text: '#22c55e', icon: CheckCircle2 },
  failed: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444', icon: XCircle },
}

// ──────────── OVERVIEW TAB ────────────
function OverviewTab({ stats }) {
  if (!stats) return <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading stats...</div>

  const cards = [
    { label: 'Total Users', value: stats.total_users, sub: `+${stats.new_users_today} today`, icon: Users, color: '#7c3aed' },
    { label: 'Active Keys', value: stats.active_keys, sub: `${stats.total_keys} total`, icon: Key, color: '#22c55e' },
    { label: 'Requests Today', value: stats.requests_today, sub: `${stats.total_requests} all time`, icon: TrendingUp, color: '#3b82f6' },
    { label: 'Pending Jobs', value: stats.pending_jobs, sub: `${stats.processing_jobs} processing`, icon: Briefcase, color: '#f59e0b' },
  ]

  const planDist = stats.plan_distribution || {}

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Admin <span className="gradient-text">Overview</span>
      </h2>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>System-wide statistics and health.</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 32 }}>
        {cards.map((c) => (
          <div key={c.label} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 16 }}>
              <span style={{ color: '#94a3b8', fontSize: 14 }}>{c.label}</span>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: `${c.color}20`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <c.icon size={18} color={c.color} />
              </div>
            </div>
            <div style={{ fontSize: 28, fontWeight: 800 }}>{c.value ?? 0}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Plan Distribution</h3>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {['free', 'starter', 'pro', 'enterprise'].map((plan) => (
            <div key={plan} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 18px', borderRadius: 10,
              background: planColors[plan]?.bg || planColors.free.bg,
            }}>
              <span style={{ color: planColors[plan]?.text || '#94a3b8', fontWeight: 700, fontSize: 20 }}>
                {planDist[plan] || 0}
              </span>
              <span style={{ color: '#94a3b8', fontSize: 13, textTransform: 'capitalize' }}>{plan}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ──────────── USERS TAB ────────────
function UsersTab({ refreshTrigger }) {
  const [users, setUsers] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedUser, setExpandedUser] = useState(null)
  const [userUsage, setUserUsage] = useState(null)
  const [showResetPw, setShowResetPw] = useState(null)
  const [resetPw, setResetPw] = useState('')
  const [showCreateKey, setShowCreateKey] = useState(null)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyTier, setNewKeyTier] = useState('free')
  const [showKey, setShowKey] = useState({})

  const load = useCallback(async (p, s) => {
    setLoading(true)
    try {
      const data = await adminGetUsers(p, s)
      setUsers(data.users || [])
      setTotalPages(data.total_pages || 1)
    } catch { toast.error('Failed to load users') }
    setLoading(false)
  }, [])

  useEffect(() => { load(page, search) }, [page, refreshTrigger])

  const handleSearch = () => { setPage(1); load(1, search) }

  const handlePlanChange = async (userId, newPlan) => {
    try {
      await adminUpdatePlan(userId, newPlan)
      toast.success('Plan updated')
      load(page, search)
    } catch { toast.error('Failed to update plan') }
  }

  const handleSetMonthlyLimit = async (userId, limit) => {
    try {
      await adminSetMonthlyLimit(userId, parseInt(limit) || 0)
      toast.success('Monthly limit updated')
      load(page, search)
    } catch { toast.error('Failed to update monthly limit') }
  }

  const handleToggleAdmin = async (userId) => {
    try {
      await adminToggleAdmin(userId)
      toast.success('Admin status toggled')
      load(page, search)
    } catch { toast.error('Failed to toggle admin') }
  }

  const handleDelete = async (userId) => {
    if (!confirm('Delete this user? All keys will be revoked.')) return
    try {
      await adminDeleteUser(userId)
      toast.success('User deleted')
      load(page, search)
    } catch { toast.error('Failed to delete user') }
  }

  const handleResetPassword = async (userId) => {
    if (!resetPw || resetPw.length < 6) return toast.error('Password must be at least 6 characters')
    try {
      await adminResetPassword(userId, resetPw)
      toast.success('Password reset successfully')
      setShowResetPw(null)
      setResetPw('')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reset password')
    }
  }

  const handleCreateKey = async (userId) => {
    if (!newKeyName) return toast.error('Enter a key name')
    try {
      const result = await adminCreateKeyForUser(userId, newKeyName, newKeyTier)
      toast.success('Key created!')
      setShowCreateKey(null)
      setNewKeyName('')
      load(page, search)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create key')
    }
  }

  const handleViewUsage = async (userId) => {
    setExpandedUser(userId)
    try {
      const data = await adminGetUserUsage(userId)
      setUserUsage(data)
    } catch { toast.error('Failed to load usage') }
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Users</h2>
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Manage users, passwords, plans, and keys.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            className="input-field"
            placeholder="Search name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            style={{ width: 240, fontSize: 13 }}
          />
          <button className="btn-secondary" onClick={handleSearch} style={{ padding: '10px 16px', fontSize: 13 }}>
            <Search size={14} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {loading ? (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 40, textAlign: 'center', color: '#64748b' }}>Loading...</div>
        ) : users.length === 0 ? (
          <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 40, textAlign: 'center', color: '#64748b' }}>No users found</div>
        ) : users.map((u) => (
          <div key={u.id} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
            {/* User Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(124,58,237,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, color: '#a78bfa', fontSize: 16 }}>
                  {u.name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: '#e2e8f0' }}>
                    {u.name}
                    {u.is_admin && <span style={{ marginLeft: 8, fontSize: 11, background: 'rgba(245,158,11,0.15)', color: '#fbbf24', padding: '2px 8px', borderRadius: 6, fontWeight: 600 }}>ADMIN</span>}
                  </div>
                  <div style={{ color: '#64748b', fontSize: 13 }}>{u.email}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <select
                  value={u.plan || 'free'}
                  onChange={(e) => handlePlanChange(u.id, e.target.value)}
                  style={{
                    background: planColors[u.plan]?.bg || planColors.free.bg,
                    color: planColors[u.plan]?.text || '#94a3b8',
                    border: '1px solid transparent',
                    borderRadius: 6,
                    padding: '6px 10px',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <span style={{ color: '#64748b', fontSize: 12 }}>{u.active_keys ?? 0} keys | {u.total_requests ?? 0} reqs</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#94a3b8', fontSize: 12 }}>
                  Limit:
                  <input
                    type="number"
                    min="0"
                    defaultValue={u.monthly_limit ?? 500}
                    onBlur={(e) => {
                      const newVal = parseInt(e.target.value)
                      if (newVal !== (u.monthly_limit ?? 500) && newVal >= 0) {
                        handleSetMonthlyLimit(u.id, newVal)
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        const newVal = parseInt(e.target.value)
                        if (newVal !== (u.monthly_limit ?? 500) && newVal >= 0) {
                          handleSetMonthlyLimit(u.id, newVal)
                        }
                      }
                    }}
                    style={{
                      background: 'rgba(10,10,26,0.6)',
                      border: '1px solid rgba(124,58,237,0.2)',
                      borderRadius: 6,
                      color: '#e2e8f0',
                      padding: '4px 8px',
                      fontSize: 12,
                      width: 80,
                      textAlign: 'center',
                    }}
                  />/mo
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn-secondary" onClick={() => handleViewUsage(u.id)} style={{ fontSize: 12, padding: '6px 12px' }}>
                <Activity size={13} /> Usage
              </button>
              <button className="btn-secondary" onClick={() => { setShowResetPw(u.id); setResetPw('') }} style={{ fontSize: 12, padding: '6px 12px' }}>
                <Lock size={13} /> Reset Password
              </button>
              <button className="btn-secondary" onClick={() => { setShowCreateKey(u.id); setNewKeyName(''); setNewKeyTier('free') }} style={{ fontSize: 12, padding: '6px 12px' }}>
                <Plus size={13} /> Create Key
              </button>
              <button onClick={() => handleToggleAdmin(u.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: u.is_admin ? '#fbbf24' : '#475569', padding: '6px 8px', borderRadius: 6, fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                {u.is_admin ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                {u.is_admin ? 'Admin' : 'User'}
              </button>
              <button onClick={() => handleDelete(u.id)} style={{ background: 'rgba(239,68,68,0.1)', border: 'none', borderRadius: 6, padding: '6px 10px', color: '#ef4444', cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                <Trash2 size={13} /> Delete
              </button>
            </div>

            {/* Expanded Usage */}
            {expandedUser === u.id && userUsage && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ marginTop: 16, padding: 16, background: 'rgba(10,10,26,0.6)', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>Usage Stats</h4>
                  <button onClick={() => setExpandedUser(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={14} /></button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 12 }}>
                  <div style={{ padding: 12, background: 'rgba(124,58,237,0.08)', borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: '#64748b' }}>Total Requests</div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>{userUsage.total_requests || 0}</div>
                  </div>
                  <div style={{ padding: 12, background: 'rgba(59,130,246,0.08)', borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: '#64748b' }}>Today</div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>{userUsage.today_requests || 0}</div>
                  </div>
                  <div style={{ padding: 12, background: 'rgba(239,68,68,0.08)', borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: '#64748b' }}>Errors</div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>{userUsage.error_count || 0}</div>
                  </div>
                  <div style={{ padding: 12, background: 'rgba(34,197,94,0.08)', borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: '#64748b' }}>Active Keys</div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>{userUsage.active_keys || 0}</div>
                  </div>
                </div>
                {userUsage.top_endpoints?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Top Endpoints</div>
                    {userUsage.top_endpoints.slice(0, 5).map((ep) => (
                      <div key={ep.endpoint} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 12 }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>{ep.endpoint}</span>
                        <span style={{ color: '#94a3b8' }}>{ep.hits}</span>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Reset Password Form */}
            {showResetPw === u.id && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ marginTop: 12, padding: 16, background: 'rgba(10,10,26,0.6)', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>Reset Password for {u.name}</h4>
                  <button onClick={() => setShowResetPw(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={14} /></button>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input className="input-field" type="password" placeholder="New password (min 6 chars)" value={resetPw} onChange={(e) => setResetPw(e.target.value)} style={{ flex: 1, fontSize: 13 }} />
                  <button className="btn-primary" onClick={() => handleResetPassword(u.id)} style={{ fontSize: 13, padding: '8px 16px' }}>Reset</button>
                </div>
              </motion.div>
            )}

            {/* Create Key Form */}
            {showCreateKey === u.id && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ marginTop: 12, padding: 16, background: 'rgba(10,10,26,0.6)', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>Create Key for {u.name}</h4>
                  <button onClick={() => setShowCreateKey(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={14} /></button>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input className="input-field" placeholder="Key name" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} style={{ flex: 1, fontSize: 13 }} />
                  <select className="input-field" value={newKeyTier} onChange={(e) => setNewKeyTier(e.target.value)} style={{ fontSize: 13, width: 120 }}>
                    <option value="free">Free</option>
                    <option value="starter">Starter</option>
                    <option value="pro">Pro</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                  <button className="btn-primary" onClick={() => handleCreateKey(u.id)} style={{ fontSize: 13, padding: '8px 16px' }}>Create</button>
                </div>
              </motion.div>
            )}
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginTop: 20 }}>
          <button className="btn-secondary" onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} style={{ padding: '8px 14px', fontSize: 13 }}>
            <ChevronLeft size={14} /> Prev
          </button>
          <span style={{ color: '#94a3b8', fontSize: 13 }}>Page {page} of {totalPages}</span>
          <button className="btn-secondary" onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages} style={{ padding: '8px 14px', fontSize: 13 }}>
            Next <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  )
}

// ──────────── KEYS TAB ────────────
function KeysTab({ refreshTrigger }) {
  const [keys, setKeys] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async (p) => {
    setLoading(true)
    try {
      const data = await adminGetKeys(p)
      setKeys(data.keys || [])
      setTotal(data.total || 0)
    } catch { toast.error('Failed to load keys') }
    setLoading(false)
  }, [])

  useEffect(() => { load(page) }, [page, refreshTrigger])

  const handleRevoke = async (keyId) => {
    if (!confirm('Revoke this key?')) return
    try {
      await adminRevokeKey(keyId)
      toast.success('Key revoked')
      load(page)
    } catch { toast.error('Failed to revoke key') }
  }

  const handleTierChange = async (keyId, tier) => {
    try {
      await adminUpdateKeyTier(keyId, tier)
      toast.success('Tier updated')
      load(page)
    } catch { toast.error('Failed to update tier') }
  }

  const maskKey = (key) => key ? key.slice(0, 10) + '...' + key.slice(-4) : '***'

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>API Keys</h2>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>{total} total keys across all users.</p>
      </div>

      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              {['Key', 'User', 'Tier', 'Requests', 'Status', 'Created', 'Actions'].map((h) => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>Loading...</td></tr>
            ) : keys.length === 0 ? (
              <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No keys found</td></tr>
            ) : keys.map((k) => (
              <tr key={k.id} style={{ borderBottom: '1px solid rgba(124,58,237,0.08)' }}>
                <td style={{ padding: '12px 16px' }}>
                  <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#94a3b8' }}>{maskKey(k.key)}</code>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ color: '#e2e8f0', fontSize: 13 }}>{k.user_name || '-'}</div>
                  <div style={{ color: '#64748b', fontSize: 11 }}>{k.user_email || ''}</div>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <select
                    value={k.tier}
                    onChange={(e) => handleTierChange(k.id, e.target.value)}
                    style={{
                      background: planColors[k.tier]?.bg || planColors.free.bg,
                      color: planColors[k.tier]?.text || '#94a3b8',
                      border: '1px solid transparent',
                      borderRadius: 6,
                      padding: '4px 8px',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    <option value="free">Free</option>
                    <option value="starter">Starter</option>
                    <option value="pro">Pro</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </td>
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{k.request_count || 0}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '3px 10px',
                    borderRadius: 12,
                    fontSize: 11,
                    fontWeight: 600,
                    background: k.is_active ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                    color: k.is_active ? '#22c55e' : '#ef4444',
                  }}>
                    {k.is_active ? 'Active' : 'Revoked'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: '#64748b', fontSize: 12 }}>
                  {k.created_at ? new Date(k.created_at).toLocaleDateString() : '-'}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  {k.is_active && (
                    <button
                      onClick={() => handleRevoke(k.id)}
                      style={{ background: 'rgba(239,68,68,0.1)', border: 'none', borderRadius: 6, padding: '4px 8px', color: '#ef4444', cursor: 'pointer' }}
                      title="Revoke key"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total > 50 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginTop: 20 }}>
          <button className="btn-secondary" onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} style={{ padding: '8px 14px', fontSize: 13 }}>
            <ChevronLeft size={14} /> Prev
          </button>
          <span style={{ color: '#94a3b8', fontSize: 13 }}>Page {page} of {Math.ceil(total / 50)}</span>
          <button className="btn-secondary" onClick={() => setPage(page + 1)} disabled={page * 50 >= total} style={{ padding: '8px 14px', fontSize: 13 }}>
            Next <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  )
}

// ──────────── JOBS TAB ────────────
function JobsTab({ refreshTrigger }) {
  const [jobs, setJobs] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async (p) => {
    setLoading(true)
    try {
      const data = await adminGetJobs(p)
      setJobs(data.jobs || [])
      setTotal(data.total || 0)
    } catch { toast.error('Failed to load jobs') }
    setLoading(false)
  }, [])

  useEffect(() => { load(page) }, [page, refreshTrigger])

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Background Jobs</h2>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>{total} total jobs. PDF and AI generation tasks.</p>
      </div>

      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              {['ID', 'Type', 'User', 'Status', 'Created', 'Completed'].map((h) => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>Loading...</td></tr>
            ) : jobs.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>No jobs found</td></tr>
            ) : jobs.map((j) => {
              const sc = statusColors[j.status] || statusColors.pending
              const StatusIcon = sc.icon
              return (
                <tr key={j.id} style={{ borderBottom: '1px solid rgba(124,58,237,0.08)' }}>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 12, color: '#94a3b8' }}>#{j.id}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span className="badge" style={{
                      background: j.job_type === 'pdf' ? 'rgba(236,72,153,0.15)' : 'rgba(99,102,241,0.15)',
                      color: j.job_type === 'pdf' ? '#f472b6' : '#818cf8',
                    }}>
                      {j.job_type?.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{j.user_name || `#${j.user_id}`}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      padding: '3px 10px', borderRadius: 12,
                      fontSize: 11, fontWeight: 600,
                      background: sc.bg, color: sc.text,
                    }}>
                      <StatusIcon size={12} />
                      {j.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#64748b', fontSize: 12 }}>
                    {j.created_at ? new Date(j.created_at).toLocaleString() : '-'}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#64748b', fontSize: 12 }}>
                    {j.completed_at ? new Date(j.completed_at).toLocaleString() : '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ──────────── USAGE / ANALYTICS TAB ────────────
function UsageTab() {
  const [daily, setDaily] = useState([])
  const [byUser, setByUser] = useState([])
  const [endpoints, setEndpoints] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminGetUsageDaily(30).catch(() => []),
      adminGetUsageByUser(20).catch(() => []),
      adminGetUsageEndpoints(15).catch(() => []),
    ]).then(([d, u, e]) => {
      setDaily(d || [])
      setByUser(u || [])
      setEndpoints(e || [])
      setLoading(false)
    })
  }, [])

  if (loading) return <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading analytics...</div>

  const maxReqs = Math.max(...daily.map((d) => d.requests || 0), 1)

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Analytics</h2>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>Real usage data across all users.</p>

      {/* Daily Chart */}
      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24, marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Requests (Last 30 Days)</h3>
        {daily.length === 0 ? (
          <p style={{ color: '#475569', textAlign: 'center', padding: 40 }}>No usage data yet</p>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 2, alignItems: 'end', height: 180 }}>
              {daily.slice(-30).map((d, i) => (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 9, color: '#64748b' }}>{d.requests}</span>
                  <div
                    style={{
                      width: '100%',
                      height: `${Math.max((d.requests / maxReqs) * 140, 4)}px`,
                      background: d.errors > 0
                        ? 'linear-gradient(to top, rgba(239,68,68,0.6), rgba(239,68,68,0.2))'
                        : 'var(--gradient-primary)',
                      borderRadius: '3px 3px 0 0',
                      minHeight: 4,
                    }}
                    title={`${d.day}: ${d.requests} reqs, ${d.unique_users || 0} users, ${d.errors} errors`}
                  />
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
              <span style={{ fontSize: 11, color: '#64748b' }}>{daily[0]?.day}</span>
              <span style={{ fontSize: 11, color: '#64748b' }}>{daily[daily.length - 1]?.day}</span>
            </div>
          </>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 20 }}>
        {/* By User */}
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Usage by User</h3>
          {byUser.length === 0 ? (
            <p style={{ color: '#475569', textAlign: 'center', padding: 40 }}>No data yet</p>
          ) : (
            <div style={{ maxHeight: 300, overflowY: 'auto' }}>
              {byUser.map((u) => (
                <div key={u.user_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid rgba(124,58,237,0.08)' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13, color: '#e2e8f0' }}>{u.name || u.email}</div>
                    <div style={{ fontSize: 11, color: '#64748b' }}>{u.email}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{u.total_requests || 0}</div>
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      <span style={{ color: planColors[u.plan]?.text || '#94a3b8' }}>{u.plan}</span>
                      {u.errors > 0 && <span style={{ color: '#ef4444', marginLeft: 8 }}>{u.errors} err</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top endpoints */}
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Top Endpoints</h3>
          {endpoints.length === 0 ? (
            <p style={{ color: '#475569', textAlign: 'center', padding: 40 }}>No data yet</p>
          ) : (
            endpoints.map((ep) => {
              const pct = endpoints[0]?.hits ? (ep.hits / endpoints[0].hits) * 100 : 0
              return (
                <div key={ep.endpoint} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#cbd5e1', maxWidth: '70%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {ep.endpoint}
                    </span>
                    <span style={{ fontSize: 12, color: '#94a3b8' }}>{ep.hits}</span>
                  </div>
                  <div style={{ height: 5, background: 'rgba(124,58,237,0.1)', borderRadius: 3 }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: 'var(--gradient-primary)', borderRadius: 3 }} />
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

// ──────────── SANDBOX TAB ────────────
const CHART_BODY = '{"dateOfBirth":"1990-05-15","timeOfBirth":"14:30","latitude":28.6139,"longitude":77.209,"timezone":"Asia/Kolkata"}'

const ALL_VARGAS = [
  { d: 1, name: 'Rasi', focus: 'General Life' },
  { d: 2, name: 'Hora', focus: 'Wealth' },
  { d: 3, name: 'Drekkana', focus: 'Siblings' },
  { d: 4, name: 'Chaturthamsa', focus: 'Property' },
  { d: 5, name: 'Panchamsa', focus: 'Power' },
  { d: 6, name: 'Shashtamsa', focus: 'Health' },
  { d: 7, name: 'Saptamsa', focus: 'Children' },
  { d: 8, name: 'D8', focus: 'Longevity' },
  { d: 9, name: 'Navamsa', focus: 'Marriage/Dharma' },
  { d: 10, name: 'Dashamamsa', focus: 'Career' },
  { d: 11, name: 'D11', focus: 'Gains' },
  { d: 12, name: 'Dwadasamsa', focus: 'Parents' },
  { d: 13, name: 'D13', focus: 'Luck/Left Eye' },
  { d: 14, name: 'D14', focus: 'Fortune' },
  { d: 15, name: 'D15', focus: 'Happiness' },
  { d: 16, name: 'Shodasamsa', focus: 'Vehicles' },
  { d: 17, name: 'D17', focus: 'Ancestry' },
  { d: 18, name: 'D18', focus: 'Obstacles' },
  { d: 19, name: 'D19', focus: 'Religion' },
  { d: 20, name: 'Vimsamsa', focus: 'Spirituality' },
  { d: 21, name: 'D21', focus: 'Troubles' },
  { d: 22, name: 'D22', focus: 'Death/Moksha' },
  { d: 23, name: 'D23', focus: 'Prosperity' },
  { d: 24, name: 'Siddhamsa', focus: 'Education' },
  { d: 25, name: 'D25', focus: 'Spiritual Merit' },
  { d: 26, name: 'D26', focus: 'Misfortunes' },
  { d: 27, name: 'Nakshatramsa', focus: 'Strength' },
  { d: 28, name: 'D28', focus: 'Servants' },
  { d: 29, name: 'D29', focus: 'Troubles (Bhaya)' },
  { d: 30, name: 'Trimshamsa', focus: 'Mishaps/Defects' },
  { d: 31, name: 'D31', focus: 'Enemies' },
  { d: 32, name: 'D32', focus: 'Accidents' },
  { d: 33, name: 'D33', focus: 'Paternal Legacy' },
  { d: 34, name: 'D34', focus: 'Fortune (D34)' },
  { d: 35, name: 'D35', focus: 'Longevity (D35)' },
  { d: 36, name: 'D36', focus: 'All Fortune' },
  { d: 37, name: 'D37', focus: 'Paternal Wealth' },
  { d: 38, name: 'D38', focus: 'Wheels/Vehicles' },
  { d: 39, name: 'D39', focus: 'Maternal Wealth' },
  { d: 40, name: 'Khavedamsa', focus: 'Purva Punya/Sins' },
  { d: 41, name: 'D41', focus: 'Material Comforts' },
  { d: 42, name: 'D42', focus: 'Paternal Ancestry' },
  { d: 43, name: 'D43', focus: 'Longevity (D43)' },
  { d: 44, name: 'D44', focus: 'Miseries' },
  { d: 45, name: 'Akshavedamsa', focus: 'Spiritual Merit' },
  { d: 46, name: 'D46', focus: 'Maternal Ancestry' },
  { d: 47, name: 'D47', focus: 'Dangers' },
  { d: 48, name: 'D48', focus: 'All Fortune (D48)' },
  { d: 49, name: 'D49', focus: 'Spiritual Practice' },
  { d: 50, name: 'D50', focus: 'Past Merit' },
  { d: 51, name: 'D51', focus: 'Obstacles (D51)' },
  { d: 52, name: 'D52', focus: 'Prosperity (D52)' },
  { d: 53, name: 'D53', focus: 'Fortune (D53)' },
  { d: 54, name: 'D54', focus: 'Prosperity (D54)' },
  { d: 55, name: 'D55', focus: 'All Aspects' },
  { d: 56, name: 'D56', focus: 'Worries' },
  { d: 57, name: 'D57', focus: 'Dangers (D57)' },
  { d: 58, name: 'D58', focus: 'Spiritual Merit (D58)' },
  { d: 59, name: 'D59', focus: 'Final Liberation' },
  { d: 60, name: 'Shashtiamsa', focus: 'Past Life/Overall' },
]

function isSvgString(str) {
  if (typeof str !== 'string') return false
  const trimmed = str.trim()
  return trimmed.startsWith('<svg') || trimmed.startsWith('<?xml') || trimmed.startsWith('\\n<svg') || trimmed.startsWith('\\n<?xml')
}

function getSvgFromData(data) {
  if (typeof data === 'string' && isSvgString(data)) return data
  if (data?.svg && isSvgString(data.svg)) return data.svg
  if (data?.data?.svg && isSvgString(data.data.svg)) return data.data.svg
  if (data?.chart && typeof data.chart === 'string' && isSvgString(data.chart)) return data.chart
  return null
}

function unescapeSvg(svg) {
  if (!svg) return svg
  return svg.replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\t/g, '\t')
}

function SandboxSvgViewer({ svgString }) {
  const [fullscreen, setFullscreen] = useState(false)
  const clean = unescapeSvg(svgString)
  const dataUrl = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(clean)))}`

  return (
    <div style={{ position: 'relative' }}>
      <button onClick={() => setFullscreen(true)} style={{ position: 'absolute', top: 8, right: 8, background: 'rgba(124,58,237,0.2)', border: 'none', borderRadius: 6, padding: 6, color: '#a78bfa', cursor: 'pointer', zIndex: 5 }}>
        <Maximize2 size={14} />
      </button>
      <div style={{ background: '#0d0d24', borderRadius: 'var(--radius)', padding: 20, textAlign: 'center', overflow: 'auto' }}>
        <img src={dataUrl} alt="Chart" style={{ maxWidth: '100%', height: 'auto', borderRadius: 8 }} />
      </div>
      {fullscreen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20, cursor: 'pointer' }} onClick={() => setFullscreen(false)}>
          <button onClick={() => setFullscreen(false)} style={{ position: 'absolute', top: 16, right: 16, background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 8, color: '#fff', cursor: 'pointer' }}>
            <X size={20} />
          </button>
          <img src={dataUrl} alt="Chart" style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: 8 }} />
        </div>
      )}
    </div>
  )
}

function SandboxTab() {
  const divisionalEndpoints = ALL_VARGAS.map(({ d, name, focus }) => ({
    method: 'POST',
    path: '/chart/divisional-svg',
    label: `D${d} ${name}${focus ? ' (' + focus + ')' : ''}`,
    needsKey: true,
    defaults: { name: `D${d}`, dateOfBirth: '1990-05-15', timeOfBirth: '14:30', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata', theme: 'dark' },
  }))

  const endpoints = [
    { method: 'GET', path: '/health', label: 'Health Check', needsKey: false },
    { method: 'POST', path: '/chart/svg', label: 'North Indian Diamond SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/chart/grid-svg', label: 'Grid Chart SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/chart/east-svg', label: 'East Indian SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/chart/moon-svg', label: 'Moon Chart SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/chart/navamsa-svg', label: 'Navamsa (D9) SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/chart/hora-svg', label: 'Hora (D2) SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/chart/sudarshana-svg', label: 'Sudarshana Chakra SVG', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    ...divisionalEndpoints,
    { method: 'POST', path: '/chart/birth-chart', label: 'Birth Chart JSON', needsKey: true, defaults: JSON.parse(CHART_BODY) },
    { method: 'POST', path: '/ai/chat', label: 'AI Chat', needsKey: true, defaults: { dateOfBirth: '1990-05-15', timeOfBirth: '14:30', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata', question: 'When will I get married?' } },
    { method: 'GET', path: '/horoscope/daily', label: 'Daily Horoscope', needsKey: true, defaults: { sign: 'aries' } },
  ]

  const [selected, setSelected] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [body, setBody] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showKey, setShowKey] = useState(false)
  const [keyLoading, setKeyLoading] = useState(true)

  // Auto-fetch admin's first API key
  useEffect(() => {
    getKeys().then((data) => {
      const keys = Array.isArray(data) ? data : data?.keys || []
      const active = keys.find((k) => k.is_active)
      if (active) setApiKey(active.key)
    }).catch(() => {}).finally(() => setKeyLoading(false))
  }, [])

  const handleSelect = (ep) => {
    setSelected(ep)
    setBody(ep.defaults ? JSON.stringify(ep.defaults, null, 2) : '')
    setResponse(null)
  }

  const handleSend = async () => {
    if (!selected) return
    setLoading(true)
    setResponse(null)
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (apiKey) headers['X-API-Key'] = apiKey

      let url = selected.path
      const fetchOptions = { method: selected.method, headers }

      if (selected.method === 'POST' && body) {
        fetchOptions.body = body
      } else if (selected.method === 'GET' && body) {
        try {
          const params = JSON.parse(body)
          const qs = new URLSearchParams(params).toString()
          url += '?' + qs
        } catch {}
      }

      const res = await fetch(url, fetchOptions)
      const ct = res.headers.get('content-type') || ''
      let data
      if (ct.includes('json')) {
        data = await res.json()
      } else {
        data = await res.text()
      }
      setResponse({ status: res.status, data, contentType: ct })
    } catch (err) {
      setResponse({ status: 0, data: { error: err.message }, contentType: 'error' })
    } finally { setLoading(false) }
  }

  // Determine if response is SVG
  const svgString = response ? getSvgFromData(response.data) : null
  const isSvg = !!svgString

  return (
    <div>
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>API <span className="gradient-text">Sandbox</span></h2>
      <p style={{ color: '#94a3b8', marginBottom: 24 }}>Test API endpoints directly. Your API key is auto-loaded.</p>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20, minHeight: 500 }}>
        {/* Endpoint List */}
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 16 }}>
          <h4 style={{ fontSize: 13, color: '#64748b', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>Endpoints</h4>
          {endpoints.map((ep, i) => (
            <button
              key={i}
              onClick={() => handleSelect(ep)}
              style={{
                width: '100%', textAlign: 'left', padding: '10px 12px', borderRadius: 8,
                border: selected === ep ? '1px solid rgba(124,58,237,0.3)' : '1px solid transparent',
                background: selected === ep ? 'rgba(124,58,237,0.1)' : 'transparent',
                color: '#e2e8f0', cursor: 'pointer', marginBottom: 4,
                fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              <span style={{
                fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                background: ep.method === 'GET' ? 'rgba(34,197,94,0.15)' : 'rgba(59,130,246,0.15)',
                color: ep.method === 'GET' ? '#22c55e' : '#60a5fa',
              }}>{ep.method}</span>
              {ep.label}
              {ep.needsKey && !apiKey && <Key size={10} color="#f59e0b" style={{ marginLeft: 'auto' }} />}
            </button>
          ))}

          <div style={{ marginTop: 16 }}>
            <label style={{ display: 'block', fontSize: 12, color: '#64748b', marginBottom: 6 }}>
              API Key {keyLoading ? '(loading...)' : apiKey ? '(auto-loaded)' : ''}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                className="input-field"
                type={showKey ? 'text' : 'password'}
                placeholder="avk_..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ fontSize: 12, paddingRight: 32 }}
              />
              <button onClick={() => setShowKey(!showKey)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>
        </div>

        {/* Request / Response */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {selected ? (
            <>
              <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                      fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 6,
                      background: selected.method === 'GET' ? 'rgba(34,197,94,0.15)' : 'rgba(59,130,246,0.15)',
                      color: selected.method === 'GET' ? '#22c55e' : '#60a5fa',
                    }}>{selected.method}</span>
                    <code style={{ fontSize: 14, fontFamily: 'var(--font-mono)', color: '#e2e8f0' }}>{selected.path}</code>
                    {selected.needsKey && !apiKey && (
                      <span style={{ fontSize: 11, color: '#f59e0b', fontWeight: 600 }}>Needs API Key</span>
                    )}
                  </div>
                  <button className="btn-primary" onClick={handleSend} disabled={loading} style={{ fontSize: 13, padding: '8px 20px' }}>
                    {loading ? 'Sending...' : <><Send size={14} /> Send</>}
                  </button>
                </div>

                {(selected.method === 'POST' || (selected.method === 'GET' && selected.defaults)) && (
                  <div>
                    <label style={{ display: 'block', fontSize: 12, color: '#64748b', marginBottom: 6 }}>
                      {selected.method === 'POST' ? 'Request Body (JSON)' : 'Query Params (JSON)'}
                    </label>
                    <textarea
                      className="input-field"
                      value={body}
                      onChange={(e) => setBody(e.target.value)}
                      rows={8}
                      style={{ fontFamily: 'var(--font-mono)', fontSize: 12, resize: 'vertical', lineHeight: 1.5 }}
                    />
                  </div>
                )}
              </div>

              {/* Response */}
              {response && (
                <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 13, color: '#94a3b8' }}>Response</span>
                    <span style={{
                      fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 6,
                      background: response.status >= 200 && response.status < 300 ? 'rgba(34,197,94,0.15)' : response.status === 0 ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                      color: response.status >= 200 && response.status < 300 ? '#22c55e' : response.status === 0 ? '#ef4444' : '#fbbf24',
                    }}>
                      {response.status || 'Error'}
                    </span>
                    {isSvg && <span style={{ fontSize: 11, color: '#a78bfa', fontWeight: 600 }}>SVG Detected</span>}
                  </div>

                  {isSvg ? (
                    <SandboxSvgViewer svgString={svgString} />
                  ) : (
                    <pre style={{
                      fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.5,
                      background: 'rgba(10,10,26,0.6)', borderRadius: 8, padding: 16,
                      maxHeight: 400, overflow: 'auto', color: '#cbd5e1', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                    }}>
                      {typeof response.data === 'string' ? response.data : JSON.stringify(response.data, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 48, textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <Terminal size={48} color="#475569" style={{ marginBottom: 16 }} />
              <p style={{ color: '#94a3b8', fontSize: 16 }}>Select an endpoint to test</p>
              <p style={{ color: '#64748b', fontSize: 13, marginTop: 8 }}>Choose from the list on the left</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ──────────── PROFILE TAB ────────────
function AdminProfileTab({ user, onUserUpdate }) {
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
      <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Admin <span className="gradient-text">Profile</span></h2>
      <p style={{ color: '#94a3b8', marginBottom: 32 }}>Manage your admin account details and password.</p>

      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 32, maxWidth: 500, marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Account Details</h3>
          {!editing ? (
            <button className="btn-secondary" onClick={() => setEditing(true)} style={{ fontSize: 13, padding: '8px 16px' }}>Edit Profile</button>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-secondary" onClick={() => { setEditing(false); setName(user?.name || ''); setEmail(user?.email || '') }} style={{ fontSize: 13, padding: '8px 16px' }}>Cancel</button>
              <button className="btn-primary" onClick={handleProfileSave} disabled={saving} style={{ fontSize: 13, padding: '8px 16px' }}>{saving ? 'Saving...' : 'Save'}</button>
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
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Role</label>
          <span className="badge" style={{ background: 'rgba(245,158,11,0.15)', color: '#fbbf24', textTransform: 'capitalize', fontSize: 14, padding: '6px 14px' }}>Admin</span>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>Member Since</label>
          <input className="input-field" value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'} readOnly />
        </div>
      </div>

      <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 32, maxWidth: 500 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Change Password</h3>
          {!showPassword ? (
            <button className="btn-secondary" onClick={() => setShowPassword(true)} style={{ fontSize: 13, padding: '8px 16px' }}>Change Password</button>
          ) : (
            <button className="btn-secondary" onClick={() => { setShowPassword(false); setCurrentPassword(''); setNewPassword(''); setConfirmPassword('') }} style={{ fontSize: 13, padding: '8px 16px' }}>Cancel</button>
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

// ──────────── MAIN ADMIN PAGE ────────────
export default function Admin() {
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [stats, setStats] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [localUser, setLocalUser] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { setLocalUser(user) }, [user])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) navigate('/login')
  }, [authLoading, isAuthenticated, navigate])

  useEffect(() => {
    if (!authLoading && isAuthenticated && user && !user.is_admin) {
      toast.error('Admin access required')
      navigate('/dashboard')
    }
  }, [authLoading, isAuthenticated, user, navigate])

  useEffect(() => {
    if (isAuthenticated && user?.is_admin) {
      adminGetStats().then(setStats).catch(() => {})
    }
  }, [isAuthenticated, user])

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72 }}>
        <div className="gradient-text" style={{ fontSize: 18 }}>Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated || !user?.is_admin) return null

  const refresh = () => setRefreshTrigger((n) => n + 1)
  const displayUser = localUser || user
  const handleUserUpdate = (updated) => setLocalUser(updated)

  return (
    <div style={{ minHeight: '100vh', display: 'flex', paddingTop: 72 }}>
      <aside
        className="dash-sidebar"
        style={{
          width: 240, borderRight: '1px solid var(--border-color)',
          padding: '24px 12px', display: 'flex', flexDirection: 'column',
          position: 'sticky', top: 72, height: 'calc(100vh - 72px)', flexShrink: 0,
        }}
      >
        <div style={{ padding: '0 14px', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <Shield size={18} color="#fbbf24" />
            <span style={{ fontSize: 14, fontWeight: 700, color: '#fbbf24' }}>Admin Panel</span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
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

        <button onClick={refresh} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, border: 'none', background: 'transparent', color: '#94a3b8', fontSize: 14, cursor: 'pointer', textAlign: 'left', marginBottom: 4 }}>
          <RefreshCw size={18} /> Refresh
        </button>
        <button onClick={() => navigate('/dashboard')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, border: 'none', background: 'transparent', color: '#94a3b8', fontSize: 14, cursor: 'pointer', textAlign: 'left' }}>
          <ExternalLink size={18} /> Developer Dashboard
        </button>
      </aside>

      <main style={{ flex: 1, padding: '32px', overflow: 'auto' }}>
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
            {activeTab === 'overview' && <OverviewTab stats={stats} />}
            {activeTab === 'users' && <UsersTab refreshTrigger={refreshTrigger} />}
            {activeTab === 'keys' && <KeysTab refreshTrigger={refreshTrigger} />}
            {activeTab === 'jobs' && <JobsTab refreshTrigger={refreshTrigger} />}
            {activeTab === 'usage' && <UsageTab />}
            {activeTab === 'sandbox' && <SandboxTab />}
            {activeTab === 'profile' && <AdminProfileTab user={displayUser} onUserUpdate={handleUserUpdate} />}
          </motion.div>
        </AnimatePresence>
      </main>

      <style>{`
        @media (max-width: 768px) {
          .dash-sidebar { width: 60px !important; }
          .dash-sidebar button { font-size: 0 !important; padding: 10px !important; justify-content: center; }
          .dash-sidebar button svg { margin: 0 !important; }
        }
      `}</style>
    </div>
  )
}
