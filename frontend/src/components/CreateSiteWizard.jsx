import { useState, useEffect, useRef } from 'react'
import {
  Check, ChevronLeft, Crown, Image as ImageIcon, Loader2, Sparkles, Trash2, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  createMySite, checkSlugAvailability, setMySiteMedia,
} from '../lib/api.js'

// Shared form/button styles and error helper used across the dashboard tabs.
export const inputStyle = {
  width: '100%', padding: '10px 14px', background: '#fff',
  border: '1px solid #e2e8f0', borderRadius: 10, color: '#0f172a',
  fontSize: 14, outline: 'none',
}
export const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 6 }
export const cardStyle = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 16, padding: 24 }
export const primaryBtn = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', background: 'var(--gradient-primary)', color: '#fff', border: 'none', borderRadius: 10, fontWeight: 600, fontSize: 14, cursor: 'pointer' }
export const ghostBtn = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', background: 'transparent', color: '#0f172a', border: '1px solid #e2e8f0', borderRadius: 10, fontWeight: 600, fontSize: 14, cursor: 'pointer' }

// Sites endpoints currently return raw FastAPI bodies ({"detail": ...} on
// errors). ResponseWrapMiddleware exists in app/middleware.py but is not
// registered; if it ever gets enabled, 4xx detail lands inside data instead.
// Accept both shapes.
export const errDetail = (e, fallback = 'Something went wrong — try again') => {
  const d = e?.response?.data
  const msg = d?.data?.detail || d?.detail || d?.message
  return typeof msg === 'string' ? msg : fallback
}

// Shared theme metadata for the site wizard and the design studio.
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

      <div className="wiz-step-body">
        {step === 1 && (
          <div key="s1" className="wiz-step-in"
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
          </div>
        )}

        {step === 2 && (
          <div key="s2" className="wiz-step-in"
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
          </div>
        )}

        {step === 3 && (
          <div key="s3" className="wiz-step-in"
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
          </div>
        )}
      </div>
    </div>
  )
}

export { TEMPLATES, PRESETS, fileToDataUrl, CreateSiteWizard }
