import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe, Plus, Trash2, ExternalLink, Check, X, Palette, FileText, Calendar,
  Store, Globe2, Eye, EyeOff, Sparkles, Clock, ChevronLeft, Settings2,
  Save, RefreshCw, LogIn, Shield, ArrowRight, Image as ImageIcon, Users,
  Bell, Crown, Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../lib/auth.jsx'
import { CLERK_ENABLED, SignedOut, SignInButton } from '../lib/clerk.jsx'
import { tenantSiteUrl } from '../lib/tenant.js'
import {
  getMySites, createMySite, getMySite, updateMySite, publishMySite, unpublishMySite,
  deleteMySite, saveMySitePage, setMySiteDomain, verifyMySiteDomain, removeMySiteDomain,
  createMyService, updateMyService, deleteMyService,
  getMyAvailability, setMyAvailability, getMyBookings, updateMyBooking,
  checkSlugAvailability, checkDomainAvailability, setMySiteMedia, setMySiteSettings, getMyLeads,
} from '../lib/api.js'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const inputStyle = {
  width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.8)',
  border: '1px solid var(--border-color)', borderRadius: 10, color: 'var(--text-primary)',
  fontSize: 14, outline: 'none',
}
const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 6 }
const cardStyle = { background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: 24 }
const primaryBtn = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', background: 'var(--gradient-primary)', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 600, fontSize: 14, cursor: 'pointer' }
const ghostBtn = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: 10, fontWeight: 600, fontSize: 14, cursor: 'pointer' }

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
  { id: 'aurora', name: 'Aurora', desc: 'Clean indigo & amber — light, modern, professional', colors: ['#4f46e5', '#d97706'] },
  { id: 'classic', name: 'Classic', desc: 'Traditional warm tones for trust', colors: ['#b45309', '#dc2626'] },
  { id: 'minimal', name: 'Minimal', desc: 'Fresh teal — calm and clutter-free', colors: ['#0f766e', '#0ea5e9'] },
  { id: 'devotional', name: 'Devotional', desc: 'Saffron & temple palette', colors: ['#ea580c', '#facc15'] },
]

const PRESETS = {
  aurora: { primaryColor: '#4f46e5', accentColor: '#d97706', bgStyle: 'light' },
  classic: { primaryColor: '#b45309', accentColor: '#dc2626', bgStyle: 'dark' },
  minimal: { primaryColor: '#0f766e', accentColor: '#0ea5e9', bgStyle: 'light' },
  devotional: { primaryColor: '#ea580c', accentColor: '#facc15', bgStyle: 'light' },
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

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 36, justifyContent: 'center' }}>
        {[1, 2, 3].map((s) => (
          <div key={s} style={{
            flex: 1, height: 5, borderRadius: 4,
            background: step >= s ? 'var(--gradient-primary)' : 'rgba(79,70,229,0.15)',
          }} />
        ))}
      </div>

      {step === 1 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <h2 style={{ fontSize: 26, fontWeight: 800, marginBottom: 8 }}>Choose your web address</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 28, lineHeight: 1.6 }}>
            This becomes your free website address. You can connect your own domain (like astrovakra.com) anytime after.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 10 }}>
            <input value={slugClean} onChange={(e) => setSlug(e.target.value)} placeholder="pandit-rajesh"
              style={{ ...inputStyle, borderTopRightRadius: 0, borderBottomRightRadius: 0 }} />
            <div style={{
              padding: '10px 14px', background: 'rgba(79,70,229,0.06)', border: '1px solid var(--border-color)',
              borderLeft: 'none', borderTopRightRadius: 10, borderBottomRightRadius: 10,
              color: 'var(--accent-purple)', fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap',
            }}>.astrovakta.com</div>
          </div>
          <div style={{ minHeight: 28, marginBottom: 8, fontSize: 14 }}>
            {slugCheck.state === 'checking' && (
              <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
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
                    background: 'none', border: 'none', color: 'var(--accent-purple)', fontWeight: 700,
                    cursor: 'pointer', textDecoration: 'underline', fontSize: 14,
                  }}>Try {slugCheck.suggestion}</button>
                )}
              </span>
            )}
          </div>
          <button className="btn-primary" disabled={!slugOk || creating}
            onClick={() => setStep(2)} style={{ ...primaryBtn, opacity: !slugOk ? 0.5 : 1, marginTop: 12 }}>
            Continue <ChevronLeft size={16} style={{ transform: 'rotate(180deg)' }} />
          </button>
        </motion.div>
      )}

      {step === 2 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <h2 style={{ fontSize: 26, fontWeight: 800, marginBottom: 8 }}>Tell us about you</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 28 }}>This appears at the top of your website. You can change it later.</p>
          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>Your name / brand</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Pandit Rajesh Vakra" style={inputStyle} />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={labelStyle}>One-line tagline</label>
            <input value={tagline} onChange={(e) => setTagline(e.target.value)} placeholder="Vedic Astrologer in Jaipur · 25+ years" style={inputStyle} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 24 }}>
            <div style={{ ...cardStyle, padding: 16 }}>
              <label style={labelStyle}><ImageIcon size={13} style={{ verticalAlign: -2 }} /> Logo (optional)</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {logoUrl
                  ? <img src={logoUrl} alt="logo" style={{ width: 48, height: 48, borderRadius: 10, objectFit: 'cover', border: '1px solid var(--border-color)' }} />
                  : <div style={{ width: 48, height: 48, borderRadius: 10, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={20} color="var(--text-muted)" /></div>}
                <label style={{ ...ghostBtn, padding: '7px 12px', fontSize: 12, cursor: 'pointer' }}>
                  {logoUrl ? 'Change' : 'Upload'}
                  <input type="file" accept="image/*" onChange={pickLogo} style={{ display: 'none' }} />
                </label>
                {logoUrl && <button onClick={() => setLogoUrl(null)} title="Remove" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626' }}><Trash2 size={15} /></button>}
              </div>
            </div>
            <div style={{ ...cardStyle, padding: 16 }}>
              <label style={labelStyle}><ImageIcon size={13} style={{ verticalAlign: -2 }} /> Hero photo (optional)</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {heroImage
                  ? <img src={heroImage} alt="hero" style={{ width: 72, height: 48, borderRadius: 8, objectFit: 'cover', border: '1px solid var(--border-color)' }} />
                  : <div style={{ width: 72, height: 48, borderRadius: 8, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={20} color="var(--text-muted)" /></div>}
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
            <button onClick={() => setStep(3)} className="btn-primary" style={primaryBtn}>Continue <ChevronLeft size={16} style={{ transform: 'rotate(180deg)' }} /></button>
          </div>
        </motion.div>
      )}

      {step === 3 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <h2 style={{ fontSize: 26, fontWeight: 800, marginBottom: 8 }}>Pick a design</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 28 }}>You can switch designs and colors anytime.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 28 }}>
            {TEMPLATES.map((t) => (
              <button key={t.id} onClick={() => setTemplate(t.id)}
                style={{
                  ...cardStyle, padding: 18, cursor: 'pointer', textAlign: 'left',
                  border: `2px solid ${template === t.id ? 'var(--accent-purple)' : 'var(--border-color)'}`,
                  background: template === t.id ? 'rgba(79,70,229,0.05)' : 'var(--bg-card)',
                }}>
                <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
                  {t.colors.map((c) => <div key={c} style={{ width: 22, height: 22, borderRadius: 6, background: c }} />)}
                </div>
                <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{t.name}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: 12, lineHeight: 1.5 }}>{t.desc}</div>
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={() => setStep(2)} style={ghostBtn}><ChevronLeft size={16} /> Back</button>
            <button onClick={submit} disabled={creating} className="btn-primary" style={{ ...primaryBtn, opacity: creating ? 0.6 : 1 }}>
              {creating ? 'Creating…' : (<><Sparkles size={16} /> Create my website</>)}
            </button>
          </div>
        </motion.div>
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

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
        {['home', 'about', 'contact'].map((k) => (
          <button key={k} onClick={() => setPageKey(k)} style={{
            ...ghostBtn, padding: '8px 18px', fontSize: 13,
            background: pageKey === k ? 'rgba(124,58,237,0.15)' : 'transparent',
            borderColor: pageKey === k ? 'var(--accent-purple)' : 'var(--border-color)',
            color: pageKey === k ? '#4f46e5' : 'var(--text-primary)',
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
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>About section title</label>
              <input value={content.aboutTitle || ''} onChange={(e) => set('aboutTitle', e.target.value)} style={inputStyle} />
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={labelStyle}>About section text</label>
              <textarea rows={4} value={content.aboutText || ''} onChange={(e) => set('aboutText', e.target.value)} style={{ ...inputStyle, resize: 'vertical' }} />
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
      toast.success('Design updated')
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
      <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Template</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 32 }}>
        {TEMPLATES.map((t) => (
          <button key={t.id} onClick={() => applyTemplate(t.id)} disabled={saving}
            style={{
              ...cardStyle, padding: 18, cursor: 'pointer', textAlign: 'left',
              border: `2px solid ${site.template === t.id ? 'var(--accent-purple)' : 'var(--border-color)'}`,
              background: site.template === t.id ? 'rgba(79,70,229,0.05)' : 'var(--bg-card)',
            }}>
            <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
              {t.colors.map((c) => <div key={c} style={{ width: 22, height: 22, borderRadius: 6, background: c }} />)}
            </div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>{t.name}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 4, lineHeight: 1.5 }}>{t.desc}</div>
          </button>
        ))}
      </div>

      <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Your logo & photo</h3>
      <div style={{ ...cardStyle, display: 'flex', gap: 32, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 32 }}>
        <div>
          <label style={labelStyle}>Logo</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {logoUrl
              ? <img src={logoUrl} alt="logo" style={{ width: 56, height: 56, borderRadius: 12, objectFit: 'cover', border: '1px solid var(--border-color)' }} />
              : <div style={{ width: 56, height: 56, borderRadius: 12, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={22} color="var(--text-muted)" /></div>}
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
              ? <img src={heroImage} alt="hero" style={{ width: 96, height: 56, borderRadius: 10, objectFit: 'cover', border: '1px solid var(--border-color)' }} />
              : <div style={{ width: 96, height: 56, borderRadius: 10, background: 'rgba(79,70,229,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ImageIcon size={22} color="var(--text-muted)" /></div>}
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

      <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Colors</h3>
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
            padding: '14px 16px', border: '1px solid var(--border-color)', borderRadius: 12, marginBottom: 10, flexWrap: 'wrap',
          }}>
            <div style={{ flex: 1, minWidth: 180 }}>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{s.name} {!s.is_active && <span style={{ color: '#64748b', fontSize: 12 }}>(hidden)</span>}</div>
              <div style={{ color: '#475569', fontSize: 13 }}>{s.description}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>₹{s.price}</div>
              <div style={{ color: '#475569', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={13} /> {s.duration_minutes}m</div>
              <button onClick={() => toggleActive(s)} title={s.is_active ? 'Hide from site' : 'Show on site'}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: s.is_active ? '#16a34a' : '#64748b' }}>
                {s.is_active ? <Eye size={17} /> : <EyeOff size={17} />}
              </button>
              <button onClick={() => remove(s)} title="Delete" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 18, marginTop: 8 }}>
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
      <p style={{ color: '#475569', fontSize: 13, marginBottom: 20 }}>Clients can only book inside these windows. Uncheck a day to mark it closed.</p>
      {rules.map((r, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 14, padding: '10px 12px',
          borderBottom: '1px solid rgba(124,58,237,0.08)', flexWrap: 'wrap',
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, width: 120, fontSize: 14, fontWeight: 600, cursor: 'pointer', opacity: r.enabled ? 1 : 0.45 }}>
            <input type="checkbox" checked={r.enabled} onChange={(e) => set(i, { enabled: e.target.checked })} style={{ accentColor: '#7c3aed' }} />
            {WEEKDAYS[i].slice(0, 3)}
          </label>
          <input type="time" value={r.start_time} disabled={!r.enabled} onChange={(e) => set(i, { start_time: e.target.value })} style={{ ...inputStyle, width: 110 }} />
          <span style={{ color: '#64748b' }}>to</span>
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
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>
        People who used your free tools (kundli etc.) and shared their contact — a warm list of potential clients.
      </p>
      {leads === null ? (
        <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading leads…</div>
      ) : leads.length === 0 ? (
        <div style={{ ...cardStyle, textAlign: 'center', color: 'var(--text-secondary)', padding: 48 }}>
          <Users size={32} style={{ marginBottom: 12 }} />
          <div>No leads yet. Your free kundli tool collects contacts automatically — share your site link to grow your client list.</div>
        </div>
      ) : (
        leads.map((l) => (
          <div key={l.id} style={{ ...cardStyle, padding: '16px 20px', marginBottom: 10, display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{l.name || 'Anonymous'}</span>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 10px', borderRadius: 12, background: 'rgba(79,70,229,0.08)', color: 'var(--accent-purple)' }}>
                  {l.tool === 'kundli' ? 'Free Kundli' : l.tool}
                </span>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
                {l.phone ? `${l.phone} · ` : ''}{l.details?.date ? `Born ${l.details.date} ${l.details.time || ''}` : ''}{l.details?.place ? ` · ${l.details.place}` : ''}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 2 }}>
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
            background: filter === v ? 'rgba(124,58,237,0.15)' : 'transparent',
            borderColor: filter === v ? 'var(--accent-purple)' : 'var(--border-color)',
            color: filter === v ? '#4f46e5' : 'var(--text-primary)',
          }}>{l}</button>
        ))}
      </div>

      {bookings === null ? (
        <div style={{ color: '#64748b', padding: 40, textAlign: 'center' }}>Loading bookings…</div>
      ) : visible.length === 0 ? (
        <div style={{ ...cardStyle, textAlign: 'center', color: '#475569', padding: 48 }}>
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
              borderColor: upcoming ? 'rgba(34,197,94,0.3)' : 'var(--border-color)',
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
                <div style={{ color: '#475569', fontSize: 13, marginTop: 4 }}>
                  {b.date} · {b.start_time}–{b.end_time}
                  {b.client_phone ? ` · ${b.client_phone}` : ''}
                  {b.amount ? ` · ₹${b.amount}` : ''}
                </div>
              </div>
              {b.status === 'confirmed' && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => setStatus(b, 'completed')} style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12 }}>
                    <Check size={13} /> Completed
                  </button>
                  <button onClick={() => setStatus(b, 'cancelled')} style={{ ...ghostBtn, padding: '7px 14px', fontSize: 12, color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}>
                    <X size={13} /> Cancel
                  </button>
                </div>
              )}
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
      const res = await setMySiteDomain(site.id, domain)
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
        <p style={{ color: '#475569', fontSize: 13, marginBottom: 20, lineHeight: 1.6 }}>
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
              <RefreshCw size={15} /> {busy ? 'Verifying…' : 'Verify DNS'}
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

// ═══════════════ SETTINGS TAB (alerts, plan, danger zone) ═══════════════
function SettingsTab({ site, reload }) {
  const [wa, setWa] = useState(site.settings?.whatsappNumber || '')
  const [alertsOn, setAlertsOn] = useState(site.settings?.bookingAlerts !== false)
  const [reminderHours, setReminderHours] = useState(site.settings?.reminderHours || 24)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setWa(site.settings?.whatsappNumber || '')
    setAlertsOn(site.settings?.bookingAlerts !== false)
    setReminderHours(site.settings?.reminderHours || 24)
  }, [site.id, site.updated_at]) // eslint-disable-line

  const saveSettings = async () => {
    setSaving(true)
    try {
      await setMySiteSettings(site.id, { whatsapp_number: wa, booking_alerts: alertsOn, reminder_hours: reminderHours })
      toast.success('Alerts settings saved')
      reload()
    } catch (e) { toast.error(errDetail(e, 'Could not save settings')) }
    finally { setSaving(false) }
  }

  return (
    <div>
      {/* WhatsApp alerts */}
      <div style={cardStyle}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bell size={17} color="var(--accent-purple)" /> WhatsApp alerts
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginBottom: 18, lineHeight: 1.6 }}>
          You and your clients get alerts on WhatsApp — booking confirmations and reminders before each appointment.
        </p>
        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>Your WhatsApp number (with country code)</label>
          <input value={wa} onChange={(e) => setWa(e.target.value)} placeholder="+91 98765 43210" style={inputStyle} />
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginBottom: 18 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
            <input type="checkbox" checked={alertsOn} onChange={(e) => setAlertsOn(e.target.checked)} style={{ accentColor: 'var(--accent-purple)' }} />
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
        <button onClick={saveSettings} disabled={saving} className="btn-primary" style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
          <Save size={15} /> {saving ? 'Saving…' : 'Save alerts settings'}
        </button>
      </div>

      {/* Plan / membership */}
      <div style={{ ...cardStyle, marginTop: 20, borderColor: 'rgba(79,70,229,0.3)' }}>
        <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Crown size={17} color="#d97706" /> Plan & membership
        </h3>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginTop: 12 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800 }}>Free <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>plan</span></div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
              Website · booking · free kundli tool · 1 custom domain
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
          if (window.confirm('Delete your website permanently? All bookings and content will be lost.')) {
            deleteMySite(site.id).then(() => { toast.success('Site deleted'); window.location.reload() }).catch(() => toast.error('Could not delete'))
          }
        }} style={{ ...ghostBtn, color: '#dc2626', borderColor: 'rgba(220,38,38,0.3)' }}>
          <Trash2 size={15} /> Delete website
        </button>
      </div>
    </div>
  )
}

// ═══════════════ MAIN PAGE ═══════════════
const TABS = [
  { id: 'content', label: 'Content', icon: FileText },
  { id: 'design', label: 'Design', icon: Palette },
  { id: 'services', label: 'Services', icon: Store },
  { id: 'hours', label: 'Hours', icon: Clock },
  { id: 'bookings', label: 'Bookings', icon: Calendar },
  { id: 'leads', label: 'Leads', icon: Users },
  { id: 'domain', label: 'Domain', icon: Globe2 },
  { id: 'settings', label: 'Settings', icon: Settings2 },
]

export default function MySite() {
  const { user, isAuthenticated, loading: authLoading, clerkSignedIn } = useAuth()
  const [sites, setSites] = useState(null)
  const [site, setSite] = useState(null)
  const [tab, setTab] = useState('content')
  const [pubBusy, setPubBusy] = useState(false)
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
        <Shield size={48} color="#64748b" />
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Sign in to manage your website</h2>
        <p style={{ color: '#475569', fontSize: 15, maxWidth: 380, textAlign: 'center' }}>
          Create and manage your astrology business website — bookings, services, domain and more.
        </p>
        {CLERK_ENABLED ? (
          <SignedOut>
            <SignInButton mode="modal">
              <button className="btn-primary" style={{ padding: '14px 32px', fontSize: 16 }}>
                <LogIn size={18} /> Sign In
              </button>
            </SignInButton>
          </SignedOut>
        ) : (
          <Link to="/login" className="btn-primary" style={{ padding: '14px 32px', fontSize: 16 }}>
            <LogIn size={18} /> Sign In <ArrowRight size={16} />
          </Link>
        )}
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', paddingTop: 72 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '28px 20px 80px' }}>
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
                setSites([s]); setTab('content')
              }} />
            </div>
          )
        ) : (
          <>
            {/* Site header bar */}
            <div style={{
              ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              gap: 16, flexWrap: 'wrap', marginBottom: 24, padding: '20px 24px',
              borderColor: site.status === 'published' ? 'rgba(34,197,94,0.3)' : 'var(--border-color)',
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <Globe size={20} color="#4f46e5" />
                  <span style={{ fontSize: 20, fontWeight: 800 }}>{site.name}</span>
                  <span style={{
                    fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 12,
                    background: site.status === 'published' ? 'rgba(34,197,94,0.12)' : 'rgba(245,158,11,0.12)',
                    color: site.status === 'published' ? '#16a34a' : '#d97706',
                  }}>{site.status === 'published' ? 'LIVE' : 'DRAFT'}</span>
                </div>
                <div style={{ color: '#475569', fontSize: 13, marginTop: 6 }}>
                  {site.custom_domain && site.domain_status === 'active'
                    ? site.custom_domain
                    : `${site.slug}.astrovakta.com`}
                  {site.status !== 'published' && ' (visible only to you until published)'}
                </div>
              </div>
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
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 24, overflowX: 'auto', paddingBottom: 4 }}>
              {TABS.map((t) => (
                <button key={t.id} onClick={() => setTab(t.id)} style={{
                  ...ghostBtn, padding: '9px 16px', fontSize: 13, whiteSpace: 'nowrap',
                  background: tab === t.id ? 'rgba(124,58,237,0.15)' : 'transparent',
                  borderColor: tab === t.id ? 'var(--accent-purple)' : 'var(--border-color)',
                  color: tab === t.id ? '#4f46e5' : 'var(--text-primary)',
                }}>
                  <t.icon size={14} /> {t.label}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
                {tab === 'content' && <ContentTab site={site} reload={reload} />}
                {tab === 'design' && <DesignTab site={site} reload={reload} />}
                {tab === 'services' && <ServicesTab site={site} reload={reload} />}
                {tab === 'hours' && <HoursTab site={site} reload={reload} />}
                {tab === 'bookings' && <BookingsTab site={site} />}
                {tab === 'leads' && <LeadsTab site={site} />}
                {tab === 'domain' && <DomainTab site={site} reload={reload} />}
                {tab === 'settings' && <SettingsTab site={site} reload={reload} />}
              </motion.div>
            </AnimatePresence>
          </>
        )}
      </div>
    </div>
  )
}
