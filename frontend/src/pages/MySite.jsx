import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe, Plus, Trash2, ExternalLink, Check, X, Palette, FileText, Calendar,
  Store, Globe2, Eye, EyeOff, Sparkles, Clock, ChevronLeft, Settings2,
  Save, LogIn, Shield, ArrowRight, Image as ImageIcon, Users,
  Bell, Crown, Loader2, LayoutDashboard, Package, ShoppingBag, Link2,
  Phone, Star, TrendingUp, IndianRupee, Menu,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth.jsx'
import { tenantSiteUrl } from '../lib/tenant.js'
import {
  getMySites, createMySite, getMySite, updateMySite, publishMySite, unpublishMySite,
  deleteMySite, saveMySitePage, setMySiteDomain, verifyMySiteDomain, removeMySiteDomain,
  createMyService, updateMyService, deleteMyService,
  getMyAvailability, setMyAvailability, getMyBookings, updateMyBooking,
  checkSlugAvailability, checkDomainAvailability, setMySiteMedia, setMySiteSettings, getMyLeads,
  getMySiteStats, getMyProducts, createMyProduct, updateMyProduct, deleteMyProduct,
  getMyOrders, updateMyOrder,
} from '../lib/api.js'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const inputStyle = {
  width: '100%', padding: '10px 14px', background: '#fff',
  border: '1px solid #e2e8f0', borderRadius: 10, color: '#0f172a',
  fontSize: 14, outline: 'none',
}
const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 6 }
const cardStyle = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 16, padding: 24 }
const primaryBtn = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', background: 'var(--gradient-primary)', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 600, fontSize: 14, cursor: 'pointer' }
const ghostBtn = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', background: 'transparent', color: '#0f172a', border: '1px solid #e2e8f0', borderRadius: 10, fontWeight: 600, fontSize: 14, cursor: 'pointer' }

// Sites endpoints currently return raw FastAPI bodies ({"detail": ...} on
// errors). ResponseWrapMiddleware exists in app/middleware.py but is not
// registered; if it ever gets enabled, 4xx detail lands inside data instead.
// Accept both shapes.
const errDetail = (e, fallback = 'Something went wrong — try again') => {
  const d = e?.response?.data
  const msg = d?.data?.detail || d?.detail || d?.message
  return typeof msg === 'string' ? msg : fallback
}

const TEMPLATES = [
  { id: 'aurora', name: 'Aurora', desc: 'Indigo & amber — clean, light, modern', colors: ['#4f46e5', '#d97706'], tier: 'Free' },
  { id: 'classic', name: 'Classic', desc: 'Traditional warm tones on a deep theme', colors: ['#b45309', '#dc2626'], tier: 'Free' },
  { id: 'minimal', name: 'Minimal', desc: 'Fresh teal — calm and clutter-free', colors: ['#0f766e', '#0ea5e9'], tier: 'Free' },
  { id: 'devotional', name: 'Devotional', desc: 'Saffron & marigold — temple-inspired', colors: ['#ea580c', '#facc15'], tier: 'Free' },
  { id: 'celestial', name: 'Celestial', desc: 'Indigo night sky, stars & elegant serif', colors: ['#4338ca', '#f472b6'], tier: 'Premium' },
  { id: 'royal', name: 'Royal Heritage', desc: 'Deep maroon & gold — regal and luxurious', colors: ['#7c2d12', '#eab308'], tier: 'Premium' },
  { id: 'tantra', name: 'Tantra', desc: 'Crimson & ember — bold, mystical', colors: ['#be123c', '#f97316'], tier: 'Premium' },
  { id: 'modern-light', name: 'Modern Studio', desc: 'Blue & violet on white — sleek agency look', colors: ['#2563eb', '#8b5cf6'], tier: 'Premium' },
]

const PRESETS = {
  aurora: { primaryColor: '#4f46e5', accentColor: '#d97706', bgStyle: 'light' },
  classic: { primaryColor: '#b45309', accentColor: '#dc2626', bgStyle: 'dark' },
  minimal: { primaryColor: '#0f766e', accentColor: '#0ea5e9', bgStyle: 'light' },
  devotional: { primaryColor: '#ea580c', accentColor: '#facc15', bgStyle: 'light' },
  celestial: { primaryColor: '#4338ca', accentColor: '#f472b6', bgStyle: 'dark', fontHeading: "'Cormorant Garamond', Georgia, serif", heroPattern: 'stars' },
  royal: { primaryColor: '#7c2d12', accentColor: '#eab308', bgStyle: 'dark', fontHeading: "'Playfair Display', Georgia, serif", heroPattern: 'mandala' },
  tantra: { primaryColor: '#be123c', accentColor: '#f97316', bgStyle: 'dark', heroPattern: 'yantra' },
  'modern-light': { primaryColor: '#2563eb', accentColor: '#8b5cf6', bgStyle: 'light', heroPattern: 'grid' },
}

// ═══════════════ IMAGE UPLOAD HELPER ═══════════════
// Client-side resize keeps the data URL well under the 500 KB backend cap
// (works identically on SQLite dev and Supabase production — no file storage).
function fileToDataUrl(file, maxDim = 1400, quality = 0.85) {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) return reject(new Error('Please choose an image file'))
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Could not read the file'))
    reader.onload = () => {
      const img = new window.Image()
      img.onerror = () => reject(new Error('Could not read the image'))
      img.onload = () => {
        const scale = Math.min(1, maxDim / Math.max(img.width, img.height))
        const canvas = document.createElement('canvas')
        canvas.width = Math.round(img.width * scale)
        canvas.height = Math.round(img.height * scale)
        canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
        // SVG has no lossy encoding — keep the original data URL if small
        if (file.type === 'image/svg+xml' && file.size < 200 * 1024) return resolve(reader.result)
        resolve(canvas.toDataURL('image/jpeg', quality))
      }
      img.src = reader.result
    }
    reader.readAsDataURL(file)
  })
}

// ═══════════════ CREATE SITE WIZARD ═══════════════
function CreateSiteWizard({ onCreated }) {
  const [step, setStep] = useState(1)
  const [slug, setSlug] = useState('')
  const [name, setName] = useState('')
  const [tagline, setTagline] = useState('')
  const [template, setTemplate] = useState('aurora')
  const [logoUrl, setLogoUrl] = useState(null)
  const [heroImage, setHeroImage] = useState(null)
  const [creating, setCreating] = useState(false)
  const slugClean = slug.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')

  // live availability check (debounced)
  const [slugCheck, setSlugCheck] = useState({ state: 'idle', suggestion: null, reason: null })
  const checkTimer = useRef(null)
  useEffect(() => {
    if (checkTimer.current) clearTimeout(checkTimer.current)
    if (!slugClean || slugClean.length < 3) { setSlugCheck({ state: 'idle', suggestion: null, reason: null }); return }
    setSlugCheck({ state: 'checking', suggestion: null, reason: null })
    checkTimer.current = setTimeout(() => {
      checkSlugAvailability(slugClean)
        .then((res) => setSlugCheck({ state: res.available ? 'available' : 'taken', suggestion: res.suggestion, reason: res.reason }))
        .catch(() => setSlugCheck({ state: 'idle', suggestion: null, reason: null }))
    }, 400)
    return () => clearTimeout(checkTimer.current)
  }, [slugClean])

  const pickLogo = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    try { setLogoUrl(await fileToDataUrl(f, 512, 0.9)) } catch (err) { toast.error(err.message) }
  }
  const pickHero = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    try { setHeroImage(await fileToDataUrl(f, 1600, 0.85)) } catch (err) { toast.error(err.message) }
  }

  const submit = async () => {
    setCreating(true)
    try {
      const site = await createMySite({ slug: slugClean, name: name || undefined, tagline: tagline || undefined, template })
      if (logoUrl || heroImage) {
        try { await setMySiteMedia(site.id, { logo_url: logoUrl || null, hero_image: heroImage || null }) } catch { /* non-fatal */ }
      }
      toast.success('Your website is created!')
      onCreated(site)
    } catch (e) {
      toast.error(errDetail(e, 'Could not create site'))
    } finally {
      setCreating(false)
    }
  }

  const slugOk = slugClean.length >= 3 && slugCheck.state === 'available'
  const stepTitles = ['Your web address', 'About you', 'Pick a design']

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      {/* progress header */}
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, justifyContent: 'center' }}>
          {[1, 2, 3].map((s) => (
            <div key={s} style={{
              flex: 1, maxWidth: 90, height: 5, borderRadius: 4,
              background: step >= s ? 'var(--gradient-primary)' : 'rgba(79,70,229,0.15)',
            }} />
          ))}
        </div>
        <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>Step {step} of 3 · {stepTitles[step - 1]}</div>
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="s1" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.25 }}
            style={{ ...cardStyle, padding: 32 }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8 }}>Choose your web address</h2>
            <p style={{ color: '#475569', fontSize: 14, marginBottom: 28, lineHeight: 1.6 }}>
              This becomes your free website address. You can connect your own domain (like astrovakra.com) anytime after.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 10 }}>
              <input value={slugClean} onChange={(e) => setSlug(e.target.value)} placeholder="pandit-rajesh" autoFocus
                style={{ ...inputStyle, borderTopRightRadius: 0, borderBottomRightRadius: 0, fontSize: 15, padding: '13px 14px' }} />
              <div style={{
                padding: '13px 14px', background: 'rgba(79,70,229,0.06)', border: '1px solid #e2e8f0',
                borderLeft: 'none', borderTopRightRadius: 10, borderBottomRightRadius: 10,
                color: '#4f46e5', fontSize: 14, fontWeight: 700, whiteSpace: 'nowrap',
              }}>.astrovakta.com</div>
            </div>
            <div style={{ minHeight: 28, marginBottom: 12, fontSize: 14 }}>
              {slugCheck.state === 'checking' && (
                <span style={{ color: '#64748b', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <Loader2 size={14} className="spin" /> Checking availability…
                </span>
              )}
              {slugCheck.state === 'available' && slugClean.length >= 3 && (
                <span style={{ color: '#059669', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <Check size={15} /> <strong>{slugClean}.astrovakta.com</strong> is available!
                </span>
              )}
              {slugCheck.state === 'taken' && (
                <span style={{ color: '#dc2626', display: 'inline-flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <X size={15} /> {slugCheck.reason || 'Already taken'}
                  {slugCheck.suggestion && (
                    <button onClick={() => setSlug(slugCheck.suggestion)} style={{
                      background: 'none', border: 'none', color: '#4f46e5', fontWeight: 700,
                      cursor: 'pointer', textDecoration: 'underline', fontSize: 14,
                    }}>Try {slugCheck.suggestion}</button>
                  )}
                </span>
              )}
            </div>
            <button className="btn-primary" disabled={!slugOk || creating}
              onClick={() => setStep(2)} style={{ ...primaryBtn, opacity: !slugOk ? 0.5 : 1, marginTop: 8, padding: '13px 32px' }}>
              Continue <ChevronLeft size={16} style={{ transform: 'rotate(180deg)' }} />
            </button>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="s2" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.25 }}
            style={{ ...cardStyle, padding: 32 }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8 }}>Tell us about you</h2>
            <p style={{ color: '#475569', fontSize: 14, marginBottom: 28 }}>This appears at the top of your website. You can change it later.</p>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Your name / brand</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Pandit Rajesh Vakra" style={{ ...inputStyle, fontSize: 15 }} />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={labelStyle}>One-line tagline</label>
              <input value={tagline} onChange={(e) => setTagline(e.target.value)} placeholder="Vedic Astrologer in Jaipur · 25+ years" style={inputStyle} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 24 }}>
              <div style={{ border: '1px solid #e2e8f0', borderRadius: 14, padding: 16 }}>
                <label style={labelStyle}><ImageIcon size={13} style={{ verticalAlign: -2 }} /> Logo (optional)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {logoUrl
                    ? <img src={logoUrl} alt="logo" style={{ width: 48, height: 48, borderRadius: 10, objectFit: 'cover', border: '1px solid #e2e8f0' }} />
                    : <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={20} color="#94a3b8" /></div>}
                  <label style={{ ...ghostBtn, padding: '7px 12px', fontSize: 12, cursor: 'pointer' }}>
                    {logoUrl ? 'Change' : 'Upload'}
                    <input type="file" accept="image/*" onChange={pickLogo} style={{ display: 'none' }} />
                  </label>
                  {logoUrl && <button onClick={() => setLogoUrl(null)} title="Remove" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}><Trash2 size={15} /></button>}
                </div>
              </div>
              <div style={{ border: '1px solid #e2e8f0', borderRadius: 14, padding: 16 }}>
                <label style={labelStyle}><ImageIcon size={13} style={{ verticalAlign: -2 }} /> Hero photo (optional)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {heroImage
                    ? <img src={heroImage} alt="hero" style={{ width: 72, height: 48, borderRadius: 8, objectFit: 'cover', border: '1px solid #e2e8f0' }} />
                    : <div style={{ width: 72, height: 48, borderRadius: 8, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={20} color="#94a3b8" /></div>}
                  <label style={{ ...ghostBtn, padding: '7px 12px', fontSize: 12, cursor: 'pointer' }}>
                    {heroImage ? 'Change' : 'Upload'}
                    <input type="file" accept="image/*" onChange={pickHero} style={{ display: 'none' }} />
                  </label>
                  {heroImage && <button onClick={() => setHeroImage(null)} title="Remove" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}><Trash2 size={15} /></button>}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setStep(1)} style={ghostBtn}><ChevronLeft size={16} /> Back</button>
              <button onClick={() => setStep(3)} className="btn-primary" style={{ ...primaryBtn, padding: '13px 32px' }}>Continue <ChevronLeft size={16} style={{ transform: 'rotate(180deg)' }} /></button>
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="s3" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.25 }}
            style={{ ...cardStyle, padding: 32 }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8 }}>Pick a design</h2>
            <p style={{ color: '#475569', fontSize: 14, marginBottom: 28 }}>You can switch designs and colors anytime — no rebuilding needed.</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14, marginBottom: 28 }}>
              {TEMPLATES.map((t) => (
                <button key={t.id} onClick={() => setTemplate(t.id)}
                  style={{
                    border: `2px solid ${template === t.id ? '#4f46e5' : '#e2e8f0'}`,
                    background: template === t.id ? 'rgba(79,70,229,0.04)' : '#fff',
                    borderRadius: 14, padding: 16, cursor: 'pointer', textAlign: 'left', position: 'relative',
                  }}>
                  {t.tier === 'Premium' && (
                    <span style={{
                      position: 'absolute', top: 10, right: 10, fontSize: 9, fontWeight: 800, letterSpacing: 0.5,
                      padding: '3px 8px', borderRadius: 10, background: 'linear-gradient(135deg,#d97706,#f59e0b)', color: '#fff',
                    }}>PREMIUM</span>
                  )}
                  {/* mini preview */}
                  <div style={{
                    height: 84, borderRadius: 10, marginBottom: 12, position: 'relative', overflow: 'hidden',
                    background: t.id === 'celestial' || t.id === 'royal' || t.id === 'tantra' || t.id === 'classic'
                      ? `linear-gradient(160deg, ${t.colors[0]}22, #0a0a1a)` : `linear-gradient(160deg, ${t.colors[0]}18, #f8fafc)`,
                    border: `1px solid ${t.colors[0]}33`,
                  }}>
                    <div style={{ position: 'absolute', top: 10, left: 10, width: 20, height: 20, borderRadius: 6, background: `linear-gradient(135deg, ${t.colors[0]}, ${t.colors[1]})` }} />
                    <div style={{ position: 'absolute', top: 40, left: 10, width: '60%', height: 8, borderRadius: 4, background: `${t.colors[0]}55` }} />
                    <div style={{ position: 'absolute', top: 56, left: 10, width: '40%', height: 6, borderRadius: 4, background: '#94a3b855' }} />
                    <div style={{ position: 'absolute', top: 40, right: 10, width: 26, height: 26, borderRadius: 6, background: `linear-gradient(135deg, ${t.colors[0]}, ${t.colors[1]})`, opacity: 0.8 }} />
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 3 }}>{t.name}</div>
                  <div style={{ color: '#64748b', fontSize: 11.5, lineHeight: 1.4 }}>{t.desc}</div>
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setStep(2)} style={ghostBtn}><ChevronLeft size={16} /> Back</button>
              <button onClick={submit} disabled={creating} className="btn-primary" style={{ ...primaryBtn, opacity: creating ? 0.6 : 1, padding: '13px 32px' }}>
                {creating ? 'Creating…' : (<><Sparkles size={16} /> Create my website</>)}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ═══════════════ OVERVIEW TAB ═══════════════
function OverviewTab({ site, reload }) {
  const [stats, setStats] = useState(null)
  useEffect(() => {
    getMySiteStats(site.id).then(setStats).catch(() => setStats(null))
  }, [site.id, site.updated_at]) // eslint-disable-line

  const statCards = stats ? [
    { label: 'Upcoming bookings', value: stats.bookings?.upcoming || 0, icon: Calendar, color: '#4f46e5' },
    { label: 'Total bookings', value: stats.bookings?.total || 0, icon: LayoutDashboard, color: '#2563eb' },
    { label: 'Leads captured', value: stats.leads?.total || 0, icon: Users, color: '#d97706' },
    { label: 'Consultation revenue', value: `₹${(stats.bookings?.confirmedRevenue || 0) + (stats.bookings?.completedRevenue || 0)}`, icon: IndianRupee, color: '#16a34a' },
    { label: 'Active services', value: stats.services?.active || 0, icon: Star, color: '#7c3aed' },
    { label: 'Store orders', value: stats.store?.ordersTotal || 0, icon: ShoppingBag, color: '#db2777' },
  ] : []

  return (
    <div>
      {stats === null ? (
        <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading your stats…</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14, marginBottom: 24 }}>
            {statCards.map((s) => (
              <div key={s.label} style={{ ...cardStyle, padding: 18 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10, background: `${s.color}15`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12,
                }}>
                  <s.icon size={18} color={s.color} />
                </div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#0f172a' }}>{s.value}</div>
                <div style={{ fontSize: 12, color: '#64748b', fontWeight: 600, marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>

          <div style={{ ...cardStyle }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Clock size={16} color="#4f46e5" /> Next appointments
            </h3>
            {(stats.upcoming || []).length === 0 ? (
              <p style={{ color: '#64748b', fontSize: 13, padding: '16px 0' }}>
                No upcoming bookings yet. Share your site link on WhatsApp and Instagram to get started!
              </p>
            ) : (
              <div style={{ marginTop: 12 }}>
                {(stats.upcoming || []).map((b) => (
                  <div key={b.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
                    padding: '12px 4px', borderBottom: '1px solid #f1f5f9', flexWrap: 'wrap',
                  }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14 }}>{b.client_name}</div>
                      <div style={{ color: '#64748b', fontSize: 12, marginTop: 2 }}>
                        {b.service_name || 'Consultation'} · {b.date} · {b.start_time}
                      </div>
                    </div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{b.amount ? `₹${b.amount}` : 'Free'}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* setup checklist */}
          <div style={{ ...cardStyle, marginTop: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendingUp size={16} color="#d97706" /> Grow faster — quick setup
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginTop: 14 }}>
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
                  <div style={{
                    width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                    background: c.ok ? '#16a34a' : '#cbd5e1', color: '#fff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Check size={12} strokeWidth={3} />
                  </div>
                  {c.text}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ═══════════════ CONTENT TAB (pages editor) ═══════════════
function ContentTab({ site, reload }) {
  const [pageKey, setPageKey] = useState('home')
  const pages = site.pages || []
  const page = pages.find((p) => p.page_key === pageKey) || { content: {} }
  const [content, setContent] = useState(page.content || {})
  const [saving, setSaving] = useState(false)

  useEffect(() => { setContent(page.content || {}) }, [pageKey, site.updated_at]) // eslint-disable-line

  const save = async () => {
    setSaving(true)
    try {
      await saveMySitePage(site.id, pageKey, { title: page.title, content })
      toast.success('Saved! Your website is updated.')
      reload()
    } catch {
      toast.error('Could not save — try again')
    } finally { setSaving(false) }
  }

  const set = (k, v) => setContent((c) => ({ ...c, [k]: v }))

  const testiList = Array.isArray(content.testimonials) ? content.testimonials : []
  const setTesti = (i, patch) => setContent((c) => ({
    ...c,
    testimonials: (c.testimonials || []).map((t, j) => (j === i ? { ...t, ...patch } : t)),
  }))

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
        {pageKey === 'home' && (
          <>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Headline (appears large at top)</label>
              <input value={content.heroTitle || ''} onChange={(e) => set('heroTitle', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Sub-headline</label>
              <textarea rows={2} value={content.heroSubtitle || ''} onChange={(e) => set('heroSubtitle', e.target.value)} style={{ ...inputStyle, resize: 'vertical' }} />
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
              <label style={labelStyle}>About section title</label>
              <input value={content.aboutTitle || ''} onChange={(e) => set('aboutTitle', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={labelStyle}>About section text</label>
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
          </>
        )}
        {(pageKey === 'about' || pageKey === 'contact') && (
          <>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Title</label>
              <input value={content.title || ''} onChange={(e) => set('title', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>Text</label>
              <textarea rows={6} value={content.text || ''} onChange={(e) => set('text', e.target.value)} style={{ ...inputStyle, resize: 'vertical' }} />
            </div>
          </>
        )}
        <button onClick={save} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  )
}

// ═══════════════ DESIGN TAB (template + theme) ═══════════════
function DesignTab({ site, reload }) {
  const [theme, setTheme] = useState(site.theme || {})
  const [saving, setSaving] = useState(false)
  const [logoUrl, setLogoUrl] = useState(site.logo_url || null)
  const [heroImage, setHeroImage] = useState(site.hero_image || null)

  useEffect(() => { setTheme(site.theme || {}) }, [site.id, site.updated_at]) // eslint-disable-line
  useEffect(() => { setLogoUrl(site.logo_url || null); setHeroImage(site.hero_image || null) }, [site.id, site.updated_at]) // eslint-disable-line

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
              ? <img src={logoUrl} alt="logo" style={{ width: 56, height: 56, borderRadius: 12, objectFit: 'cover', border: '1px solid #e2e8f0' }} />
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
        {(site.services || []).map((s) => (
          <div key={s.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
            padding: '14px 16px', border: '1px solid #e2e8f0', borderRadius: 12, marginBottom: 10, flexWrap: 'wrap',
          }}>
            <div style={{ flex: 1, minWidth: 180 }}>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{s.name} {!s.is_active && <span style={{ color: '#94a3b8', fontSize: 12 }}>(hidden)</span>}</div>
              <div style={{ color: '#64748b', fontSize: 13 }}>{s.description}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>₹{s.price}</div>
              <div style={{ color: '#64748b', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={13} /> {s.duration_minutes}m</div>
              <button onClick={() => toggleActive(s)} title={s.is_active ? 'Hide from site' : 'Show on site'}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: s.is_active ? '#16a34a' : '#94a3b8' }}>
                {s.is_active ? <Eye size={17} /> : <EyeOff size={17} />}
              </button>
              <button onClick={() => remove(s)} title="Delete" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: 18, marginTop: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 14 }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={labelStyle}>New service name</label>
              <input value={svc.name} onChange={(e) => setSvc((s) => ({ ...s, name: e.target.value }))} placeholder="Gemstone Consultation" style={inputStyle} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={labelStyle}>Description (optional)</label>
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
    </div>
  )
}

// ═══════════════ STORE TAB (products + orders) ═══════════════
function StoreTab({ site, reload }) {
  const [sub, setSub] = useState('products')
  const [products, setProducts] = useState(null)
  const [orders, setOrders] = useState(null)
  const [form, setForm] = useState({ name: '', description: '', price: 500, stock: -1 })
  const [busy, setBusy] = useState(false)

  const loadProducts = () => getMyProducts(site.id).then(setProducts).catch(() => setProducts([]))
  const loadOrders = () => getMyOrders(site.id).then(setOrders).catch(() => setOrders([]))
  useEffect(() => {
    if (sub === 'products') loadProducts()
    else loadOrders()
  }, [sub, site.id, site.updated_at]) // eslint-disable-line

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
        {[['products', 'Products', Package], ['orders', 'Orders', ShoppingBag]].map(([id, label, Icon]) => (
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

      {sub === 'products' && (
        <>
          {products === null ? (
            <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading products…</div>
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

          <div style={cardStyle}>
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Add a product</h3>
            <form onSubmit={addProduct}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 14 }}>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={labelStyle}>Product name</label>
                  <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Yellow Sapphire (Pukhraj) 5.25 ct" style={inputStyle} />
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={labelStyle}>Description (optional)</label>
                  <input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Certified, government-lab tested" style={inputStyle} />
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
        </>
      )}

      {sub === 'orders' && (
        <>
          {orders === null ? (
            <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading orders…</div>
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

// ═══════════════ LEADS TAB ═══════════════
function LeadsTab({ site }) {
  const [leads, setLeads] = useState(null)

  const load = () => getMyLeads(site.id).then(setLeads).catch(() => setLeads([]))
  useEffect(() => { load() }, [site.id]) // eslint-disable-line

  const waLink = (phone) => {
    const digits = (phone || '').replace(/[^\d]/g, '')
    if (digits.length === 10) return `https://wa.me/91${digits}`
    if (digits.length > 10) return `https://wa.me/${digits}`
    return null
  }

  return (
    <div>
      <p style={{ color: '#475569', fontSize: 14, marginBottom: 20 }}>
        People who used your free tools (kundli etc.) and shared their contact — a warm list of potential clients.
      </p>
      {leads === null ? (
        <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading leads…</div>
      ) : leads.length === 0 ? (
        <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 48 }}>
          <Users size={32} style={{ marginBottom: 12 }} />
          <div>No leads yet. Your free kundli tool collects contacts automatically — share your site link to grow your client list.</div>
        </div>
      ) : (
        leads.map((l) => (
          <div key={l.id} style={{ ...cardStyle, padding: '16px 20px', marginBottom: 10, display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{l.name || 'Anonymous'}</span>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12, background: 'rgba(79,70,229,0.08)', color: '#4f46e5' }}>
                  {l.tool === 'kundli' ? 'Free Kundli' : l.tool}
                </span>
              </div>
              <div style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
                {l.phone ? `${l.phone} · ` : ''}{l.details?.date ? `Born ${l.details.date} ${l.details.time || ''}` : ''}{l.details?.place ? ` · ${l.details.place}` : ''}
              </div>
              <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 2 }}>
                {l.details?.ascendant ? `Ascendant ${l.details.ascendant}` : ''}{l.details?.moonSign ? ` · Moon ${l.details.moonSign}` : ''} · {new Date(l.created_at).toLocaleDateString()}
              </div>
            </div>
            {l.phone && waLink(l.phone) && (
              <a href={waLink(l.phone)} target="_blank" rel="noopener noreferrer">
                <button className="btn-primary" style={{ padding: '8px 16px', fontSize: 13 }}>
                  WhatsApp <ArrowRight size={13} />
                </button>
              </a>
            )}
          </div>
        ))
      )}
    </div>
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
        <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading bookings…</div>
      ) : visible.length === 0 ? (
        <div style={{ ...cardStyle, textAlign: 'center', color: '#64748b', padding: 48 }}>
          <Calendar size={32} style={{ marginBottom: 12 }} />
          <div>No bookings yet. Share your site link on WhatsApp and Instagram to get your first booking!</div>
        </div>
      ) : (
        visible.map((b) => {
          const upcoming = b.date >= today && b.status === 'confirmed'
          return (
            <div key={b.id} style={{
              ...cardStyle, padding: '16px 20px', marginBottom: 10, display: 'flex',
              justifyContent: 'space-between', alignItems: 'center', gap: 14, flexWrap: 'wrap',
              borderColor: upcoming ? 'rgba(34,197,94,0.3)' : '#e2e8f0',
            }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontWeight: 700, fontSize: 15 }}>{b.client_name}</span>
                  <span style={{
                    fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12,
                    background: b.status === 'confirmed' ? 'rgba(34,197,94,0.12)' : b.status === 'completed' ? 'rgba(59,130,246,0.12)' : 'rgba(239,68,68,0.12)',
                    color: b.status === 'confirmed' ? '#16a34a' : b.status === 'completed' ? '#2563eb' : '#ef4444',
                  }}>{b.status.replace('_', ' ')}</span>
                </div>
                <div style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
                  {b.date} · {b.start_time}–{b.end_time}
                  {b.client_phone ? ` · ${b.client_phone}` : ''}
                  {b.amount ? ` · ₹${b.amount}` : ''}
                </div>
                {b.notes && <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 3 }}>📝 {b.notes}</div>}
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {b.client_phone && (
                  <a href={`https://wa.me/${String(b.client_phone).replace(/[^\d]/g, '').length >= 10 ? String(b.client_phone).replace(/[^\d]/g, '') : '91' + String(b.client_phone).replace(/[^\d]/g, '')}?text=${encodeURIComponent(`Namaste ${b.client_name}, confirming your consultation on ${b.date} at ${b.start_time}. — ${site.name}`)}`}
                    target="_blank" rel="noopener noreferrer" style={{ ...ghostBtn, padding: '7px 12px', fontSize: 12 }}>
                    WhatsApp
                  </a>
                )}
                {b.status === 'confirmed' && (
                  <>
                    <button onClick={() => setStatus(b, 'completed')} style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12 }}>
                      <Check size={13} /> Completed
                    </button>
                    <button onClick={() => setStatus(b, 'cancelled')} style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12, color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}>
                      <X size={13} /> Cancel
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}

// ═══════════════ DOMAIN TAB ═══════════════
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
      toast.success('Domain saved — now add the DNS record and verify')
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
          Use your own domain like <strong>astrovakra.com</strong> instead of the free address. Free SSL (the 🔒 padlock) is included automatically.
        </p>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
          <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="astrovakra.com"
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
            <div style={{ fontWeight: 700, marginBottom: 6 }}>DNS setup — do this at your domain provider (GoDaddy, Namecheap, etc.)</div>
            Add a <strong>CNAME record</strong>:<br />
            Name / Host: <code style={{ color: '#1e293b' }}>www</code> · Value / Target: <code style={{ color: '#1e293b' }}>sites.astrovakta.com</code><br />
            Then tap <strong>Verify DNS</strong>. DNS changes can take 5 minutes to a few hours.
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

// ═══════════════ SETTINGS TAB (alerts, social, contact, plan, danger zone) ═══════════════
function SettingsTab({ site, reload }) {
  const [wa, setWa] = useState(site.settings?.whatsappNumber || '')
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
  }, [site.id, site.updated_at]) // eslint-disable-line

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
          <label style={labelStyle}>Tagline</label>
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
  { id: 'leads', label: 'Leads', icon: Users },
  { id: 'domain', label: 'Domain', icon: Globe2 },
  { id: 'settings', label: 'Settings', icon: Settings2 },
]

export default function MySite() {
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const [sites, setSites] = useState(null)
  const [site, setSite] = useState(null)
  const [tab, setTab] = useState('overview')
  const [pubBusy, setPubBusy] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const navigate = useNavigate()

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
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72 }}>
        <div className="gradient-text" style={{ fontSize: 18, fontWeight: 600 }}>Loading…</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: 72, flexDirection: 'column', gap: 20 }}>
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
    <div style={{ minHeight: '100vh', paddingTop: 72, background: '#f8fafc' }}>
      {/* top bar */}
      <div style={{ background: '#fff', borderBottom: '1px solid #e2e8f0' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {site && (
              <button className="mysite-mobile-nav-btn" onClick={() => setMobileNavOpen((o) => !o)}
                style={{ display: 'none', background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: 6, color: '#0f172a' }}>
                <Menu size={18} />
              </button>
            )}
            {site ? (
              <>
                <Globe size={20} color="#4f46e5" />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 17, fontWeight: 800 }}>{site.name}</span>
                    <span style={{
                      fontSize: 10.5, fontWeight: 700, padding: '2px 10px', borderRadius: 12,
                      background: site.status === 'published' ? 'rgba(34,197,94,0.12)' : 'rgba(245,158,11,0.12)',
                      color: site.status === 'published' ? '#16a34a' : '#d97706',
                    }}>{site.status === 'published' ? 'LIVE' : 'DRAFT'}</span>
                  </div>
                  <div style={{ color: '#64748b', fontSize: 12, marginTop: 1 }}>
                    {site.custom_domain && site.domain_status === 'active' ? site.custom_domain : `${site.slug}.astrovakta.com`}
                  </div>
                </div>
              </>
            ) : (
              <span style={{ fontSize: 16, fontWeight: 700 }}>My Website</span>
            )}
          </div>
          {site && (
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {site.status === 'published' && (
                <a href={tenantSiteUrl(site.slug)} target="_blank" rel="noopener noreferrer">
                  <button style={ghostBtn}><ExternalLink size={15} /> View site</button>
                </a>
              )}
              <button onClick={togglePublish} disabled={pubBusy} className="btn-primary" style={{ ...primaryBtn, opacity: pubBusy ? 0.6 : 1 }}>
                {site.status === 'published' ? (<><EyeOff size={15} /> Unpublish</>) : (<><Sparkles size={15} /> Publish site</>)}
              </button>
            </div>
          )}
        </div>
      </div>

      <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', gap: 0, alignItems: 'flex-start' }}>
        {/* sidebar */}
        {site && (
          <aside
            className="mysite-sidebar"
            style={{
              width: 220, flexShrink: 0, borderRight: '1px solid #e2e8f0', background: '#fff',
              padding: '20px 12px', position: 'sticky', top: 121, bottom: 0,
              minHeight: 'calc(100vh - 121px)', display: 'flex', flexDirection: 'column', gap: 2,
            }}>
            {TABS.map((t) => (
              <button key={t.id} onClick={() => { setTab(t.id); setMobileNavOpen(false) }}
                className={tab === t.id ? 'mysite-tab-active' : ''}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10,
                  fontSize: 14, fontWeight: tab === t.id ? 700 : 500, cursor: 'pointer',
                  background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                  color: tab === t.id ? '#4f46e5' : '#475569',
                  border: 'none', textAlign: 'left', transition: 'all 0.15s',
                }}>
                <t.icon size={16} /> {t.label}
              </button>
            ))}
            <div style={{ marginTop: 'auto', padding: '12px 14px' }}>
              <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.6 }}>
                Signed in as<br />
                <span style={{ color: '#475569', fontWeight: 600 }}>{user?.email}</span>
              </div>
            </div>
          </aside>
        )}

        {/* main panel */}
        <div style={{ flex: 1, padding: '28px 24px 80px', minWidth: 0 }}>
          {site === null ? (
            sites === null ? (
              <div style={{ color: '#64748b', padding: 60, textAlign: 'center' }}>Loading…</div>
            ) : (
              <div>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <h1 style={{ fontSize: 34, fontWeight: 800, marginBottom: 10 }}>Create your website</h1>
                  <p style={{ color: '#475569', fontSize: 16 }}>Live in under a minute — no coding, no design skills.</p>
                </div>
                <CreateSiteWizard onCreated={(s) => {
                  getMySite(s.id).then(setSite).catch(() => setSite(s))
                  setSites([s]); setTab('overview')
                }} />
              </div>
            )
          ) : (
            <AnimatePresence mode="wait">
              <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
                {tab === 'overview' && <OverviewTab site={site} reload={reload} />}
                {tab === 'content' && <ContentTab site={site} reload={reload} />}
                {tab === 'design' && <DesignTab site={site} reload={reload} />}
                {tab === 'services' && <ServicesTab site={site} reload={reload} />}
                {tab === 'store' && <StoreTab site={site} reload={reload} />}
                {tab === 'hours' && <HoursTab site={site} reload={reload} />}
                {tab === 'bookings' && <BookingsTab site={site} />}
                {tab === 'leads' && <LeadsTab site={site} />}
                {tab === 'domain' && <DomainTab site={site} reload={reload} />}
                {tab === 'settings' && <SettingsTab site={site} reload={reload} />}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* mobile tab bar */}
      {site && (
        <div className="mysite-mobile-tabs" style={{
          display: 'none', position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 50,
          background: '#fff', borderTop: '1px solid #e2e8f0', padding: '8px 6px',
          overflowX: 'auto',
        }}>
          <div style={{ display: 'flex', gap: 4, minWidth: 'max-content' }}>
            {TABS.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
                  padding: '6px 10px', borderRadius: 10, fontSize: 10.5, fontWeight: tab === t.id ? 700 : 500,
                  background: tab === t.id ? 'rgba(79,70,229,0.08)' : 'transparent',
                  color: tab === t.id ? '#4f46e5' : '#64748b', border: 'none', cursor: 'pointer',
                }}>
                <t.icon size={17} /> {t.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @media (max-width: 900px) {
          .mysite-sidebar { display: none !important; }
          .mysite-mobile-tabs { display: block !important; }
          .mysite-mobile-nav-btn { display: flex !important; }
        }
        .mysite-tab-active:hover { background: rgba(79,70,229,0.12) !important; }
      `}</style>
    </div>
  )
}
