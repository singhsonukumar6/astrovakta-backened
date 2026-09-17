import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe, Plus, Trash2, ExternalLink, Check, X, Palette, FileText, Calendar,
  Store, Globe2, Eye, EyeOff, Sparkles, Clock, ChevronLeft, Settings2,
  Save, LogIn, Shield, ArrowRight, Image as ImageIcon, Users,
  Bell, Crown, Loader2, LayoutDashboard, Package, ShoppingBag, Link2,
  Phone, Star, TrendingUp, IndianRupee, Menu, LogOut, PanelLeft, Home,
  Key, Bot, ScrollText, Zap, BarChart3, User,
  Share2, Copy, Calendar as CalendarIcon, Clock as ClockIcon, Video, MousePointerClick, Link as LinkIcon,
  Info, RefreshCw, UserPlus, FileText as InvoiceIcon, Send, Mail, MessageCircle, Pencil,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth.jsx'
import KundaliReport from './KundaliReport.jsx'
import DashboardLoader from '../components/DashboardLoader.jsx'
import {
  TEMPLATES, PRESETS, fileToDataUrl, inputStyle, labelStyle, cardStyle,
  primaryBtn, ghostBtn, errDetail,
} from '../components/CreateSiteWizard.jsx'
import { APIKeys, AIProvidersTab, ReportsTab, UsagePanel, Profile } from '../components/DevTabs.jsx'
import { tenantSiteUrl, parseYouTubeId } from '../lib/tenant.js'
import {
  getMySites, createMySite, getMySite, updateMySite, publishMySite, unpublishMySite,
  deleteMySite, saveMySitePage, setMySiteDomain, verifyMySiteDomain, removeMySiteDomain,
  createMyService, updateMyService, deleteMyService,
  getMyAvailability, setMyAvailability, getMyBookings, updateMyBooking,
  checkSlugAvailability, checkDomainAvailability, setMySiteMedia, setMySiteSettings, getMyLeads,
  getMyClients, createMyClient, updateMyClient, deleteMyClient, convertMyLead,
  getMyInvoices, createMyInvoice, sendMyInvoice, setMyInvoiceStatus, deleteMyInvoice,
  getMySiteStats, getMyProducts, createMyProduct, updateMyProduct, deleteMyProduct,
  getMyOrders, updateMyOrder, getKeys,
  getMySocial, generateSocialPost, createSocialPost, updateSocialPost, deleteSocialPost, socialPostMedia,
  getMyCredits, rechargeCredits, getMyAnalytics,
  getMyCatalog, importCatalogProduct,
  getMyIntegrations, getIntegrationProviders, beginStoreConnect, connectStore, disconnectStore, pushToStore, pullStoreOrders, wooOneClickStart,
  aiGenerateSiteContent,
} from '../lib/api.js'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


// ═══════════════ OVERVIEW TAB ═══════════════
function OverviewTab({ site, reload }) {
  const [stats, setStats] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [credits, setCredits] = useState(null)
  const [leads, setLeads] = useState([])
  const [orders, setOrders] = useState([])
  const [recharging, setRecharging] = useState('')

  useEffect(() => {
    getMySiteStats(site.id).then(setStats).catch(() => setStats(null))
    getMyAnalytics(site.id, 30).then(setAnalytics).catch(() => setAnalytics(null))
    getMyCredits(site.id).then(setCredits).catch(() => setCredits(null))
    getMyLeads(site.id).then((l) => setLeads((l.leads || []).slice(0, 5))).catch(() => setLeads([]))
    getMyOrders(site.id).then((o) => setOrders((o.orders || []).slice(0, 5))).catch(() => setOrders([]))
  }, [site.id, site.updated_at]) // eslint-disable-line

  const doRecharge = async (packId) => {
    setRecharging(packId)
    try {
      const res = await rechargeCredits(site.id, packId)
      if (res.checkout_url) { window.location.href = res.checkout_url; return }
      toast.success(`Recharged! New balance: ${res.balance} credits`)
      getMyCredits(site.id).then(setCredits)
    } catch (e) { toast.error(errDetail(e, 'Recharge failed')) }
    finally { setRecharging('') }
  }

  const revenue = stats ? (stats.bookings?.confirmedRevenue || 0) + (stats.bookings?.completedRevenue || 0) + (stats.store?.revenue || 0) : 0
  const maxViews = Math.max(1, ...(analytics?.daily || []).map((d) => d.views))

  const statCards = stats ? [
    { label: 'Visitors (30d)', value: analytics?.visitors ?? '—', icon: Users, color: '#8b5cf6' },
    { label: 'Pageviews (30d)', value: analytics?.pageviews ?? '—', icon: TrendingUp, color: '#0ea5e9' },
    { label: 'Total bookings', value: stats.bookings?.total || 0, icon: Calendar, color: '#4f46e5' },
    { label: 'Leads captured', value: stats.leads?.total || 0, icon: Users, color: '#d97706' },
    { label: 'Earnings', value: `₹${Number(revenue).toLocaleString('en-IN')}`, icon: IndianRupee, color: '#16a34a' },
    { label: 'Store orders', value: stats.store?.ordersTotal || 0, icon: ShoppingBag, color: '#db2777' },
  ] : []

  return (
    <div>
      {/* stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
        {statCards.map((c) => (
          <div key={c.label} style={{ ...cardStyle, padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <div style={{ width: 30, height: 30, borderRadius: 9, background: `${c.color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <c.icon size={15} color={c.color} />
              </div>
              <span style={{ fontSize: 11.5, fontWeight: 700, color: '#64748b' }}>{c.label}</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 900 }}>{c.value}</div>
          </div>
        ))}
        {!stats && <div style={{ ...cardStyle, padding: 16, color: '#64748b' }}>Loading…</div>}
      </div>

      {/* traffic chart + credits */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12, marginTop: 14, alignItems: 'stretch' }}>
        <div style={cardStyle}>
          <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 2 }}>Visitors & pageviews — last 30 days</h3>
          <p style={{ fontSize: 12, color: '#94a3b8', margin: '0 0 12px' }}>{analytics?.pageviews ?? 0} views · {analytics?.visitors ?? 0} visitors</p>
          {!analytics ? <div style={{ color: '#64748b', padding: 20, textAlign: 'center' }}>Loading…</div> : (analytics.daily || []).length === 0 ? (
            <div style={{ color: '#94a3b8', fontSize: 13, padding: '26px 0', textAlign: 'center' }}>No traffic yet — share your site link to start tracking.</div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 120 }}>
              {analytics.daily.map((d) => (
                <div key={d.date} title={`${d.date}: ${d.views} views`} style={{
                  flex: 1, minWidth: 4, background: 'linear-gradient(180deg, #4f46e5, #818cf8)',
                  borderRadius: 3, height: `${Math.max(4, (d.views / maxViews) * 100)}%`,
                }} />
              ))}
            </div>
          )}
          {!!(analytics?.topTools || []).length && (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: '#64748b', marginBottom: 6 }}>MOST USED TOOLS</div>
              {analytics.topTools.map((t) => (
                <div key={t.tool} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, padding: '3px 0' }}>
                  <span style={{ textTransform: 'capitalize' }}>{t.tool}</span><b>{t.count}</b>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* credits card */}
        <div style={{ ...cardStyle, borderColor: 'rgba(79,70,229,0.35)', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 2, display: 'flex', alignItems: 'center', gap: 7 }}>
            <Crown size={15} color="#d97706" /> Credits
          </h3>
          <div style={{ fontSize: 34, fontWeight: 900, margin: '6px 0 2px' }}>{credits?.balance ?? '—'}</div>
          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>remaining</div>
          <div style={{ fontSize: 11.5, color: '#64748b', lineHeight: 1.8, marginBottom: 12 }}>
            Kundli 2 · Matching 3 · Dosha 2<br />Horoscope/Panchang 1 · AI 5
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 'auto' }}>
            {(credits?.packs || []).map((p) => (
              <button key={p.id} onClick={() => doRecharge(p.id)} disabled={!!recharging}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '9px 12px', borderRadius: 10,
                  border: '1.5px solid rgba(79,70,229,0.3)', background: '#fff', cursor: 'pointer', fontSize: 12.5, fontWeight: 700, opacity: recharging && recharging !== p.id ? 0.5 : 1 }}>
                <span>{p.credits.toLocaleString('en-IN')} credits</span>
                <span style={{ color: '#4f46e5' }}>₹{p.price}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* recent activity columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginTop: 14 }}>
        <div style={cardStyle}>
          <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 10 }}>Recent leads</h3>
          {leads.length === 0 ? <div style={{ color: '#94a3b8', fontSize: 13 }}>No leads yet.</div> : leads.map((l) => (
            <div key={l.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 0', borderBottom: '1px solid #f8fafc' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{l.name || l.email || 'Anonymous'}</div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>{l.tool} · {String(l.created_at || '').slice(0, 10)}</div>
              </div>
              {!!l.phone && <a href={`https://wa.me/${String(l.phone).replace(/[^\d]/g, '')}`} target="_blank" rel="noopener noreferrer" style={{ fontSize: 11.5, fontWeight: 700, color: '#16a34a', textDecoration: 'none' }}>WhatsApp →</a>}
            </div>
          ))}
        </div>
        <div style={cardStyle}>
          <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 10 }}>Recent orders</h3>
          {orders.length === 0 ? <div style={{ color: '#94a3b8', fontSize: 13 }}>No orders yet.</div> : orders.map((o) => (
            <div key={o.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 0', borderBottom: '1px solid #f8fafc' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>#{o.id} · {o.client_name}</div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>{String(o.created_at || '').slice(0, 10)}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 800, fontSize: 13 }}>₹{o.amount}</div>
                <span style={{ fontSize: 10.5, fontWeight: 700, padding: '1px 7px', borderRadius: 8,
                  background: o.status === 'new' ? 'rgba(245,158,11,0.12)' : o.status === 'cancelled' ? 'rgba(239,68,68,0.12)' : 'rgba(34,197,94,0.12)',
                  color: o.status === 'new' ? '#d97706' : o.status === 'cancelled' ? '#dc2626' : '#16a34a' }}>{o.status}</span>
              </div>
            </div>
          ))}
        </div>
        <div style={cardStyle}>
          <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 10 }}>Next appointments</h3>
          {(stats?.bookings?.upcomingList || []).slice(0, 5).map((b) => (
            <div key={b.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid #f8fafc' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{b.client_name}</div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>{b.service_name || 'Consultation'} · {b.date} {b.start_time}</div>
              </div>
              <div style={{ fontWeight: 700, fontSize: 13 }}>{b.amount ? `₹${b.amount}` : ''}</div>
            </div>
          ))}
        </div>
      </div>

      {/* earnings report */}
      <div style={{ ...cardStyle, marginTop: 14 }}>
        <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 7 }}>
          <IndianRupee size={15} color="#16a34a" /> Earnings report
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
          {[
            ['Consultations (confirmed)', stats?.bookings?.confirmedRevenue || 0],
            ['Consultations (completed)', stats?.bookings?.completedRevenue || 0],
            ['Store orders (lifetime)', stats?.store?.revenue || 0],
            ['Total', revenue],
          ].map(([label, val], i) => (
            <div key={label} style={{ padding: 12, borderRadius: 10, background: i === 3 ? 'rgba(34,197,94,0.08)' : 'rgba(127,127,127,0.05)', border: i === 3 ? '1px solid rgba(34,197,94,0.3)' : 'none' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: i === 3 ? '#16a34a' : '#64748b' }}>{label.toUpperCase()}</div>
              <div style={{ fontWeight: 900, fontSize: 19, marginTop: 3 }}>₹{Number(val).toLocaleString('en-IN')}</div>
            </div>
          ))}
        </div>
      </div>

      {/* setup checklist */}
      <div style={{ ...cardStyle, marginTop: 14 }}>
        <h3 style={{ fontSize: 14, fontWeight: 800, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <TrendingUp size={15} color="#d97706" /> Grow faster — quick setup
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginTop: 12 }}>
          {[
            { ok: site.hero_image, text: 'Add your photo (hero image)' },
            { ok: site.settings?.whatsappNumber, text: 'Set your WhatsApp number' },
            { ok: site.custom_domain, text: 'Connect your own domain' },
            { ok: (site.settings?.instagram || site.settings?.youtube || site.settings?.facebook), text: 'Add your social media links' },
          ].map((c) => (
            <div key={c.text} style={{
              display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, fontWeight: 600,
              color: c.ok ? '#16a34a' : '#475569', padding: '10px 14px',
              background: c.ok ? 'rgba(34,197,94,0.06)' : 'rgba(79,70,229,0.04)', borderRadius: 10,
            }}>
              {c.ok ? <Check size={15} color="#16a34a" /> : <span style={{ width: 15, height: 15, borderRadius: '50%', border: '2px solid #cbd5e1', display: 'inline-block' }} />}
              {c.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ═══════════════ AI WRITER DIALOG ═══════════════
// Shared "Write with AI" flow: explains WHAT it will write (per-field
// context), asks the tenant what to focus on, shows a clear "AI is working"
// state while generating, and previews the result before applying it.
const AI_FIELD_META = {
  heroTitle: {
    label: 'Homepage headline',
    hint: 'A short, punchy headline at the very top of your homepage — max 8 words. First thing every visitor reads.',
    ph: 'e.g. mention 15+ years of experience, celebrity clients, Patna-based',
  },
  heroSubtitle: {
    label: 'Sub-headline',
    hint: '1–2 sentences right under the headline — what you offer and why a visitor should book with you.',
    ph: 'e.g. focus on career & marriage readings, online video consultations',
  },
  aboutTitle: {
    label: 'About section title',
    hint: 'A short title for your About section — max 6 words.',
    ph: 'e.g. keep it traditional, mention your lineage or guru',
  },
  aboutText: {
    label: 'About section text',
    hint: '2–3 short paragraphs about you — your background, experience and how you work with clients.',
    ph: 'e.g. mention Jyotish Acharya degree, 10,000+ kundlis read, TV appearances',
  },
  pageTitle: { label: 'Page title', hint: 'A short title for this page.', ph: '' },
  pageText: { label: 'Page text', hint: '2–3 welcoming paragraphs for this page — what the visitor can do here and how to reach you.', ph: '' },
  serviceDescription: {
    label: 'Service description',
    hint: 'One sentence of 15–35 words describing this service — what the client gets and how the session runs.',
    ph: 'e.g. 45-minute video call, includes a written remedy summary',
  },
  tagline: {
    label: 'Tagline',
    hint: 'One short line shown under your name in the site header — max 10 words.',
    ph: 'e.g. highlight trust, accuracy, or your specialisation',
  },
}

function AiWriterDialog({ site, field, contextKey, onClose, onApply }) {
  const meta = AI_FIELD_META[field] || { label: 'Website copy', hint: 'AI-written copy for your website.', ph: '' }
  const [instructions, setInstructions] = useState('')
  const [tone, setTone] = useState('warm')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  const run = async () => {
    setBusy(true); setResult(null)
    try {
      const res = await aiGenerateSiteContent(site.id, {
        field, tone, instructions: instructions.trim() || undefined, context_key: contextKey || undefined,
      })
      if (res?.text) setResult(res)
      else toast.error('Could not generate — try again')
    } catch {
      toast.error('Could not generate — try again')
    } finally { setBusy(false) }
  }

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget && !busy) onClose() }}
      style={{ position: 'fixed', inset: 0, zIndex: 200, background: 'rgba(15,23,42,0.55)', backdropFilter: 'blur(3px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 18 }}>
      <motion.div
        initial={{ opacity: 0, y: 18, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 26 }}
        style={{ width: 'min(560px, 100%)', background: '#fff', borderRadius: 18, padding: 24, boxShadow: '0 24px 64px rgba(15,23,42,0.35)' }}>

        {/* header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 800, fontSize: 16, color: '#0f172a' }}>
            <Sparkles size={17} color="#4f46e5" /> Write with AI
          </div>
          <button type="button" onClick={() => { if (!busy) onClose() }} aria-label="Close"
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 22, lineHeight: 1 }}>×</button>
        </div>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#475569', marginBottom: 14 }}>
          {meta.label}{contextKey && field === 'serviceDescription' ? ` — ${contextKey}` : ''}
        </div>

        {/* what I'll write — context so the tenant knows what this produces */}
        <div style={{ display: 'flex', gap: 10, padding: '12px 14px', borderRadius: 12, background: 'rgba(79,70,229,0.05)', border: '1px dashed rgba(79,70,229,0.3)', marginBottom: 16 }}>
          <Info size={15} color="#4f46e5" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: 0.6, color: '#4f46e5', marginBottom: 3 }}>WHAT I'LL WRITE</div>
            <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.6 }}>{meta.hint}</div>
          </div>
        </div>

        {busy ? (
          /* generating — unmistakable "AI is working" state */
          <div style={{ textAlign: 'center', padding: '26px 10px 20px' }}>
            <Loader2 size={32} className="spin" color="#4f46e5" style={{ margin: '0 auto 14px', display: 'block' }} />
            <div style={{ fontWeight: 800, fontSize: 15.5, color: '#0f172a' }}>Writing your {meta.label.toLowerCase()}…</div>
            <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 5 }}>The AI is working — this usually takes a few seconds.</div>
          </div>
        ) : result ? (
          <>
            <div style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: 0.6, color: '#16a34a', marginBottom: 7 }}>
              {result.ai ? 'GENERATED WITH YOUR AI PROVIDER' : 'STARTER DRAFT — ADD AN AI PROVIDER FOR PERSONALISED COPY'}
            </div>
            <div style={{ padding: 16, borderRadius: 12, border: '1px solid #e2e8f0', background: '#f8fafc', fontSize: 14.5, lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 16, maxHeight: 220, overflowY: 'auto', color: '#0f172a' }}>
              {result.text}
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button type="button" onClick={() => onApply(result.text)} className="btn-primary" style={primaryBtn}>
                <Check size={15} /> Use this text
              </button>
              <button type="button" onClick={run} style={ghostBtn}>
                <RefreshCw size={14} /> Try again
              </button>
              <button type="button" onClick={() => setResult(null)} style={ghostBtn}>
                Edit instructions
              </button>
            </div>
          </>
        ) : (
          <>
            <label style={labelStyle}>What should the AI focus on? (optional)</label>
            <textarea value={instructions} onChange={(e) => setInstructions(e.target.value)} rows={3}
              placeholder={meta.ph || 'Anything special to include — the AI weaves it in naturally'}
              style={{ ...inputStyle, resize: 'vertical', marginBottom: 14 }} />
            <label style={labelStyle}>Tone</label>
            <select value={tone} onChange={(e) => setTone(e.target.value)} style={{ ...inputStyle, marginBottom: 18 }}>
              <option value="warm">Warm & inviting</option>
              <option value="professional">Professional</option>
              <option value="spiritual">Spiritual / devotional</option>
              <option value="friendly">Friendly & easygoing</option>
            </select>
            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" onClick={run} className="btn-primary" style={primaryBtn}>
                <Sparkles size={15} /> Generate
              </button>
              <button type="button" onClick={onClose} style={ghostBtn}>Cancel</button>
            </div>
            <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 12, lineHeight: 1.5 }}>
              Uses the AI provider from your AI Providers tab — without one you still get solid starter copy.
            </div>
          </>
        )}
      </motion.div>
    </div>
  )
}

// ═══════════════ CONTENT TAB (pages editor + AI copy generation) ═══════════════
function ContentTab({ site, reload }) {
  const [pageKey, setPageKey] = useState('home')
  const pages = site.pages || []
  const page = pages.find((p) => p.page_key === pageKey) || { content: {} }
  const [content, setContent] = useState(page.content || {})
  const [saving, setSaving] = useState(false)
  const [aiDialog, setAiDialog] = useState(null) // { field, contextKey } → AiWriterDialog

  useEffect(() => { setContent(page.content || {}) }, [pageKey, site.updated_at]) // eslint-disable-line

  const save = async () => {
    setSaving(true)
    try {
      // Drop fully-empty editor rows (added via "Add button/link/video" but
      // never filled in) so they don't pile up as junk in the saved content.
      const clean = { ...content }
      for (const k of ['heroButtons', 'links', 'videos', 'testimonials', 'whyPoints']) {
        if (Array.isArray(clean[k])) {
          clean[k] = clean[k].filter((row) => row && Object.values(row).some((v) => String(v ?? '').trim()))
        }
      }
      await saveMySitePage(site.id, pageKey, { title: page.title, content: clean })
      toast.success('Saved! Your website is updated.')
      reload()
    } catch {
      toast.error('Could not save — try again')
    } finally { setSaving(false) }
  }

  const set = (k, v) => setContent((c) => ({ ...c, [k]: v }))

  // Opens the shared AI writer: shows field context, asks what to focus on,
  // generates with a visible working state, previews before applying.
  const GenBtn = ({ field, contextKey }) => (
    <button type="button" onClick={() => setAiDialog({ field, contextKey })} title="Write this for me with AI"
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5, marginLeft: 10, padding: '5px 12px',
        borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: 'pointer',
        border: '1px solid rgba(79,70,229,0.35)', color: '#4f46e5', background: 'rgba(79,70,229,0.06)',
      }}>
      <Sparkles size={12} /> Write with AI
    </button>
  )

  const testiList = Array.isArray(content.testimonials) ? content.testimonials : []
  const setTesti = (i, patch) => setContent((c) => ({
    ...c,
    testimonials: (c.testimonials || []).map((t, j) => (j === i ? { ...t, ...patch } : t)),
  }))

  const aiCard = (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 9,
      border: '1px dashed rgba(79,70,229,0.35)', borderRadius: 14, padding: '12px 16px',
      marginBottom: 20, background: 'rgba(79,70,229,0.03)',
      fontSize: 13, color: '#64748b', lineHeight: 1.6,
    }}>
      <Sparkles size={14} color="#4f46e5" style={{ flexShrink: 0, marginTop: 3 }} />
      <span>
        Tap <b style={{ color: '#4f46e5' }}>Write with AI</b> on any field — it explains what it will write,
        asks what you want to focus on, and drafts the copy for you in seconds.
        Uses the AI provider from your <b>AI Providers</b> tab.
      </span>
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
        {['home', 'about', 'contact'].map((k) => (
          <button key={k} onClick={() => setPageKey(k)} style={{
            ...ghostBtn, padding: '8px 18px', fontSize: 13,
            background: pageKey === k ? 'rgba(79,70,229,0.1)' : 'transparent',
            borderColor: pageKey === k ? '#4f46e5' : '#e2e8f0',
            color: pageKey === k ? '#4f46e5' : '#0f172a',
          }}>
            <FileText size={14} /> {k === 'home' ? 'Home' : k === 'about' ? 'About' : 'Contact'}
          </button>
        ))}
      </div>

      <div style={cardStyle}>
        {aiCard}
        {pageKey === 'home' && (
          <>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Headline (appears large at top)<GenBtn field="heroTitle" /></label>
              <input value={content.heroTitle || ''} onChange={(e) => set('heroTitle', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Sub-headline<GenBtn field="heroSubtitle" /></label>
              <textarea rows={2} value={content.heroSubtitle || ''} onChange={(e) => set('heroSubtitle', e.target.value)} style={{ ...inputStyle, resize: 'vertical' }} />
            </div>

            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Hero badge (small line above the headline)</label>
              <input value={content.heroBadge || ''} onChange={(e) => set('heroBadge', e.target.value)}
                placeholder="e.g. 15+ years of Vedic astrology (leave blank for your tagline)" style={inputStyle} />
            </div>

            {/* Hero buttons editor */}
            <div style={{ border: '1px solid #e2e8f0', borderRadius: 14, padding: 18, marginBottom: 18 }}>
              <label style={{ ...labelStyle, fontSize: 15, display: 'flex', alignItems: 'center', gap: 7 }}>
                <MousePointerClick size={15} color="#4f46e5" /> Hero buttons
              </label>
              <p style={{ fontSize: 12.5, color: '#94a3b8', margin: '4px 0 12px', lineHeight: 1.5 }}>
                Up to 3 buttons on your homepage hero. Link to a section (#book, #tools), a page (#/kundli, #/shop, #/about) or any https:// URL.
                Leave empty for the defaults.
              </p>
              {(content.heroButtons || []).map((b, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                  <input value={b.label || ''} placeholder="Button text (Book Now)" style={{ ...inputStyle, flex: '1 1 130px' }}
                    onChange={(e) => set('heroButtons', content.heroButtons.map((x, j) => (j === i ? { ...x, label: e.target.value } : x)))} />
                  <input value={b.href || ''} placeholder="#book or https://…" style={{ ...inputStyle, flex: '1.2 1 150px' }}
                    onChange={(e) => set('heroButtons', content.heroButtons.map((x, j) => (j === i ? { ...x, href: e.target.value } : x)))} />
                  <select value={b.variant || 'outline'} style={{ ...inputStyle, width: 110, flexShrink: 0 }}
                    onChange={(e) => set('heroButtons', content.heroButtons.map((x, j) => (j === i ? { ...x, variant: e.target.value } : x)))}>
                    <option value="primary">Primary</option>
                    <option value="outline">Outline</option>
                  </select>
                  <button onClick={() => set('heroButtons', content.heroButtons.filter((_, j) => j !== i))} title="Remove"
                    style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: 8 }}>
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
              {(content.heroButtons || []).length < 3 && (
                <button onClick={() => set('heroButtons', [...(content.heroButtons || []), { label: '', href: '', variant: 'outline' }])}
                  style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12 }}>
                  <Plus size={13} /> Add button
                </button>
              )}
            </div>

            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12,
              padding: 16, background: 'rgba(79,70,229,0.04)', borderRadius: 12, marginBottom: 18,
            }}>
              {[
                ['statsYears', 'Years of practice (e.g. 15+)'],
                ['statsReadings', 'Kundlis read (e.g. 10,000+)'],
                ['statsRating', 'Client rating (e.g. 4.9)'],
              ].map(([k, ph]) => (
                <div key={k}>
                  <label style={{ ...labelStyle, fontSize: 12 }}>{ph}</label>
                  <input value={content[k] || ''} onChange={(e) => set(k, e.target.value)} style={{ ...inputStyle, fontSize: 13 }} />
                </div>
              ))}
            </div>

            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>About section title<GenBtn field="aboutTitle" /></label>
              <input value={content.aboutTitle || ''} onChange={(e) => set('aboutTitle', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={labelStyle}>About section text<GenBtn field="aboutText" /></label>
              <textarea rows={4} value={content.aboutText || ''} onChange={(e) => set('aboutText', e.target.value)} style={{ ...inputStyle, resize: 'vertical' }} />
            </div>

            {/* Testimonials editor */}
            <div style={{
              border: '1px solid #e2e8f0', borderRadius: 14, padding: 18, marginBottom: 24,
            }}>
              <label style={{ ...labelStyle, fontSize: 15 }}>Client testimonials (shown on your site)</label>
              {testiList.map((t, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'flex-start' }}>
                  <input value={t.name || ''} onChange={(e) => setTesti(i, { name: e.target.value })} placeholder="Client name" style={{ ...inputStyle, width: 130, flexShrink: 0 }} />
                  <textarea value={t.text || ''} onChange={(e) => setTesti(i, { text: e.target.value })} placeholder="What they said…" rows={2} style={{ ...inputStyle, resize: 'vertical', flex: 1 }} />
                  <button onClick={() => setContent((c) => ({ ...c, testimonials: (c.testimonials || []).filter((_, j) => j !== i) }))}
                    title="Remove" style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: 8 }}>
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
              <button onClick={() => setContent((c) => ({ ...c, testimonials: [...(c.testimonials || []), { name: '', text: '', rating: 5 }] }))}
                style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12 }}>
                <Plus size={13} /> Add testimonial
              </button>
            </div>

            {/* YouTube videos manager */}
            <div style={{ border: '1px solid #e2e8f0', borderRadius: 14, padding: 18, marginBottom: 24 }}>
              <label style={{ ...labelStyle, fontSize: 15, display: 'flex', alignItems: 'center', gap: 7 }}>
                <Video size={15} color="#dc2626" /> YouTube videos
              </label>
              <p style={{ fontSize: 12.5, color: '#94a3b8', margin: '4px 0 12px', lineHeight: 1.5 }}>
                Paste links from your channel — they play right on your homepage. Up to 6 videos.
              </p>
              {(content.videos || []).map((v, i) => {
                const vid = parseYouTubeId(v.url || '')
                const upd = (patch) => set('videos', content.videos.map((x, j) => (j === i ? { ...x, ...patch } : x)))
                return (
                  <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                    {vid
                      ? <img src={`https://i.ytimg.com/vi/${vid}/default.jpg`} alt="" style={{ width: 64, height: 44, borderRadius: 8, objectFit: 'cover', flexShrink: 0 }} />
                      : <div style={{ width: 64, height: 44, borderRadius: 8, background: '#f1f5f9', flexShrink: 0 }} />}
                    <input value={v.url || ''} onChange={(e) => upd({ url: e.target.value })}
                      placeholder="https://www.youtube.com/watch?v=…" style={{ ...inputStyle, flex: '1.4 1 190px' }} />
                    <input value={v.title || ''} onChange={(e) => upd({ title: e.target.value })}
                      placeholder="Title (optional)" style={{ ...inputStyle, flex: '1 1 130px' }} />
                    <button onClick={() => set('videos', content.videos.filter((_, j) => j !== i))} title="Remove"
                      style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: 8 }}>
                      <Trash2 size={15} />
                    </button>
                    {v.url && !vid && <div style={{ width: '100%', fontSize: 12, color: '#d97706' }}>Hmm, that doesn't look like a YouTube link — paste the full URL.</div>}
                  </div>
                )
              })}
              {(content.videos || []).length < 6 && (
                <button onClick={() => set('videos', [...(content.videos || []), { url: '', title: '' }])}
                  style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12 }}>
                  <Plus size={13} /> Add video
                </button>
              )}
              {(content.videos || []).length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <label style={{ ...labelStyle, fontSize: 12 }}>Videos section title (optional)</label>
                  <input value={content.videosTitle || ''} onChange={(e) => set('videosTitle', e.target.value)}
                    placeholder="Watch &amp; Learn" style={{ ...inputStyle, fontSize: 13 }} />
                </div>
              )}
            </div>

            {/* Linktree-style links manager */}
            <div style={{ border: '1px solid #e2e8f0', borderRadius: 14, padding: 18, marginBottom: 24 }}>
              <label style={{ ...labelStyle, fontSize: 15, display: 'flex', alignItems: 'center', gap: 7 }}>
                <LinkIcon size={15} color="#4f46e5" /> My links (Linktree style)
              </label>
              <p style={{ fontSize: 12.5, color: '#94a3b8', margin: '4px 0 12px', lineHeight: 1.5 }}>
                Extra links shown as tap-friendly rows on your homepage — other websites, booking pages, donation pages, anything.
                Your social profiles (Settings tab) appear here automatically too.
              </p>
              {(content.links || []).map((l, i) => {
                const upd = (patch) => set('links', content.links.map((x, j) => (j === i ? { ...x, ...patch } : x)))
                return (
                  <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                    <input value={l.label || ''} onChange={(e) => upd({ label: e.target.value })}
                      placeholder="Label (My other website)" style={{ ...inputStyle, flex: '1 1 140px' }} />
                    <input value={l.url || ''} onChange={(e) => upd({ url: e.target.value })}
                      placeholder="https://…" style={{ ...inputStyle, flex: '1.4 1 190px' }} />
                    <button onClick={() => set('links', content.links.filter((_, j) => j !== i))} title="Remove"
                      style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: 8 }}>
                      <Trash2 size={15} />
                    </button>
                  </div>
                )
              })}
              {(content.links || []).length < 8 && (
                <button onClick={() => set('links', [...(content.links || []), { label: '', url: '' }])}
                  style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12 }}>
                  <Plus size={13} /> Add link
                </button>
              )}
              {(content.links || []).length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <label style={{ ...labelStyle, fontSize: 12 }}>Links section title (optional)</label>
                  <input value={content.linksTitle || ''} onChange={(e) => set('linksTitle', e.target.value)}
                    placeholder="Find Me Online" style={{ ...inputStyle, fontSize: 13 }} />
                </div>
              )}
            </div>
          </>
        )}
        {(pageKey === 'about' || pageKey === 'contact') && (
          <>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Title<GenBtn field="pageTitle" contextKey={pageKey} /></label>
              <input value={content.title || ''} onChange={(e) => set('title', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Text<GenBtn field="pageText" contextKey={pageKey} /></label>
              <textarea rows={6} value={content.text || ''} onChange={(e) => set('text', e.target.value)} style={{ ...inputStyle, resize: 'vertical' }} />
            </div>
          </>
        )}
        <button onClick={save} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>

      {aiDialog && (
        <AiWriterDialog
          site={site}
          field={aiDialog.field}
          contextKey={aiDialog.contextKey}
          onClose={() => setAiDialog(null)}
          onApply={(text) => {
            set(aiDialog.field, text)
            setAiDialog(null)
            toast.success('Added — edit freely, then Save changes')
          }}
        />
      )}
    </div>
  )
}

// ═══════════════ DESIGN TAB (template + theme) ═══════════════
function DesignTab({ site, reload }) {
  const [theme, setTheme] = useState(site.theme || {})
  const [saving, setSaving] = useState(false)
  const [logoUrl, setLogoUrl] = useState(site.logo_url || null)
  const [heroImage, setHeroImage] = useState(site.hero_image || null)
  const [brandMode, setBrandMode] = useState(site.settings?.brandMode || 'logo_text')
  const [logoSize, setLogoSize] = useState(site.settings?.logoSize || 38)

  useEffect(() => { setTheme(site.theme || {}) }, [site.id, site.updated_at]) // eslint-disable-line
  useEffect(() => {
    setLogoUrl(site.logo_url || null); setHeroImage(site.hero_image || null)
    setBrandMode(site.settings?.brandMode || 'logo_text'); setLogoSize(site.settings?.logoSize || 38)
  }, [site.id, site.updated_at]) // eslint-disable-line

  const applyTemplate = async (tid) => {
    const merged = { ...theme, ...PRESETS[tid] }
    setTheme(merged)
    setSaving(true)
    try {
      await updateMySite(site.id, { template: tid, theme: merged })
      toast.success('Theme applied!')
      reload()
    } catch { toast.error('Could not update design') }
    finally { setSaving(false) }
  }

  const saveTheme = async (t) => {
    setSaving(true)
    try {
      await updateMySite(site.id, { theme: t })
      toast.success('Colors saved')
      reload()
    } catch { toast.error('Could not save colors') }
    finally { setSaving(false) }
  }

  const saveMedia = async (data) => {
    setSaving(true)
    try {
      await setMySiteMedia(site.id, data)
      toast.success('Brand images updated')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not update images')) }
    finally { setSaving(false) }
  }

  const saveBrand = async () => {
    setSaving(true)
    try {
      await setMySiteSettings(site.id, { brand_mode: brandMode, logo_size: logoSize })
      toast.success('Brand display saved')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not save brand settings')) }
    finally { setSaving(false) }
  }

  const pickLogo = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    try {
      const dataUrl = await fileToDataUrl(f, 512, 0.9)
      setLogoUrl(dataUrl)
      await saveMedia({ logo_url: dataUrl })
    } catch (err) { toast.error(err.message) }
  }
  const pickHero = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    try {
      const dataUrl = await fileToDataUrl(f, 1600, 0.85)
      setHeroImage(dataUrl)
      await saveMedia({ hero_image: dataUrl })
    } catch (err) { toast.error(err.message) }
  }

  const set = (k, v) => setTheme((t) => ({ ...t, [k]: v }))

  return (
    <div>
      <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6 }}>Professional themes</h3>
      <p style={{ color: '#64748b', fontSize: 13, marginBottom: 18 }}>One tap applies the whole look — colors, fonts and background.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 14, marginBottom: 32 }}>
        {TEMPLATES.map((t) => (
          <button key={t.id} onClick={() => applyTemplate(t.id)} disabled={saving}
            style={{
              ...cardStyle, padding: 16, cursor: 'pointer', textAlign: 'left', position: 'relative',
              border: `2px solid ${site.template === t.id ? '#4f46e5' : '#e2e8f0'}`,
              background: site.template === t.id ? 'rgba(79,70,229,0.04)' : '#fff',
            }}>
            {t.tier === 'Premium' && (
              <span style={{
                position: 'absolute', top: 10, right: 10, fontSize: 9, fontWeight: 800, letterSpacing: 0.5,
                padding: '3px 8px', borderRadius: 10, background: 'linear-gradient(135deg,#d97706,#f59e0b)', color: '#fff',
              }}>PREMIUM</span>
            )}
            <div style={{
              height: 84, borderRadius: 10, marginBottom: 12, position: 'relative', overflow: 'hidden',
              background: t.id === 'celestial' || t.id === 'royal' || t.id === 'tantra' || t.id === 'classic'
                ? `linear-gradient(160deg, ${t.colors[0]}22, #0a0a1a)` : `linear-gradient(160deg, ${t.colors[0]}18, #f8fafc)`,
              border: `1px solid ${t.colors[0]}33`,
            }}>
              <div style={{ position: 'absolute', top: 10, left: 10, width: 20, height: 20, borderRadius: 6, background: `linear-gradient(135deg, ${t.colors[0]}, ${t.colors[1]})` }} />
              <div style={{ position: 'absolute', top: 40, left: 10, width: '60%', height: 8, borderRadius: 4, background: `${t.colors[0]}55` }} />
              <div style={{ position: 'absolute', top: 40, right: 10, width: 26, height: 26, borderRadius: 6, background: `linear-gradient(135deg, ${t.colors[0]}, ${t.colors[1]})`, opacity: 0.8 }} />
            </div>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{t.name}</div>
            <div style={{ color: '#64748b', fontSize: 11.5, marginTop: 4, lineHeight: 1.4 }}>{t.desc}</div>
          </button>
        ))}
      </div>

      <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 16 }}>Your logo & photo</h3>
      <div style={{ ...cardStyle, display: 'flex', gap: 32, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 32 }}>
        <div>
          <label style={labelStyle}>Logo</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {logoUrl
              ? <img src={logoUrl} alt="logo" style={{ height: logoSize, width: 'auto', maxWidth: logoSize * 3, borderRadius: 10, objectFit: 'contain', border: '1px solid #e2e8f0', background: '#fff', padding: 4 }} />
              : <div style={{ width: 56, height: 56, borderRadius: 12, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={22} color="#94a3b8" /></div>}
            <label style={{ ...ghostBtn, padding: '8px 14px', fontSize: 13, cursor: 'pointer' }}>
              {logoUrl ? 'Change' : 'Upload'}
              <input type="file" accept="image/*" onChange={pickLogo} style={{ display: 'none' }} />
            </label>
            {logoUrl && (
              <button onClick={() => { setLogoUrl(null); saveMedia({ logo_url: null }) }} title="Remove logo"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}><Trash2 size={15} /></button>
            )}
          </div>
        </div>
        <div>
          <label style={labelStyle}>Hero photo (appears on your homepage)</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {heroImage
              ? <img src={heroImage} alt="hero" style={{ width: 96, height: 56, borderRadius: 10, objectFit: 'cover', border: '1px solid #e2e8f0' }} />
              : <div style={{ width: 96, height: 56, borderRadius: 10, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={22} color="#94a3b8" /></div>}
            <label style={{ ...ghostBtn, padding: '8px 14px', fontSize: 13, cursor: 'pointer' }}>
              {heroImage ? 'Change' : 'Upload'}
              <input type="file" accept="image/*" onChange={pickHero} style={{ display: 'none' }} />
            </label>
            {heroImage && (
              <button onClick={() => { setHeroImage(null); saveMedia({ hero_image: null }) }} title="Remove photo"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}><Trash2 size={15} /></button>
            )}
          </div>
        </div>
      </div>

      <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 16 }}>Header brand display</h3>
      <div style={{ ...cardStyle, display: 'flex', gap: 32, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 32 }}>
        <div>
          <label style={labelStyle}>Show on your site header</label>
          <select value={brandMode} onChange={(e) => setBrandMode(e.target.value)} style={{ ...inputStyle, width: 'auto', padding: '10px 14px' }}>
            <option value="logo_text">Logo + name & tagline</option>
            <option value="logo">Logo only</option>
            <option value="text">Name & tagline only</option>
          </select>
        </div>
        <div>
          <label style={labelStyle}>Logo size — {logoSize}px {logoUrl && '(preview at left)'}</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <input type="range" min="20" max="96" step="2" value={logoSize}
              onChange={(e) => setLogoSize(Number(e.target.value))}
              style={{ width: 180, accentColor: '#4f46e5', cursor: 'pointer' }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#475569', minWidth: 34 }}>{logoSize}px</span>
          </div>
        </div>
        <button onClick={saveBrand} disabled={saving} style={{ ...primaryBtn, opacity: saving ? 0.7 : 1 }}>
          Save brand display
        </button>
      </div>
      <p style={{ color: '#94a3b8', fontSize: 12.5, margin: '-18px 0 32' }}>
        Logos of any shape work — wide or tall images are never cropped. Changes go live on your website immediately.
      </p>

      <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 16 }}>Fine-tune colors</h3>
      <div style={{ ...cardStyle, display: 'flex', gap: 32, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <label style={labelStyle}>Primary color</label>
          <input type="color" value={theme.primaryColor || '#4f46e5'} onChange={(e) => set('primaryColor', e.target.value)}
            style={{ width: 64, height: 40, border: 'none', background: 'none', cursor: 'pointer', borderRadius: 8 }} />
        </div>
        <div>
          <label style={labelStyle}>Accent color</label>
          <input type="color" value={theme.accentColor || '#d97706'} onChange={(e) => set('accentColor', e.target.value)}
            style={{ width: 64, height: 40, border: 'none', background: 'none', cursor: 'pointer', borderRadius: 8 }} />
        </div>
        <div>
          <label style={labelStyle}>Background style</label>
          <select value={theme.bgStyle || 'light'} onChange={(e) => set('bgStyle', e.target.value)} style={{ ...inputStyle, width: 'auto', padding: '10px 14px' }}>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
        <button onClick={() => saveTheme(theme)} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save colors'}
        </button>
      </div>
    </div>
  )
}

// ═══════════════ SERVICES TAB ═══════════════
function ServicesTab({ site, reload }) {
  const [svc, setSvc] = useState({ name: '', description: '', duration_minutes: 30, price: 500 })
  const [busy, setBusy] = useState(false)
  const [aiDialog, setAiDialog] = useState(false) // serviceDescription writer

  const addService = async () => {
    if (!svc.name.trim()) return toast.error('Give the service a name')
    setBusy(true)
    try {
      await createMyService(site.id, svc)
      toast.success('Service added')
      setSvc({ name: '', description: '', duration_minutes: 30, price: 500 })
      reload()
    } catch {
      toast.error('Could not add service')
    } finally { setBusy(false) }
  }

  const toggleActive = async (s) => {
    try {
      await updateMyService(site.id, s.id, { ...s, is_active: !s.is_active })
      reload()
    } catch { toast.error('Could not update') }
  }

  const remove = async (s) => {
    try {
      await deleteMyService(site.id, s.id)
      toast.success('Service removed')
      reload()
    } catch { toast.error('Could not remove') }
  }

  return (
    <div>
      <div style={cardStyle}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 18 }}>Your consultation services</h3>
        <div style={{ border: '1px solid #e2e8f0', borderRadius: 12, overflowX: 'auto', marginBottom: 6 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5, minWidth: 640 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
                {['Service', 'Price', 'Duration', 'Visible', ''].map((h) => (
                  <th key={h} style={{ textAlign: 'left', padding: '10px 14px', fontSize: 11.5, fontWeight: 800, color: '#64748b' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(site.services || []).map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 700 }}>{s.name} {!s.is_active && <span style={{ color: '#94a3b8', fontSize: 11.5 }}>(hidden)</span>}</div>
                    {s.description && <div style={{ color: '#64748b', fontSize: 12.5, maxWidth: 380 }}>{s.description}</div>}
                  </td>
                  <td style={{ padding: '10px 14px', fontWeight: 700 }}>₹{s.price}</td>
                  <td style={{ padding: '10px 14px', color: '#64748b' }}>{s.duration_minutes} min</td>
                  <td style={{ padding: '10px 14px' }}>
                    <button onClick={() => toggleActive(s)} title={s.is_active ? 'Hide from site' : 'Show on site'}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: s.is_active ? '#16a34a' : '#94a3b8' }}>
                      {s.is_active ? <Eye size={16} /> : <EyeOff size={16} />}
                    </button>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <button onClick={() => remove(s)} title="Delete" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: 18, marginTop: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 14 }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={labelStyle}>New service name</label>
              <input value={svc.name} onChange={(e) => setSvc((s) => ({ ...s, name: e.target.value }))} placeholder="Gemstone Consultation" style={inputStyle} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={labelStyle}>Description (optional)
                <button type="button" onClick={() => {
                  if (!svc.name.trim()) return toast.error('Give the service a name first')
                  setAiDialog(true)
                }} style={{ marginLeft: 8, padding: '3px 10px', borderRadius: 7, fontSize: 11.5, fontWeight: 700, cursor: 'pointer', border: '1px solid rgba(79,70,229,0.35)', color: '#4f46e5', background: 'rgba(79,70,229,0.06)' }}>
                  ✨ Write with AI
                </button>
              </label>
              <input value={svc.description} onChange={(e) => setSvc((s) => ({ ...s, description: e.target.value }))} placeholder="Find your right gemstone by kundli" style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Duration (minutes)</label>
              <input type="number" min="5" value={svc.duration_minutes} onChange={(e) => setSvc((s) => ({ ...s, duration_minutes: +e.target.value }))} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Price (₹)</label>
              <input type="number" min="0" value={svc.price} onChange={(e) => setSvc((s) => ({ ...s, price: +e.target.value }))} style={inputStyle} />
            </div>
          </div>
          <button onClick={addService} disabled={busy} className="btn-primary" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}>
            <Plus size={15} /> Add service
          </button>
        </div>
      </div>

      {aiDialog && (
        <AiWriterDialog
          site={site}
          field="serviceDescription"
          contextKey={svc.name.trim()}
          onClose={() => setAiDialog(false)}
          onApply={(text) => {
            setSvc((s) => ({ ...s, description: text }))
            setAiDialog(false)
            toast.success('Description added — Add the service to save it')
          }}
        />
      )}
    </div>
  )
}

// ═══════════════ STORE TAB (products + orders) ═══════════════
function StoreTab({ site, reload }) {
  // Returning from a provider's approval screen → open Integrations directly
  // so the success/error banner and the new connection are visible.
  const [sub, setSub] = useState(() =>
    new URLSearchParams(window.location.search).get('status') === 'ok' ? 'integrations' : 'products')
  const [catalog, setCatalog] = useState(null)
  const [importPrice, setImportPrice] = useState({})
  const [integrations, setIntegrations] = useState([])
  const [providers, setProviders] = useState(null) // {shopify_one_click, woocommerce_one_click}
  const [domains, setDomains] = useState({ shopify: '', woocommerce: '' }) // per-provider input
  const [showManual, setShowManual] = useState(false)
  const [connForm, setConnForm] = useState({ provider: 'woocommerce', shop_domain: '', api_key: '', api_secret: '', access_token: '' })
  const [wooKey, setWooKey] = useState(null)
  const [wooSteps, setWooSteps] = useState([])
  const [banners, setBanners] = useState((site.settings?.storeBanners) || [])
  const [sections, setSections] = useState((site.settings?.storeSections) || [])
  useEffect(() => {
    setBanners(site.settings?.storeBanners || [])
    setSections(site.settings?.storeSections || [])
  }, [site.id, site.updated_at]) // eslint-disable-line

  const addBannerFile = (file) => {
    if (!file) return
    if (file.size > 900_000) return toast.error('Banner too large — use an image under 900 KB')
    const reader = new FileReader()
    reader.onload = () => setBanners((b) => [...b, { image: reader.result, title: '', subtitle: '', link: '#/shop' }])
    reader.readAsDataURL(file)
  }

  const saveLayout = async () => {
    setBusy(true)
    try {
      await setMySiteSettings(site.id, { store_banners: banners, store_sections: sections })
      toast.success('Store layout saved — refresh your site to see it')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not save layout')) }
    finally { setBusy(false) }
  }
  const [oauthResult, setOauthResult] = useState(null) // {status, message} from the provider redirect
  const [pushSel, setPushSel] = useState([])
  const [products, setProducts] = useState(null)
  const [orders, setOrders] = useState(null)
  // null → chooser ("add own" vs "import from catalog"); 'own' → create form
  const [addMode, setAddMode] = useState(null)
  const [form, setForm] = useState({ name: '', description: '', price: 500, stock: -1, category: '' })
  const [busy, setBusy] = useState(false)
  const [connecting, setConnecting] = useState(null) // provider id while awaiting redirect

  // The OAuth callback lands on /mysite/store?status=…&message=…
  useEffect(() => {
    const q = new URLSearchParams(window.location.search)
    if (q.get('status')) {
      setOauthResult({ status: q.get('status'), message: q.get('message') || '' })
      q.delete('status'); q.delete('message')
      window.history.replaceState({}, '', `${window.location.pathname}${q.toString() ? `?${q}` : ''}`)
    }
  }, [])

  const loadProducts = () => getMyProducts(site.id).then(setProducts).catch(() => setProducts([]))
  const loadOrders = () => getMyOrders(site.id).then(setOrders).catch(() => setOrders([]))
  useEffect(() => {
    if (sub === 'products') loadProducts()
    else loadOrders()
  }, [sub, site.id, site.updated_at]) // eslint-disable-line

  const loadCatalog = () => getMyCatalog(site.id).then(setCatalog).catch(() => setCatalog({ categories: [], products: [] }))
  useEffect(() => { if (sub === 'catalog') loadCatalog() }, [sub, site.id]) // eslint-disable-line

  const loadIntegrations = () => {
    getMyIntegrations(site.id).then((d) => { setIntegrations(d.integrations || []) }).catch(() => setIntegrations([]))
    getIntegrationProviders(site.id).then(setProviders).catch(() => setProviders(null))
  }
  useEffect(() => { if (sub === 'integrations' || sub === 'layout') { loadIntegrations(); loadProducts() } }, [sub, site.id]) // eslint-disable-line

  // After a successful OAuth redirect, refresh the integration list — the
  // connection was created by the backend callback, not by this tab.
  useEffect(() => {
    if (oauthResult?.status === 'ok' && sub === 'integrations') loadIntegrations()
  }, [oauthResult, sub]) // eslint-disable-line

  const startOneClick = async (provider) => {
    const domain = (domains[provider] || '').trim()
    if (!domain) return toast.error(provider === 'shopify' ? 'Enter your Shopify store domain (e.g. mystore.myshopify.com)' : 'Enter your store domain (e.g. mystore.com)')
    if (provider === 'shopify' && providers && providers.shopify_one_click === false) {
      return toast.error('One-click Shopify is not enabled on this deployment — use "Advanced" below')
    }
    setConnecting(provider)
    try {
      const res = await beginStoreConnect(site.id, provider, domain)
      window.location.href = res.authorize_url // provider's own approval screen
    } catch (e) {
      const detail = errDetail(e, '')
      if (e.response?.status === 405 || /method not allowed/i.test(detail)) {
        toast.error('The server does not support one-click connect yet — it needs a backend update. Use "Advanced" below for now.')
      } else {
        toast.error(errDetail(e, 'Could not start the connection'))
      }
      setConnecting(null)
    }
  }

  const doConnect = async (e) => {
    e.preventDefault(); setBusy(true)
    try {
      await connectStore(site.id, connForm)
      toast.success('Store connected')
      setConnForm({ provider: connForm.provider, shop_domain: '', api_key: '', api_secret: '', access_token: '' })
      loadIntegrations()
    } catch (e2) { toast.error(errDetail(e2, 'Could not connect the store')) }
    finally { setBusy(false) }
  }

  const doPush = async (cid) => {
    if (!pushSel.length) return toast.error('Select products first')
    setBusy(true)
    try {
      const res = await pushToStore(site.id, cid, pushSel)
      const ok = (res.results || []).filter((r) => r.ok).length
      toast.success(`Pushed ${ok}/${res.results.length} products`)
      setPushSel([])
    } catch (e2) { toast.error(errDetail(e2, 'Push failed')) }
    finally { setBusy(false) }
  }

  const doPull = async (cid) => {
    setBusy(true)
    try {
      const res = await pullStoreOrders(site.id, cid)
      toast.success(`${res.imported || 0} new orders imported (${res.skipped || 0} already known)`)
    } catch (e2) { toast.error(errDetail(e2, 'Pull failed')) }
    finally { setBusy(false) }
  }

  const doImport = async (mp) => {
    const price = importPrice[mp.id] ?? mp.mrp
    setBusy(true)
    try {
      await importCatalogProduct(site.id, mp.id, price)
      toast.success(`Imported — listed at ₹${price} (your cost ₹${mp.cost})`)
      loadCatalog(); loadProducts()
    } catch (e) { toast.error(errDetail(e, 'Import failed')) }
    finally { setBusy(false) }
  }

  const addProduct = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return toast.error('Give the product a name')
    setBusy(true)
    try {
      let image
      const f = e.target.elements?.photo?.files?.[0]
      if (f) image = await fileToDataUrl(f, 900, 0.85)
      await createMyProduct(site.id, { ...form, image: image || undefined })
      toast.success('Product added')
      setForm({ name: '', description: '', price: 500, stock: -1 })
      e.target.reset?.()
      loadProducts()
      reload()
    } catch (err) {
      toast.error(errDetail(err, 'Could not add product'))
    } finally { setBusy(false) }
  }

  const toggleProduct = async (p) => {
    try {
      await updateMyProduct(site.id, p.id, { name: p.name, price: p.price, is_active: !p.is_active })
      loadProducts()
    } catch { toast.error('Could not update') }
  }

  const removeProduct = async (p) => {
    try {
      await deleteMyProduct(site.id, p.id)
      toast.success('Product removed')
      loadProducts()
      reload()
    } catch { toast.error('Could not remove') }
  }

  const setOrderStatus = async (o, status) => {
    try {
      await updateMyOrder(site.id, o.id, { status })
      loadOrders()
    } catch { toast.error('Could not update order') }
  }

  const orderBadge = {
    new: { bg: 'rgba(245,158,11,0.12)', c: '#d97706' },
    confirmed: { bg: 'rgba(34,197,94,0.12)', c: '#16a34a' },
    fulfilled: { bg: 'rgba(59,130,246,0.12)', c: '#2563eb' },
    cancelled: { bg: 'rgba(239,68,68,0.12)', c: '#ef4444' },
  }

  return (
    <div>
      {/* toggle store visibility */}
      <div style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 14, flexWrap: 'wrap', marginBottom: 20 }}>
        <div>
          <h3 style={{ fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Store size={16} color="#4f46e5" /> Online store on your website
          </h3>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
            Sell gemstones, rudraksha, puja items and reports. {site.settings?.showStore ? 'The store is live on your site.' : 'Turn on to show the Shop section to visitors.'}
          </p>
        </div>
        <button
          onClick={async () => {
            try {
              await setMySiteSettings(site.id, { show_store: !site.settings?.showStore })
              toast.success(site.settings?.showStore ? 'Store hidden' : 'Store is live on your site!')
              reload()
            } catch (e) { toast.error(errDetail(e)) }
          }}
          className={site.settings?.showStore ? 'btn-primary' : ''}
          style={site.settings?.showStore ? primaryBtn : { ...ghostBtn, borderColor: '#4f46e5', color: '#4f46e5' }}>
          {site.settings?.showStore ? <><Eye size={15} /> Store live</> : <><EyeOff size={15} /> Enable store</>}
        </button>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {[['products', 'Products', Package], ['layout', 'Store layout', Palette], ['catalog', 'Import catalog', ShoppingBag], ['integrations', 'Integrations', Link2], ['orders', 'Orders', ShoppingBag]].map(([id, label, Icon]) => (
          <button key={id} onClick={() => setSub(id)} style={{
            ...ghostBtn, padding: '8px 18px', fontSize: 13,
            background: sub === id ? 'rgba(79,70,229,0.1)' : 'transparent',
            borderColor: sub === id ? '#4f46e5' : '#e2e8f0',
            color: sub === id ? '#4f46e5' : '#0f172a',
          }}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

                      {sub === 'integrations' && (
          <div style={{ ...cardStyle, marginBottom: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginBottom: 16 }}>
              <button onClick={async () => {
                try {
                  const d = await wooOneClickStart(site.id)
                  setWooKey(d.activation_key)
                  setWooSteps(d.plugin_instructions || [])
                } catch (e) { toast.error(errDetail(e, 'Could not start the connect')) }
              }} style={{ padding: '14px', borderRadius: 12, border: '2px solid #7c3aed', background: 'rgba(124,58,237,0.06)', cursor: 'pointer', textAlign: 'left' }}>
                <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 3 }}>🛒 WooCommerce — one click</div>
                <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>Install our plugin, paste one key, done. No API keys to copy.</div>
              </button>
              <button onClick={() => toast('Shopify one-click needs the AstroVakta Shopify app — coming soon. Use the token method below for now.', { icon: 'ℹ️' })}
                style={{ padding: '14px', borderRadius: 12, border: '2px solid #e2e8f0', background: '#fff', cursor: 'pointer', textAlign: 'left' }}>
                <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 3 }}>🟢 Shopify — one click</div>
                <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>Approve once on Shopify's screen — no tokens.</div>
              </button>
            </div>
            {wooKey && (
              <div style={{ padding: 14, borderRadius: 12, background: 'rgba(79,70,229,0.06)', border: '1px solid rgba(79,70,229,0.25)', marginBottom: 16 }}>
                <div style={{ fontWeight: 800, fontSize: 13.5, marginBottom: 6 }}>Your activation key</div>
                <code style={{ display: 'inline-block', background: '#fff', padding: '8px 12px', borderRadius: 8, fontSize: 13.5, border: '1px solid #e2e8f0', userSelect: 'all' }}>{wooKey}</code>
                <div style={{ marginTop: 10, fontSize: 12.5, color: '#64748b', lineHeight: 1.8 }}>
                  {(wooSteps.length ? wooSteps : ['1. Install the AstroVakta Connect plugin in WordPress.', '2. Paste this key in the plugin settings.', '3. Click Connect.']).map((st, i) => <div key={i}>{st}</div>)}
                </div>
              </div>
            )}
            {oauthResult && (
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 14px', borderRadius: 10,
                marginBottom: 16, fontSize: 13.5, lineHeight: 1.5,
                background: oauthResult.status === 'ok' ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
                border: `1px solid ${oauthResult.status === 'ok' ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
                color: oauthResult.status === 'ok' ? '#166534' : '#991b1b',
              }}>
                <span style={{ fontSize: 16 }}>{oauthResult.status === 'ok' ? '✓' : '⚠'}</span>
                <span style={{ flex: 1 }}>{oauthResult.message}</span>
                <button onClick={() => setOauthResult(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0, fontSize: 15, lineHeight: 1 }}><X size={14} /></button>
              </div>
            )}

            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Connect your store</h3>
            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16, lineHeight: 1.6 }}>
              Push your products to your store and pull its orders back here — no API keys to create or
              copy. Enter the store address, click connect, and approve on the next screen. Done.
              WooCommerce is live; Shopify one-click is coming soon (until then, Shopify stores can be
              connected from "Advanced" below).
            </p>

            {(integrations || []).length > 0 && (
              <div style={{ marginBottom: 18 }}>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: '#475569', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.4 }}>Connected stores</div>
                {integrations.map((c) => (
                  <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 12, marginBottom: 8, flexWrap: 'wrap', background: '#f8fafc' }}>
                    <span style={{ width: 30, height: 30, borderRadius: 8, background: c.provider === 'shopify' ? '#95bf47' : '#7f54b3', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, fontWeight: 800 }}>
                      {c.provider === 'shopify' ? 'S' : 'W'}
                    </span>
                    <span style={{ fontWeight: 700, fontSize: 14, flex: 1, minWidth: 140 }}>
                      {c.provider === 'shopify' ? 'Shopify' : 'WooCommerce'} — {c.shop_domain}
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginLeft: 8, fontSize: 11.5, fontWeight: 700, color: '#16a34a' }}><Check size={12} /> connected</span>
                    </span>
                    {c.provider === 'shopify' && (
                      <button onClick={() => doPull(c.id)} disabled={busy} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12.5 }}>Pull orders</button>
                    )}
                    <button onClick={() => doPush(c.id)} disabled={busy || !pushSel.length} style={{ ...primaryBtn, padding: '6px 12px', fontSize: 12.5, opacity: pushSel.length ? 1 : 0.5 }}>
                      Push selected ({pushSel.length})
                    </button>
                    <button onClick={async () => { await disconnectStore(site.id, c.id); loadIntegrations() }}
                      style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: 12.5, textDecoration: 'underline' }}>
                      Disconnect
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginBottom: 14 }}>
              {[[
                'shopify', 'Shopify', '#95bf47', 'mystore.myshopify.com',
                false, // coming soon — flip to true once SHOPIFY_CLIENT_ID/SECRET are set on the server
              ], [
                'woocommerce', 'WooCommerce', '#7f54b3', 'mystore.com',
                true,
              ]].map(([id, label, color, ph, enabled]) => (
                <div key={id} style={{ border: '1px solid #e2e8f0', borderRadius: 14, padding: 16, display: 'flex', flexDirection: 'column', gap: 10, opacity: enabled ? 1 : 0.6, position: 'relative' }}>
                  {!enabled && (
                    <span style={{ position: 'absolute', top: 12, right: 12, fontSize: 10, fontWeight: 800, letterSpacing: 0.5, background: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0', borderRadius: 999, padding: '3px 8px', textTransform: 'uppercase' }}>
                      Coming soon
                    </span>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ width: 34, height: 34, borderRadius: 10, background: color, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 800 }}>
                      {label[0]}
                    </span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14.5 }}>{label}</div>
                      <div style={{ fontSize: 11.5, color: '#64748b' }}>{enabled ? 'One-click connect' : 'One-click connect — coming soon'}</div>
                    </div>
                  </div>
                  <input
                    value={domains[id] || ''}
                    onChange={(e) => setDomains((d) => ({ ...d, [id]: e.target.value }))}
                    onKeyDown={(e) => { if (e.key === 'Enter' && enabled) startOneClick(id) }}
                    placeholder={ph}
                    style={inputStyle}
                    disabled={!enabled}
                  />
                  <button
                    onClick={() => startOneClick(id)}
                    disabled={!enabled || connecting === id}
                    className={enabled ? 'btn-primary' : ''}
                    style={{ ...primaryBtn, justifyContent: 'center', opacity: enabled && connecting !== id ? 1 : 0.6, fontSize: 13.5, padding: '10px 16px', background: enabled ? undefined : '#94a3b8' }}>
                    {enabled
                      ? (connecting === id ? <><Loader2 size={15} className="spin" /> Redirecting…</> : <><Zap size={15} /> Connect {label} in one click</>)
                      : <>Coming soon</>}
                  </button>
                </div>
              ))}
            </div>

            <button onClick={() => setShowManual((s) => !s)} style={{ background: 'none', border: 'none', color: '#4f46e5', fontWeight: 600, fontSize: 12.5, cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>
              {showManual ? 'Hide' : 'Advanced'} — connect manually with API keys
            </button>
            {showManual && (
              <form onSubmit={doConnect} style={{ marginTop: 12, padding: 16, border: '1px dashed #cbd5e1', borderRadius: 12 }}>
                <p style={{ fontSize: 12.5, color: '#64748b', marginBottom: 12, lineHeight: 1.6 }}>
                  For stores that can't use one-click (e.g. a WooCommerce site on plain http).
                  WooCommerce: paste the Consumer Key/Secret from WooCommerce → Settings → Advanced → REST API.
                  Shopify: create a custom app with write_products/read_orders scopes and paste the Admin API access token.
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10, marginBottom: 10 }}>
                  <select value={connForm.provider} onChange={(e) => setConnForm({ ...connForm, provider: e.target.value })} style={inputStyle}>
                    <option value="woocommerce">WooCommerce</option>
                    <option value="shopify">Shopify</option>
                  </select>
                  <input value={connForm.shop_domain} onChange={(e) => setConnForm({ ...connForm, shop_domain: e.target.value })} placeholder="mystore.com" style={inputStyle} />
                  {connForm.provider === 'woocommerce' ? (
                    <>
                      <input value={connForm.api_key} onChange={(e) => setConnForm({ ...connForm, api_key: e.target.value })} placeholder="Consumer key (ck_…)" style={inputStyle} />
                      <input value={connForm.api_secret} onChange={(e) => setConnForm({ ...connForm, api_secret: e.target.value })} placeholder="Consumer secret (cs_…)" style={inputStyle} />
                    </>
                  ) : (
                    <input value={connForm.access_token} onChange={(e) => setConnForm({ ...connForm, access_token: e.target.value })} placeholder="Admin API access token (shpat_…)" style={inputStyle} />
                  )}
                </div>
                <button type="submit" disabled={busy} className="btn-primary" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}>Connect store</button>
              </form>
            )}

            {(products || []).length > 0 && (
              <div style={{ marginTop: 18 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#475569', marginBottom: 8 }}>Your products — tick to push:</div>
                {products.map((p) => (
                  <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', fontSize: 13.5, cursor: 'pointer', color: '#334155' }}>
                    <input type="checkbox" checked={pushSel.includes(p.id)}
                      onChange={(e) => setPushSel((s2) => e.target.checked ? [...s2, p.id] : s2.filter((x) => x !== p.id))}
                      style={{ accentColor: '#4f46e5' }} />
                    {p.name} — ₹{p.price}
                  </label>
                ))}
              </div>
            )}
          </div>
        )}
        {sub === 'layout' && (
          <div style={{ ...cardStyle, marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Storefront layout</h3>
            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 14, lineHeight: 1.6 }}>
              Control your shop's home page: a rotating banner carousel and curated sections (best selling, top products, trending). Changes appear on your live store immediately.
            </p>

            {/* banners */}
            <div style={{ fontSize: 13.5, fontWeight: 800, margin: '14px 0 8px' }}>Banner carousel</div>
            {!banners.length && <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 8 }}>No banners — add the first one below.</div>}
            {banners.map((b, i) => (
              <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap' }}>
                <img src={b.image} alt="" style={{ width: 72, height: 40, borderRadius: 8, objectFit: 'cover' }} />
                <input value={b.title} onChange={(e) => setBanners(banners.map((x, j) => j === i ? { ...x, title: e.target.value } : x))} placeholder="Title (Navratri Sale)" style={{ ...inputStyle, flex: 1, minWidth: 120 }} />
                <input value={b.subtitle} onChange={(e) => setBanners(banners.map((x, j) => j === i ? { ...x, subtitle: e.target.value } : x))} placeholder="Subtitle (Up to 20% off)" style={{ ...inputStyle, flex: 1.4, minWidth: 140 }} />
                <button onClick={() => setBanners(banners.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer' }}><Trash2 size={15} /></button>
              </div>
            ))}
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '9px 14px', borderRadius: 10, border: '1.5px dashed #cbd5e1', cursor: 'pointer', fontWeight: 700, fontSize: 13, color: '#475569', marginTop: 8 }}>
              <Plus size={14} /> Add banner image
              <input type="file" accept="image/*" style={{ display: 'none' }} onChange={(e) => addBannerFile(e.target.files?.[0])} />
            </label>

            {/* sections */}
            <div style={{ fontSize: 13.5, fontWeight: 800, margin: '20px 0 8px' }}>Sections</div>
            {!sections.length && <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 8 }}>No sections — add Best Selling, Top Products or Trending below.</div>}
            {sections.map((sec, i) => (
              <div key={i} style={{ padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 12, marginBottom: 10 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
                  <input value={sec.title} onChange={(e) => setSections(sections.map((x, j) => j === i ? { ...x, title: e.target.value } : x))} placeholder="Section title" style={{ ...inputStyle, flex: 1, minWidth: 140 }} />
                  <select value={sec.kind} onChange={(e) => setSections(sections.map((x, j) => j === i ? { ...x, kind: e.target.value } : x))} style={{ ...inputStyle, width: 160 }}>
                    <option value="manual">Chosen products</option>
                    <option value="bestselling">Best selling (auto)</option>
                    <option value="top">Top products (auto)</option>
                    <option value="trending">Trending (auto)</option>
                  </select>
                  <button onClick={() => setSections(sections.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer' }}><Trash2 size={15} /></button>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {(products || []).map((p) => {
                    const on = (sec.product_ids || []).includes(p.id)
                    return (
                      <button key={p.id} onClick={() => setSections(sections.map((x, j) => j === i ? { ...x, product_ids: on ? x.product_ids.filter((id) => id !== p.id) : [...(x.product_ids || []), p.id] } : x))}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 10px', borderRadius: 999, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                          border: `1.5px solid ${on ? '#4f46e5' : '#e2e8f0'}`, background: on ? 'rgba(79,70,229,0.08)' : '#fff', color: on ? '#4f46e5' : '#475569' }}>
                        {on ? '✓ ' : ''}{p.name.slice(0, 24)} · ₹{p.price}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              {['Best Selling', 'Top Products', 'Trending'].map((t) => (
                <button key={t} onClick={() => setSections([...sections, { title: t, kind: t.toLowerCase().includes('best') ? 'bestselling' : t.toLowerCase().includes('top') ? 'top' : 'trending', product_ids: [] }])}
                  style={{ ...ghostBtn, padding: '8px 12px', fontSize: 12.5 }}>+ {t}</button>
              ))}
              <button onClick={() => setSections([...sections, { title: '', kind: 'manual', product_ids: [] }])} style={{ ...ghostBtn, padding: '8px 12px', fontSize: 12.5 }}>+ Custom section</button>
            </div>

            <button onClick={saveLayout} disabled={busy} className="btn-primary" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}>
              <Save size={15} /> {busy ? 'Saving…' : 'Save store layout'}
            </button>
          </div>
        )}
{sub === 'catalog' && (
          <div style={{ ...cardStyle, marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Import from master catalog</h3>
            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 14, lineHeight: 1.6 }}>
              Products curated by AstroVakta. Your cost = MRP − margin. List at MRP or set your own price — you keep the difference.
            </p>
            {!catalog ? <DashboardLoader label="Loading catalog" size={44} /> : (
              <>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                <button onClick={() => setImportCat('all')} style={{ padding: '7px 14px', borderRadius: 999, cursor: 'pointer', fontSize: 12.5, fontWeight: 700, border: '1.5px solid ' + (importCat === 'all' ? '#4f46e5' : '#e2e8f0'), background: importCat === 'all' ? '#4f46e5' : '#fff', color: importCat === 'all' ? '#fff' : '#475569' }}>All categories</button>
                {(catalog.categories || []).map((c) => (
                  <button key={c.id} onClick={() => setImportCat(c.name)} style={{ padding: '7px 14px', borderRadius: 999, cursor: 'pointer', fontSize: 12.5, fontWeight: 700, border: '1.5px solid ' + (importCat === c.name ? '#4f46e5' : '#e2e8f0'), background: importCat === c.name ? '#4f46e5' : '#fff', color: importCat === c.name ? '#fff' : '#475569' }}>{c.name}</button>
                ))}
              </div>
              {(catalog.products || []).filter((mp) => importCat === 'all' || mp.category === importCat).map((mp) => (
                <div key={mp.id} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 0', borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap' }}>
                  {mp.image ? <img src={mp.image} alt="" style={{ width: 52, height: 52, borderRadius: 10, objectFit: 'cover' }} /> : <div style={{ width: 52, height: 52, borderRadius: 10, background: '#f1f5f9' }} />}
                  <div style={{ flex: 1, minWidth: 180 }}>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{mp.name} <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>{mp.category}</span></div>
                    <div style={{ fontSize: 12.5, color: '#64748b' }}>MRP ₹{mp.mrp} · your cost ₹{mp.cost} · min price ₹{mp.cost}</div>
                  </div>
                  {mp.imported ? (
                    <span style={{ fontSize: 12.5, fontWeight: 700, color: '#16a34a' }}>Imported ✓ (₹{mp.current_price})</span>
                  ) : (
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <input type="number" value={importPrice[mp.id] ?? mp.mrp} min={mp.cost}
                        onChange={(e) => setImportPrice((p) => ({ ...p, [mp.id]: Number(e.target.value) }))}
                        placeholder={`₹${mp.mrp}`} style={{ ...inputStyle, width: 100 }} />
                      <button onClick={() => doImport(mp)} disabled={busy} className="btn-primary" style={{ ...primaryBtn, padding: '8px 14px', fontSize: 13 }}>
                        Import
                      </button>
                    </div>
                  )}
                </div>
              ))}
              </>
            )}
          </div>
        )}
{sub === 'products' && (
        <>
          {products === null ? (
            <DashboardLoader label="Loading products" />
          ) : products.length === 0 ? (
            <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 40 }}>
              <Package size={32} style={{ marginBottom: 12 }} />
              <div>No products yet. Add your first product below — it appears in your site's Shop section.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))', gap: 14, marginBottom: 24 }}>
              {products.map((p) => (
                <div key={p.id} style={{ ...cardStyle, padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {p.image
                    ? <img src={p.image} alt={p.name} style={{ width: '100%', height: 130, objectFit: 'cover', borderRadius: 10 }} />
                    : <div style={{ width: '100%', height: 130, borderRadius: 10, background: 'rgba(79,70,229,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Package size={28} color="#cbd5e1" /></div>}
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{p.name} {!p.is_active && <span style={{ color: '#94a3b8', fontSize: 11, fontWeight: 600 }}>(hidden)</span>}</div>
                    {p.description && <div style={{ color: '#64748b', fontSize: 12, marginTop: 3, lineHeight: 1.5 }}>{p.description}</div>}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontWeight: 800, fontSize: 15 }}>₹{p.price}</div>
                    <div style={{ fontSize: 12, color: p.stock === -1 ? '#94a3b8' : p.stock > 0 ? '#16a34a' : '#ef4444', fontWeight: 600 }}>
                      {p.stock === -1 ? 'Unlimited' : p.stock > 0 ? `${p.stock} in stock` : 'Out of stock'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, borderTop: '1px solid #f1f5f9', paddingTop: 10 }}>
                    <button onClick={() => toggleProduct(p)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: p.is_active ? '#16a34a' : '#94a3b8', flex: 1, display: 'flex', justifyContent: 'center' }}>
                      {p.is_active ? <Eye size={16} /> : <EyeOff size={16} />}
                    </button>
                    <button onClick={() => removeProduct(p)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', flex: 1, display: 'flex', justifyContent: 'center' }}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {addMode === null ? (
            <div style={{ ...cardStyle, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
              <button onClick={() => setAddMode('own')} style={{ padding: '18px', borderRadius: 14, border: '2px solid #e2e8f0', background: '#fff', cursor: 'pointer', textAlign: 'left' }}>
                <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 4 }}>➕ Add your own product</div>
                <div style={{ fontSize: 12.5, color: '#64748b', lineHeight: 1.5 }}>Create a product from scratch — name, price, stock and photos.</div>
              </button>
              <button onClick={() => setSub('catalog')} style={{ padding: '18px', borderRadius: 14, border: '2px solid rgba(79,70,229,0.4)', background: 'rgba(79,70,229,0.05)', cursor: 'pointer', textAlign: 'left' }}>
                <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 4 }}>📦 Import products from AstroVakta</div>
                <div style={{ fontSize: 12.5, color: '#64748b', lineHeight: 1.5 }}>Browse the master catalog by category — certified products with ready photos & details.</div>
              </button>
            </div>
          ) : (
            <div style={cardStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700 }}>Add your own product</h3>
                <button onClick={() => setAddMode(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', fontSize: 13, textDecoration: 'underline' }}>Close</button>
              </div>
              <form onSubmit={async (e) => { const ok = await addProduct(e); if (ok !== false) setAddMode(null) }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 14 }}>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={labelStyle}>Product name</label>
                    <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Yellow Sapphire (Pukhraj) 5.25 ct" style={inputStyle} />
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={labelStyle}>Category (optional — type a new one or pick existing)</label>
                    <input list="prod-cats" value={form.category || ''} onChange={(e) => setForm((f2) => ({ ...f2, category: e.target.value }))} placeholder="Gemstones / Rudraksha / Bracelets…" style={inputStyle} />
                    <datalist id="prod-cats">
                      {[...new Set([...(catalog?.categories || []).map((c) => c.name), ...products.map((p2) => p2.category).filter(Boolean)])].map((c) => (
                        <option key={c} value={c} />
                      ))}
                    </datalist>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={labelStyle}>Description (optional)</label>
                    <input value={form.description} onChange={(e) => setForm((f2) => ({ ...f2, description: e.target.value }))} placeholder="Certified, government-lab tested" style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Price (₹)</label>
                    <input type="number" min="0" value={form.price} onChange={(e) => setForm((f) => ({ ...f, price: +e.target.value }))} style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Stock (-1 = unlimited)</label>
                    <input type="number" min="-1" value={form.stock} onChange={(e) => setForm((f) => ({ ...f, stock: +e.target.value }))} style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Photo (optional)</label>
                    <input type="file" name="photo" accept="image/*" style={{ ...inputStyle, padding: '7px 10px', fontSize: 12 }} />
                  </div>
                </div>
                <button type="submit" disabled={busy} className="btn-primary" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}>
                  <Plus size={15} /> {busy ? 'Adding…' : 'Add product'}
                </button>
              </form>
            </div>
          )}
        </>
      )}

      {sub === 'orders' && (
        <>
          {orders === null ? (
            <DashboardLoader label="Loading orders" />
          ) : orders.length === 0 ? (
            <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 40 }}>
              <ShoppingBag size={32} style={{ marginBottom: 12 }} />
              <div>No orders yet. When visitors buy from your store, orders appear here with WhatsApp follow-up links.</div>
            </div>
          ) : (
            orders.map((o) => (
              <div key={o.id} style={{ ...cardStyle, padding: '16px 20px', marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1, minWidth: 220 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 700, fontSize: 15 }}>#{o.id} · {o.client_name}</span>
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12,
                        background: orderBadge[o.status]?.bg, color: orderBadge[o.status]?.c,
                      }}>{o.status}</span>
                    </div>
                    <div style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
                      {o.client_phone ? `${o.client_phone} · ` : ''}{new Date(o.created_at).toLocaleString()}
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                      {(o.items || []).map((it, i) => (
                        <span key={i} style={{ fontSize: 12, background: 'rgba(79,70,229,0.06)', padding: '3px 10px', borderRadius: 8, color: '#475569' }}>
                          {it.name} × {it.qty} (₹{it.price})
                        </span>
                      ))}
                    </div>
                    {o.address && <div style={{ color: '#64748b', fontSize: 12, marginTop: 8 }}>📍 {o.address}</div>}
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 800, fontSize: 17, marginBottom: 10 }}>₹{o.amount}</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      {o.client_phone && (
                        <a href={`https://wa.me/${String(o.client_phone).replace(/[^\d]/g, '').length >= 10 ? String(o.client_phone).replace(/[^\d]/g, '') : '91' + String(o.client_phone).replace(/[^\d]/g, '')}`}
                          target="_blank" rel="noopener noreferrer" style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12 }}>
                          WhatsApp
                        </a>
                      )}
                      {o.status === 'new' && (
                        <>
                          <button onClick={() => setOrderStatus(o, 'confirmed')} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, borderColor: 'rgba(34,197,94,0.4)', color: '#16a34a' }}>
                            <Check size={13} /> Confirm
                          </button>
                          <button onClick={() => setOrderStatus(o, 'cancelled')} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, borderColor: 'rgba(239,68,68,0.4)', color: '#ef4444' }}>
                            <X size={13} /> Cancel
                          </button>
                        </>
                      )}
                      {o.status === 'confirmed' && (
                        <button onClick={() => setOrderStatus(o, 'fulfilled')} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, borderColor: 'rgba(59,130,246,0.4)', color: '#2563eb' }}>
                          <Check size={13} /> Fulfilled
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </>
      )}
    </div>
  )
}

// ═══════════════ HOURS TAB (availability) ═══════════════
function HoursTab({ site, reload }) {
  const [rules, setRules] = useState([])
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    const flat = Array.isArray(site.availability) ? site.availability : []
    // normalize to one row per weekday for the simple editor
    const byDay = {}
    flat.forEach((r) => { byDay[r.weekday] = { start_time: r.start_time, end_time: r.end_time } })
    setRules(WEEKDAYS.map((_, i) => byDay[i] ? { enabled: true, ...byDay[i] } : { enabled: false, start_time: '10:00', end_time: '18:00' }))
    setDirty(false)
  }, [site.id, site.updated_at]) // eslint-disable-line

  const set = (i, patch) => {
    setRules((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)))
    setDirty(true)
  }

  const save = async () => {
    const payload = rules
      .map((r, weekday) => (r.enabled ? { weekday, start_time: r.start_time, end_time: r.end_time } : null))
      .filter(Boolean)
    try {
      await setMyAvailability(site.id, payload)
      toast.success('Working hours saved')
      reload()
    } catch (e) {
      toast.error(errDetail(e, 'Could not save hours'))
    }
  }

  return (
    <div style={cardStyle}>
      <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6 }}>Weekly working hours</h3>
      <p style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>Clients can only book inside these windows. Uncheck a day to mark it closed.</p>
      {rules.map((r, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 14, padding: '10px 12px',
          borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap',
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, width: 120, fontSize: 14, fontWeight: 600, cursor: 'pointer', opacity: r.enabled ? 1 : 0.45 }}>
            <input type="checkbox" checked={r.enabled} onChange={(e) => set(i, { enabled: e.target.checked })} style={{ accentColor: '#4f46e5' }} />
            {WEEKDAYS[i].slice(0, 3)}
          </label>
          <input type="time" value={r.start_time} disabled={!r.enabled} onChange={(e) => set(i, { start_time: e.target.value })} style={{ ...inputStyle, width: 110 }} />
          <span style={{ color: '#94a3b8' }}>to</span>
          <input type="time" value={r.end_time} disabled={!r.enabled} onChange={(e) => set(i, { end_time: e.target.value })} style={{ ...inputStyle, width: 110 }} />
        </div>
      ))}
      <button onClick={save} disabled={!dirty} className="btn-primary" style={{ ...primaryBtn, marginTop: 18, opacity: dirty ? 1 : 0.5 }}>
        <Save size={15} /> Save working hours
      </button>
    </div>
  )
}

// ═══════════════ LEADS & CLIENTS TAB ═══════════════
const _th = { fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, color: '#94a3b8', textAlign: 'left', padding: '10px 14px', borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' }
const _td = { padding: '12px 14px', fontSize: 13.5, borderBottom: '1px solid #f1f5f9', verticalAlign: 'middle' }

function DataTable({ head, children }) {
  return (
    <div style={{ ...cardStyle, padding: 0, overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 640 }}>
        <thead><tr>{head.map((h, i) => <th key={i} style={_th}>{h}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}

function Modal({ title, onClose, children, wide }) {
  return (
    <>
      <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 90 }} onClick={onClose} />
      <div style={{
        position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 95,
        background: '#fff', borderRadius: 18, padding: 26, width: wide ? 'min(680px, calc(100vw - 32px))' : 'min(440px, calc(100vw - 32px))',
        maxHeight: 'calc(100vh - 60px)', overflowY: 'auto', boxShadow: '0 24px 70px rgba(15,23,42,0.28)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <h3 style={{ fontSize: 17, fontWeight: 800, margin: 0 }}>{title}</h3>
          <button onClick={onClose} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 30, height: 30, borderRadius: 8, border: 'none', background: '#f1f5f9', color: '#475569', cursor: 'pointer' }}>
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </>
  )
}

const waLink = (phone) => {
  const digits = (phone || '').replace(/[^\d]/g, '')
  if (digits.length === 10) return `https://wa.me/91${digits}`
  if (digits.length > 10) return `https://wa.me/${digits}`
  return null
}

const invoicePublicUrl = (inv) => `${window.location.origin}/invoice/${inv.token}`

// Lead source labels/colors (kundli, matching, newsletter, enquiry, callback…)
const LEAD_SOURCE_META = {
  kundli: { label: 'Free Kundli', bg: 'rgba(79,70,229,0.08)', fg: '#4f46e5' },
  kundli_basic: { label: 'Free Kundli', bg: 'rgba(79,70,229,0.08)', fg: '#4f46e5' },
  matching: { label: 'Match Making', bg: 'rgba(236,72,153,0.08)', fg: '#db2777' },
  dosha: { label: 'Dosha Report', bg: 'rgba(239,68,68,0.08)', fg: '#dc2626' },
  newsletter: { label: 'Newsletter', bg: 'rgba(14,165,233,0.1)', fg: '#0284c7' },
  enquiry: { label: 'Contact Form', bg: 'rgba(245,158,11,0.1)', fg: '#d97706' },
  callback: { label: 'Call Back', bg: 'rgba(34,197,94,0.1)', fg: '#16a34a' },
  horoscope: { label: 'Horoscope', bg: 'rgba(168,85,247,0.1)', fg: '#9333ea' },
}

function LeadsClientsTab({ site }) {
  const [view, setView] = useState('leads')            // leads | clients | invoices
  const [leads, setLeads] = useState(null)
  const [clients, setClients] = useState(null)
  const [invoices, setInvoices] = useState(null)
  const [clientForm, setClientForm] = useState(null)   // { id?, name, email, phone, notes }
  const [saving, setSaving] = useState(false)
  const [invoiceFor, setInvoiceFor] = useState(null)   // client → open composer

  const load = () => {
    getMyLeads(site.id).then(setLeads).catch(() => setLeads([]))
    getMyClients(site.id).then(setClients).catch(() => setClients([]))
    getMyInvoices(site.id).then(setInvoices).catch(() => setInvoices([]))
  }
  useEffect(() => { load() }, [site.id]) // eslint-disable-line

  const convert = async (l) => {
    try {
      await convertMyLead(site.id, l.id)
      toast.success(`${l.name || 'Lead'} added to your clients`)
      load()
    } catch (e) { toast.error(errDetail(e, 'Could not convert lead')) }
  }

  const saveClient = async (e) => {
    e?.preventDefault?.()
    if (!clientForm.name?.trim()) return toast.error('Name is required')
    setSaving(true)
    try {
      const data = { name: clientForm.name.trim(), email: clientForm.email?.trim() || null, phone: clientForm.phone?.trim() || null, notes: clientForm.notes?.trim() || null }
      if (clientForm.id) await updateMyClient(site.id, clientForm.id, data)
      else await createMyClient(site.id, data)
      toast.success(clientForm.id ? 'Client updated' : 'Client added')
      setClientForm(null); load()
    } catch (e2) { toast.error(errDetail(e2, 'Could not save client')) } finally { setSaving(false) }
  }

  const removeClient = async (c) => {
    if (!window.confirm(`Remove ${c.name} from clients? Their invoices stay on record.`)) return
    try { await deleteMyClient(site.id, c.id); toast.success('Client removed'); load() }
    catch (e) { toast.error(errDetail(e, 'Could not remove client')) }
  }

  const sendInvoice = async (inv) => {
    try {
      await sendMyInvoice(site.id, inv.id)
      toast.success(`Invoice ${inv.number} emailed to ${inv.client_name}`)
      load()
    } catch (e) { toast.error(errDetail(e, 'Could not send email')) }
  }

  const shareInvoice = async (inv) => {
    const url = invoicePublicUrl(inv)
    const msg = `Namaste 🙏 Here is your invoice ${inv.number} from ${site.name} — ${url}`
    const link = waLink(inv.client_phone)
    if (link) window.open(`${link}?text=${encodeURIComponent(msg)}`, '_blank')
    else {
      try { await navigator.clipboard.writeText(msg); toast.success('Invoice link copied — paste it in WhatsApp') }
      catch { toast.error('Could not copy the link') }
    }
  }

  const markPaid = async (inv) => {
    try { await setMyInvoiceStatus(site.id, inv.id, 'paid'); toast.success(`Invoice ${inv.number} marked paid`); load() }
    catch (e) { toast.error(errDetail(e, 'Could not update invoice')) }
  }

  const removeInvoice = async (inv) => {
    if (!window.confirm(`Delete invoice ${inv.number}? This cannot be undone.`)) return
    try { await deleteMyInvoice(site.id, inv.id); toast.success('Invoice deleted'); load() }
    catch (e) { toast.error(errDetail(e, 'Could not delete invoice')) }
  }

  const chip = (status) => {
    const s = { draft: ['rgba(148,163,184,0.15)', '#64748b'], sent: ['rgba(59,130,246,0.12)', '#2563eb'], paid: ['rgba(34,197,94,0.12)', '#16a34a'] }[status] || ['rgba(148,163,184,0.15)', '#64748b']
    return <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 12, background: s[0], color: s[1] }}>{status}</span>
  }

  const count = { leads: leads?.length ?? 0, clients: clients?.length ?? 0, invoices: invoices?.length ?? 0 }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 18 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {[['leads', 'Leads', Users], ['clients', 'Clients', UserPlus], ['invoices', 'Invoices', InvoiceIcon]].map(([v, l, Icon]) => (
            <button key={v} onClick={() => setView(v)} style={{
              ...ghostBtn, padding: '8px 18px', fontSize: 13.5,
              background: view === v ? 'rgba(79,70,229,0.08)' : 'transparent',
              borderColor: view === v ? '#4f46e5' : '#e2e8f0',
              color: view === v ? '#4f46e5' : '#0f172a',
            }}>
              <Icon size={14} /> {l} {count[v] > 0 && <span style={{ opacity: 0.6 }}>({count[v]})</span>}
            </button>
          ))}
        </div>
        {view === 'clients' && (
          <button onClick={() => setClientForm({ name: '', email: '', phone: '', notes: '' })} className="btn-primary" style={{ ...primaryBtn, padding: '9px 18px', fontSize: 13.5 }}>
            <UserPlus size={15} /> Add client
          </button>
        )}
        {view === 'invoices' && (
          <button
            onClick={() => (clients?.length ? setInvoiceFor(clients[0]) : toast.error('Add a client first'))}
            className="btn-primary" style={{ ...primaryBtn, padding: '9px 18px', fontSize: 13.5 }}>
            <InvoiceIcon size={15} /> New invoice
          </button>
        )}
      </div>

      {/* ── LEADS ── */}
      {view === 'leads' && (leads === null
        ? <DashboardLoader label="Loading leads" />
        : leads.length === 0
          ? <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 48 }}>
              <Users size={32} style={{ marginBottom: 12 }} />
              <div>No leads yet. Your free kundli tool collects contacts automatically — share your site link to grow your client list.</div>
            </div>
          : <DataTable head={['Name', 'Contact', 'Source', 'Birth details', 'Captured', '']}>
              {leads.map((l) => (
                <tr key={l.id}>
                  <td style={{ ..._td, fontWeight: 700 }}>{l.name || 'Anonymous'}</td>
                  <td style={_td}>
                    <div>{l.phone || '—'}</div>
                    {l.email && <div style={{ fontSize: 12, color: '#94a3b8' }}>{l.email}</div>}
                  </td>
                  <td style={_td}><span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12, background: LEAD_SOURCE_META[l.tool]?.bg || 'rgba(79,70,229,0.08)', color: LEAD_SOURCE_META[l.tool]?.fg || '#4f46e5' }}>{LEAD_SOURCE_META[l.tool]?.label || (l.tool || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}</span></td>
                  <td style={{ ..._td, color: '#64748b', fontSize: 12.5 }}>
                    {l.details?.date ? `${l.details.date} ${l.details.time || ''}` : typeof l.details === 'string' && l.details ? l.details.slice(0, 90) : '—'}{l.details?.place ? ` · ${l.details.place}` : ''}
                  </td>
                  <td style={{ ..._td, color: '#94a3b8', fontSize: 12.5, whiteSpace: 'nowrap' }}>{l.created_at ? new Date(l.created_at).toLocaleDateString() : '—'}</td>
                  <td style={{ ..._td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {l.client_id ? (
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#16a34a', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                        <Check size={14} /> Client
                      </span>
                    ) : (
                      <button onClick={() => convert(l)} style={{ ...ghostBtn, padding: '6px 14px', fontSize: 12.5, borderColor: 'rgba(34,197,94,0.45)', color: '#16a34a' }}>
                        <UserPlus size={13} /> Convert
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </DataTable>)}

      {/* ── CLIENTS ── */}
      {view === 'clients' && (clients === null
        ? <DashboardLoader label="Loading clients" />
        : clients.length === 0
          ? <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 48 }}>
              <UserPlus size={32} style={{ marginBottom: 12 }} />
              <div>No clients yet. Convert a lead above or add one manually — then invoice them in one click.</div>
            </div>
          : <DataTable head={['Name', 'Contact', 'Source', 'Added', '']}>
              {clients.map((c) => (
                <tr key={c.id}>
                  <td style={{ ..._td, fontWeight: 700 }}>{c.name}</td>
                  <td style={_td}>
                    <div>{c.phone || '—'}</div>
                    {c.email && <div style={{ fontSize: 12, color: '#94a3b8' }}>{c.email}</div>}
                  </td>
                  <td style={_td}>
                    <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12, background: c.source === 'lead' ? 'rgba(234,179,8,0.12)' : 'rgba(148,163,184,0.15)', color: c.source === 'lead' ? '#b45309' : '#64748b' }}>
                      {c.source === 'lead' ? 'Converted lead' : 'Manual'}
                    </span>
                  </td>
                  <td style={{ ..._td, color: '#94a3b8', fontSize: 12.5, whiteSpace: 'nowrap' }}>{c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}</td>
                  <td style={{ ..._td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                      <button onClick={() => setInvoiceFor(c)} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12 }}>
                        <InvoiceIcon size={13} /> Invoice
                      </button>
                      <button onClick={() => setClientForm(c)} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12 }}>
                        <Pencil size={13} />
                      </button>
                      <button onClick={() => removeClient(c)} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, borderColor: 'rgba(239,68,68,0.35)', color: '#ef4444' }}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </DataTable>)}

      {/* ── INVOICES ── */}
      {view === 'invoices' && (invoices === null
        ? <DashboardLoader label="Loading invoices" />
        : invoices.length === 0
          ? <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 48 }}>
              <InvoiceIcon size={32} style={{ marginBottom: 12 }} />
              <div>No invoices yet. Create one for a client — it gets a shareable link you can send by email or WhatsApp.</div>
            </div>
          : <DataTable head={['Invoice', 'Client', 'Amount', 'Status', 'Due', '']}>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td style={{ ..._td, fontWeight: 700, whiteSpace: 'nowrap' }}>{inv.number}</td>
                  <td style={_td}>{inv.client_name}</td>
                  <td style={{ ..._td, fontWeight: 800 }}>₹{inv.total}</td>
                  <td style={_td}>{chip(inv.status)}</td>
                  <td style={{ ..._td, color: '#64748b', fontSize: 12.5, whiteSpace: 'nowrap' }}>{inv.due_date ? new Date(inv.due_date).toLocaleDateString() : '—'}</td>
                  <td style={{ ..._td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                      <a href={invoicePublicUrl(inv)} target="_blank" rel="noopener noreferrer" style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, textDecoration: 'none' }}>
                        <ExternalLink size={13} />
                      </a>
                      <button onClick={() => sendInvoice(inv)} disabled={!inv.client_email} title={inv.client_email ? `Email to ${inv.client_email}` : 'No email on this client'} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, opacity: inv.client_email ? 1 : 0.4 }}>
                        <Mail size={13} />
                      </button>
                      <button onClick={() => shareInvoice(inv)} title="Send on WhatsApp" style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12 }}>
                        <MessageCircle size={13} />
                      </button>
                      {inv.status !== 'paid' && (
                        <button onClick={() => markPaid(inv)} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, borderColor: 'rgba(34,197,94,0.45)', color: '#16a34a' }}>
                          <Check size={13} /> Paid
                        </button>
                      )}
                      <button onClick={() => removeInvoice(inv)} style={{ ...ghostBtn, padding: '6px 12px', fontSize: 12, borderColor: 'rgba(239,68,68,0.35)', color: '#ef4444' }}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </DataTable>)}

      {/* ── add / edit client modal ── */}
      {clientForm && (
        <Modal title={clientForm.id ? 'Edit client' : 'Add client'} onClose={() => setClientForm(null)}>
          <form onSubmit={saveClient} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div><label style={labelStyle}>Name *</label>
              <input value={clientForm.name || ''} onChange={(e) => setClientForm((f) => ({ ...f, name: e.target.value }))} placeholder="Full name" style={inputStyle} autoFocus /></div>
            <div><label style={labelStyle}>Email (for invoices)</label>
              <input type="email" value={clientForm.email || ''} onChange={(e) => setClientForm((f) => ({ ...f, email: e.target.value }))} placeholder="you@example.com" style={inputStyle} /></div>
            <div><label style={labelStyle}>Phone (WhatsApp)</label>
              <input value={clientForm.phone || ''} onChange={(e) => setClientForm((f) => ({ ...f, phone: e.target.value }))} placeholder="+91 98xxxxxxx" style={inputStyle} /></div>
            <div><label style={labelStyle}>Notes</label>
              <textarea value={clientForm.notes || ''} onChange={(e) => setClientForm((f) => ({ ...f, notes: e.target.value }))} placeholder="Birth details, preferences…" rows={3} style={{ ...inputStyle, resize: 'vertical' }} /></div>
            <button type="submit" disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
              {saving ? 'Saving…' : clientForm.id ? 'Save changes' : 'Add client'}
            </button>
          </form>
        </Modal>
      )}

      {/* ── invoice composer ── */}
      {invoiceFor && (
        <InvoiceComposer
          site={site}
          clients={clients || []}
          initialClientId={invoiceFor.id}
          onClose={() => setInvoiceFor(null)}
          onCreated={() => { setInvoiceFor(null); setView('invoices'); load() }}
        />
      )}
    </div>
  )
}

// Invoice composer: pick client, line items, tax, due date → creates a draft invoice
function InvoiceComposer({ site, clients, initialClientId, onClose, onCreated }) {
  const [clientId, setClientId] = useState(initialClientId || clients[0]?.id)
  const [items, setItems] = useState([{ name: '', qty: 1, price: 0 }])
  const [taxRate, setTaxRate] = useState(0)
  const [dueDate, setDueDate] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)

  const setItem = (i, k, v) => setItems((arr) => arr.map((it, j) => (j === i ? { ...it, [k]: k === 'name' ? v : k === 'price' ? v : Math.max(1, Number(v) || 1) } : it)))
  const subtotal = items.reduce((s, it) => s + (Number(it.price) || 0) * (Number(it.qty) || 1), 0)
  const tax = Math.round(subtotal * (Number(taxRate) || 0) / 100)

  const create = async () => {
    const clean = items.filter((it) => it.name?.trim())
    if (!clientId) return toast.error('Pick a client')
    if (!clean.length) return toast.error('Add at least one item')
    setSaving(true)
    try {
      await createMyInvoice(site.id, {
        client_id: clientId, items: clean, tax_rate: Number(taxRate) || 0,
        due_date: dueDate || null, notes: notes.trim() || null,
      })
      toast.success('Invoice created — send it by email or WhatsApp')
      onCreated()
    } catch (e) { toast.error(errDetail(e, 'Could not create invoice')) } finally { setSaving(false) }
  }

  return (
    <Modal title="New invoice" onClose={onClose} wide>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
          <div><label style={labelStyle}>Client *</label>
            <select value={clientId || ''} onChange={(e) => setClientId(Number(e.target.value))} style={inputStyle}>
              {clients.map((c) => <option key={c.id} value={c.id}>{c.name}{c.email ? ` — ${c.email}` : ''}</option>)}
            </select></div>
          <div><label style={labelStyle}>Due date</label>
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} style={inputStyle} /></div>
        </div>

        <div>
          <label style={labelStyle}>Items *</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 90px 110px 34px', gap: 8, fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
              <span>Description</span><span>Qty</span><span>Price (₹)</span><span />
            </div>
            {items.map((it, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 90px 110px 34px', gap: 8, alignItems: 'center' }}>
                <input value={it.name} onChange={(e) => setItem(i, 'name', e.target.value)} placeholder="e.g. Consultation — 1 hour" style={inputStyle} />
                <input type="number" min="1" value={it.qty} onChange={(e) => setItem(i, 'qty', e.target.value)} style={inputStyle} />
                <input type="number" min="0" value={it.price} onChange={(e) => setItem(i, 'price', e.target.value)} style={inputStyle} />
                <button type="button" onClick={() => setItems((arr) => (arr.length > 1 ? arr.filter((_, j) => j !== i) : arr))}
                  style={{ ...ghostBtn, padding: '8px 0', justifyContent: 'center', color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}>
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
            <button type="button" onClick={() => setItems((arr) => [...arr, { name: '', qty: 1, price: 0 }])} style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12.5, alignSelf: 'flex-start' }}>
              <Plus size={13} /> Add item
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 12 }}>
          <div><label style={labelStyle}>Tax %</label>
            <input type="number" min="0" max="50" value={taxRate} onChange={(e) => setTaxRate(e.target.value)} style={inputStyle} /></div>
          <div><label style={labelStyle}>Notes (shown on invoice)</label>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. Payment via UPI on consultation day" style={inputStyle} /></div>
        </div>

        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: '12px 16px', display: 'flex', justifyContent: 'flex-end', gap: 24, fontSize: 14, flexWrap: 'wrap' }}>
          <span style={{ color: '#64748b' }}>Subtotal <b style={{ color: '#0f172a' }}>₹{subtotal}</b></span>
          <span style={{ color: '#64748b' }}>Tax <b style={{ color: '#0f172a' }}>₹{tax}</b></span>
          <span style={{ color: '#64748b' }}>Total <b style={{ color: '#0f172a', fontSize: 16 }}>₹{subtotal + tax}</b></span>
        </div>

        <button onClick={create} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          {saving ? 'Creating…' : 'Create invoice'}
        </button>
      </div>
    </Modal>
  )
}

// ═══════════════ BOOKINGS TAB ═══════════════
function BookingsTab({ site }) {
  const [bookings, setBookings] = useState(null)
  const [filter, setFilter] = useState('')

  const load = () => getMyBookings(site.id).then(setBookings).catch(() => setBookings([]))
  useEffect(() => { load() }, [site.id]) // eslint-disable-line

  const setStatus = async (b, status) => {
    try {
      await updateMyBooking(site.id, b.id, { status })
      load()
    } catch { toast.error('Could not update booking') }
  }

  const today = new Date().toISOString().slice(0, 10)
  const visible = (bookings || []).filter((b) => !filter || b.status === filter)

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {[['', 'All'], ['confirmed', 'Upcoming'], ['completed', 'Completed'], ['cancelled', 'Cancelled'], ['no_show', 'No-show']].map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)} style={{
            ...ghostBtn, padding: '7px 16px', fontSize: 13,
            background: filter === v ? 'rgba(79,70,229,0.1)' : 'transparent',
            borderColor: filter === v ? '#4f46e5' : '#e2e8f0',
            color: filter === v ? '#4f46e5' : '#0f172a',
          }}>{l}</button>
        ))}
      </div>

      {bookings === null ? (
        <DashboardLoader label="Loading bookings" />
      ) : visible.length === 0 ? (
        <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 48 }}>
          <Calendar size={32} style={{ marginBottom: 12 }} />
          <div>No bookings yet. Share your site link on WhatsApp and Instagram to get your first booking!</div>
        </div>
      ) : (
        <div style={{ ...cardStyle, padding: 0, overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5, minWidth: 720 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
                {['Client', 'Date & time', 'Service', 'Amount', 'Status', ''].map((h) => (
                  <th key={h} style={{ textAlign: 'left', padding: '11px 14px', fontSize: 11.5, fontWeight: 800, color: '#64748b', letterSpacing: 0.4 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((b) => (
                <tr key={b.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '11px 14px' }}>
                    <div style={{ fontWeight: 700 }}>{b.client_name}</div>
                    {b.client_phone && <div style={{ fontSize: 11.5, color: '#94a3b8' }}>{b.client_phone}</div>}
                  </td>
                  <td style={{ padding: '11px 14px', whiteSpace: 'nowrap' }}>{b.date} · {b.start_time}–{b.end_time}</td>
                  <td style={{ padding: '11px 14px' }}>{b.service_name || 'Consultation'}</td>
                  <td style={{ padding: '11px 14px', fontWeight: 700 }}>{b.amount ? `₹${b.amount}` : '—'}</td>
                  <td style={{ padding: '11px 14px' }}>
                    <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12,
                      background: b.status === 'confirmed' ? 'rgba(34,197,94,0.12)' : b.status === 'completed' ? 'rgba(59,130,246,0.12)' : 'rgba(239,68,68,0.12)',
                      color: b.status === 'confirmed' ? '#16a34a' : b.status === 'completed' ? '#2563eb' : '#ef4444' }}>{b.status.replace('_', ' ')}</span>
                  </td>
                  <td style={{ padding: '11px 14px', whiteSpace: 'nowrap' }}>
                    {b.client_phone && (
                      <a href={`https://wa.me/${String(b.client_phone).replace(/[^\d]/g, '').length >= 10 ? String(b.client_phone).replace(/[^\d]/g, '') : '91' + String(b.client_phone).replace(/[^\d]/g, '')}?text=${encodeURIComponent(`Namaste ${b.client_name}, confirming your consultation on ${b.date} at ${b.start_time}. — ${site.name}`)}`}
                        target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, fontWeight: 700, color: '#16a34a', textDecoration: 'none', marginRight: 10 }}>WhatsApp</a>
                    )}
                    {b.status === 'confirmed' && (
                      <>
                        <button onClick={() => setStatus(b, 'completed')} style={{ fontSize: 12, fontWeight: 700, border: '1px solid #e2e8f0', background: '#fff', borderRadius: 8, padding: '5px 10px', cursor: 'pointer', marginRight: 6 }}>Complete</button>
                        <button onClick={() => setStatus(b, 'cancelled')} style={{ fontSize: 12, fontWeight: 700, border: '1px solid rgba(239,68,68,0.3)', background: '#fff', borderRadius: 8, padding: '5px 10px', cursor: 'pointer', color: '#dc2626' }}>Cancel</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ═══════════════ DOMAIN TAB ═══════════════
// One DNS record row with a copy button — values are the Vercel records the
// main frontend is hosted on (A 76.76.21.21 for the apex, CNAME
// cname.vercel-dns.com for www / subdomains).

// Second-level suffixes: yourname.co.in has three labels but is an apex.
const _SECOND_LEVEL_SUFFIXES = new Set([
  'co.in', 'net.in', 'org.in', 'firm.in', 'gen.in', 'ind.in', 'ac.in', 'edu.in',
  'res.in', 'gov.in', 'mil.in', 'co.uk', 'org.uk', 'ac.uk', 'gov.uk', 'com.au',
  'net.au', 'org.au', 'co.nz', 'co.za', 'com.br', 'com.mx', 'co.jp', 'or.jp', 'ne.jp',
])
const isSubdomain = (d) => {
  const parts = (d || '').toLowerCase().split('.').filter(Boolean)
  if (parts.length < 3) return false
  if (parts.length === 3 && _SECOND_LEVEL_SUFFIXES.has(parts.slice(-2).join('.'))) return false
  return true
}

function DnsRow({ label, cells }) {
  const copyAll = () => {
    const text = cells.map(([k, v]) => `${k}: ${v}`).join('\n')
    navigator.clipboard?.writeText(text).then(() => toast.success('Record copied'))
  }
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
      background: 'rgba(255,255,255,0.65)', border: '1px solid rgba(245,158,11,0.35)',
      borderRadius: 10, padding: '10px 12px',
    }}>
      <span style={{ fontSize: 12, fontWeight: 800, color: '#92400e', minWidth: 110 }}>{label}</span>
      {cells.map(([k, v]) => (
        <span key={k} style={{ fontSize: 12.5 }}>
          <span style={{ color: '#92400e', fontWeight: 600 }}>{k}: </span>
          <code style={{ color: '#1e293b', background: 'rgba(245,158,11,0.1)', padding: '2px 7px', borderRadius: 6 }}>{v}</code>
        </span>
      ))}
      <button type="button" onClick={copyAll} title="Copy record"
        style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: 4, background: 'none', border: '1px solid rgba(245,158,11,0.45)', color: '#92400e', borderRadius: 8, padding: '4px 9px', fontSize: 11.5, fontWeight: 700, cursor: 'pointer' }}>
        <Copy size={12} /> Copy
      </button>
    </div>
  )
}

function DomainTab({ site, reload }) {
  const [domain, setDomain] = useState(site.custom_domain || '')
  const [busy, setBusy] = useState(false)
  const [verifyResult, setVerifyResult] = useState(null)
  const [domainCheck, setDomainCheck] = useState(null)

  // live availability check (debounced)
  useEffect(() => {
    if (site.custom_domain) return
    const d = domain.trim().toLowerCase()
    if (!d || !d.includes('.')) { setDomainCheck(null); return }
    const timer = setTimeout(() => {
      checkDomainAvailability(d)
        .then((res) => setDomainCheck(res))
        .catch(() => setDomainCheck(null))
    }, 400)
    return () => clearTimeout(timer)
  }, [domain, site.custom_domain])

  const connect = async () => {
    if (!domain.trim()) return toast.error('Enter your domain')
    setBusy(true)
    try {
      await setMySiteDomain(site.id, domain)
      toast.success('Domain saved — add the DNS records below, then verify')
      setVerifyResult(null)
      reload()
    } catch (e) {
      toast.error(errDetail(e, 'Could not connect domain'))
    } finally { setBusy(false) }
  }

  const verify = async () => {
    setBusy(true)
    try {
      const res = await verifyMySiteDomain(site.id)
      setVerifyResult(res)
      if (res?.verified) toast.success('Domain verified and live!')
      else toast.error(res?.message || 'DNS not ready yet')
      reload()
    } catch (e) {
      toast.error(errDetail(e, 'Verification failed'))
    } finally { setBusy(false) }
  }

  const disconnect = async () => {
    setBusy(true)
    try {
      await removeMySiteDomain(site.id)
      setDomain('')
      setVerifyResult(null)
      toast.success('Domain disconnected')
      reload()
    } catch { toast.error('Could not disconnect') }
    finally { setBusy(false) }
  }

  const active = site.domain_status === 'active'

  return (
    <div>
      <div style={cardStyle}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6 }}>Your own domain</h3>
        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 20, lineHeight: 1.6 }}>
          Use your own domain — <strong>yourname.com</strong>, a subdomain like <strong>astro.yourname.com</strong>, anything you own — instead of the free address. Free SSL (the 🔒 padlock) is included automatically.
        </p>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
          <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="yourname.com or astro.yourname.com"
            disabled={active} style={{ ...inputStyle, flex: 1, minWidth: 220 }} />
          {!site.custom_domain ? (
            <button onClick={connect} disabled={busy} className="btn-primary" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}>
              <Globe2 size={15} /> {busy ? 'Working…' : 'Connect'}
            </button>
          ) : active ? (
            <button onClick={disconnect} disabled={busy} style={{ ...ghostBtn, color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}>
              Disconnect
            </button>
          ) : (
            <button onClick={verify} disabled={busy} className="btn-primary" style={{ ...primaryBtn, opacity: busy ? 0.6 : 1 }}>
              Verify DNS
            </button>
          )}
        </div>

        {/* live availability feedback */}
        {!site.custom_domain && domainCheck && domain.includes('.') && (
          <div style={{ minHeight: 24, marginBottom: 10, fontSize: 14 }}>
            {domainCheck.valid && domainCheck.available ? (
              <span style={{ color: '#059669', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Check size={15} /> <strong>{domain}</strong> is available to connect
              </span>
            ) : (
              <span style={{ color: '#dc2626', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <X size={15} /> {domainCheck.reason || 'That domain cannot be connected'}
              </span>
            )}
          </div>
        )}

        {site.custom_domain && !active && (
          <div style={{
            background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
            borderRadius: 12, padding: '16px 18px', fontSize: 13, color: '#d97706', lineHeight: 1.8,
          }}>
            {isSubdomain(site.custom_domain) ? (
              <>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>
                  DNS setup — add this record at your domain provider (GoDaddy, Namecheap, BigRock…)
                </div>
                <p style={{ margin: '0 0 10px', color: '#b45309' }}>
                  Open your DNS settings and add the CNAME below so <strong>{site.custom_domain}</strong> points to your site:
                </p>
                <div style={{ display: 'grid', gap: 8 }}>
                  <DnsRow label="CNAME (subdomain)" cells={[['Type', 'CNAME'], ['Name / Host', site.custom_domain], ['Value', 'cname.vercel-dns.com']]} />
                </div>
                <p style={{ margin: '10px 0 0', color: '#b45309' }}>
                  Some providers show the host as just <code style={{ color: '#1e293b' }}>{site.custom_domain.split('.')[0]}</code> — that's the same record. Delete any other A/CNAME records for <code style={{ color: '#1e293b' }}>{site.custom_domain}</code> so they don't conflict.
                </p>
              </>
            ) : (
              <>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>
                  DNS setup — add these records at your domain provider (GoDaddy, Namecheap, BigRock…)
                </div>
                <p style={{ margin: '0 0 10px', color: '#b45309' }}>
                  Open your domain's DNS settings and add the two records below so <strong>{site.custom_domain}</strong> and <strong>www.{site.custom_domain}</strong> both point to your site:
                </p>
                <div style={{ display: 'grid', gap: 8 }}>
                  <DnsRow label="A record (apex)" cells={[['Type', 'A'], ['Name / Host', '@'], ['Value', '76.76.21.21']]} />
                  <DnsRow label="CNAME (www)" cells={[['Type', 'CNAME'], ['Name / Host', 'www'], ['Value', 'cname.vercel-dns.com']]} />
                </div>
                <p style={{ margin: '10px 0 0', color: '#b45309' }}>
                  Some providers ask for a full host name — use <code style={{ color: '#1e293b' }}>www.{site.custom_domain}</code> instead of <code style={{ color: '#1e293b' }}>www</code>. Delete any other A/CNAME records for <code style={{ color: '#1e293b' }}>@</code> or <code style={{ color: '#1e293b' }}>www</code> so they don't conflict.
                </p>
              </>
            )}
            <p style={{ margin: '8px 0 0', color: '#b45309' }}>
              Save, then tap <strong>Verify DNS</strong> — DNS changes can take 5 minutes to a few hours to propagate.
            </p>
            {verifyResult && !verifyResult.verified && (
              <div style={{ marginTop: 10, color: '#dc2626' }}>{verifyResult.message}</div>
            )}
          </div>
        )}

        {active && (
          <div style={{
            background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)',
            borderRadius: 12, padding: '14px 18px', fontSize: 14, color: '#16a34a', fontWeight: 600,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <Check size={16} /> {site.custom_domain} is connected and live with SSL.
          </div>
        )}
      </div>
    </div>
  )
}

// ═══════════════ SOCIAL TAB (content automation + queue + one-tap sharing) ═══════════════
const SOCIAL_PLATFORMS = [
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'facebook', label: 'Facebook' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'x', label: 'X / Twitter' },
  { id: 'telegram', label: 'Telegram' },
  { id: 'linkedin', label: 'LinkedIn' },
]

function SocialTab({ site, reload }) {
  const [posts, setPosts] = useState(null)
  const [content, setContent] = useState('')
  const [topic, setTopic] = useState('')
  const [platforms, setPlatforms] = useState(['whatsapp', 'facebook'])
  const [scheduleAt, setScheduleAt] = useState('')
  const [autoDaily, setAutoDaily] = useState(site.settings?.socialAutoDaily || false)
  const [busy, setBusy] = useState('')
  const siteUrl = tenantSiteUrl(site.slug)
  const [media, setMedia] = useState({})

  const makeMedia = async (key, content, format) => {
    setMedia((m) => ({ ...m, [key]: 'loading' }))
    try {
      const url = await socialPostMedia(site.id, content, format)
      setMedia((m) => ({ ...m, [key]: url }))
    } catch { setMedia((m) => ({ ...m, [key]: 'error' })); toast.error('Could not render media') }
  }

  const MediaPreview = ({ k, name }) => {
    const u = media[k]
    if (!u || u === 'loading' || u === 'error') return null
    const dl = u.startsWith('data:video') ? `post-${name}.mp4` : `post-${name}.png`
    return (
      <div style={{ marginTop: 10 }}>
        {u.startsWith('data:video')
          ? <video src={u} controls style={{ width: '100%', maxWidth: 300, borderRadius: 12 }} />
          : <img src={u} alt="post media" style={{ width: '100%', maxWidth: 300, borderRadius: 12 }} />}
        <a href={u} download={dl} style={{ display: 'inline-block', marginTop: 6, fontSize: 12.5, fontWeight: 700, color: '#4f46e5', textDecoration: 'none' }}>
          ⬇ Download {u.startsWith('data:video') ? 'video' : 'image'}
        </a>
      </div>
    )
  }

  const load = (ensure) => {
    getMySocial(site.id, ensure ? 1 : 0).then(setPosts).catch(() => setPosts([]))
  }
  useEffect(() => { load(true) }, [site.id]) // eslint-disable-line

  const doGenerate = async (kind) => {
    setBusy(kind)
    try {
      const res = await generateSocialPost(site.id, kind, topic)
      setContent(res.content)
      toast.success('Post drafted — edit it if you like, then schedule or share')
    } catch (e) { toast.error(errDetail(e, 'Could not generate a post')) }
    finally { setBusy('') }
  }

  const addToQueue = async (status) => {
    if (!content.trim()) return toast.error('Generate or write a post first')
    if (status === 'scheduled' && !scheduleAt) return toast.error('Pick a date & time to schedule')
    setBusy('save')
    try {
      await createSocialPost(site.id, { content, platforms: platforms.join(','), scheduled_at: scheduleAt || undefined, status })
      setContent(''); setTopic(''); setScheduleAt('')
      toast.success(status === 'scheduled' ? 'Added to your queue' : 'Saved as draft')
      load()
    } catch (e) { toast.error(errDetail(e, 'Could not save the post')) }
    finally { setBusy('') }
  }

  const toggleAuto = async () => {
    const next = !autoDaily
    setAutoDaily(next)
    try {
      await setMySiteSettings(site.id, { social_auto_daily: next })
      toast.success(next ? 'Daily post will be auto-drafted every morning' : 'Auto-daily turned off')
      reload()
    } catch { setAutoDaily(!next); toast.error('Could not update setting') }
  }

  const shareLinks = (post) => {
    const enc = encodeURIComponent(post.content)
    return {
      whatsapp: `https://wa.me/?text=${enc}`,
      telegram: `https://t.me/share/url?url=${encodeURIComponent(siteUrl)}&text=${enc}`,
      x: `https://twitter.com/intent/tweet?text=${enc}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(siteUrl)}&quote=${enc.slice(0, 300)}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(siteUrl)}`,
      instagram: null,
    }
  }

  const markPosted = async (post) => {
    try {
      await updateSocialPost(site.id, post.id, { content: post.content, status: 'posted' })
      toast.success('Marked as posted')
      load()
    } catch { toast.error('Could not update') }
  }

  const removePost = async (post) => {
    try {
      await deleteSocialPost(site.id, post.id)
      load()
    } catch { toast.error('Could not delete') }
  }

  const statusChip = (s) => ({
    draft: { bg: 'rgba(148,163,184,0.15)', color: '#64748b' },
    scheduled: { bg: 'rgba(59,130,246,0.12)', color: '#2563eb' },
    posted: { bg: 'rgba(34,197,94,0.12)', color: '#16a34a' },
    cancelled: { bg: 'rgba(239,68,68,0.12)', color: '#dc2626' },
  }[s] || { bg: '#eee', color: '#666' })

  return (
    <div>
      {/* automation setting */}
      <div style={{ ...cardStyle, marginBottom: 20, borderColor: 'rgba(79,70,229,0.3)' }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Share2 size={17} color="#4f46e5" /> Social media automation
        </h3>
        <p style={{ fontSize: 13.5, color: '#64748b', marginBottom: 12, lineHeight: 1.6 }}>
          Ready-to-post updates generated from your live panchang and the festival calendar — daily panchang posts,
          festival greetings and consultation promos. Share them anywhere in one tap.
        </p>
        <label style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
          <input type="checkbox" checked={autoDaily} onChange={toggleAuto} style={{ accentColor: '#4f46e5', width: 16, height: 16 }} />
          Auto-create today's panchang post every morning (queued for 9:00 AM)
        </label>
      </div>

      {/* composer */}
      <div style={{ ...cardStyle, marginBottom: 20 }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 12 }}>Compose a post</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
          {[['daily', '📅 Daily panchang'], ['festival', '🪔 Festival greeting'], ['promo', '📣 Consultation promo']].map(([kind, label]) => (
            <button key={kind} onClick={() => doGenerate(kind)} disabled={!!busy}
              style={{ ...ghostBtn, padding: '9px 14px', fontSize: 13, opacity: busy ? 0.6 : 1 }}>
              {busy === kind ? <Loader2 size={14} className="spin" /> : label}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Custom topic (e.g. benefits of Rudraksha)" style={inputStyle} />
          <button onClick={() => doGenerate('custom')} disabled={!!busy || !topic.trim()} style={{ ...primaryBtn, padding: '10px 16px', fontSize: 13, opacity: busy || !topic.trim() ? 0.6 : 1, whiteSpace: 'nowrap' }}>
            {busy === 'custom' ? <Loader2 size={14} className="spin" /> : 'Draft'}
          </button>
        </div>
        <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={8}
          placeholder="Your post will appear here — edit freely before scheduling."
          style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6 }} />
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', margin: '12px 0' }}>
          {SOCIAL_PLATFORMS.map((p) => (
            <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, fontWeight: 600, cursor: 'pointer', color: '#475569' }}>
              <input type="checkbox" checked={platforms.includes(p.id)}
                onChange={(e) => setPlatforms((cur) => e.target.checked ? [...cur, p.id] : cur.filter((x) => x !== p.id))}
                style={{ accentColor: '#4f46e5' }} />
              {p.label}
            </label>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <input type="datetime-local" value={scheduleAt} onChange={(e) => setScheduleAt(e.target.value)} style={{ ...inputStyle, maxWidth: 230 }} />
          <button onClick={() => addToQueue('scheduled')} disabled={busy === 'save'} className="btn-primary" style={{ ...primaryBtn, opacity: busy === 'save' ? 0.6 : 1 }}>
            <CalendarIcon size={15} /> Schedule
          </button>
          <button onClick={() => addToQueue('draft')} disabled={busy === 'save'} style={{ ...ghostBtn, opacity: busy === 'save' ? 0.6 : 1 }}>
            Save as draft
          </button>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          <button onClick={() => makeMedia('composer-i', content, 'image')} disabled={!content.trim()} style={{ ...ghostBtn, padding: '8px 12px', fontSize: 12.5, opacity: !content.trim() ? 0.5 : 1 }}>🖼 Generate image card</button>
          <button onClick={() => makeMedia('composer-v', content, 'video')} disabled={!content.trim()} style={{ ...ghostBtn, padding: '8px 12px', fontSize: 12.5, opacity: !content.trim() ? 0.5 : 1 }}>🎬 Generate video</button>
        </div>
        {content.trim() && <><MediaPreview k="composer-i" name="draft-i" /><MediaPreview k="composer-v" name="draft-v" /></>}
      </div>

      {/* queue */}
      <h3 style={{ fontSize: 17, fontWeight: 700, margin: '24px 0 12px' }}>
        Content queue {posts ? `(${posts.length})` : ''}
      </h3>
      {posts === null ? (
        <DashboardLoader label="Loading posts" size={44} />
      ) : posts.length === 0 ? (
        <div style={{ ...cardStyle, color: '#64748b', textAlign: 'center', padding: 32 }}>
          No posts yet — generate one above or turn on auto-daily.
        </div>
      ) : (
        posts.map((post) => {
          const chip = statusChip(post.status)
          const links = shareLinks(post)
          return (
            <div key={post.id} style={{ ...cardStyle, marginBottom: 12, padding: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, fontWeight: 800, padding: '3px 10px', borderRadius: 12, background: chip.bg, color: chip.color }}>{post.status}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 12, background: '#f1f5f9', color: '#475569' }}>{post.kind}</span>
                  {post.scheduled_at && <span style={{ fontSize: 12, color: '#64748b', display: 'inline-flex', alignItems: 'center', gap: 4 }}><ClockIcon size={12} /> {String(post.scheduled_at).replace('T', ' ')}</span>}
                </div>
                <button onClick={() => removePost(post)} title="Delete" style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: 4 }}>
                  <Trash2 size={15} />
                </button>
              </div>
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 13.5, lineHeight: 1.65, color: '#334155', marginBottom: 12 }}>{post.content}</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                {SOCIAL_PLATFORMS.filter((p) => links[p.id]).map((p) => (
                  <a key={p.id} href={links[p.id]} target="_blank" rel="noopener noreferrer"
                    onClick={() => { if (post.status !== 'posted') markPosted(post) }}
                    style={{ fontSize: 12, fontWeight: 700, padding: '6px 10px', borderRadius: 8, border: '1px solid #e2e8f0', color: '#475569', textDecoration: 'none' }}>
                    {p.label}
                  </a>
                ))}
                <button onClick={() => { navigator.clipboard.writeText(post.content); toast.success('Copied — paste it in the app, then it is marked posted') }}
                  style={{ fontSize: 12, fontWeight: 700, padding: '6px 10px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#fff', color: '#475569', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                  <Copy size={12} /> Copy {post.platforms?.includes('instagram') ? '(Instagram)' : ''}
                </button>
                {post.status !== 'posted' && (
                  <button onClick={() => markPosted(post)} style={{ fontSize: 12, fontWeight: 700, padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(34,197,94,0.4)', background: 'rgba(34,197,94,0.08)', color: '#16a34a', cursor: 'pointer' }}>
                    Mark posted
                  </button>
                )}
                <button onClick={() => makeMedia('p' + post.id + 'i', post.content, 'image')} style={{ fontSize: 12, fontWeight: 700, padding: '6px 10px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#fff', color: '#475569', cursor: 'pointer' }}>🖼 Image</button>
                <button onClick={() => makeMedia('p' + post.id + 'v', post.content, 'video')} style={{ fontSize: 12, fontWeight: 700, padding: '6px 10px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#fff', color: '#475569', cursor: 'pointer' }}>🎬 Video</button>
              </div>
              <MediaPreview k={'p' + post.id + 'i'} name={post.id + '-i'} />
              <MediaPreview k={'p' + post.id + 'v'} name={post.id + '-v'} />
            </div>
          )
        })
      )}
    </div>
  )
}

// ═══════════════ SETTINGS TAB (alerts, social, contact, plan, danger zone) ═══════════════
function SettingsTab({ site, reload }) {
  const [wa, setWa] = useState(site.settings?.whatsappNumber || '')
  const [aiDialog, setAiDialog] = useState(false) // tagline writer
  const [alertsOn, setAlertsOn] = useState(site.settings?.bookingAlerts !== false)
  const [reminderHours, setReminderHours] = useState(site.settings?.reminderHours || 24)
  const [social, setSocial] = useState({
    instagram: site.settings?.instagram || '',
    youtube: site.settings?.youtube || '',
    facebook: site.settings?.facebook || '',
    twitter: site.settings?.twitter || '',
    linkedin: site.settings?.linkedin || '',
    telegram: site.settings?.telegram || '',
    websiteUrl: site.settings?.websiteUrl || '',
  })
  const [contact, setContact] = useState({
    email: site.settings?.email || '',
    phone: site.settings?.phone || '',
    city: site.settings?.city || '',
  })
  const [showTestimonials, setShowTestimonials] = useState(site.settings?.showTestimonials !== false)
  const [payMode, setPayMode] = useState(site.settings?.paymentsMode || 'later')
  const [upiId, setUpiId] = useState(site.settings?.upiId || '')
  const [razorpayKeyId, setRazorpayKeyId] = useState(site.settings?.razorpayKeyId || '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setWa(site.settings?.whatsappNumber || '')
    setAlertsOn(site.settings?.bookingAlerts !== false)
    setReminderHours(site.settings?.reminderHours || 24)
    setSocial({
      instagram: site.settings?.instagram || '',
      youtube: site.settings?.youtube || '',
      facebook: site.settings?.facebook || '',
      twitter: site.settings?.twitter || '',
      linkedin: site.settings?.linkedin || '',
      telegram: site.settings?.telegram || '',
      websiteUrl: site.settings?.websiteUrl || '',
    })
    setContact({
      email: site.settings?.email || '',
      phone: site.settings?.phone || '',
      city: site.settings?.city || '',
    })
    setShowTestimonials(site.settings?.showTestimonials !== false)
    setPayMode(site.settings?.paymentsMode || 'later')
    setUpiId(site.settings?.upiId || '')
    setRazorpayKeyId(site.settings?.razorpayKeyId || '')
  }, [site.id, site.updated_at]) // eslint-disable-line

  const savePayments = async () => {
    setSaving(true)
    try {
      await setMySiteSettings(site.id, { payments_mode: payMode, upi_id: upiId, razorpay_key_id: razorpayKeyId })
      toast.success('Payment settings saved')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not save payment settings')) }
    finally { setSaving(false) }
  }

  const saveAlerts = async () => {
    setSaving(true)
    try {
      await setMySiteSettings(site.id, { whatsapp_number: wa, booking_alerts: alertsOn, reminder_hours: reminderHours })
      toast.success('Alerts settings saved')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not save settings')) }
    finally { setSaving(false) }
  }

  const saveSocial = async () => {
    setSaving(true)
    try {
      await setMySiteSettings(site.id, {
        instagram: social.instagram, youtube: social.youtube, facebook: social.facebook,
        twitter: social.twitter, linkedin: social.linkedin, telegram: social.telegram,
        website_url: social.websiteUrl,
        contact_email: contact.email, contact_phone: contact.phone, city: contact.city,
        show_testimonials: showTestimonials,
      })
      toast.success('Links saved — they now appear on your site')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not save links')) }
    finally { setSaving(false) }
  }

  const socialFields = [
    ['instagram', 'Instagram URL or @handle'],
    ['youtube', 'YouTube channel URL'],
    ['facebook', 'Facebook page URL'],
    ['twitter', 'Twitter / X URL'],
    ['linkedin', 'LinkedIn URL'],
    ['telegram', 'Telegram URL'],
    ['websiteUrl', 'Any other website link'],
  ]

  return (
    <div>
      {/* WhatsApp alerts */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bell size={17} color="#4f46e5" /> WhatsApp alerts
        </h3>
        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 18, lineHeight: 1.6 }}>
          You and your clients get alerts on WhatsApp — booking confirmations and reminders before each appointment.
        </p>
        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>Your WhatsApp number (with country code)</label>
          <input value={wa} onChange={(e) => setWa(e.target.value)} placeholder="+91 98765 43210" style={inputStyle} />
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginBottom: 18 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
            <input type="checkbox" checked={alertsOn} onChange={(e) => setAlertsOn(e.target.checked)} style={{ accentColor: '#4f46e5' }} />
            Booking confirmations & reminders
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600 }}>
            Remind client
            <select value={reminderHours} onChange={(e) => setReminderHours(+e.target.value)} style={{ ...inputStyle, width: 'auto', padding: '6px 10px' }}>
              <option value={1}>1 hour</option>
              <option value={3}>3 hours</option>
              <option value={24}>1 day</option>
              <option value={48}>2 days</option>
            </select>
            before
          </label>
        </div>
        <button onClick={saveAlerts} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save alerts settings'}
        </button>
      </div>

      {/* Social links + contact */}
      <div style={{ ...cardStyle, marginTop: 20 }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Link2 size={17} color="#4f46e5" /> Social media & contact
        </h3>
        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 18, lineHeight: 1.6 }}>
          These links appear in your website's header, footer and contact section.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14, marginBottom: 20 }}>
          {socialFields.map(([key, ph]) => (
            <div key={key}>
              <label style={labelStyle}>{ph}</label>
              <input value={social[key]} onChange={(e) => setSocial((s) => ({ ...s, [key]: e.target.value }))}
                placeholder="https://…" style={inputStyle} />
            </div>
          ))}
          <div>
            <label style={labelStyle}>Contact email (shown to visitors)</label>
            <input value={contact.email} onChange={(e) => setContact((c) => ({ ...c, email: e.target.value }))} placeholder="pandit@example.com" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Contact phone (shown to visitors)</label>
            <input value={contact.phone} onChange={(e) => setContact((c) => ({ ...c, phone: e.target.value }))} placeholder="+91 98765 43210" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>City (good for local SEO)</label>
            <input value={contact.city} onChange={(e) => setContact((c) => ({ ...c, city: e.target.value }))} placeholder="Jaipur, Rajasthan" style={inputStyle} />
          </div>
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer', marginBottom: 18 }}>
          <input type="checkbox" checked={showTestimonials} onChange={(e) => setShowTestimonials(e.target.checked)} style={{ accentColor: '#4f46e5' }} />
          Show testimonials section on my website
        </label>
        <button onClick={saveSocial} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save links & contact'}
        </button>
      </div>

      {/* Payments */}
      <div style={{ ...cardStyle, marginTop: 20 }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <IndianRupee size={17} color="#16a340" /> Payments for bookings
        </h3>
        <p style={{ fontSize: 13.5, color: '#64748b', marginBottom: 16, lineHeight: 1.6 }}>
          Choose how clients pay when they book. Visitor details are always captured first, so you never lose a lead.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 10, marginBottom: 14 }}>
          {[
            { id: 'later', title: 'Pay later', desc: 'No online payment. Confirm bookings personally on WhatsApp.' },
            { id: 'upi', title: 'UPI (GPay, PhonePe, Paytm)', desc: 'Clients get a one-tap UPI link for the consultation amount.' },
            { id: 'razorpay', title: 'Razorpay', desc: 'Cards, UPI, netbanking via Razorpay Checkout on your site.' },
          ].map((opt) => (
            <button key={opt.id} type="button" onClick={() => setPayMode(opt.id)} style={{
              textAlign: 'left', padding: '12px 14px', borderRadius: 12, cursor: 'pointer',
              border: `2px solid ${payMode === opt.id ? '#4f46e5' : '#e2e8f0'}`,
              background: payMode === opt.id ? 'rgba(79,70,229,0.05)' : '#fff',
            }}>
              <div style={{ fontWeight: 800, fontSize: 13.5, marginBottom: 3 }}>{opt.title}</div>
              <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>{opt.desc}</div>
            </button>
          ))}
        </div>
        {payMode === 'upi' && (
          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Your UPI ID</label>
            <input value={upiId} onChange={(e) => setUpiId(e.target.value)} placeholder="yourname@bank (e.g. okhdfc, ybl, paytm)" style={inputStyle} />
          </div>
        )}
        {payMode === 'razorpay' && (
          <div style={{ marginBottom: 14 }}>
            <label style={labelStyle}>Razorpay Key ID</label>
            <input value={razorpayKeyId} onChange={(e) => setRazorpayKeyId(e.target.value)} placeholder="rzp_live_xxxxxxxx (from your Razorpay dashboard)" style={inputStyle} />
          </div>
        )}
        <button onClick={savePayments} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save payment settings'}
        </button>
      </div>

      {/* Plan / membership */}
      <div style={{ ...cardStyle, marginTop: 20, borderColor: 'rgba(79,70,229,0.3)' }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Crown size={17} color="#d97706" /> Plan & membership
        </h3>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginTop: 12 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800 }}>Free <span style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8' }}>plan</span></div>
            <div style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
              Website · booking · free kundli tool · store · 1 custom domain
            </div>
          </div>
          <button className="btn-primary" style={{ ...primaryBtn, opacity: 0.85 }} onClick={() => toast('Pro plan with payments, ecommerce & social posting is coming soon!', { icon: '🚀' })}>
            Upgrade to Pro
          </button>
        </div>
      </div>

      {/* Site identity */}
      <div style={{ ...cardStyle, marginTop: 20 }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 18 }}>Site identity</h3>
        <div style={{ marginBottom: 18 }}>
          <label style={labelStyle}>Site name</label>
          <input defaultValue={site.name} onBlur={(e) => updateMySite(site.id, { name: e.target.value }).then(reload).catch(() => {})} style={inputStyle} />
        </div>
        <div style={{ marginBottom: 18 }}>
          <label style={labelStyle}>Tagline
            <button type="button" onClick={() => setAiDialog(true)} style={{ marginLeft: 8, padding: '3px 10px', borderRadius: 7, fontSize: 11.5, fontWeight: 700, cursor: 'pointer', border: '1px solid rgba(79,70,229,0.35)', color: '#4f46e5', background: 'rgba(79,70,229,0.06)' }}>
              ✨ Write with AI
            </button>
          </label>
          <input defaultValue={site.tagline} onBlur={(e) => updateMySite(site.id, { tagline: e.target.value }).then(reload).catch(() => {})} style={inputStyle} />
        </div>
        <button onClick={() => {
          if (window.confirm('Delete your website permanently? All bookings, orders and content will be lost.')) {
            deleteMySite(site.id).then(() => { toast.success('Site deleted'); window.location.reload() }).catch(() => toast.error('Could not delete'))
          }
        }} style={{ ...ghostBtn, color: '#dc2626', borderColor: 'rgba(220,38,38,0.3)' }}>
          <Trash2 size={15} /> Delete website
        </button>
      </div>

      {aiDialog && (
        <AiWriterDialog
          site={site}
          field="tagline"
          onClose={() => setAiDialog(false)}
          onApply={(text) => {
            setAiDialog(false)
            updateMySite(site.id, { tagline: text }).then(reload).catch(() => toast.error('Could not save'))
          }}
        />
      )}
    </div>
  )
}

// ═══════════════ MAIN PAGE (sidebar dashboard) ═══════════════
const TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'content', label: 'Content', icon: FileText },
  { id: 'design', label: 'Design', icon: Palette },
  { id: 'services', label: 'Services', icon: Star },
  { id: 'store', label: 'Store', icon: Store },
  { id: 'hours', label: 'Hours', icon: Clock },
  { id: 'bookings', label: 'Bookings', icon: Calendar },
  { id: 'leads', label: 'Leads & Clients', icon: Users },
  { id: 'social', label: 'Social', icon: Share2 },
  { id: 'domain', label: 'Domain', icon: Globe2 },
  { id: 'settings', label: 'Settings', icon: Settings2 },
]

// Developer tools (formerly the /dashboard page) + account, grouped in the same sidebar.
const DEV_TABS = [
  { id: 'keys', label: 'API Keys', icon: Key },
  { id: 'ai', label: 'AI Providers', icon: Bot },
  { id: 'reports', label: 'Reports', icon: ScrollText },
  { id: 'kundali', label: 'Kundali Report', icon: Zap },
  { id: 'usage', label: 'Usage', icon: BarChart3 },
]

const ACCOUNT_TABS = [
  { id: 'account', label: 'Account', icon: User },
]

export default function MySite() {
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth()
  const [sites, setSites] = useState(null)
  const [site, setSite] = useState(null)
  const { tab: tabParam } = useParams()
  const VALID_TABS = [...TABS, ...DEV_TABS, ...ACCOUNT_TABS].map((t) => t.id)
  const tab = VALID_TABS.includes(tabParam) ? tabParam : 'overview'
  const navigate = useNavigate()
  const goToTab = (t) => navigate(`/mysite/${t}`)
  const [pubBusy, setPubBusy] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('av-sidebar-collapsed') === '1')
  const [avatarOpen, setAvatarOpen] = useState(false)
  const [keys, setKeys] = useState([])
  const [displayUser, setDisplayUser] = useState(null)
  const avatarRef = useRef(null)
  
  useEffect(() => { setDisplayUser(user) }, [user])

  useEffect(() => {
    if (isAuthenticated) {
      getKeys().then((data) => setKeys(Array.isArray(data) ? data : data.keys || [])).catch(() => {})
    }
  }, [isAuthenticated])

  const refreshKeys = () => {
    getKeys().then((data) => setKeys(Array.isArray(data) ? data : data.keys || [])).catch(() => {})
  }

  useEffect(() => {
    if (!avatarOpen) return
    const close = (e) => { if (avatarRef.current && !avatarRef.current.contains(e.target)) setAvatarOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [avatarOpen])

  useEffect(() => {
    if (!isAuthenticated) return
    getMySites().then((list) => {
      setSites(list)
      // list rows lack pages/services/availability — fetch the full bundle
      if (list && list.length > 0) {
        getMySite(list[0].id).then(setSite).catch(() => setSite(list[0]))
      }
    }).catch(() => setSites([]))
  }, [isAuthenticated])

  useEffect(() => {
    if (tabParam !== tab) navigate(`/mysite/${tab}`, { replace: true })
  }, [tabParam, tab, navigate])

  // No website yet → first-run onboarding (wizard lives at /onboarding)
  useEffect(() => {
    if (sites !== null && sites.length === 0) navigate('/onboarding', { replace: true })
  }, [sites, navigate])

  const reload = () => {
    if (!site) return
    getMySite(site.id).then((s) => { setSite(s); setSites((prev) => (prev || []).map((x) => (x.id === s.id ? s : x))) }).catch(() => {})
  }

  const togglePublish = async () => {
    setPubBusy(true)
    try {
      if (site.status === 'published') {
        await unpublishMySite(site.id)
        toast.success('Site is now private (draft)')
      } else {
        await publishMySite(site.id)
        toast.success('🎉 Your website is live!')
      }
      reload()
    } catch { toast.error('Could not update — try again') }
    finally { setPubBusy(false) }
  }

  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <DashboardLoader label="Loading your dashboard" size={84} />
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 20 }}>
        <Shield size={48} color="#94a3b8" />
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Sign in to manage your website</h2>
        <p style={{ color: '#475569', fontSize: 15, maxWidth: 380, textAlign: 'center' }}>
          Create and manage your astrology business website — bookings, services, domain and more.
        </p>
        <div style={{ display: 'flex', gap: 12 }}>
          <Link to="/login" className="btn-primary" style={{ padding: '14px 32px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <LogIn size={18} /> Sign In
          </Link>
          <Link to="/register" className="btn-secondary" style={{ padding: '14px 32px', fontSize: 16, display: 'flex', alignItems: 'center' }}>
            Create free account
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9' }}>
      {/* fixed dashboard top bar */}
      <header style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: 60, zIndex: 60,
        background: 'rgba(255,255,255,0.94)', backdropFilter: 'blur(10px)', borderBottom: '1px solid #e2e8f0',
        display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px',
      }}>
        {site && (
          <>
            <button className="mysite-collapse-btn" onClick={() => { setSidebarCollapsed((c) => { localStorage.setItem('av-sidebar-collapsed', c ? '0' : '1'); return !c }) }}
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, borderRadius: 9, border: 'none', background: 'transparent', color: '#475569', cursor: 'pointer' }}>
              <PanelLeft size={18} />
            </button>
            <button className="mysite-mobile-nav-btn" onClick={() => setMobileNavOpen(true)}
              style={{ display: 'none', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, borderRadius: 9, border: '1px solid #e2e8f0', background: '#fff', color: '#0f172a', cursor: 'pointer' }}>
              <Menu size={19} />
            </button>
          </>
        )}
        {site ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, flex: 1 }}>
            <span style={{ fontSize: 14.5, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{site.name}</span>
            <span style={{
              fontSize: 10, fontWeight: 800, padding: '2px 9px', borderRadius: 12, flexShrink: 0,
              background: site.status === 'published' ? 'rgba(34,197,94,0.12)' : 'rgba(245,158,11,0.12)',
              color: site.status === 'published' ? '#16a34a' : '#d97706',
            }}>{site.status === 'published' ? 'LIVE' : 'DRAFT'}</span>
            <span className="mysite-domain" style={{ color: '#94a3b8', fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {site.custom_domain && site.domain_status === 'active' ? site.custom_domain : `${site.slug}.astrovakta.com`}
            </span>
          </div>
        ) : (
          <span style={{ fontSize: 14, fontWeight: 600, color: '#64748b', flex: 1 }}>Website builder</span>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {site && site.status === 'published' && (
            <a className="mysite-view-site" href={tenantSiteUrl(site.slug)} target="_blank" rel="noopener noreferrer"
              style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: '#475569', textDecoration: 'none', padding: '7px 12px', borderRadius: 9, border: '1px solid #e2e8f0', background: '#fff' }}>
              <ExternalLink size={14} /> <span className="mysite-btn-label">View site</span>
            </a>
          )}
          {site && (
            <button onClick={togglePublish} disabled={pubBusy}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', background: 'var(--gradient-primary)', color: '#fff', border: 'none', borderRadius: 9, fontWeight: 600, fontSize: 13, cursor: pubBusy ? 'wait' : 'pointer', opacity: pubBusy ? 0.6 : 1 }}>
              {site.status === 'published' ? <EyeOff size={14} /> : <Sparkles size={14} />}
              <span className="mysite-btn-label">{site.status === 'published' ? 'Unpublish' : 'Publish site'}</span>
            </button>
          )}
          {/* profile avatar + menu */}
          <div ref={avatarRef} style={{ position: 'relative' }}>
            <button onClick={() => setAvatarOpen((o) => !o)} title={user?.name || user?.email}
              style={{ width: 36, height: 36, borderRadius: '50%', border: '2px solid #e2e8f0', background: 'var(--gradient-primary)', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', textTransform: 'uppercase' }}>
              {(user?.name || user?.email || '?').trim().charAt(0)}
            </button>
            <AnimatePresence>
              {avatarOpen && (
                <motion.div initial={{ opacity: 0, y: -6, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: 0.98 }} transition={{ duration: 0.14 }}
                  style={{ position: 'absolute', right: 0, top: 46, width: 232, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 14, boxShadow: '0 16px 40px rgba(15,23,42,0.14)', padding: 8, zIndex: 70 }}>
                  <div style={{ padding: '9px 11px', borderBottom: '1px solid #f1f5f9', marginBottom: 5 }}>
                    <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 2 }}>{user?.name || 'Astrologer'}</div>
                    <div style={{ fontSize: 12, color: '#64748b', wordBreak: 'break-all' }}>{user?.email}</div>
                  </div>
                  <button onClick={() => { setAvatarOpen(false); navigate('/') }}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '9px 11px', borderRadius: 9, border: 'none', background: 'transparent', color: '#334155', fontSize: 13.5, fontWeight: 500, cursor: 'pointer', textAlign: 'left' }}>
                    <Home size={15} /> Back to home
                  </button>
                  <button onClick={() => { setAvatarOpen(false); logout(); navigate('/') }}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '9px 11px', borderRadius: 9, border: 'none', background: 'transparent', color: '#dc2626', fontSize: 13.5, fontWeight: 600, cursor: 'pointer', textAlign: 'left' }}>
                    <LogOut size={15} /> Log Out
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      <div style={{ display: 'flex', paddingTop: 60, minHeight: '100vh', alignItems: 'stretch' }}>
        {/* fixed collapsible sidebar (desktop) */}
        {site && (
          <aside className="mysite-sidebar" style={{
            position: 'fixed', top: 60, bottom: 0, left: 0, zIndex: 40,
            width: sidebarCollapsed ? 66 : 216, background: '#fff', borderRight: '1px solid #e2e8f0',
            padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 3,
            transition: 'width 0.2s ease', overflowX: 'hidden', overflowY: 'auto',
          }}>
            {TABS.map((t) => (
              <button key={t.id} onClick={() => goToTab(t.id)} title={sidebarCollapsed ? t.label : undefined}
                className={tab === t.id ? 'mysite-tab-active' : ''}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: sidebarCollapsed ? 'center' : 'flex-start', gap: 11,
                  padding: '10px 12px', borderRadius: 10, fontSize: 13.5, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                  background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                  color: tab === t.id ? '#4f46e5' : '#475569',
                  border: 'none', textAlign: 'left', transition: 'all 0.15s', flexShrink: 0, whiteSpace: 'nowrap',
                }}>
                <t.icon size={17} style={{ flexShrink: 0 }} />
                {!sidebarCollapsed && t.label}
              </button>
            ))}
            <div style={{ height: 1, background: '#f1f5f9', margin: '10px 2px', flexShrink: 0 }} />
            {!sidebarCollapsed && (
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 1.2, color: '#94a3b8', padding: '2px 12px 6px', flexShrink: 0 }}>DEVELOPER</div>
            )}
            {DEV_TABS.map((t) => (
              <button key={t.id} onClick={() => goToTab(t.id)} title={sidebarCollapsed ? t.label : undefined}
                className={tab === t.id ? 'mysite-tab-active' : ''}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: sidebarCollapsed ? 'center' : 'flex-start', gap: 11,
                  padding: '10px 12px', borderRadius: 10, fontSize: 13.5, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                  background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                  color: tab === t.id ? '#4f46e5' : '#475569',
                  border: 'none', textAlign: 'left', transition: 'all 0.15s', flexShrink: 0, whiteSpace: 'nowrap',
                }}>
                <t.icon size={17} style={{ flexShrink: 0 }} />
                {!sidebarCollapsed && t.label}
              </button>
            ))}
            <div style={{ height: 1, background: '#f1f5f9', margin: '10px 2px', flexShrink: 0 }} />
            {!sidebarCollapsed && (
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 1.2, color: '#94a3b8', padding: '2px 12px 6px', flexShrink: 0 }}>ACCOUNT</div>
            )}
            {ACCOUNT_TABS.map((t) => (
              <button key={t.id} onClick={() => goToTab(t.id)} title={sidebarCollapsed ? t.label : undefined}
                className={tab === t.id ? 'mysite-tab-active' : ''}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: sidebarCollapsed ? 'center' : 'flex-start', gap: 11,
                  padding: '10px 12px', borderRadius: 10, fontSize: 13.5, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                  background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                  color: tab === t.id ? '#4f46e5' : '#475569',
                  border: 'none', textAlign: 'left', transition: 'all 0.15s', flexShrink: 0, whiteSpace: 'nowrap',
                }}>
                <t.icon size={17} style={{ flexShrink: 0 }} />
                {!sidebarCollapsed && t.label}
              </button>
            ))}
            {user?.is_admin && (
              <button onClick={() => navigate('/admin')} title={sidebarCollapsed ? 'Admin Panel' : undefined}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: sidebarCollapsed ? 'center' : 'flex-start', gap: 11,
                  marginTop: 8, padding: '10px 12px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer',
                  border: '1px solid rgba(245,158,11,0.35)', background: 'rgba(245,158,11,0.08)', color: '#d97706',
                  textAlign: 'left', whiteSpace: 'nowrap', flexShrink: 0,
                }}>
                <Shield size={16} style={{ flexShrink: 0 }} />
                {!sidebarCollapsed && 'Admin Panel'}
              </button>
            )}
            {!sidebarCollapsed && (
              <div style={{ marginTop: 'auto', padding: '12px 8px 4px' }}>
                <div style={{ fontSize: 11.5, color: '#94a3b8', lineHeight: 1.6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  Signed in as<br />
                  <span style={{ color: '#475569', fontWeight: 600 }}>{user?.email}</span>
                </div>
              </div>
            )}
          </aside>
        )}

        {/* mobile drawer */}
        {site && (
          <AnimatePresence>
            {mobileNavOpen && (
              <>
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.18 }}
                  onClick={() => setMobileNavOpen(false)}
                  style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.45)', zIndex: 75 }} />
                <motion.aside initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }} transition={{ type: 'tween', duration: 0.22 }}
                  style={{ position: 'fixed', top: 0, bottom: 0, left: 0, width: 258, background: '#fff', zIndex: 80, padding: '14px 12px', display: 'flex', flexDirection: 'column', gap: 3, borderRadius: '0 18px 18px 0', overflowY: 'auto' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '2px 6px 12px', borderBottom: '1px solid #f1f5f9', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                      <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Sparkles size={14} color="#fff" />
                      </div>
                      <span style={{ fontSize: 15, fontWeight: 800, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 170 }}>{site.name}</span>
                    </div>
                    <button onClick={() => setMobileNavOpen(false)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: 8, border: 'none', background: '#f1f5f9', color: '#475569', cursor: 'pointer' }}>
                      <X size={17} />
                    </button>
                  </div>
                  {TABS.map((t) => (
                    <button key={t.id} onClick={() => { goToTab(t.id); setMobileNavOpen(false) }}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 11, padding: '11px 12px', borderRadius: 10,
                        fontSize: 14, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                        background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                        color: tab === t.id ? '#4f46e5' : '#475569', border: 'none', textAlign: 'left',
                      }}>
                      <t.icon size={17} /> {t.label}
                    </button>
                  ))}
                  <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 1.2, color: '#94a3b8', padding: '12px 12px 4px' }}>DEVELOPER</div>
                  {DEV_TABS.map((t) => (
                    <button key={t.id} onClick={() => { goToTab(t.id); setMobileNavOpen(false) }}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 11, padding: '11px 12px', borderRadius: 10,
                        fontSize: 14, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                        background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                        color: tab === t.id ? '#4f46e5' : '#475569', border: 'none', textAlign: 'left',
                      }}>
                      <t.icon size={17} /> {t.label}
                    </button>
                  ))}
                  <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 1.2, color: '#94a3b8', padding: '12px 12px 4px' }}>ACCOUNT</div>
                  {ACCOUNT_TABS.map((t) => (
                    <button key={t.id} onClick={() => { goToTab(t.id); setMobileNavOpen(false) }}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 11, padding: '11px 12px', borderRadius: 10,
                        fontSize: 14, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                        background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                        color: tab === t.id ? '#4f46e5' : '#475569', border: 'none', textAlign: 'left',
                      }}>
                      <t.icon size={17} /> {t.label}
                    </button>
                  ))}
                  {user?.is_admin && (
                    <button onClick={() => { setMobileNavOpen(false); navigate('/admin') }}
                      style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '11px 12px', borderRadius: 10, border: '1px solid rgba(245,158,11,0.35)', background: 'rgba(245,158,11,0.08)', color: '#d97706', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginTop: 8 }}>
                      <Shield size={16} /> Admin Panel
                    </button>
                  )}
                  <div style={{ marginTop: 'auto', padding: '14px 8px 6px', borderTop: '1px solid #f1f5f9' }}>
                    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>
                      Signed in as<br /><span style={{ color: '#475569', fontWeight: 600, wordBreak: 'break-all' }}>{user?.email}</span>
                    </div>
                    <button onClick={() => { setMobileNavOpen(false); logout(); navigate('/') }}
                      style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '10px 12px', borderRadius: 10, border: '1px solid #fecaca', background: '#fef2f2', color: '#dc2626', fontSize: 13.5, fontWeight: 600, cursor: 'pointer' }}>
                      <LogOut size={15} /> Log Out
                    </button>
                  </div>
                </motion.aside>
              </>
            )}
          </AnimatePresence>
        )}

        {/* main panel */}
        <main className="mysite-main" style={{
          flex: 1, minWidth: 0, padding: '26px 26px 90px',
          marginLeft: site ? (sidebarCollapsed ? 66 : 216) : 0, transition: 'margin-left 0.2s ease',
        }}>
          {site === null ? (
            <DashboardLoader label="Loading your site" size={72} full />
          ) : (
            <div key={tab} className="mysite-tab-fade">
              {tab === 'overview' && <OverviewTab site={site} reload={reload} />}
              {tab === 'content' && <ContentTab site={site} reload={reload} />}
              {tab === 'design' && <DesignTab site={site} reload={reload} />}
              {tab === 'services' && <ServicesTab site={site} reload={reload} />}
              {tab === 'store' && <StoreTab site={site} reload={reload} />}
              {tab === 'hours' && <HoursTab site={site} reload={reload} />}
              {tab === 'bookings' && <BookingsTab site={site} />}
              {tab === 'leads' && <LeadsClientsTab site={site} />}
              {tab === 'social' && <SocialTab site={site} reload={reload} />}
              {tab === 'domain' && <DomainTab site={site} reload={reload} />}
              {tab === 'settings' && <SettingsTab site={site} reload={reload} />}
              {tab === 'keys' && <APIKeys keys={keys} onRefresh={refreshKeys} />}
              {tab === 'ai' && <AIProvidersTab />}
              {tab === 'reports' && <ReportsTab />}
              {tab === 'kundali' && <KundaliReport />}
              {tab === 'usage' && <UsagePanel keys={keys} />}
              {tab === 'account' && <Profile user={displayUser || user} onUserUpdate={setDisplayUser} />}
            </div>
          )}
        </main>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .mysite-sidebar { display: none !important; }
          .mysite-collapse-btn { display: none !important; }
          .mysite-mobile-nav-btn { display: flex !important; }
          .mysite-domain { display: none !important; }
          .mysite-main { margin-left: 0 !important; padding: 18px 14px 90px !important; }
        }
        @media (max-width: 640px) {
          .mysite-btn-label { display: none !important; }
          .mysite-view-site { padding: 7px 9px !important; }
        }
        .mysite-tab-active:hover { background: rgba(79,70,229,0.12) !important; }
        .mysite-tab-fade { animation: mysiteTabIn 0.18s ease; }
        @keyframes mysiteTabIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
      `}</style>
    </div>
  )
}
