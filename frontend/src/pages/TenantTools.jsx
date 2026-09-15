import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { CalendarDays, ChevronDown, ChevronRight, Gem, Hash, Heart, LogOut, Moon, ScrollText, ShoppingBag, Sparkles, AlertTriangle, CheckCircle2, Loader2, Menu as MenuIcon, X as XIcon, Calendar as CalendarIcon } from 'lucide-react'
import PlaceAutocomplete from '../components/PlaceAutocomplete.jsx'
import { signUpWithEmailAndVerify } from '../lib/firebase.js'
import {
  publicKundliTool, publicKundliFull, publicMatchingTool, publicDoshaTool,
  publicPersonalHoroscope, publicNumerologyTool, publicGemstoneTool, publicMuhuratTool, publicLuckyTool,
  getTenantSession, getMyTenantBookings, getMyTenantOrders,
  cancelMyTenantBooking, cancelMyTenantOrder, publicPlaceOrder,
} from '../lib/api.js'
import { tenantAuthReturnKey } from '../lib/tenant.js'

// ─────────── floating WhatsApp chat button (every public tenant page) ───────────
// Opens a wa.me chat with the astrologer's own number and a starter message.
export function WhatsAppFab({ site, message }) {
  const raw = String(site?.settings?.whatsappNumber || '').replace(/[^\d]/g, '')
  if (!raw) return null
  const href = `https://wa.me/${raw}?text=${encodeURIComponent(message || `Namaste ${site.name || ''}, I want to book a consultation.`.trim())}`
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" title="Chat on WhatsApp" aria-label="Chat on WhatsApp"
      style={{ position: 'fixed', bottom: 22, right: 22, zIndex: 80, textDecoration: 'none' }}>
      {/* pulse ring */}
      <motion.span
        initial={{ opacity: 0 }} animate={{ opacity: [0.55, 0, 0] }} transition={{ duration: 2.2, repeat: Infinity, ease: 'easeOut' }}
        style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: '#16a34a' }} />
      <motion.span
        initial={{ scale: 0, rotate: -30 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: 'spring', stiffness: 260, damping: 16, delay: 0.4 }}
        whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.92 }}
        style={{
          position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center',
          width: 54, height: 54, borderRadius: '50%', background: '#16a34a', color: '#fff',
          boxShadow: '0 8px 24px rgba(22,163,74,0.4)',
        }}>
        <svg width="27" height="27" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
      </motion.span>
    </a>
  )
}


// ─────────── shared header for EVERY public tenant page ───────────
// The astrologer's brand bar: logo, nav links, Tools dropdown (click to
// open, click again or outside to close), Book Now, and the visitor chip.
// Below 840px the links collapse into a hamburger sheet.

const HEADER_TOOLS = [
  ['#/horoscope', 'Horoscope', 'Daily to yearly forecasts'],
  ['#/muhurat', 'Muhurat', 'Auspicious timings'],
  ['#/numerology', 'Numerology', 'Numbers & name analysis'],
  ['#/gemstone', 'Gemstone', 'Stone recommendations'],
  ['#/lucky', 'Lucky Today', 'Numbers, colours & days'],
]

export function TenantHeader({ site, theme, COLORS, showStore, active }) {
  const [toolsOpen, setToolsOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const toolsRef = useRef(null)
  const navRef = useRef(null)
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`

  useEffect(() => {
    const onDoc = (e) => {
      if (toolsRef.current && !toolsRef.current.contains(e.target)) setToolsOpen(false)
      if (navRef.current && !navRef.current.contains(e.target)) setMobileOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const goHash = () => { setToolsOpen(false); setMobileOpen(false) }

  const linkStyle = (href) => ({
    color: active && href === active ? COLORS.text : COLORS.textDim,
    textDecoration: 'none', fontSize: 14, fontWeight: 600,
  })

  const navLinks = (
    <>
      <a href="#/about" style={linkStyle('#/about')}>About</a>
      <a href="#/services" style={linkStyle('#/services')}>Services</a>
      {showStore && <a href="#/shop" style={linkStyle('#/shop')}>Shop</a>}
      <a href="#/kundli" style={linkStyle('#/kundli')}>Free Kundli</a>
      <a href="#/matching" style={linkStyle('#/matching')}>Match Making</a>
      <div ref={toolsRef} style={{ position: 'relative' }}>
        <button type="button" onClick={() => setToolsOpen((o) => !o)}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 14, fontWeight: 600, color: COLORS.textDim }}>
          Tools
          <ChevronDown size={14} style={{ transform: toolsOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
        </button>
        {toolsOpen && (
          <div style={{
            position: 'absolute', top: 'calc(100% + 10px)', left: 0, zIndex: 100, minWidth: 230,
            background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 14,
            boxShadow: '0 16px 40px rgba(0,0,0,0.18)', padding: 8, overflow: 'hidden',
          }}>
            {HEADER_TOOLS.map(([href, label, hint]) => (
              <a key={href} href={href} onClick={goHash}
                style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '9px 12px', borderRadius: 10, textDecoration: 'none' }}>
                <span style={{ fontSize: 14, fontWeight: 700, color: COLORS.text }}>{label}</span>
                <span style={{ fontSize: 11.5, color: COLORS.textDim }}>{hint}</span>
              </a>
            ))}
          </div>
        )}
      </div>
      <VisitorChip site={site} COLORS={COLORS} theme={theme} />
      <a href="#book" onClick={goHash} style={{
        padding: '9px 20px', borderRadius: 10, background: gradient, color: '#fff', textDecoration: 'none',
        display: 'flex', alignItems: 'center', gap: 6,
      }}><CalendarIcon size={15} /> Book Now</a>
    </>
  )

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 90,
      background: theme.bgStyle === 'light' ? 'rgba(255,255,255,0.85)' : 'rgba(10,10,26,0.85)',
      backdropFilter: 'blur(12px)', borderBottom: `1px solid ${COLORS.border}`,
    }}>
      {/* hamburger — screens narrower than the full nav */}
      <div className="tenant-header-hamburger" style={{ display: 'none', padding: '12px 16px', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <a href="#top" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', color: COLORS.text }}>
          <BrandMark site={site} gradient={gradient} />
          <div>
            <div style={{ fontWeight: 800, fontSize: 15 }}>{site?.name}</div>
            {site?.tagline && <div style={{ fontSize: 10.5, opacity: 0.6 }}>{site.tagline}</div>}
          </div>
        </a>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <a href="#book" onClick={goHash} style={{ padding: '8px 14px', borderRadius: 9, background: gradient, color: '#fff', textDecoration: 'none', fontWeight: 700, fontSize: 13 }}>
            Book Now
          </a>
          <button type="button" onClick={() => setMobileOpen((o) => !o)} aria-label="Menu"
            style={{ background: 'none', border: `1px solid ${COLORS.border}`, borderRadius: 9, padding: 7, cursor: 'pointer', color: COLORS.text, display: 'flex' }}>
            {mobileOpen ? <XIcon size={18} /> : <MenuIcon size={18} />}
          </button>
        </div>
      </div>

      {/* desktop bar */}
      <div className="tenant-header-desktop" style={{ maxWidth: 1000, margin: '0 auto', padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <a href="#top" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', color: COLORS.text }}>
          <BrandMark site={site} gradient={gradient} />
          <div>
            <div style={{ fontWeight: 800, fontSize: 16 }}>{site?.name}</div>
            {site?.tagline && <div style={{ fontSize: 11, opacity: 0.6 }}>{site.tagline}</div>}
          </div>
        </a>
        <nav style={{ display: 'flex', gap: 18, alignItems: 'center', fontSize: 14, fontWeight: 600 }}>
          {navLinks}
        </nav>
      </div>

      {/* mobile sheet */}
      {mobileOpen && (
        <div ref={navRef} style={{
          padding: '10px 16px 18px', display: 'flex', flexDirection: 'column', gap: 4,
          borderTop: `1px solid ${COLORS.border}`, background: theme.bgStyle === 'light' ? 'rgba(255,255,255,0.97)' : 'rgba(10,10,26,0.97)',
        }}>
          {[['#/about', 'About'], ['#/services', 'Services'], ...(showStore ? [['#/shop', 'Shop']] : []), ['#/kundli', 'Free Kundli'], ['#/matching', 'Match Making']].map(([href, label]) => (
            <a key={href} href={href} onClick={goHash} style={{ ...linkStyle(href), padding: '10px 4px', borderBottom: `1px solid ${COLORS.border}` }}>{label}</a>
          ))}
          <div style={{ padding: '10px 4px 2px', fontWeight: 800, fontSize: 12, letterSpacing: 0.6, color: COLORS.textDim }}>TOOLS</div>
          {HEADER_TOOLS.map(([href, label]) => (
            <a key={href} href={href} onClick={goHash} style={{ ...linkStyle(href), padding: '10px 4px', borderBottom: `1px solid ${COLORS.border}` }}>{label}</a>
          ))}
          <div style={{ padding: '12px 4px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <VisitorChip site={site} COLORS={COLORS} theme={theme} />
            <a href="#book" onClick={goHash} style={{
              padding: '9px 20px', borderRadius: 10, background: gradient, color: '#fff', textDecoration: 'none',
              display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, fontSize: 14,
            }}><CalendarIcon size={15} /> Book Now</a>
          </div>
        </div>
      )}
      <style>{`@media (max-width: 840px) {
        .tenant-header-desktop { display: none !important; }
        .tenant-header-hamburger { display: flex !important; }
      }`}</style>
    </header>
  )
}

function BrandMark({ site, gradient }) {
  if (site?.logo_url) {
    return <img src={site.logo_url} alt={site.name} style={{ width: 38, height: 38, borderRadius: 12, objectFit: 'cover' }} />
  }
  return (
    <div style={{ width: 38, height: 38, borderRadius: 12, background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 16 }}>
      {(site?.name || 'A').charAt(0)}
    </div>
  )
}

// Visitor sign-in chip / avatar in the header (shared across all pages).
function VisitorChip({ site, COLORS, theme }) {
  const slug = site?.slug
  const [session, setSession] = useState(() => getTenantSession(slug))
  if (!slug) return null
  if (!session) {
    return <a href="#/signin" style={{ textDecoration: 'none', fontSize: 14, fontWeight: 600, color: COLORS.textDim }}>Sign in</a>
  }
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 13.5, fontWeight: 600, color: COLORS.text }}>
      <a href="#/account" title="My account — consultations & orders"
        style={{ display: 'inline-flex', alignItems: 'center', gap: 8, textDecoration: 'none', color: COLORS.text }}>
        <span style={{ width: 26, height: 26, borderRadius: '50%', background: theme.primaryColor, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800 }}>
          {(session.user?.name || session.user?.email || '?').trim().charAt(0).toUpperCase()}
        </span>
        <span style={{ maxWidth: 90, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{session.user?.name || session.user?.email}</span>
      </a>
      <button onClick={() => { localStorage.removeItem(`tenantAuth_${slug}`); setSession(null) }}
        style={{ background: 'none', border: 'none', color: COLORS.textDim, cursor: 'pointer', fontSize: 12.5, textDecoration: 'underline', padding: 0 }}>
        Sign out
      </button>
    </span>
  )
}

// ─────────── shared bits for tenant tool pages ───────────
const errText = (e) => {
  const d = e?.response?.data
  const msg = d?.data?.detail || d?.detail || d?.message
  return (typeof msg === 'string' && msg) || 'Something went wrong — please try again'
}

function ToolShell({ site, COLORS, gradient, theme, showStore, active, title, subtitle, icon: Icon, children }) {
  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <TenantHeader site={site} theme={theme} COLORS={COLORS} showStore={showStore} active={active} />
      <main style={{ maxWidth: 900, margin: '0 auto', padding: '36px 18px 90px' }}>
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <h1 style={{ fontSize: 32, fontWeight: 900, letterSpacing: '-0.5px', margin: '0 0 10px' }}>{title}</h1>
          <p style={{ color: COLORS.textDim, fontSize: 15, lineHeight: 1.7, maxWidth: 560, margin: '0 auto' }}>{subtitle}</p>
        </div>
        {children}
      </main>
      <WhatsAppFab site={site} />
    </div>
  )
}
const theme_color = (gradient) => gradient.match(/#[0-9a-f]{3,8}/i)?.[0] || '#4f46e5'

const inputStyle = {
  width: '100%', padding: '11px 14px', borderRadius: 10, fontSize: 14,
  border: '1px solid rgba(127,127,127,0.35)', background: 'rgba(127,127,127,0.05)',
  color: 'inherit', outline: 'none',
}
const labelStyle = { display: 'block', fontSize: 12, fontWeight: 700, color: 'inherit', opacity: 0.65, marginBottom: 5 }

// ─────────── birth date / time selectors ───────────
// Dropdown-based pickers (Day–Month–Year and Hour–Minute–AM/PM) so every
// visitor gets the same, familiar selector on phone and desktop. The form
// keeps storing machine formats: date 'YYYY-MM-DD', time 'HH:MM' (24h).

const MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTHS_FULL = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

const fmtDate = (iso) => {
  if (!iso) return '—'
  const [y, m, d] = String(iso).slice(0, 10).split('-').map(Number)
  if (!y || !m || !d) return iso
  return `${d} ${MONTHS_SHORT[m - 1]} ${y}`
}

const fmtTime = (iso) => {
  if (!iso) return '—'
  const [h, m] = String(iso).slice(0, 5).split(':').map(Number)
  if (Number.isNaN(h)) return iso
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}

function Sel({ value, onChange, placeholder, options, style }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} style={{ ...inputStyle, padding: '11px 8px', cursor: 'pointer', ...style }}>
      <option value="">{placeholder}</option>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

// Dropdowns fire one part at a time, so keep the chosen parts in local state
// and only push the composed value up once the date is complete; resetting
// on every partial change made the selects snap back to their placeholder.
function DateSelector({ value, onChange }) {
  const parse = (v) => {
    const [y, m, d] = v ? v.split('-').map(Number) : [null, null, null]
    return { y: y || null, m: m || null, d: d || null }
  }
  const [parts, setParts] = useState(parse(value))
  useEffect(() => { setParts(parse(value)) }, [value])
  const thisYear = new Date().getFullYear()
  const years = []
  for (let v = thisYear; v >= 1900; v--) years.push(v)
  const maxDay = parts.y && parts.m ? new Date(parts.y, parts.m, 0).getDate() : 31
  const set = (y, m, d) => {
    const p = { y: y || null, m: m || null, d: d || null }
    if (p.y && p.m && p.d) p.d = Math.min(p.d, new Date(p.y, p.m, 0).getDate())
    setParts(p)
    onChange(p.y && p.m && p.d ? `${p.y}-${String(p.m).padStart(2, '0')}-${String(p.d).padStart(2, '0')}` : '')
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr 1.1fr', gap: 8 }}>
      <Sel placeholder="Day" value={parts.d || ''} options={Array.from({ length: maxDay }, (_, i) => ({ value: i + 1, label: i + 1 }))} onChange={(v) => set(parts.y, parts.m, v === '' ? null : Number(v))} />
      <Sel placeholder="Month" value={parts.m || ''} options={MONTHS_FULL.map((nm, i) => ({ value: i + 1, label: nm }))} onChange={(v) => set(parts.y, v === '' ? null : Number(v), parts.d)} />
      <Sel placeholder="Year" value={parts.y || ''} options={years.map((v) => ({ value: v, label: v }))} onChange={(v) => set(v === '' ? null : Number(v), parts.m, parts.d)} />
    </div>
  )
}

function TimeSelector({ value, onChange }) {
  const parse = (v) => {
    if (!v) return { h: null, m: null, ap: '' }
    const [H, M] = v.split(':').map(Number)
    return { h: H % 12 || 12, m: M, ap: H < 12 ? 'AM' : 'PM' }
  }
  const [parts, setParts] = useState(parse(value))
  useEffect(() => { setParts(parse(value)) }, [value])
  const set = (h, m, ap) => {
    const p = { h: h || null, m, ap: ap || '' }
    setParts(p)
    if (p.h && p.m != null && p.ap) {
      const H = p.ap === 'PM' ? (p.h % 12) + 12 : p.h % 12
      onChange(`${String(H).padStart(2, '0')}:${String(p.m).padStart(2, '0')}`)
    } else onChange('')
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.1fr', gap: 8 }}>
      <Sel placeholder="Hour" value={parts.h || ''} options={Array.from({ length: 12 }, (_, i) => ({ value: i + 1, label: String(i + 1).padStart(2, '0') }))} onChange={(v) => set(v === '' ? null : Number(v), parts.m, parts.ap)} />
      <Sel placeholder="Min" value={parts.m == null ? '' : parts.m} options={Array.from({ length: 60 }, (_, i) => ({ value: i, label: String(i).padStart(2, '0') }))} onChange={(v) => set(parts.h, v === '' ? null : Number(v), parts.ap)} />
      <Sel placeholder="AM/PM" value={parts.ap} options={[{ value: 'AM', label: 'AM' }, { value: 'PM', label: 'PM' }]} onChange={(v) => set(parts.h, parts.m, v)} />
    </div>
  )
}

function BirthFields({ value, onChange }) {
  const set = (k, v) => onChange({ ...value, [k]: v })
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
      <div>
        <label style={labelStyle}>Birth date *</label>
        <DateSelector value={value.date} onChange={(v) => set('date', v)} />
      </div>
      <div>
        <label style={labelStyle}>Birth time *</label>
        <TimeSelector value={value.time} onChange={(v) => set('time', v)} />
      </div>
      <div style={{ gridColumn: '1 / -1' }}>
        <label style={labelStyle}>Birth place *</label>
        <PlaceAutocomplete inputStyle={inputStyle} placeholder="Start typing and pick your city"
          onSelect={(sel) => onChange({ ...value, place: sel?.label || '', lat: sel?.lat, lon: sel?.lon, tz: sel?.tz })} />
      </div>
    </div>
  )
}

// Languages the API can translate the report into (app/i18n/languages.py).
const LANGUAGES = [
  ['en', 'English'],
  ['hi', 'हिन्दी (Hindi)'],
  ['ta', 'தமிழ் (Tamil)'],
  ['te', 'తెలుగు (Telugu)'],
  ['kn', 'ಕನ್ನಡ (Kannada)'],
  ['ml', 'മലയാളം (Malayalam)'],
  ['bn', 'বাংলা (Bengali)'],
  ['mr', 'मराठी (Marathi)'],
  ['gu', 'ગુજરાતી (Gujarati)'],
  ['pa', 'ਪੰਜਾਬੀ (Punjabi)'],
]

function LangSelect({ value, onChange }) {
  return (
    <div>
      <label style={labelStyle}>Report language</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} style={{ ...inputStyle, cursor: 'pointer' }}>
        {LANGUAGES.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
      </select>
    </div>
  )
}

// ─────────── DETAILED KUNDLI PAGE (#/kundli) ───────────
export function KundliPage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [form, setForm] = useState({ name: '', phone: '', date: '', time: '', place: '', lat: null, lon: null, tz: null, lang: 'en' })
  const [result, setResult] = useState(null)
  const [full, setFull] = useState(null)
  const [dosha, setDosha] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  // Prefill from the landing-page mini form
  useEffect(() => {
    try {
      const pre = JSON.parse(sessionStorage.getItem('kundli_prefill') || 'null')
      if (pre) { setForm((f) => ({ ...f, ...pre })); sessionStorage.removeItem('kundli_prefill') }
    } catch { /* ignore */ }
  }, [])

  // Every field matters — the chart can't be cast without it.
  const validate = () => {
    if (!form.name.trim()) return 'Please enter your name'
    const digits = form.phone.replace(/\D/g, '')
    const local = digits.replace(/^91(?=\d{10}$)/, '').replace(/^0(?=\d{10}$)/, '')
    if (!/^[6-9]\d{9}$/.test(local)) return 'Please enter a valid 10-digit mobile number'
    if (!form.date) return 'Please select your birth date'
    if (!form.time) return 'Please select your birth time'
    if (form.lat == null || form.lon == null) return 'Please select your birth place from the suggestions'
    return null
  }

  const submit = async (e) => {
    e.preventDefault()
    const problem = validate()
    if (problem) { setError(problem); return }
    setBusy(true); setError(null)
    try {
      const payload = {
        name: form.name.trim(),
        phone: form.phone.trim(),
        date: form.date, time: form.time,
        place: (form.place || undefined),
        lat: form.lat ?? undefined, lon: form.lon ?? undefined, tz: form.tz || undefined,
        detail: true,
        chart_theme: theme.bgStyle === 'dark' ? 'dark' : 'light',
        lang: form.lang,
      }
      const res = await publicKundliFull(resolve, payload)
      setResult(res.core)
      setFull(res)
      publicDoshaTool(resolve, {
        date: form.date, time: form.time,
        lat: form.lat ?? undefined, lon: form.lon ?? undefined, tz: form.tz || undefined,
        lang: form.lang,
      }).then(setDosha).catch(() => setDosha(null))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/kundli" icon={ScrollText}
      title="Free Kundli" subtitle={`Complete Vedic birth chart with lagna, planets, dasha and dosha analysis — computed on a professional Swiss-ephemeris engine, presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
            <div><label style={labelStyle}>Your name *</label>
              <input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Full name" style={inputStyle} /></div>
            <div><label style={labelStyle}>Mobile number *</label>
              <input type="tel" inputMode="numeric" maxLength={15} value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="10-digit mobile (WhatsApp)" style={inputStyle} /></div>
          </div>
          <BirthFields value={form} onChange={setForm} />
          <LangSelect value={form.lang} onChange={(v) => set('lang', v)} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: '14px' }}>
            {busy ? 'Calculating…' : 'Generate Detailed Kundli'}
          </button>
          {busy && <div style={{ fontSize: 12.5, color: COLORS.textDim, textAlign: 'center' }}>
            Casting the chart and analysing dashas, divisional charts & Lal Kitab — this can take a few seconds.
          </div>}
        </motion.form>
      ) : (
        <KundliResult result={result} dosha={dosha} full={full} theme={theme} COLORS={COLORS}
          onBack={() => { setResult(null); setFull(null); setDosha(null) }} site={site}
          birth={{ name: form.name, phone: form.phone, date: form.date, time: form.time, place: form.place }} />
      )}
    </ToolShell>
  )
}

function Section({ title, COLORS, children }) {
  return (
    <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 22, marginBottom: 16 }}>
      <h3 style={{ fontSize: 13, fontWeight: 800, letterSpacing: 0.8, color: COLORS.textDim, margin: '0 0 14px', textTransform: 'uppercase' }}>{title}</h3>
      {children}
    </div>
  )
}

// ─────────── kundli result presentation ───────────

const LORD_COLORS = { Sun: '#f59e0b', Moon: '#94a3b8', Mars: '#ef4444', Mercury: '#10b981', Jupiter: '#eab308', Venus: '#f472b6', Saturn: '#64748b', Rahu: '#3b82f6', Ketu: '#8b5cf6' }
const TODAY = new Date().toISOString().slice(0, 10)
const inRange = (from, to) => !!from && !!to && String(from).slice(0, 10) <= TODAY && TODAY < String(to).slice(0, 10)

const VARGAS = {
  D2: ['Hora', 'Wealth & finances'], D3: ['Drekkana', 'Siblings & courage'],
  D4: ['Chaturthamsa', 'Property, home & fortune'], D7: ['Saptamsa', 'Children & progeny'],
  D9: ['Navamsa', 'Marriage, spouse & dharma'], D10: ['Dashamsa', 'Career & profession'],
  D12: ['Dwadasamsa', 'Parents & ancestry'], D16: ['Shodasamsa', 'Vehicles & comforts'],
  D20: ['Vimsamsa', 'Spirituality & devotion'], D24: ['Siddhamsa', 'Education & learning'],
  D27: ['Nakshatramsa', 'Strengths & weaknesses'], D30: ['Trimshamsa', 'Challenges & mishaps'],
  D40: ['Khavedamsa', 'Maternal legacy & merit'], D45: ['Akshavedamsa', 'Paternal legacy & character'],
  D60: ['Shashtiamsa', 'Past-life karma — the finest division'],
}

const grahan_present = (g) => g?.grahanPresent ?? g?.present ?? false
const shrapit_present = (s) => s?.shrapitPresent ?? s?.present ?? false

const chipsWrap = { display: 'flex', flexWrap: 'wrap', gap: 6 }
const chipStyle = (COLORS) => ({
  fontSize: 11.5, fontWeight: 600, padding: '3px 9px', borderRadius: 999,
  border: `1px solid ${COLORS.border}`, background: 'rgba(127,127,127,0.07)', color: COLORS.textDim,
})
const Remedies = ({ v, COLORS }) => {
  if (!v) return null
  const items = (Array.isArray(v) ? v : [String(v)]).filter(Boolean)
  if (!items.length) return null
  return <div style={chipsWrap}>{items.map((r, i) => <span key={i} style={chipStyle(COLORS)}>{r}</span>)}</div>
}

const Stat = ({ k, v, sub, COLORS }) => (
  <div style={{ padding: 12, background: 'rgba(127,127,127,0.06)', borderRadius: 10 }}>
    <div style={{ fontSize: 11, color: COLORS.textDim, fontWeight: 600 }}>{k}</div>
    <div style={{ fontWeight: 800, fontSize: 15 }}>{v || '—'}</div>
    {sub && <div style={{ fontSize: 11.5, color: COLORS.textDim, marginTop: 2 }}>{sub}</div>}
  </div>
)

// ── collapsible dasha tree ──
function DashaTree({ nodes, COLORS }) {
  const [open, setOpen] = useState(() => {
    const o = {}
    const walk = (list) => list.forEach((n) => { o[n.id] = (n.depth < 2 || n.childActive); if (n.children?.length) walk(n.children) })
    walk(nodes); return o
  })
  const toggle = (id) => setOpen((s) => ({ ...s, [id]: !s[id] }))
  const setAll = (v) => {
    const o = {}
    const walk = (list) => list.forEach((n) => { o[n.id] = v; if (n.children?.length) walk(n.children) })
    walk(nodes); setOpen(o)
  }
  const anyClosed = nodes.some((n) => !open[n.id])

  const Row = ({ n }) => (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', padding: '7px 10px', borderRadius: 10, marginBottom: 4,
        background: n.active ? `color-mix(in srgb, ${n.color} 13%, transparent)` : 'transparent',
        border: `1px solid ${n.active ? `${n.color}55` : 'transparent'}`,
      }}>
        {n.children?.length
          ? <button onClick={() => toggle(n.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: COLORS.textDim, padding: 2, display: 'flex' }}>
              {open[n.id] ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </button>
          : <span style={{ width: 19, textAlign: 'center', color: n.color, fontSize: 14 }}>•</span>}
        <span style={{ width: 9, height: 9, borderRadius: '50%', background: n.color, flexShrink: 0 }} />
        <span style={{ fontWeight: 700, fontSize: 13.5 }}>{n.name}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.textDim, background: 'rgba(127,127,127,0.1)', padding: '2px 7px', borderRadius: 6 }}>{n.tag}</span>
        {n.active && <span style={{ fontSize: 10.5, fontWeight: 800, color: '#fff', background: n.color, padding: '2px 8px', borderRadius: 999 }}>RUNNING NOW</span>}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: COLORS.textDim, whiteSpace: 'nowrap' }}>{fmtDate(n.from)} – {fmtDate(n.to)}</span>
      </div>
      {n.note && <div style={{ fontSize: 12, color: COLORS.textDim, lineHeight: 1.5, margin: '-2px 0 6px 36px' }}>{n.note}</div>}
      {open[n.id] && n.children?.length > 0 && (
        <div style={{ marginLeft: 18, borderLeft: `1.5px dashed ${COLORS.border}`, paddingLeft: 10 }}>
          {n.children.map((c) => <Row key={c.id} n={c} />)}
        </div>
      )}
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginBottom: 10 }}>
        <button onClick={() => setAll(true)} style={{ ...inputStyle, width: 'auto', padding: '6px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>Expand all</button>
        <button onClick={() => setAll(false)} disabled={!anyClosed} style={{ ...inputStyle, width: 'auto', padding: '6px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer', opacity: anyClosed ? 1 : 0.4 }}>Collapse all</button>
      </div>
      {nodes.map((n) => <Row key={n.id} n={n} />)}
      <div style={{ fontSize: 11.5, color: COLORS.textDim, marginTop: 10, lineHeight: 1.6 }}>
        MD = Mahadasha (major period) · AD = Antardasha (sub-period) · PD = Pratyantardasha (sub-sub-period). Tap a row to open or close its sub-periods.
      </div>
    </div>
  )
}

// ── per-system tree builders ──
const systemBuilders = [
  (full, lc) => {
    const md = full?.vimshottari?.mahadashas
    if (!Array.isArray(md) || !md.length) return null
    const walk = (list, level, prefix) => (list || []).map((n, i) => ({
      id: `${prefix}${i}`, name: n.planet,
      tag: level === 0 ? 'MD' : level === 1 ? 'AD' : 'PD',
      from: n.startDate, to: n.endDate, color: lc(n.planet), depth: level,
      children: level < 2 ? walk(level === 0 ? n.antardasha : n.pratyantardasha, level + 1, `${prefix}${i}-`) : [],
    }))
    return { key: 'vimshottari', label: 'Vimshottari', desc: 'The classical 120-year cycle — the most widely used dasha system, counted from the Moon nakshatra at birth.', nodes: walk(md, 0, 'v') }
  },
  (full, lc) => {
    const y = full?.yogini?.data
    if (!y?.mahadashas?.length) return null
    return {
      key: 'yogini', label: 'Yogini',
      desc: `36-year Yogini cycle — begins with ${y.startYogini} Yogini (Moon in ${y.moonNakshatra} nakshatra).`,
      nodes: y.mahadashas.map((m, i) => ({
        id: `y${i}`, name: m.yogini, tag: `Yogini · lord ${m.rulingPlanet}`,
        from: m.startDate, to: m.endDate, color: lc(m.rulingPlanet), depth: 0,
        note: [m.nature, m.description].filter(Boolean).join(' — '), children: [],
      })),
    }
  },
  (full, lc) => {
    const a = full?.ashtottari?.data
    if (!a?.mahadashas?.length) return null
    return {
      key: 'ashtottari', label: 'Ashtottari',
      desc: `108-year Ashtottari cycle — begins with ${a.startLord} (Moon in ${a.moonNakshatra} nakshatra).`,
      nodes: a.mahadashas.map((m, i) => ({
        id: `a${i}`, name: m.lord, tag: `MD · cycle ${m.cycle} · ${m.years} yr`,
        from: m.startDate, to: m.endDate, color: lc(m.lord), depth: 0, children: [],
      })),
    }
  },
  (full, lc) => {
    const k = full?.kalachakra?.data
    if (!k?.mahadashas?.length) return null
    return {
      key: 'kalachakra', label: 'Kalachakra',
      desc: `Kalachakra dasha — counted from the Moon's nakshatra pada (${k.moonPada}) in ${k.moonSign}.`,
      nodes: k.mahadashas.map((m, i) => ({
        id: `k${i}`, name: m.lord, tag: `MD · ${m.years} yr`,
        from: m.startDate, to: m.endDate, color: lc(m.lord), depth: 0, children: [],
      })),
    }
  },
  (full, lc) => {
    const c = full?.chara?.data
    if (!c?.mahadashas?.length) return null
    const walk = (list, level, prefix) => (list || []).map((n, i) => ({
      id: `${prefix}${i}`, name: n.sign,
      tag: level === 0 ? `MD · lord ${n.lord}` : level === 1 ? 'AD' : 'PD',
      from: n.startDate, to: n.endDate, color: lc(n.lord), depth: level,
      children: level < 2 ? walk(level === 0 ? n.antardasha : n.pratyantar, level + 1, `${prefix}${i}-`) : [],
    }))
    return {
      key: 'chara', label: 'Chara (Jaimini)',
      desc: 'Jaimini Chara dasha — sign-based periods starting from the ascendant sign.',
      nodes: walk(c.mahadashas, 0, 'c'),
    }
  },
]

function DashaSystems({ full, theme, COLORS }) {
  const lordColor = (lord) => LORD_COLORS[lord] || theme.primaryColor
  const systems = systemBuilders.map((f) => f(full, lordColor)).filter(Boolean)
  const [sel, setSel] = useState(systems[0]?.key)
  const sys = systems.find((s) => s.key === sel) || systems[0]
  if (!sys) return null
  // Flag the running period (and its ancestors) so the tree auto-expands to it.
  const markActive = (n) => {
    n.active = inRange(n.from, n.to)
    n.childActive = (n.children || []).some(markActive)
    return n.active || n.childActive
  }
  sys.nodes.forEach(markActive)
  return (
    <Section title="All Dasha Systems" COLORS={COLORS}>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        {systems.map((s) => (
          <button key={s.key} onClick={() => setSel(s.key)} style={{
            padding: '7px 14px', borderRadius: 999, fontSize: 12.5, fontWeight: 700, cursor: 'pointer',
            border: `1.5px solid ${sys.key === s.key ? theme.primaryColor : COLORS.border}`,
            background: sys.key === s.key ? theme.primaryColor : 'transparent',
            color: sys.key === s.key ? '#fff' : COLORS.text,
          }}>{s.label}</button>
        ))}
      </div>
      {sys.desc && <p style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6, margin: '0 0 14px' }}>{sys.desc}</p>}
      <DashaTree key={sys.key} nodes={sys.nodes} COLORS={COLORS} />
    </Section>
  )
}

// ── divisional charts ──
function VargaView({ entries, theme, COLORS }) {
  const [open, setOpen] = useState(() => Object.fromEntries(entries.map((e) => [e.d, e.d === '9'])))
  const allOpen = entries.every((e) => open[e.d])
  const toggleAll = () => setOpen(Object.fromEntries(entries.map((e) => [e.d, !allOpen])))
  return (
    <Section title="Divisional Charts (Varga Kundli)" COLORS={COLORS}>
      <p style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6, margin: '0 0 14px' }}>
        Each varga chart divides the zodiac finely to zoom into one area of life — marriage, career, education and more.
        The D1 birth chart is shown under the “Kundli Chart” tab.
      </p>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginBottom: 12 }}>
        <button onClick={toggleAll} style={{ ...inputStyle, width: 'auto', padding: '6px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
          {allOpen ? 'Collapse all' : 'Expand all'}
        </button>
      </div>
      {entries.map((e) => {
        const [name, focus] = VARGAS[`D${e.d}`] || [`D${e.d}`, '']
        const isOpen = open[e.d]
        return (
          <div key={e.d} style={{ border: `1px solid ${COLORS.border}`, borderRadius: 12, marginBottom: 10, overflow: 'hidden' }}>
            <button onClick={() => setOpen((s) => ({ ...s, [e.d]: !s[e.d] }))}
              style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '12px 14px', background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit', textAlign: 'left' }}>
              {isOpen ? <ChevronDown size={16} color={COLORS.textDim} /> : <ChevronRight size={16} color={COLORS.textDim} />}
              <span style={{ fontWeight: 800, fontSize: 14 }}>D{e.d} — {e.chart?.name || name}</span>
              <span style={{ fontSize: 12, color: COLORS.textDim }}>· {e.chart?.focus || focus}</span>
              {e.chart?.ascendant?.sign && <span style={{ marginLeft: 'auto', fontSize: 12, color: COLORS.textDim, whiteSpace: 'nowrap' }}>Asc: {e.chart.ascendant.sign}</span>}
            </button>
            {isOpen && (
              <div style={{ padding: '0 14px 16px' }}>
                <div style={{ maxWidth: 460, color: COLORS.text }} dangerouslySetInnerHTML={{ __html: e.svg }} />
              </div>
            )}
          </div>
        )
      })}
    </Section>
  )
}

// ── KP & extras ──
const SEVERITY_COLOR = { High: '#dc2626', Medium: '#d97706', Low: '#16a34a', None: '#16a34a' }

function KpExtras({ full, theme, COLORS, site }) {
  const kp = full?.kpRulingPlanets && !full.kpRulingPlanets.error ? (full.kpRulingPlanets.data || full.kpRulingPlanets) : null
  const dh = full?.dhaiya && !full.dhaiya.error ? (full.dhaiya.data || full.dhaiya) : null
  const extraDoshas = full?.doshaCompute && !full.doshaCompute.error
    ? (Array.isArray(full.doshaCompute.data) ? full.doshaCompute.data : []) : []
  if (!kp && !dh && !extraDoshas.length) return null
  return (
    <>
      {kp && (
        <Section title="KP Astrology — Ruling Planets" COLORS={COLORS}>
          <p style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6, margin: '0 0 14px' }}>
            In KP (Krishnamurti Paddhati), a small set of “ruling planets” taken from the ascendant, the Moon and the weekday
            is used for precise predictions, muhurat (electional) and prashna (horary) charts.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 10, marginBottom: 16 }}>
            <Stat k="Ascendant (Lagna)" v={kp.ascendant?.sign} sub={kp.ascendant ? `Lord ${kp.ascendant.lord} · Star ${kp.ascendant.starLord} · Sub ${kp.ascendant.subLord}` : ''} COLORS={COLORS} />
            <Stat k="Moon" v={kp.moon?.sign} sub={kp.moon ? `Lord ${kp.moon.signLord} · Star ${kp.moon.starLord} · Sub ${kp.moon.subLord}` : ''} COLORS={COLORS} />
            <Stat k="Day at birth" v={kp.day?.weekday} sub={kp.day ? `Day lord: ${kp.day.lord}` : ''} COLORS={COLORS} />
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
              <thead><tr>{['Planet', 'Role', 'Sign', 'House', 'Star Lord', 'Sub Lord', 'Notes'].map((h) => (
                <th key={h} style={{ textAlign: 'left', padding: '8px 10px', borderBottom: `1px solid ${COLORS.border}`, fontSize: 11, color: COLORS.textDim, whiteSpace: 'nowrap' }}>{h}</th>
              ))}</tr></thead>
              <tbody>
                {(kp.rulingPlanets || []).map((r, i) => (
                  <tr key={i}>
                    <td style={{ padding: '8px 10px', fontWeight: 700, whiteSpace: 'nowrap' }}>
                      <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: LORD_COLORS[r.planet] || theme.primaryColor, marginRight: 7 }} />
                      {r.planet}
                    </td>
                    <td style={{ padding: '8px 10px', color: COLORS.textDim }}>{r.role}</td>
                    <td style={{ padding: '8px 10px' }}>{r.sign || '—'}</td>
                    <td style={{ padding: '8px 10px' }}>{r.house || '—'}</td>
                    <td style={{ padding: '8px 10px' }}>{r.starLord || '—'}</td>
                    <td style={{ padding: '8px 10px' }}>{r.subLord || '—'}</td>
                    <td style={{ padding: '8px 10px', color: COLORS.textDim, fontSize: 11.5 }}>
                      {[r.isRetrograde && 'retrograde', r.isCombust && 'combust', r.houseStatus].filter(Boolean).join(' · ') || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {dh && (
        <Section title="Sade Sati & Dhaiya — Saturn Transit" COLORS={COLORS}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
            <span style={{ fontWeight: 800, fontSize: 16 }}>{dh.currentStatus?.phase || 'Status unavailable'}</span>
            {dh.currentStatus?.severity && (
              <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', background: SEVERITY_COLOR[dh.currentStatus.severity] || theme.primaryColor, padding: '3px 10px', borderRadius: 999 }}>
                {dh.currentStatus.severity}
              </span>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10, marginBottom: 14 }}>
            <Stat k="Your Moon sign" v={dh.moonSign} COLORS={COLORS} />
            <Stat k="Saturn transiting" v={dh.saturnSign} COLORS={COLORS} />
            <Stat k="Distance from Moon" v={dh.signsFromMoon != null ? `${dh.signsFromMoon} sign${dh.signsFromMoon === 1 ? '' : 's'}` : '—'} COLORS={COLORS} />
          </div>
          {dh.currentStatus?.description && <p style={{ fontSize: 13.5, lineHeight: 1.7, margin: '0 0 12px' }}>{dh.currentStatus.description}</p>}
          {dh.currentStatus?.remedies?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 0.5, color: COLORS.textDim, marginBottom: 6 }}>SUGGESTED REMEDIES</div>
              <Remedies v={dh.currentStatus.remedies} COLORS={COLORS} />
            </div>
          )}
          {dh.generalAdvice && <p style={{ fontSize: 12.5, color: COLORS.textDim, lineHeight: 1.6, margin: 0 }}>{dh.generalAdvice}</p>}
        </Section>
      )}

      {extraDoshas.length > 0 && (
        <Section title="Dosha Scan — Yogas to Know" COLORS={COLORS}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {extraDoshas.map((d, i) => (
              <div key={i} style={{ padding: 13, borderRadius: 12, border: `1px solid ${COLORS.border}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                  {d.present ? <AlertTriangle size={16} color="#dc2626" /> : <CheckCircle2 size={16} color="#16a34a" />}
                  <span style={{ fontWeight: 800, fontSize: 14 }}>{d.name}</span>
                  {d.present
                    ? <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', background: SEVERITY_COLOR[d.severity] || '#dc2626', padding: '2px 9px', borderRadius: 999 }}>{d.severity || 'Present'}</span>
                    : <span style={{ fontSize: 11, fontWeight: 700, color: '#16a34a' }}>Not present</span>}
                </div>
                {d.description && <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6, marginBottom: d.present && d.remedies?.length ? 8 : 0 }}>{d.description}</div>}
                {d.present && d.remedies?.length > 0 && <Remedies v={d.remedies} COLORS={COLORS} />}
              </div>
            ))}
          </div>
          <div style={{ fontSize: 12.5, color: COLORS.textDim, marginTop: 10 }}>
            Manglik, Grahan and Shrapit doshas are covered in the “Dosha Report” tab. For a detailed personal reading, book a consultation with {site?.name || 'the astrologer'}.
          </div>
        </Section>
      )}
    </>
  )
}

// ── Lal Kitab ──
function LalKitabView({ lk, COLORS }) {
  if (!lk) return null
  return (
    <>
      <Section title="Lal Kitab Reading" COLORS={COLORS}>
        <p style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6, margin: '0 0 12px' }}>
          Lal Kitab (the Red Book) reads planets through their house placement and prescribes simple, practical remedies (upay).
        </p>
        {lk.ascendant && (
          <div style={{ display: 'inline-flex', gap: 14, alignItems: 'center', padding: '10px 16px', borderRadius: 10, background: 'rgba(127,127,127,0.07)', fontSize: 13.5 }}>
            <strong>Lal Kitab Lagna:</strong> {lk.ascendant.sign}{lk.ascendant.degree != null ? ` · ${lk.ascendant.degree}°` : ''}
          </div>
        )}
      </Section>

      <Section title="Planets — Nature, Effects & Upay" COLORS={COLORS}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {(lk.planets || []).map((p, i) => (
            <div key={i} style={{ padding: 15, borderRadius: 12, border: `1px solid ${COLORS.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap', marginBottom: 8 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: LORD_COLORS[p.planet] || 'var(--border-color)', flexShrink: 0 }} />
                <span style={{ fontWeight: 800, fontSize: 15 }}>{p.planet}</span>
                <span style={chipStyle(COLORS)}>House {p.house}{p.houseSignification ? ` — ${p.houseSignification}` : ''}</span>
                {p.sign && <span style={chipStyle(COLORS)}>{p.sign}</span>}
                {p.degree != null && <span style={chipStyle(COLORS)}>{p.degree}°</span>}
              </div>
              {p.nature && <div style={{ fontSize: 12.5, color: COLORS.textDim, marginBottom: 8 }}><strong style={{ color: COLORS.text }}>Nature:</strong> {p.nature}</div>}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginBottom: p.effects?.length ? 10 : 0 }}>
                {p.positiveTraits && (
                  <div style={{ fontSize: 12.5, lineHeight: 1.6, padding: '8px 11px', borderRadius: 9, background: 'rgba(34,197,94,0.07)', border: '1px solid rgba(34,197,94,0.25)' }}>
                    <strong style={{ color: '#16a34a' }}>Favourable:</strong> {p.positiveTraits}
                  </div>
                )}
                {p.negativeTraits && (
                  <div style={{ fontSize: 12.5, lineHeight: 1.6, padding: '8px 11px', borderRadius: 9, background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.22)' }}>
                    <strong style={{ color: '#dc2626' }}>Challenging:</strong> {p.negativeTraits}
                  </div>
                )}
              </div>
              {p.effects?.length > 0 && (
                <ul style={{ margin: '0 0 10px', paddingLeft: 18, fontSize: 12.5, color: COLORS.textDim, lineHeight: 1.7 }}>
                  {p.effects.filter(Boolean).map((e, j) => <li key={j}>{e}</li>)}
                </ul>
              )}
              {p.remedies && (
                <div style={{ padding: '10px 12px', borderRadius: 9, background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)', fontSize: 12.5, lineHeight: 1.6 }}>
                  <strong>Upay (remedies):</strong> {p.remedies}
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      <Section title="Houses — What They Govern" COLORS={COLORS}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
          {(lk.houses || []).map((h, i) => (
            <div key={i} style={{ padding: 13, borderRadius: 12, border: `1px solid ${COLORS.border}`, fontSize: 12.5 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 800, fontSize: 13.5 }}>House {h.house}</span>
                {h.name && <span style={{ color: COLORS.textDim }}>{h.name}</span>}
              </div>
              <div style={{ color: COLORS.textDim, marginBottom: 6 }}>
                {h.sign && <>Sign: <strong style={{ color: COLORS.text }}>{h.sign}</strong>{h.signLord ? ` (lord ${h.signLord})` : ''}</>}
              </div>
              {h.planets?.length > 0 && (
                <div style={{ marginBottom: 6 }}>
                  {h.planets.map((pl, j) => (
                    <span key={j} style={{ ...chipStyle(COLORS), marginRight: 5, marginBottom: 5, display: 'inline-block' }}>
                      {pl.planet} ({pl.status}{pl.degree != null ? `, ${pl.degree}°` : ''})
                    </span>
                  ))}
                </div>
              )}
              {h.elements?.length > 0 && <div style={{ color: COLORS.textDim, marginBottom: 4 }}>Governs: {h.elements.join(', ')}</div>}
              {h.generalRemedies?.length > 0 && <div style={{ color: COLORS.textDim }}>Upay: {h.generalRemedies.join(' · ')}</div>}
            </div>
          ))}
        </div>
      </Section>
    </>
  )
}

function KundliResult({ result, dosha, full, theme, COLORS, onBack, site, birth }) {
  const [view, setView] = useState('summary')
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const lordColor = (lord) => LORD_COLORS[lord] || theme.primaryColor
  const wa = String(site?.settings?.whatsappNumber || '').replace(/[^\d]/g, '')

  const vimsMd = Array.isArray(full?.vimshottari?.mahadashas) ? full.vimshottari.mahadashas : null
  const lk = full?.lalKitab && !full.lalKitab.error ? (full.lalKitab.data || full.lalKitab) : null
  const vargaEntries = Object.entries(full || {})
    .filter(([k, v]) => k.startsWith('divisional') && v && !v.error && v.svg)
    .map(([k, v]) => ({ d: k.replace('divisional', ''), chart: v.chart || {}, svg: v.svg }))
    .sort((a, b) => Number(a.d) - Number(b.d))
  const hasSystems = systemBuilders.some((f) => f(full, lordColor))
  const hasKp = !!full && (full.kpRulingPlanets || full.dhaiya || full.doshaCompute)

  const tabBtn = (id, label) => (
    <button onClick={() => setView(id)} style={{
      padding: '8px 16px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer',
      border: `1.5px solid ${view === id ? theme.primaryColor : COLORS.border}`,
      background: view === id ? theme.primaryColor : 'transparent',
      color: view === id ? '#fff' : COLORS.text,
    }}>{label}</button>
  )

  const doshaItems = [
    dosha?.manglik && {
      ok: !dosha.manglik.manglikPresent,
      title: dosha.manglik.manglikPresent ? `Manglik dosha — ${dosha.manglik.severityLabel || 'present'}` : 'No Manglik dosha',
      detail: dosha.manglik.summary,
    },
    dosha?.grahan && {
      ok: !grahan_present(dosha.grahan),
      title: grahan_present(dosha.grahan) ? 'Grahan dosha detected' : 'No Grahan dosha',
      detail: dosha.grahan.summary || dosha.grahan.description,
    },
    dosha?.shrapit && {
      ok: !shrapit_present(dosha.shrapit),
      title: shrapit_present(dosha.shrapit) ? 'Shrapit dosha detected' : 'No Shrapit dosha',
      detail: dosha.shrapit.summary || dosha.shrapit.description,
    },
  ].filter(Boolean)

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      {/* birth details strip */}
      <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: '14px 18px', marginBottom: 16, display: 'flex', flexWrap: 'wrap', gap: '6px 24px', fontSize: 13.5 }}>
        {[
          ['Name', birth?.name], ['Mobile', birth?.phone],
          ['Date', fmtDate(birth?.date || result.birthDate)], ['Time', fmtTime(birth?.time || result.birthTime)],
          ['Place', birth?.place || result.birthPlace],
        ].filter(([, v]) => v).map(([k, v]) => (
          <span key={k}><strong style={{ opacity: 0.6, fontWeight: 600 }}>{k}:</strong> {v}</span>
        ))}
      </div>

      {/* dosha alerts */}
      {dosha && doshaItems.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginBottom: 16 }}>
          {doshaItems.map((d, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '12px 14px', borderRadius: 12, alignItems: 'flex-start', border: `1px solid ${d.ok ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)'}`, background: d.ok ? 'rgba(34,197,94,0.07)' : 'rgba(239,68,68,0.07)' }}>
              {d.ok ? <CheckCircle2 size={17} color="#16a34a" style={{ flexShrink: 0, marginTop: 1 }} /> : <AlertTriangle size={17} color="#dc2626" style={{ flexShrink: 0, marginTop: 1 }} />}
              <div>
                <div style={{ fontWeight: 800, fontSize: 13.5 }}>{d.title}</div>
                {d.detail && <div style={{ fontSize: 12, color: COLORS.textDim, marginTop: 2, lineHeight: 1.5 }}>{String(d.detail).slice(0, 140)}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* view tabs */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {tabBtn('summary', 'Summary')}
        {result.chartSvg && tabBtn('chart', 'Kundli Chart')}
        {tabBtn('planets', 'Planets & Houses')}
        {(vimsMd || result.dasha) && tabBtn('dasha', 'Dasha')}
        {hasSystems && tabBtn('systems', 'All Dasha Systems')}
        {dosha && tabBtn('dosha', 'Dosha Report')}
        {hasKp && tabBtn('kp', 'KP & Extras')}
        {vargaEntries.length > 0 && tabBtn('varga', 'Divisional Charts')}
        {lk && tabBtn('lal', 'Lal Kitab')}
      </div>

      {view === 'summary' && (
        <>
          <Section title="Birth Details" COLORS={COLORS}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
              <Stat k="Name" v={birth?.name} COLORS={COLORS} />
              <Stat k="Mobile" v={birth?.phone} COLORS={COLORS} />
              <Stat k="Birth date" v={fmtDate(birth?.date || result.birthDate)} COLORS={COLORS} />
              <Stat k="Birth time" v={fmtTime(birth?.time || result.birthTime)} COLORS={COLORS} />
              <Stat k="Birth place" v={birth?.place || result.birthPlace} COLORS={COLORS} />
            </div>
          </Section>
          <Section title="Chart Summary" COLORS={COLORS}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
              <Stat k="Ascendant (Lagna)" v={result.ascendant?.sign} COLORS={COLORS} />
              <Stat k="Lagna Lord" v={result.ascendant?.lord} COLORS={COLORS} />
              <Stat k="Lagna Nakshatra" v={result.ascendant?.nakshatra} COLORS={COLORS} />
              <Stat k="Moon Sign (Rashi)" v={result.moonSign} COLORS={COLORS} />
              <Stat k="Birth Nakshatra" v={result.moonNakshatra} COLORS={COLORS} />
              <Stat k="Sun Sign" v={result.sunSign} COLORS={COLORS} />
              <Stat k="Lucky Gemstone" v={result.gemstone?.stone} sub={result.gemstone?.forLord ? `For ${result.gemstone.forLord}` : ''} COLORS={COLORS} />
            </div>
            {result.currentDasha?.mahadasha && (
              <div style={{ marginTop: 14, padding: '13px 16px', borderRadius: 12, background: `color-mix(in srgb, ${lordColor(result.currentDasha.mahadasha)} 12%, transparent)`, border: `1px solid ${lordColor(result.currentDasha.mahadasha)}44` }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.5, opacity: 0.7, marginBottom: 3 }}>RUNNING MAHADASHA</div>
                <div style={{ fontWeight: 800, fontSize: 16 }}>
                  {result.currentDasha.mahadasha}
                  {result.currentDasha.antardasha && <> → <span style={{ fontSize: 14 }}>{result.currentDasha.antardasha} antardasha</span></>}
                  <span style={{ fontSize: 12, fontWeight: 600, opacity: 0.65 }}>
                    {' '}· till {fmtDate(result.currentDasha.to)}
                    {result.currentDasha.antardashaFrom && result.currentDasha.antardashaTo
                      ? ` (AD ${fmtDate(result.currentDasha.antardashaFrom)} – ${fmtDate(result.currentDasha.antardashaTo)})` : ''}
                  </span>
                </div>
              </div>
            )}
          </Section>
        </>
      )}

      {view === 'chart' && result.chartSvg && (
        <Section title="North-Indian Kundli Chart (Lagna Kundli)" COLORS={COLORS}>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ width: '100%', maxWidth: 560, color: COLORS.text }} dangerouslySetInnerHTML={{ __html: result.chartSvg }} />
          </div>
        </Section>
      )}

      {view === 'planets' && (
        <Section title="Planets" COLORS={COLORS}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead><tr>{['Planet', 'Sign', 'House', 'Degree', 'Notes'].map((h) => <th key={h} style={{ textAlign: 'left', padding: '8px 10px', borderBottom: `1px solid ${COLORS.border}`, fontSize: 11.5, color: COLORS.textDim }}>{h}</th>)}</tr></thead>
              <tbody>
                {(result.planets || []).map((p) => (
                  <tr key={p.name}>
                    <td style={{ padding: '8px 10px', fontWeight: 700 }}>{p.name}{p.retrograde ? ' ℞' : ''}{p.combust ? ' ¤' : ''}</td>
                    <td style={{ padding: '8px 10px' }}>{p.sign}</td>
                    <td style={{ padding: '8px 10px' }}>{p.house}</td>
                    <td style={{ padding: '8px 10px' }}>{p.degreeDMS || '—'}</td>
                    <td style={{ padding: '8px 10px', color: COLORS.textDim, fontSize: 12 }}>{[p.retrograde && 'retrograde', p.combust && 'combust'].filter(Boolean).join(' · ') || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: 11.5, color: COLORS.textDim, marginTop: 8 }}>℞ retrograde · ¤ combust</div>
        </Section>
      )}

      {view === 'planets' && (
        <Section title="Houses (Bhava)" COLORS={COLORS}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 8 }}>
            {(result.houses || []).map((h, i) => (
              <div key={i} style={{ padding: 10, background: 'rgba(127,127,127,0.06)', borderRadius: 10, fontSize: 12.5 }}>
                <span style={{ fontWeight: 800 }}>H{i + 1}</span> · {h.sign}
                {h.planets ? <div style={{ color: COLORS.textDim, marginTop: 2 }}>{h.planets}</div> : null}
              </div>
            ))}
          </div>
        </Section>
      )}

      {view === 'dasha' && (
        <Section title="Vimshottari Mahadasha Timeline" COLORS={COLORS}>
          {(vimsMd || result.dasha || []).map((d, i) => {
            const lord = d.lord || d.planet
            const from = d.from || d.startDate
            const to = d.to || d.endDate
            const active = inRange(from, to)
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderRadius: 10, marginBottom: 6, border: `1px solid ${active ? lordColor(lord) : COLORS.border}`, background: active ? `color-mix(in srgb, ${lordColor(lord)} 12%, transparent)` : 'transparent' }}>
                <div style={{ width: 30, height: 30, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: lordColor(lord), color: '#fff', fontWeight: 800, fontSize: 11 }}>{lord?.slice(0, 2)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>{lord} Mahadasha {active && <span style={{ fontSize: 11, color: lordColor(lord) }}>· running now</span>}</div>
                  <div style={{ fontSize: 12, color: COLORS.textDim }}>{fmtDate(from)} → {fmtDate(to)}</div>
                </div>
              </div>
            )
          })}
          {hasSystems && (
            <button onClick={() => setView('systems')} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, marginTop: 8, background: 'transparent', color: theme.primaryColor, borderColor: theme.primaryColor }}>
              Explore all dasha systems with sub-periods →
            </button>
          )}
        </Section>
      )}

      {view === 'systems' && <DashaSystems full={full} theme={theme} COLORS={COLORS} />}

      {view === 'dosha' && dosha && (
        <Section title="Dosha Analysis & Remedies" COLORS={COLORS}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {doshaItems.map((d, i) => (
              <div key={i} style={{ padding: 14, borderRadius: 12, border: `1px solid ${COLORS.border}` }}>
                <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                  {d.ok ? <CheckCircle2 size={16} color="#16a34a" /> : <AlertTriangle size={16} color="#dc2626" />} {d.title}
                </div>
                {d.detail && <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.65 }}>{d.detail}</div>}
              </div>
            ))}
            {dosha.manglik?.remedies && (
              <div style={{ padding: 14, borderRadius: 12, border: `1px solid ${COLORS.border}` }}>
                <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 6 }}>Suggested remedies</div>
                <Remedies v={dosha.manglik.remedies} COLORS={COLORS} />
              </div>
            )}
            <div style={{ fontSize: 12.5, color: COLORS.textDim }}>For a detailed personal reading of these yogas, book a consultation with {site?.name || 'the astrologer'}.</div>
          </div>
        </Section>
      )}

      {view === 'kp' && <KpExtras full={full} theme={theme} COLORS={COLORS} site={site} />}

      {view === 'varga' && vargaEntries.length > 0 && <VargaView entries={vargaEntries} theme={theme} COLORS={COLORS} />}

      {view === 'lal' && <LalKitabView lk={lk} COLORS={COLORS} />}

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 6 }}>
        <button onClick={onBack} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 260 }}>Generate another kundli</button>
        <a href={wa ? `https://wa.me/${wa}?text=${encodeURIComponent(`Namaste, I generated my kundli on your site (${birth?.name || ''}, ${fmtDate(birth?.date)}). I'd like a detailed consultation.`)}` : '#/'}
          target={wa ? '_blank' : undefined} rel="noopener noreferrer" style={{ textDecoration: 'none', flex: 1, minWidth: 200 }}>
          <button style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, background: gradient, color: '#fff', border: 'none' }}>
            <Sparkles size={14} style={{ verticalAlign: '-2px', marginRight: 6 }} />Book a detailed consultation
          </button>
        </a>
      </div>
    </motion.div>
  )
}

// ─────────── MATCH MAKING PAGE (#/matching) ───────────
export function MatchingPage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [boy, setBoy] = useState({ date: '', time: '', place: '', lat: null, lon: null, tz: null })
  const [girl, setGirl] = useState({ date: '', time: '', place: '', lat: null, lon: null, tz: null })
  const [lang, setLang] = useState('en')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    if (!boy.date || !boy.time || !girl.date || !girl.time) { setError('Please enter birth date and time for both partners'); return }
    setBusy(true); setError(null)
    try {
      const clean = (p) => ({ date: p.date, time: p.time, lat: p.lat ?? undefined, lon: p.lon ?? undefined, tz: p.tz || undefined, place: p.place || undefined })
      setResult(await publicMatchingTool(resolve, { boy: clean(boy), girl: clean(girl), lang }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const scorePct = result ? Math.round((result.summary?.totalScore || 0) / 36 * 100) : 0

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/matching" icon={Heart}
      title="Match Making (Gun Milan)" subtitle={`Ashtakoota compatibility across all 36 gunas, with manglik analysis for both partners — presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[
            { key: 'boy', label: 'Boy — Birth Details', value: boy, set: setBoy },
            { key: 'girl', label: 'Girl — Birth Details', value: girl, set: setGirl },
          ].map((p) => (
            <div key={p.key} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 22 }}>
              <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 800 }}>{p.label}</h3>
              <BirthFields value={p.value} onChange={p.set} COLORS={COLORS} />
            </div>
          ))}
          <LangSelect value={lang} onChange={setLang} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', padding: 14, opacity: busy ? 0.7 : 1 }}>
            {busy ? 'Matching kundlis…' : 'Check Compatibility'}
          </button>
        </form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {/* score hero */}
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 30, textAlign: 'center', marginBottom: 16 }}>
            <div style={{ fontSize: 56, fontWeight: 900, letterSpacing: '-2px', color: theme.primaryColor }}>
              {result.summary?.totalScore}<span style={{ fontSize: 24, opacity: 0.5 }}> / 36</span>
            </div>
            <div style={{ height: 8, borderRadius: 6, background: 'rgba(127,127,127,0.15)', margin: '12px auto 10px', maxWidth: 320, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: scorePct + '%', borderRadius: 6, background: gradient, transition: 'width 0.6s ease' }} />
            </div>
            <div style={{ fontSize: 19, fontWeight: 800 }}>{result.summary?.verdict}</div>
            <div style={{ color: COLORS.textDim, fontSize: 13.5, marginTop: 4 }}>{result.summary?.verdictDetail}</div>
          </div>

          {/* profiles */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            {[['Boy', result.maleProfile, result.boyManglik], ['Girl', result.femaleProfile, result.girlManglik]].map(([label, prof, mang]) => (
              <div key={label} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18, fontSize: 13.5 }}>
                <div style={{ fontWeight: 800, marginBottom: 8 }}>{label}</div>
                <div style={{ lineHeight: 1.9, color: COLORS.textDim }}>
                  Moon sign: <strong style={{ color: COLORS.text }}>{prof?.moonSign}</strong><br />
                  Nakshatra: <strong style={{ color: COLORS.text }}>{prof?.moonNakshatra} (pada {prof?.moonNakshatraPada})</strong><br />
                  Ascendant: <strong style={{ color: COLORS.text }}>{prof?.ascendant}</strong><br />
                  Manglik: <strong style={{ color: mang?.manglikPresent ? '#dc2626' : '#16a34a' }}>{mang?.manglikPresent ? `Yes${mang.severityLabel ? ` (${mang.severityLabel})` : ''}` : 'No'}</strong>
                </div>
              </div>
            ))}
          </div>

          {/* 36 gunas */}
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 22, marginBottom: 16 }}>
            <h3 style={{ margin: '0 0 14px', fontSize: 13, fontWeight: 800, letterSpacing: 0.8, color: COLORS.textDim, textTransform: 'uppercase' }}>Ashtakoota — 36 Gunas</h3>
            {(result.ashtakootaGunas || []).map((g) => (
              <div key={g.name} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, marginBottom: 4 }}>
                  <span style={{ fontWeight: 700 }}>{g.name}</span>
                  <span style={{ fontWeight: 800 }}>{g.score} / {g.maxScore}</span>
                </div>
                <div style={{ height: 6, borderRadius: 5, background: 'rgba(127,127,127,0.15)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: (g.score / g.maxScore * 100) + '%', background: gradient, borderRadius: 5 }} />
                </div>
                {g.description && <div style={{ fontSize: 12, color: COLORS.textDim, marginTop: 3, lineHeight: 1.5 }}>{g.description}</div>}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button onClick={() => setResult(null)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 240, flex: 1 }}>Check another match</button>
            <a href="#/" style={{ textDecoration: 'none', flex: 1, minWidth: 220 }}>
              <button style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, background: gradient, color: '#fff', border: 'none' }}>
                Book a detailed matching consultation
              </button>
            </a>
          </div>
        </motion.div>
      )}
    </ToolShell>
  )
}

// ─────────── VISITOR SIGN-IN (#/signin) — per-tenant accounts ───────────
export function TenantSignIn({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [mode, setMode] = useState('signin')
  const [form, setForm] = useState({ email: '', password: '', name: '' })
  const [googleOn, setGoogleOn] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [verifySent, setVerifySent] = useState(false)
  const [passForm, setPassForm] = useState({ a: '', b: '' })

  useEffect(() => {
    fetch(`/sites/site/auth/config?${new URLSearchParams(resolve)}`)
      .then((r) => r.json()).then((c) => setGoogleOn(!!c.googleEnabled)).catch(() => {})
  }, [])

  const save = (data) => {
    localStorage.setItem(`tenantAuth_${site.slug}`, JSON.stringify({ token: data.tenant_token, user: data.tenant_user }))
    // Return to wherever the visitor was headed (booking, shop, account…).
    let back = '#/'
    try {
      back = sessionStorage.getItem(tenantAuthReturnKey(site.slug)) || '#/'
      sessionStorage.removeItem(tenantAuthReturnKey(site.slug))
    } catch { /* ignore */ }
    window.location.hash = back
  }

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (!form.email || !form.password || (mode === 'signup' && !form.name)) { setError('Please fill all fields'); return }
    setBusy(true)
    try {
      const qs = new URLSearchParams(resolve).toString()
      if (mode === 'signup') {
        const res = await fetch(`/sites/site/auth/register?${qs}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || data.message || 'Sign-up failed')
        // verification email through Firebase (best-effort — account works regardless)
        try { await signUpWithEmailAndVerify(form.email, form.password); setVerifySent(true) } catch { /* provider exists or SDK off */ }
        save(data)
        return
      }
      const res = await fetch(`/sites/site/auth/login?${qs}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: form.email, password: form.password }) })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || 'Sign-in failed')
      save(data)
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  const google = async () => {
    setError(null); setBusy(true)
    try {
      const { signInWithFirebase } = await import('../lib/firebase.js')
      const fu = await signInWithFirebase('google')
      const qs = new URLSearchParams(resolve).toString()
      const res = await fetch(`/sites/site/auth/firebase?${qs}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ idToken: await fu.getIdToken() }) })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Google sign-in failed')
      if (data.hasPassword === false) {
        window.__pendingTenantAuth = data
        setMode('setpass')
        return
      }
      save(data)
    } catch (err) { setError(err.message || 'Google sign-in failed') } finally { setBusy(false) }
  }

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/signin" icon={Heart}
      title={mode === 'signin' ? `Sign in to ${site.name}` : `Create your ${site.name} account`}
      subtitle="Save your kundlis, track bookings and manage your readings — your account is private to this site.">
      <form onSubmit={submit} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 460, margin: '0 auto' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {['signin', 'signup'].map((m) => (
            <button key={m} type="button" onClick={() => { setMode(m); setError(null) }}
              style={{ flex: 1, padding: '9px', borderRadius: 10, cursor: 'pointer', fontWeight: 700, fontSize: 13.5,
                border: `1.5px solid ${mode === m ? theme.primaryColor : COLORS.border}`,
                background: mode === m ? theme.primaryColor : 'transparent', color: mode === m ? '#fff' : COLORS.text }}>
              {m === 'signin' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>
        {mode === 'signup' && (
          <div><label style={labelStyle}>Your name</label>
            <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Full name" style={inputStyle} /></div>
        )}
        <div><label style={labelStyle}>Email</label>
          <input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="you@example.com" style={inputStyle} /></div>
        <div><label style={labelStyle}>Password {mode === 'signup' && '(min 8 characters)'}</label>
          <input type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} placeholder="••••••••" style={inputStyle} /></div>
        {verifySent && <div style={{ color: '#16a34a', fontSize: 13, background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 10, padding: 10 }}>
          Account created — we sent a verification link to your email.
        </div>}
        {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
        <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', padding: 13, opacity: busy ? 0.7 : 1 }}>
          {busy ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'}
        </button>
        {mode === 'setpass' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ padding: 12, borderRadius: 10, background: 'rgba(79,70,229,0.06)', border: '1px solid rgba(79,70,229,0.25)', fontSize: 13, lineHeight: 1.6 }}>
              You're signed in with Google. Create a password to also sign in with your email next time.
            </div>
            <div><label style={labelStyle}>New password (min 8 characters)</label>
              <input type="password" value={passForm.a} onChange={(e) => setPassForm({ ...passForm, a: e.target.value })} placeholder="••••••••" style={inputStyle} /></div>
            <div><label style={labelStyle}>Confirm password</label>
              <input type="password" value={passForm.b} onChange={(e) => setPassForm({ ...passForm, b: e.target.value })} placeholder="••••••••" style={inputStyle} /></div>
            <button type="button" disabled={busy}
              onClick={async () => {
                if (passForm.a.length < 8) { setError('Password must be at least 8 characters'); return }
                if (passForm.a !== passForm.b) { setError('Passwords do not match'); return }
                setBusy(true); setError(null)
                try {
                  const pending = window.__pendingTenantAuth
                  const qs = new URLSearchParams(resolve).toString()
                  const res = await fetch(`/sites/site/auth/set-password?${qs}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${pending.tenant_token}` }, body: JSON.stringify({ password: passForm.a }) })
                  if (!res.ok) throw new Error('Could not set password')
                  delete window.__pendingTenantAuth
                  save(pending)
                } catch (err) { setError(err.message) } finally { setBusy(false) }
              }}
              style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', padding: 13 }}>
              Save password & continue
            </button>
            <button type="button" onClick={() => { const p2 = window.__pendingTenantAuth; delete window.__pendingTenantAuth; if (p2) save(p2) }}
              style={{ background: 'none', border: 'none', color: COLORS.textDim, fontSize: 12.5, cursor: 'pointer', textDecoration: 'underline' }}>
              Skip for now
            </button>
          </div>
        )}
        {mode !== 'setpass' && googleOn && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: COLORS.textDim, fontSize: 12, fontWeight: 600 }}>
              <span style={{ flex: 1, height: 1, background: COLORS.border }} /> OR <span style={{ flex: 1, height: 1, background: COLORS.border }} />
            </div>
            <button type="button" onClick={google} disabled={busy}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: '12px', borderRadius: 999, border: `1px solid ${COLORS.border}`, background: 'transparent', fontWeight: 700, fontSize: 14, color: COLORS.text, cursor: 'pointer' }}>
              <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.3 6.1 29.4 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.6-.4-3.9z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.3 6.1 29.4 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C41.4 35.4 44 30.2 44 24c0-1.3-.1-2.6-.4-3.9z"/></svg>
              Continue with Google
            </button>
          </>
        )}
      </form>
    </ToolShell>
  )
}

// ─────────── VISITOR ACCOUNT (#/account) — my consultations & orders ───────────
const STATUS_STYLE = {
  confirmed: { bg: 'rgba(34,197,94,0.12)', color: '#16a34a' },
  completed: { bg: 'rgba(59,130,246,0.12)', color: '#2563eb' },
  cancelled: { bg: 'rgba(127,127,127,0.15)', color: '#6b7280' },
  new: { bg: 'rgba(234,179,8,0.14)', color: '#b45309' },
  fulfilled: { bg: 'rgba(34,197,94,0.12)', color: '#16a34a' },
}
const StatusChip = ({ status }) => {
  const s = STATUS_STYLE[status] || STATUS_STYLE.new
  return (
    <span style={{ padding: '3px 10px', borderRadius: 999, fontSize: 11.5, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.4, background: s.bg, color: s.color }}>
      {status}
    </span>
  )
}

const inr = (amount, currency) => (currency === 'INR' || !currency ? `₹${amount || 0}` : `${currency} ${amount || 0}`)

export function TenantAccount({ site, resolve, theme, COLORS, slug, services = [] }) {
  const sKey = slug || site.slug
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [session, setSession] = useState(() => getTenantSession(sKey))
  const [tab, setTab] = useState('bookings')
  const [bookings, setBookings] = useState(null)
  const [orders, setOrders] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const signedOut = () => { localStorage.removeItem(`tenantAuth_${sKey}`); setSession(null) }

  const load = () => {
    if (!getTenantSession(sKey)?.token) return
    setBookings(null); setOrders(null)
    getMyTenantBookings(resolve, sKey)
      .then(setBookings)
      .catch((e) => { if (e?.response?.status === 401) signedOut(); else setBookings([]) })
    getMyTenantOrders(resolve, sKey)
      .then(setOrders)
      .catch((e) => { if (e?.response?.status === 401) signedOut(); else setOrders([]) })
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  if (!session?.token) {
    return (
      <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/account" icon={Heart}
        title={`My Account — ${site.name}`}
        subtitle="Sign in to see your consultations and orders.">
        <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 30, textAlign: 'center', maxWidth: 460, margin: '0 auto' }}>
          <div style={{ fontSize: 14.5, opacity: 0.75, lineHeight: 1.7, marginBottom: 16 }}>
            Your appointments and orders on {site.name} live in this account — sign in to manage them.
          </div>
          <button
            onClick={() => { try { sessionStorage.setItem(tenantAuthReturnKey(sKey), '#/account') } catch { /* ignore */ } window.location.hash = '#/signin' }}
            style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', padding: 13 }}>
            Sign in / Create account
          </button>
        </div>
      </ToolShell>
    )
  }

  const user = session.user || {}
  const today = new Date().toISOString().slice(0, 10)
  const serviceName = (b) => services.find((s) => s.id === b.service_id)?.name || 'Consultation'

  const cancelBooking = async (b) => {
    setBusyId(`b${b.id}`)
    try {
      await cancelMyTenantBooking(resolve, sKey, b.id)
      setBookings((list) => list.map((x) => (x.id === b.id ? { ...x, status: 'cancelled' } : x)))
      toast.success('Consultation cancelled.')
    } catch (e) { toast.error(errText(e)) } finally { setBusyId(null) }
  }
  const cancelOrder = async (o) => {
    setBusyId(`o${o.id}`)
    try {
      await cancelMyTenantOrder(resolve, sKey, o.id)
      setOrders((list) => list.map((x) => (x.id === o.id ? { ...x, status: 'cancelled' } : x)))
      toast.success('Order cancelled.')
    } catch (e) { toast.error(errText(e)) } finally { setBusyId(null) }
  }

  const card = { background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: '16px 18px' }
  const smallBtn = { background: 'transparent', border: '1px solid rgba(220,38,38,0.45)', color: '#dc2626', borderRadius: 9, padding: '7px 14px', fontSize: 12.5, fontWeight: 700, cursor: 'pointer' }

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/account" icon={Heart}
      title={`My Account — ${site.name}`}
      subtitle="Track your consultations and orders, all in one place.">
      {/* profile strip */}
      <div style={{ ...card, display: 'flex', alignItems: 'center', gap: 14, maxWidth: 640, margin: '0 auto 22px' }}>
        <span style={{ width: 44, height: 44, borderRadius: '50%', background: gradient, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 800, flexShrink: 0 }}>
          {(user.name || user.email || '?').trim().charAt(0).toUpperCase()}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 800, fontSize: 15.5 }}>{user.name || 'Welcome!'}</div>
          <div style={{ fontSize: 13, color: COLORS.textDim, overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.email}</div>
        </div>
        <button onClick={signedOut} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'none', border: `1px solid ${COLORS.border}`, color: COLORS.textDim, borderRadius: 9, padding: '7px 12px', fontSize: 12.5, fontWeight: 700, cursor: 'pointer', flexShrink: 0 }}>
          <LogOut size={13} /> Sign out
        </button>
      </div>

      {/* tabs */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 20 }}>
        {[['bookings', 'Consultations', CalendarDays, bookings], ['orders', 'Orders', ShoppingBag, orders]].map(([key, label, Icon, data]) => (
          <button key={key} onClick={() => setTab(key)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '9px 18px', borderRadius: 999, cursor: 'pointer', fontWeight: 700, fontSize: 13.5,
              border: `1.5px solid ${tab === key ? theme.primaryColor : COLORS.border}`,
              background: tab === key ? theme.primaryColor : 'transparent', color: tab === key ? '#fff' : COLORS.text }}>
            <Icon size={14} /> {label}{Array.isArray(data) ? ` (${data.length})` : ''}
          </button>
        ))}
      </div>

      <div style={{ maxWidth: 640, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {tab === 'bookings' && (bookings === null ? <Loading /> : bookings.length === 0 ? <Empty label="No consultations yet." site={site} /> : (
          bookings.map((b) => {
            const cancellable = b.status === 'confirmed' && b.date >= today
            return (
              <div key={b.id} style={card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: 15 }}>{serviceName(b)}</div>
                    <div style={{ fontSize: 13.5, color: COLORS.textDim, marginTop: 3 }}>
                      {fmtDate(b.date)} · {fmtTime(b.start_time)}–{fmtTime(b.end_time)}
                    </div>
                  </div>
                  <StatusChip status={b.status || 'confirmed'} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 10, borderTop: `1px dashed ${COLORS.border}`, gap: 10, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 13.5 }}>{b.amount ? inr(b.amount, b.currency) : 'Free'}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 12, color: COLORS.textDim }}>Payment: {b.payment_status || 'none'}</span>
                    {cancellable && (
                      <button onClick={() => cancelBooking(b)} disabled={busyId === `b${b.id}`} style={smallBtn}>
                        {busyId === `b${b.id}` ? 'Cancelling…' : 'Cancel'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        ))}

        {tab === 'orders' && (orders === null ? <Loading /> : orders.length === 0 ? <Empty label="No orders yet." site={site} /> : (
          orders.map((o) => {
            const cancellable = o.status === 'new' || o.status === 'confirmed'
            return (
              <div key={o.id} style={card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: 15 }}>Order #{o.id}</div>
                    <div style={{ fontSize: 13, color: COLORS.textDim, marginTop: 3 }}>Placed {fmtDate(String(o.created_at || '').slice(0, 10))}</div>
                  </div>
                  <StatusChip status={o.status || 'new'} />
                </div>
                <div style={{ fontSize: 13.5, marginTop: 10, lineHeight: 1.6 }}>
                  {(o.items || []).map((it) => `${it.qty}× ${it.name}`).join(' · ')}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 10, borderTop: `1px dashed ${COLORS.border}`, gap: 10, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 13.5 }}>{inr(o.amount, o.currency)}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 12, color: COLORS.textDim }}>Payment: {o.payment_status || 'none'}</span>
                    {cancellable && (
                      <button onClick={() => cancelOrder(o)} disabled={busyId === `o${o.id}`} style={smallBtn}>
                        {busyId === `o${o.id}` ? 'Cancelling…' : 'Cancel'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        ))}
      </div>
    </ToolShell>
  )
}

const Loading = () => (
  <div style={{ textAlign: 'center', padding: 30, opacity: 0.6, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
    <Loader2 size={18} className="spin" /> Loading…
  </div>
)

const Empty = ({ label, site }) => (
  <div style={{ textAlign: 'center', padding: '30px 16px', border: '1px dashed rgba(127,127,127,0.4)', borderRadius: 16 }}>
    <div style={{ fontSize: 14.5, opacity: 0.7, marginBottom: 14 }}>{label}</div>
    <a href="#book" style={{ display: 'inline-flex', padding: '9px 20px', borderRadius: 10, background: 'linear-gradient(135deg,#7c3aed,#eab308)', color: '#fff', fontWeight: 700, fontSize: 13.5, textDecoration: 'none' }}>
      Book on {site.name}
    </a>
  </div>
)


// ─────────── SHOP PAGE (#/shop) + PRODUCT DETAIL (#/shop/:id) ───────────
const RATING = (id) => 4.3 + ((Number(id) * 37) % 7) / 10   // stable 4.3–4.9
const VIEWERS = (id) => 9 + ((Number(id) * 13) % 40)
const SOLD = (id) => 30 + ((Number(id) * 29) % 170)

function Stars({ id, COLORS }) {
  const r = RATING(id)
  return (
    <span style={{ color: '#f59e0b', fontSize: 12.5, fontWeight: 700 }}>
      {'★'.repeat(Math.round(r))}{'☆'.repeat(5 - Math.round(r))} <span style={{ color: COLORS.textDim }}>({r.toFixed(1)})</span>
    </span>
  )
}

function PriceBlock({ p, COLORS, big }) {
  const save = p.mrp && p.mrp > p.price ? Math.round((1 - p.price / p.mrp) * 100) : 0
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
      <span style={{ fontWeight: 900, fontSize: big ? 30 : 18, color: theme_color('x') === 'x' ? '#111' : '#111' }}>₹{p.price}</span>
      {!!save && <span style={{ color: COLORS.textDim, textDecoration: 'line-through', fontSize: big ? 16 : 13 }}>MRP ₹{p.mrp}</span>}
      {!!save && <span style={{ background: 'rgba(34,197,94,0.12)', color: '#16a34a', fontWeight: 800, fontSize: big ? 14 : 11.5, borderRadius: 8, padding: '2px 8px' }}>SAVE {save}%</span>}
    </div>
  )
}

// ═══════════════ MODERN STORE (cart + COD/online checkout) ═══════════════

const CART_KEY = (slug) => `cart_${slug}`

function useCart(slug) {
  const [cart, setCart] = useState(() => {
    try { return JSON.parse(localStorage.getItem(CART_KEY(slug)) || '{}') } catch { return {} }
  })
  useEffect(() => { localStorage.setItem(CART_KEY(slug), JSON.stringify(cart)) }, [cart])
  const items = Object.entries(cart).map(([id, q]) => ({ id: Number(id), qty: q }))
  return {
    cart, items, count: items.reduce((s, i) => s + i.qty, 0),
    add: (id, qty = 1) => setCart((c) => ({ ...c, [id]: Math.min(9, (c[id] || 0) + qty) })),
    setQty: (id, qty) => setCart((c) => { const n = { ...c }; if (qty <= 0) delete n[id]; else n[id] = Math.min(9, qty); return n }),
    remove: (id) => setCart((c) => { const n = { ...c }; delete n[id]; return n }),
    clear: () => setCart({}),
  }
}

const money = (n) => '₹' + Number(n || 0).toLocaleString('en-IN')
const isVideoSrc = (src) => /\.(mp4|webm|mov)(\?|$)/i.test(src || '') || (src || '').startsWith('data:video')

function ShopHeader({ site, slug, cart, COLORS, theme, onCart }) {
  return (
    <header style={{ background: COLORS.surface, borderBottom: `1px solid ${COLORS.border}`, padding: '12px 18px', position: 'sticky', top: 0, zIndex: 40, display: 'flex', alignItems: 'center', gap: 12 }}>
      <a href="#/" style={{ textDecoration: 'none', color: COLORS.text, fontWeight: 800, fontSize: 15, display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        {site.logo_url && <img src={site.logo_url} alt="" style={{ width: 28, height: 28, borderRadius: 8, objectFit: 'cover' }} />}
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{site.name}</span>
      </a>
      <a href="#/shop" style={{ fontSize: 13.5, fontWeight: 700, color: COLORS.textDim, textDecoration: 'none' }}>Shop</a>
      <div style={{ flex: 1 }} />
      <a href="#/signin" style={{ fontSize: 13, fontWeight: 700, color: COLORS.textDim, textDecoration: 'none', whiteSpace: 'nowrap' }}>Sign in</a>
      <button onClick={onCart} style={{ position: 'relative', background: 'none', border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: '7px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, color: COLORS.text, fontWeight: 700, fontSize: 13.5 }}>
        🛒 Cart
        {cart.count > 0 && (
          <span style={{ position: 'absolute', top: -7, right: -7, background: '#dc2626', color: '#fff', borderRadius: 999, minWidth: 18, height: 18, fontSize: 11, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{cart.count}</span>
        )}
      </button>
    </header>
  )
}

function CartDrawer({ open, onClose, cart, products, COLORS, theme, site, resolve, slug }) {
  // Hooks must run unconditionally (rules of hooks) — the null return for a
  // closed drawer comes after them.
  const [stage, setStage] = useState('cart') // cart | address | pay | done
  const [form, setForm] = useState(() => {
    try {
      const s2 = JSON.parse(localStorage.getItem(`tenantAuth_${slug}`) || 'null')
      return { name: s2?.user?.name || '', phone: s2?.user?.phone || s2?.user?.email || '', address: '', pincode: '', city: '' }
    } catch { return { name: '', phone: '', address: '', pincode: '', city: '' } }
  })
  const [payMode, setPayMode] = useState('cod')
  const [placed, setPlaced] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const wa = String(site.settings?.whatsappNumber || '').replace(/[^\d]/g, '')
  const inp = { width: '100%', padding: '11px 13px', borderRadius: 10, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.text, fontSize: 14, outline: 'none' }

  const place = async () => {
    setBusy(true); setError(null)
    try {
      const res = await publicPlaceOrder(resolve, {
        items: rows.map((r) => ({ product_id: r.p.id, name: r.p.name, qty: r.qty, price: r.p.price })),
        client_name: form.name, client_phone: form.phone,
        address: [form.address, form.city, form.pincode].filter(Boolean).join(', '),
        notes: payMode === 'cod' ? 'Cash on delivery' : 'Online payment',
      })
      setPlaced(res); setStage('done'); cart.clear()
    } catch (e) { setError(e.response?.data?.detail || 'Could not place the order') }
    finally { setBusy(false) }
  }

  const payOnline = () => {
    // UPI intent / Razorpay happen after the order exists; simplest reliable path:
    // place the order first with 'online' note, then show payment options.
    place()
  }

  if (!open) return null
  const rows = cart.items.map((i) => ({ ...i, p: products.find((x) => x.id === i.id) })).filter((r) => r.p)
  const subtotal = rows.reduce((s, r) => s + r.p.price * r.qty, 0)

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 100 }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 'min(420px, 100%)', background: COLORS.surface, borderLeft: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', animation: 'cartIn 0.22s ease' }}>
        <style>{`@keyframes cartIn { from { transform: translateX(30px); opacity: 0.4 } to { transform: none; opacity: 1 } }`}</style>
        <div style={{ padding: '16px 18px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 800, fontSize: 16 }}>
            {stage === 'cart' ? `Your cart (${cart.count})` : stage === 'address' ? 'Delivery details' : stage === 'pay' ? 'Payment' : 'Order placed'}
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: COLORS.textDim, cursor: 'pointer', fontSize: 20 }}>×</button>
        </div>

        {stage === 'cart' && (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
              {rows.length === 0 ? (
                <div style={{ textAlign: 'center', color: COLORS.textDim, padding: 50, fontSize: 14.5 }}>Your cart is empty.<br /><a href="#/shop" onClick={onClose} style={{ color: theme.primaryColor, fontWeight: 700, textDecoration: 'none' }}>Browse products →</a></div>
              ) : rows.map((r) => (
                <div key={r.p.id} style={{ display: 'flex', gap: 10, padding: '10px 0', borderBottom: `1px solid ${COLORS.border}` }}>
                  {r.p.images?.[0]
                    ? (isVideoSrc(r.p.images[0]) ? <video src={r.p.images[0]} muted style={{ width: 54, height: 54, borderRadius: 10, objectFit: 'cover' }} /> : <img src={r.p.images[0]} alt="" style={{ width: 54, height: 54, borderRadius: 10, objectFit: 'cover' }} />)
                    : <div style={{ width: 54, height: 54, borderRadius: 10, background: 'rgba(127,127,127,0.1)' }} />}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 700, fontSize: 13.5, lineHeight: 1.3 }}>{r.p.name}</div>
                    <div style={{ color: COLORS.textDim, fontSize: 12.5, margin: '3px 0 6px' }}>{money(r.p.price)}</div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: '2px 8px' }}>
                      <button onClick={() => cart.setQty(r.p.id, r.qty - 1)} style={{ background: 'none', border: 'none', color: COLORS.text, cursor: 'pointer', fontWeight: 800 }}>−</button>
                      <span style={{ fontWeight: 800, fontSize: 13 }}>{r.qty}</span>
                      <button onClick={() => cart.setQty(r.p.id, r.qty + 1)} style={{ background: 'none', border: 'none', color: COLORS.text, cursor: 'pointer', fontWeight: 800 }}>+</button>
                    </div>
                  </div>
                  <button onClick={() => cart.remove(r.p.id)} style={{ background: 'none', border: 'none', color: COLORS.textDim, cursor: 'pointer', fontSize: 16 }}>🗑</button>
                </div>
              ))}
            </div>
            {rows.length > 0 && (
              <div style={{ padding: '14px 16px', borderTop: `1px solid ${COLORS.border}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, marginBottom: 4 }}><span style={{ color: COLORS.textDim }}>Subtotal</span><b>{money(subtotal)}</b></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: COLORS.textDim, marginBottom: 10 }}><span>Delivery</span><span style={{ color: '#16a34a', fontWeight: 700 }}>FREE</span></div>
                <button onClick={() => setStage('address')} style={{ width: '100%', padding: 14, borderRadius: 12, border: 'none', background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff', fontWeight: 800, fontSize: 15, cursor: 'pointer' }}>
                  Checkout — {money(subtotal)}
                </button>
              </div>
            )}
          </>
        )}

        {stage === 'address' && (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Full name *" style={inp} />
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone (WhatsApp) *" style={inp} />
              <textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} placeholder="Full address (house, street, area) *" rows={3} style={{ ...inp, resize: 'vertical' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="City *" style={inp} />
                <input value={form.pincode} onChange={(e) => setForm({ ...form, pincode: e.target.value })} placeholder="Pincode *" style={inp} />
              </div>
              {error && <div style={{ color: '#dc2626', fontSize: 13 }}>{error}</div>}
            </div>
            <div style={{ padding: '14px 16px', borderTop: `1px solid ${COLORS.border}`, display: 'flex', gap: 8 }}>
              <button onClick={() => setStage('cart')} style={{ padding: 13, borderRadius: 12, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontWeight: 700, cursor: 'pointer' }}>←</button>
              <button onClick={() => { if (!form.name.trim() || !form.phone.trim() || !form.address.trim()) { setError('Name, phone and address are required'); return } setError(null); setStage('pay') }}
                style={{ flex: 1, padding: 13, borderRadius: 12, border: 'none', background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff', fontWeight: 800, fontSize: 15, cursor: 'pointer' }}>
                Continue to payment
              </button>
            </div>
          </>
        )}

        {stage === 'pay' && (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px' }}>
              <div style={{ padding: '10px 12px', borderRadius: 10, background: 'rgba(127,127,127,0.06)', marginBottom: 14, fontSize: 13, color: COLORS.textDim, lineHeight: 1.6 }}>
                Deliver to <b style={{ color: COLORS.text }}>{form.name}</b> · {form.address}{form.city ? `, ${form.city}` : ''} {form.pincode} · {form.phone}
              </div>
              {[
                { id: 'cod', icon: '💵', title: 'Cash on Delivery', desc: 'Pay when your order arrives. Most popular.' },
                { id: 'online', icon: '⚡', title: 'Pay online (UPI)', desc: 'GPay, PhonePe, Paytm — pay now, faster dispatch.' },
              ].map((m) => (
                <button key={m.id} onClick={() => setPayMode(m.id)} style={{
                  width: '100%', textAlign: 'left', display: 'flex', gap: 12, alignItems: 'flex-start', padding: 14, borderRadius: 12, cursor: 'pointer', marginBottom: 10,
                  border: `2px solid ${payMode === m.id ? theme.primaryColor : COLORS.border}`,
                  background: payMode === m.id ? `color-mix(in srgb, ${theme.primaryColor} 8%, transparent)` : 'transparent',
                }}>
                  <span style={{ fontSize: 22 }}>{m.icon}</span>
                  <span>
                    <span style={{ display: 'block', fontWeight: 800, fontSize: 14.5 }}>{m.title}</span>
                    <span style={{ display: 'block', fontSize: 12.5, color: COLORS.textDim, marginTop: 2 }}>{m.desc}</span>
                  </span>
                </button>
              ))}
              {error && <div style={{ color: '#dc2626', fontSize: 13 }}>{error}</div>}
            </div>
            <div style={{ padding: '14px 16px', borderTop: `1px solid ${COLORS.border}`, display: 'flex', gap: 8 }}>
              <button onClick={() => setStage('address')} style={{ padding: 13, borderRadius: 12, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontWeight: 700, cursor: 'pointer' }}>←</button>
              <button onClick={payMode === 'online' ? payOnline : place} disabled={busy}
                style={{ flex: 1, padding: 13, borderRadius: 12, border: 'none', background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff', fontWeight: 800, fontSize: 15, cursor: 'pointer', opacity: busy ? 0.7 : 1 }}>
                {busy ? 'Placing…' : payMode === 'cod' ? `Place order — ${money(subtotal)}` : `Pay & order — ${money(subtotal)}`}
              </button>
            </div>
          </>
        )}

        {stage === 'done' && placed && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '28px 18px', textAlign: 'center' }}>
            <div style={{ fontSize: 46, marginBottom: 8 }}>🎉</div>
            <div style={{ fontWeight: 900, fontSize: 20, marginBottom: 6 }}>Order #{placed.id} confirmed!</div>
            <div style={{ color: COLORS.textDim, fontSize: 13.5, lineHeight: 1.7, marginBottom: 18 }}>
              {site.name} will contact you on {form.phone} to confirm delivery.<br />
              {payMode === 'cod' ? 'Keep the amount ready at delivery.' : 'Complete payment on the link sent to you for faster dispatch.'}
            </div>
            {wa && (
              <a href={`https://wa.me/${wa}?text=${encodeURIComponent(`Namaste, I placed order #${placed.id}.`)}`} target="_blank" rel="noopener noreferrer"
                style={{ display: 'inline-block', background: '#16a34a', color: '#fff', fontWeight: 700, fontSize: 13.5, borderRadius: 10, padding: '11px 18px', textDecoration: 'none', marginBottom: 14 }}>
                Confirm on WhatsApp
              </a>
            )}
            <div><button onClick={onClose} style={{ padding: '11px 22px', borderRadius: 10, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.text, fontWeight: 700, cursor: 'pointer' }}>Continue shopping</button></div>
          </div>
        )}
      </div>
    </div>
  )
}


function BannerCarousel({ banners }) {
  const [idx, setIdx] = useState(0)
  useEffect(() => {
    if (banners.length < 2) return
    const t = setInterval(() => setIdx((i) => (i + 1) % banners.length), 4500)
    return () => clearInterval(t)
  }, [banners.length])
  const b = banners[idx] || banners[0]
  return (
    <div style={{ position: 'relative', height: 'min(300px, 38vw)', minHeight: 180, background: '#0f172a' }}>
      {banners.map((bn, i) => (
        <img key={i} src={bn.image} alt="" style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
          opacity: i === idx ? 1 : 0, transition: 'opacity 0.6s ease',
        }} />
      ))}
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(0,0,0,0.15), rgba(0,0,0,0.55))', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: '26px 22px' }}>
        {b.title && <div style={{ color: '#fff', fontWeight: 900, fontSize: 'clamp(20px, 4vw, 34px)', textShadow: '0 2px 12px rgba(0,0,0,0.5)' }}>{b.title}</div>}
        {b.subtitle && <div style={{ color: 'rgba(255,255,255,0.92)', fontSize: 'clamp(13px, 2.2vw, 16px)', marginTop: 4, textShadow: '0 1px 8px rgba(0,0,0,0.5)' }}>{b.subtitle}</div>}
        <a href={b.link || '#/shop'} style={{ marginTop: 12, alignSelf: 'flex-start', background: '#fff', color: '#0f172a', fontWeight: 800, fontSize: 14, borderRadius: 999, padding: '10px 20px', textDecoration: 'none' }}>Shop now →</a>
      </div>
      {banners.length > 1 && (
        <div style={{ position: 'absolute', bottom: 12, right: 16, display: 'flex', gap: 6 }}>
          {banners.map((_, i) => (
            <button key={i} onClick={() => setIdx(i)} style={{ width: i === idx ? 22 : 8, height: 8, borderRadius: 999, border: 'none', cursor: 'pointer', background: i === idx ? '#fff' : 'rgba(255,255,255,0.5)', transition: 'width 0.3s' }} />
          ))}
        </div>
      )}
    </div>
  )
}

function sectionProducts(sec, products) {
  if (sec.kind === 'manual' || (sec.product_ids || []).length) {
    return (sec.product_ids || []).map((id) => products.find((p) => p.id === id)).filter(Boolean)
  }
  const day = Math.floor(Date.now() / 86400000)
  if (sec.kind === 'bestselling') return products.slice(0, 8)
  if (sec.kind === 'top') return [...products].sort((a, b) => b.price - a.price).slice(0, 8)
  return [...products].sort((a, b) => ((a.id * day) % 100) - ((b.id * day) % 100)).slice(0, 8)
}

export function ShopPage({ site, resolve, theme, COLORS, slug }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const products = (site._products || [])
  const cats = [...new Set(products.map((p) => p.category).filter(Boolean))]
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('all')
  const [sort, setSort] = useState('featured')
  const [cartOpen, setCartOpen] = useState(false)
  const cart = useCart(slug || site.slug)

  let list = products.filter((p) => (cat === 'all' || p.category === cat) &&
    (!q.trim() || (p.name + ' ' + (p.description || '')).toLowerCase().includes(q.trim().toLowerCase())))
  if (sort === 'low') list = [...list].sort((a, b) => a.price - b.price)
  if (sort === 'high') list = [...list].sort((a, b) => b.price - a.price)

  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <ShopHeader site={site} slug={slug} cart={cart} COLORS={COLORS} theme={theme} onCart={() => setCartOpen(true)} />
      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} cart={cart} products={products} COLORS={COLORS} theme={theme} site={site} resolve={resolve} slug={slug || site.slug} />

      {/* banner carousel (tenant-controlled) or default hero */}
      {(site.settings?.storeBanners || []).length > 0 ? <BannerCarousel banners={site.settings.storeBanners} /> : (
        <div style={{ background: gradient, color: '#fff', padding: '46px 20px', textAlign: 'center' }}>
          <h1 style={{ fontSize: 33, fontWeight: 900, margin: '0 0 8px', letterSpacing: '-0.5px' }}>{site.name} Store</h1>
          <p style={{ margin: 0, fontSize: 15, opacity: 0.92 }}>Certified gemstones, rudraksha, bracelets & healing puja kits · Energised before dispatch · Free delivery</p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 16, flexWrap: 'wrap', fontSize: 13, fontWeight: 700 }}>
            <span>🚚 Free shipping</span><span>💵 Cash on delivery</span><span>✅ 100% authentic</span>
          </div>
        </div>
      )}

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '22px 16px 90px' }}>
        {/* search + filters */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search gemstones, rudraksha…"
            style={{ flex: 1, minWidth: 200, padding: '11px 16px', borderRadius: 999, border: `1px solid ${COLORS.border}`, background: COLORS.surface, color: COLORS.text, fontSize: 14, outline: 'none' }} />
          <select value={sort} onChange={(e) => setSort(e.target.value)} style={{ padding: '10px 14px', borderRadius: 999, border: `1px solid ${COLORS.border}`, background: COLORS.surface, color: COLORS.text, fontSize: 13 }}>
            <option value="featured">Featured</option><option value="low">Price: low → high</option><option value="high">Price: high → low</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 22 }}>
          <button onClick={() => setCat('all')} style={pill('all', cat, theme)}>All</button>
          {cats.map((c) => <button key={c} onClick={() => setCat(c)} style={pill(c, cat, theme)}>{c}</button>)}
        </div>

        {/* tenant-curated sections */}
        {(site.settings?.storeSections || []).map((sec, si) => {
          const secProducts = sectionProducts(sec, products)
          if (!secProducts.length) return null
          return (
            <div key={si} style={{ marginBottom: 26 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>
                  {sec.kind === 'bestselling' ? '🏆 ' : sec.kind === 'trending' ? '📈 ' : sec.kind === 'top' ? '⭐ ' : ''}{sec.title || 'Products'}
                </h2>
                <a href="#/shop" style={{ fontSize: 12.5, fontWeight: 700, color: theme.primaryColor, textDecoration: 'none' }}>View all →</a>
              </div>
              <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 6, scrollSnapType: 'x mandatory' }}>
                {secProducts.map((p) => (
                  <a key={p.id} href={`#/shop/${p.id}`} style={{ textDecoration: 'none', color: 'inherit', flex: '0 0 170px', scrollSnapAlign: 'start' }}>
                    <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 14, overflow: 'hidden', height: '100%' }}>
                      {p.images?.[0] && !isVideoSrc(p.images[0])
                        ? <img src={p.images[0]} alt="" style={{ width: '100%', aspectRatio: '1/1', objectFit: 'cover', display: 'block', background: '#fff' }} />
                        : <div style={{ width: '100%', aspectRatio: '1/1', background: '#f1f5f9' }} />}
                      <div style={{ padding: 10 }}>
                        <div style={{ fontSize: 12.5, fontWeight: 700, lineHeight: 1.35, marginBottom: 4 }}>{p.name}</div>
                        <div style={{ fontWeight: 900, fontSize: 14 }}>₹{Number(p.price).toLocaleString('en-IN')}</div>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )
        })}

        {!list.length ? (
          <div style={{ textAlign: 'center', color: COLORS.textDim, padding: 60 }}>No products match — try another search.</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(225px, 1fr))', gap: 16 }}>
            {list.map((p, i) => {
              const save = p.mrp && p.mrp > p.price ? Math.round((1 - p.price / p.mrp) * 100) : 0
              return (
                <div key={p.id} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                  <a href={`#/shop/${p.id}`} style={{ textDecoration: 'none', color: 'inherit', position: 'relative', display: 'block', background: '#fff' }}>
                    {p.images?.[0]
                      ? (isVideoSrc(p.images[0])
                          ? <video src={p.images[0]} muted style={{ width: '100%', aspectRatio: '1/1', objectFit: 'cover', display: 'block' }} />
                          : <img src={p.images[0]} alt={p.name} style={{ width: '100%', aspectRatio: '1/1', objectFit: 'cover', display: 'block' }} />)
                      : <div style={{ width: '100%', aspectRatio: '1/1', background: '#f1f5f9' }} />}
                    {i < 2 && <span style={{ position: 'absolute', top: 10, left: 10, background: '#dc2626', color: '#fff', fontWeight: 800, fontSize: 10.5, borderRadius: 8, padding: '3px 8px' }}>🔥 BESTSELLER</span>}
                    {!!save && <span style={{ position: 'absolute', top: 10, right: 10, background: 'rgba(34,197,94,0.95)', color: '#fff', fontWeight: 800, fontSize: 11, borderRadius: 8, padding: '3px 8px' }}>{save}% OFF</span>}
                  </a>
                  <div style={{ padding: 13, display: 'flex', flexDirection: 'column', flex: 1 }}>
                    {p.category && <div style={{ fontSize: 10.5, fontWeight: 800, letterSpacing: 0.6, color: COLORS.textDim, textTransform: 'uppercase', marginBottom: 4 }}>{p.category}</div>}
                    <a href={`#/shop/${p.id}`} style={{ textDecoration: 'none', color: 'inherit', fontWeight: 700, fontSize: 14, lineHeight: 1.4, marginBottom: 6 }}>{p.name}</a>
                    <Stars id={p.id} COLORS={COLORS} />
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 7, marginTop: 8 }}>
                      <span style={{ fontWeight: 900, fontSize: 17 }}>₹{Number(p.price).toLocaleString('en-IN')}</span>
                      {!!save && <span style={{ color: COLORS.textDim, textDecoration: 'line-through', fontSize: 12.5 }}>₹{p.mrp}</span>}
                    </div>
                    <button onClick={() => { cart.add(p.id); setCartOpen(true) }}
                      style={{ marginTop: 10, width: '100%', padding: '10px 8px', borderRadius: 10, border: 'none', background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff', fontWeight: 800, fontSize: 13.5, cursor: 'pointer' }}>
                      Add to Cart
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>
      <WhatsAppFab site={site} />
    </div>
  )
}

export function ProductPage({ site, resolve, theme, COLORS, productId, slug }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const products = site._products || []
  const p = products.find((x) => String(x.id) === String(productId))
  const [img, setImg] = useState(0)
  const [cartOpen, setCartOpen] = useState(false)
  const [buyNow, setBuyNow] = useState(false)
  const cart = useCart(slug || site.slug)

  if (!p) {
    return <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 14 }}>
      <p>Product not found.</p><a href="#/shop" style={{ color: theme.primaryColor, fontWeight: 700 }}>← Back to shop</a>
    </div>
  }

  const images = (p.images?.length ? p.images : [p.image]).filter(Boolean)
  const related = products.filter((x) => x.id !== p.id && x.category && x.category === p.category).slice(0, 4)
  const save = p.mrp && p.mrp > p.price ? Math.round((1 - p.price / p.mrp) * 100) : 0

  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <ShopHeader site={site} slug={slug} cart={cart} COLORS={COLORS} theme={theme} onCart={() => setCartOpen(true)} />
      <CartDrawer open={cartOpen} onClose={() => { setCartOpen(false); setBuyNow(false) }} cart={buyNow ? cart : cart} products={products} COLORS={COLORS} theme={theme} site={site} resolve={resolve} slug={slug || site.slug} />
      <main style={{ maxWidth: 1000, margin: '0 auto', padding: '26px 16px 90px' }}>
        <div style={{ fontSize: 12.5, color: COLORS.textDim, marginBottom: 16 }}>
          <a href="#/" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Home</a> / <a href="#/shop" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Shop</a>{p.category ? <> / <span>{p.category}</span></> : null} / <span style={{ color: COLORS.text }}>{p.name}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 28 }}>
          <div>
            <div style={{ background: '#fff', borderRadius: 18, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
              {images[img] && (isVideoSrc(images[img])
                ? <video src={images[img]} controls style={{ width: '100%', aspectRatio: '1/1', objectFit: 'cover', display: 'block', background: '#0f172a' }} />
                : <img src={images[img]} alt={p.name} style={{ width: '100%', aspectRatio: '1/1', objectFit: 'cover', display: 'block' }} />)}
            </div>
            {images.length > 1 && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                {images.map((im, i) => (
                  <div key={i} onClick={() => setImg(i)} style={{ borderRadius: 10, cursor: 'pointer', border: i === img ? `2.5px solid ${theme.primaryColor}` : `1px solid ${COLORS.border}`, opacity: i === img ? 1 : 0.75 }}>
                    {isVideoSrc(im)
                      ? <video src={im} muted style={{ width: 62, height: 62, objectFit: 'cover', borderRadius: 8, display: 'block' }} />
                      : <img src={im} alt="" style={{ width: 62, height: 62, objectFit: 'cover', borderRadius: 8, display: 'block' }} />}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div>
            {p.category && <div style={{ fontSize: 11.5, fontWeight: 800, letterSpacing: 0.8, textTransform: 'uppercase', color: COLORS.textDim, marginBottom: 6 }}>{p.category}</div>}
            <h1 style={{ fontSize: 26, fontWeight: 900, margin: '0 0 10px', lineHeight: 1.25 }}>{p.name}</h1>
            <Stars id={p.id} COLORS={COLORS} />
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 9, margin: '14px 0 4px', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 900, fontSize: 30 }}>₹{Number(p.price).toLocaleString('en-IN')}</span>
              {!!save && <span style={{ color: COLORS.textDim, textDecoration: 'line-through', fontSize: 16 }}>MRP ₹{p.mrp}</span>}
              {!!save && <span style={{ background: 'rgba(34,197,94,0.12)', color: '#16a34a', fontWeight: 800, fontSize: 14, borderRadius: 8, padding: '3px 10px' }}>SAVE {save}%</span>}
            </div>
            <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 14 }}>Inclusive of all taxes · Free delivery</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#dc2626' }}>🔥 {VIEWERS(p.id)} people viewed this in the last 24 hours</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#d97706' }}>⚡ {SOLD(p.id)}+ sold this month</div>
              <div style={{ fontSize: 13, color: COLORS.textDim }}>✓ Energised & blessed before dispatch · ✓ Authenticity certificate included</div>
            </div>
            <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
              <button onClick={() => { cart.add(p.id); setCartOpen(true) }}
                style={{ flex: 1, padding: 14, borderRadius: 12, border: `1.5px solid ${theme.primaryColor}`, background: 'transparent', color: theme.primaryColor, fontWeight: 800, fontSize: 15, cursor: 'pointer' }}>
                Add to Cart
              </button>
              <button onClick={() => { cart.add(p.id); setCartOpen(true) }}
                style={{ flex: 1, padding: 14, borderRadius: 12, border: 'none', background: gradient, color: '#fff', fontWeight: 900, fontSize: 15, cursor: 'pointer' }}>
                Buy Now
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12, color: COLORS.textDim, background: 'rgba(127,127,127,0.05)', borderRadius: 12, padding: 12 }}>
              <span>💵 Cash on delivery available</span><span>⚡ UPI / online payment</span>
              <span>🚚 Free shipping in India</span><span>↩️ 7-day easy returns</span>
            </div>
          </div>
        </div>

        {p.description && (
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 22, marginTop: 26 }}>
            <h3 style={{ margin: '0 0 10px', fontSize: 15, fontWeight: 800 }}>About this product</h3>
            <div style={{ fontSize: 14, lineHeight: 1.8, color: COLORS.textDim, whiteSpace: 'pre-wrap' }}>{p.description}</div>
          </div>
        )}

        {!!(p.attributes?.length) && (
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 22, marginTop: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 800 }}>Specifications</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5 }}>
              <tbody>
                {p.attributes.map((a, i) => (
                  <tr key={i}>
                    <td style={{ padding: '8px 10px', color: COLORS.textDim, borderBottom: `1px solid ${COLORS.border}`, width: '40%' }}>{a.name}</td>
                    <td style={{ padding: '8px 10px', fontWeight: 700, borderBottom: `1px solid ${COLORS.border}` }}>{a.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {related.length > 0 && (
          <div style={{ marginTop: 26 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 800 }}>You may also like</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))', gap: 12 }}>
              {related.map((r2) => (
                <a key={r2.id} href={`#/shop/${r2.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 14, overflow: 'hidden' }}>
                    {r2.images?.[0] && !isVideoSrc(r2.images[0])
                      ? <img src={r2.images[0]} alt="" style={{ width: '100%', aspectRatio: '1/1', objectFit: 'cover', display: 'block', background: '#fff' }} />
                      : <div style={{ width: '100%', aspectRatio: '1/1', background: '#f1f5f9' }} />}
                    <div style={{ padding: 10 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 700, lineHeight: 1.35 }}>{r2.name}</div>
                      <div style={{ fontWeight: 900, fontSize: 14, marginTop: 4 }}>₹{Number(r2.price).toLocaleString('en-IN')}</div>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}
      </main>
      <WhatsAppFab site={site} />
    </div>
  )
}
const pill = (c, active, theme) => ({
  padding: '8px 16px', borderRadius: 999, cursor: 'pointer', fontSize: 13, fontWeight: 700,
  border: `1.5px solid ${active === c ? theme.primaryColor : '#cbd5e1'}`,
  background: active === c ? theme.primaryColor : 'transparent',
  color: active === c ? '#fff' : 'inherit',
})


export function HoroscopePage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [form, setForm] = useState({ date: '', time: '', place: '', lat: null, lon: null, tz: null, period: 'daily', lang: 'en' })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.date || !form.time) return setError('Please select your birth date and time')
    if (form.lat == null) return setError('Please select your birth place from the suggestions')
    setBusy(true); setError(null)
    try {
      setResult(await publicPersonalHoroscope(resolve, {
        date: form.date, time: form.time, period: form.period,
        lat: form.lat, lon: form.lon, tz: form.tz, lang: form.lang,
      }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const h = result?.horoscope || {}
  const overview = h.overview || h.description || ''
  const sections = ['career', 'love', 'finance', 'health'].filter((s) => h[s])

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/horoscope" icon={Moon}
      title="Personal Horoscope" subtitle={`Your own ${form.period === 'daily' ? 'daily' : form.period} forecast computed from your birth chart — not a generic sun-sign column. Presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={labelStyle}>Forecast period</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {HORO_PERIODS.map(([id, label]) => (
                <button type="button" key={id} onClick={() => set('period', id)} style={{
                  ...inputStyle, cursor: 'pointer', fontWeight: 700, padding: '9px 16px', borderRadius: 999,
                  background: form.period === id ? gradient : 'transparent',
                  color: form.period === id ? '#fff' : 'inherit',
                  border: form.period === id ? 'none' : `1px solid ${COLORS.border}`,
                }}>{label}</button>
              ))}
            </div>
          </div>
          <BirthFields value={form} onChange={setForm} />
          <LangSelect value={form.lang} onChange={(v) => set('lang', v)} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: 14 }}>
            {busy ? 'Reading your chart…' : 'Get My Horoscope'}
          </button>
        </motion.form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 26 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
              <div style={{ fontWeight: 800, fontSize: 18 }}>Your {result.period} horoscope</div>
              <span style={{ background: gradient, color: '#fff', fontWeight: 700, fontSize: 12, borderRadius: 8, padding: '4px 10px', textTransform: 'capitalize' }}>{result.period}</span>
            </div>
            {h.sign && <div style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 10 }}>Moon sign: <strong style={{ color: COLORS.text }}>{h.sign}</strong></div>}
            <p style={{ fontSize: 15, lineHeight: 1.8, margin: 0 }}>{overview}</p>
          </div>
          {sections.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
              {sections.map((s) => (
                <div key={s} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 20 }}>
                  <div style={{ fontWeight: 800, textTransform: 'capitalize', marginBottom: 8, fontSize: 14 }}>{s}</div>
                  {typeof h[s] === 'string'
                    ? <div style={{ fontSize: 13.5, lineHeight: 1.7, color: COLORS.textDim }}>{h[s]}</div>
                    : <>
                        <div style={{ fontSize: 12.5, color: '#16a34a', marginBottom: 6 }}>✔ {h[s]?.positive}</div>
                        <div style={{ fontSize: 12.5, color: '#d97706' }}>⚠ {h[s]?.challenging}</div>
                      </>}
                </div>
              ))}
            </div>
          )}
          {h.luckyColor && <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 16, fontSize: 13.5 }}>Lucky colour today: <strong>{h.luckyColor}</strong></div>}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button onClick={() => setResult(null)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 240 }}>Check another period</button>
            <button onClick={submit} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, background: gradient, color: '#fff', border: 'none', flex: 1, minWidth: 200 }}>Refresh forecast</button>
          </div>
        </motion.div>
      )}
    </ToolShell>
  )
}

// ─────────── NUMEROLOGY PAGE (#/numerology) ───────────
export function NumerologyPage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [form, setForm] = useState({ name: '', date: '', mobile: '', lang: 'en' })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return setError('Please enter your full name')
    if (!form.date) return setError('Please select your birth date')
    const digits = form.mobile.replace(/\D/g, '')
    if (form.mobile && !/^[6-9]\d{9}$/.test(digits)) return setError('Please enter a valid 10-digit mobile number')
    setBusy(true); setError(null)
    try {
      setResult(await publicNumerologyTool(resolve, {
        fullName: form.name.trim(), date: form.date,
        mobileNumber: form.mobile || undefined, lang: form.lang,
      }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const CARD = (num, title, desc, interp) => (
    <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 22 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <div style={{ width: 46, height: 46, borderRadius: 14, background: gradient, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 22 }}>{num}</div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 14.5 }}>{title}</div>
          {interp?.rating && <div style={{ fontSize: 12, color: interp.rating >= 4 ? '#16a34a' : interp.rating >= 3 ? '#d97706' : '#dc2626', fontWeight: 700 }}>Rating: {interp.rating}/5</div>}
        </div>
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.7, color: COLORS.textDim, marginBottom: interp ? 10 : 0 }}>{desc}</div>
      {interp && <>
        {interp.positive_traits?.length > 0 && <div style={{ marginBottom: 8 }}><strong style={{ fontSize: 12 }}>Strengths:</strong> {interp.positive_traits.join(', ')}</div>}
        {interp.challenges?.length > 0 && <div style={{ marginBottom: 8 }}><strong style={{ fontSize: 12 }}>Watch out for:</strong> {interp.challenges.join(', ')}</div>}
        {interp.career_suggestions?.length > 0 && <div style={{ marginBottom: 8 }}><strong style={{ fontSize: 12 }}>Good careers:</strong> {interp.career_suggestions.join(', ')}</div>}
        {interp.relationships && <div style={{ fontSize: 12.5 }}><strong>Relationships:</strong> {interp.relationships}</div>}
      </>}
    </div>
  )

  const unwrap = (x) => x?.data || x
  const lp = unwrap(result?.lifePath), dn = unwrap(result?.destiny), sl = unwrap(result?.soul), mb = unwrap(result?.mobile)

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/numerology" icon={Hash}
      title="Numerology" subtitle={`Your life path, destiny and soul numbers — and what your mobile number says about you. Presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
            <div><label style={labelStyle}>Full name *</label>
              <input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Name as on documents" style={inputStyle} /></div>
            <div><label style={labelStyle}>Mobile number (optional)</label>
              <input type="tel" inputMode="numeric" maxLength={15} value={form.mobile} onChange={(e) => set('mobile', e.target.value)} placeholder="Your mobile number" style={inputStyle} /></div>
          </div>
          <div><label style={labelStyle}>Birth date *</label>
            <DateSelector value={form.date} onChange={(v) => set('date', v)} /></div>
          <LangSelect value={form.lang} onChange={(v) => set('lang', v)} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: 14 }}>
            {busy ? 'Calculating…' : 'Reveal My Numbers'}
          </button>
        </motion.form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
            {lp && CARD(lp.number, 'Life Path Number', lp.description, lp.interpretation)}
            {dn && CARD(dn.number, 'Destiny Number', dn.description, dn.interpretation)}
            {sl && CARD(sl.number, 'Soul Urge Number', sl.description, sl.interpretation)}
            {mb && CARD(mb.number, 'Mobile Number', mb.description, { ...mb.interpretation, rating: mb.rating })}
          </div>
          <button onClick={() => setResult(null)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 240 }}>Check another name</button>
        </motion.div>
      )}
    </ToolShell>
  )
}

// ─────────── GEMSTONE PAGE (#/gemstone) ───────────
export function GemstonePage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [form, setForm] = useState({ date: '', time: '', place: '', lat: null, lon: null, tz: null, lang: 'en' })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.date || !form.time) return setError('Please select your birth date and time')
    if (form.lat == null) return setError('Please select your birth place from the suggestions')
    setBusy(true); setError(null)
    try {
      setResult(await publicGemstoneTool(resolve, {
        date: form.date, time: form.time, lat: form.lat, lon: form.lon, tz: form.tz, lang: form.lang,
      }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const g = (result?.gemstone?.data || result?.gemstone || {})
  const gem = g.gemstone || {}
  const wear = g.wearing || {}
  const alt = g.alternateGemstone
  const KV = ([k, v]) => v ? <div key={k} style={{ padding: '10px 14px', borderBottom: `1px solid ${COLORS.border}` }}><span style={{ color: COLORS.textDim, fontSize: 12.5, display: 'block' }}>{k}</span><span style={{ fontWeight: 700, fontSize: 14 }}>{String(v)}</span></div> : null

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/gemstone" icon={Gem}
      title="Gemstone Recommendation" subtitle={`Which gemstone suits your chart — computed from your ascendant and current dasha, not guesswork. Presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <BirthFields value={form} onChange={setForm} />
          <LangSelect value={form.lang} onChange={(v) => set('lang', v)} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: 14 }}>
            {busy ? 'Reading your chart…' : 'Find My Gemstone'}
          </button>
        </motion.form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 26, textAlign: 'center' }}>
            {gem.imageUrl && <img src={gem.imageUrl} alt={gem.name} style={{ width: 84, height: 84, borderRadius: 18, objectFit: 'cover', marginBottom: 10 }} onError={(e) => { e.currentTarget.style.display = 'none' }} />}
            <div style={{ fontSize: 26, fontWeight: 900, color: theme.primaryColor }}>{gem?.name || '—'}</div>
            {gem?.hindiName && <div style={{ color: COLORS.textDim, fontSize: 14, marginTop: 2 }}>{gem.hindiName}</div>}
            {g.planet && <div style={{ marginTop: 10, fontSize: 13, background: 'rgba(127,127,127,0.06)', borderRadius: 10, padding: '8px 14px', display: 'inline-block' }}>For planet <strong>{g.planet}</strong></div>}
            {g.recommendationReason && <div style={{ marginTop: 8, fontSize: 12.5, color: COLORS.textDim }}>Recommended because: {g.recommendationReason}</div>}
          </div>
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, overflow: 'hidden' }}>
            {[
              ['Color', gem?.color],
              ['Quality to look for', gem?.quality],
              ['Wear on finger', wear?.finger],
              ['Metal', wear?.metal],
              ['Weight', wear?.weightRange],
              ['Best day to start', wear?.day],
              ['Mantra', wear?.mantra],
            ].map(KV)}
          </div>
          {(wear?.dos?.length > 0 || wear?.donts?.length > 0) && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
              {wear?.dos?.length > 0 && (
                <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18 }}>
                  <div style={{ fontWeight: 800, color: '#16a34a', fontSize: 13, marginBottom: 10 }}>Do's</div>
                  {wear.dos.map((d, i) => <div key={i} style={{ fontSize: 13, lineHeight: 1.7 }}>✓ {d}</div>)}
                </div>
              )}
              {wear?.donts?.length > 0 && (
                <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18 }}>
                  <div style={{ fontWeight: 800, color: '#dc2626', fontSize: 13, marginBottom: 10 }}>Don'ts</div>
                  {wear.donts.map((d, i) => <div key={i} style={{ fontSize: 13, lineHeight: 1.7 }}>✕ {d}</div>)}
                </div>
              )}
            </div>
          )}
          {alt && (
            <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18 }}>
              <div style={{ fontWeight: 800, fontSize: 13.5, marginBottom: 6 }}>Alternative: {alt.name} {alt.hindiName ? `(${alt.hindiName})` : ''}</div>
              <div style={{ fontSize: 13, color: COLORS.textDim }}>{alt.reason}</div>
            </div>
          )}
          <div style={{ fontSize: 12.5, color: COLORS.textDim }}>Gemstones influence your chart's energy — {site?.name || 'consult your astrologer'} can confirm the right weight and muhurat before you buy.</div>
          <button onClick={() => setResult(null)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 240 }}>Check another chart</button>
        </motion.div>
      )}
    </ToolShell>
  )
}

// ─────────── MUHURAT PAGE (#/muhurat) ───────────
const MUHURAT_TASKS = [
  ['marriage', 'Marriage', '💍'], ['engagement', 'Engagement', '💞'],
  ['business-opening', 'Business opening', '🏪'], ['house-warming', 'House warming (Griha Pravesh)', '🏠'],
  ['property-purchase', 'Property purchase', '🔑'], ['vehicle-purchase', 'Vehicle purchase', '🚗'],
  ['naming-ceremony', 'Naming ceremony (Namkaran)', '👶'],
]

export function MuhuratPage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [task, setTask] = useState('marriage')
  const [date, setDate] = useState('')
  const [lang, setLang] = useState('en')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    if (!date) return setError('Please select the date you are planning for')
    setBusy(true); setError(null)
    try {
      setResult(await publicMuhuratTool(resolve, { task, date, lang }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const m = (result?.muhurat?.data || result?.muhurat || {})
  const verdict = m.verdict || m.recommendation
  const windows = m.muhurat || m.favorablePeriods || m.timeWindows || []
  const good = windows.filter((w) => (w.rating || '').toLowerCase() !== 'avoid')
  const notes = m.reasons || m.notes || []
  const panchang = m.panchang || {}

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/muhurat" icon={CalendarDays}
      title="Shubh Muhurat" subtitle={`Find the auspicious time for weddings, griha pravesh, business openings and more — checked against tithi, nakshatra, rahu kaal and choghadiya. Presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div><label style={labelStyle}>What are you planning? *</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 8 }}>
              {MUHURAT_TASKS.map(([id, label, emoji]) => (
                <button type="button" key={id} onClick={() => setTask(id)} style={{
                  ...inputStyle, cursor: 'pointer', textAlign: 'left', fontWeight: 700, padding: '12px 14px',
                  borderColor: task === id ? theme.primaryColor : COLORS.border,
                  background: task === id ? `${theme.primaryColor}14` : 'transparent',
                }}>{emoji} {label}</button>
              ))}
            </div>
          </div>
          <div><label style={labelStyle}>Planning date *</label>
            <DateSelector value={date} onChange={setDate} /></div>
          <LangSelect value={lang} onChange={setLang} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: 14 }}>
            {busy ? 'Checking the panchang…' : 'Find Auspicious Timings'}
          </button>
        </motion.form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 26 }}>
            <div style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 6 }}>{MUHURAT_TASKS.find(([id]) => id === result.task)?.[1]} — {fmtDate(result.date)}</div>
            <div style={{ fontSize: 20, fontWeight: 900, color: good.length > 0 ? '#16a34a' : '#d97706' }}>
              {good.length > 0 ? `✓ ${good.length} auspicious window${good.length > 1 ? 's' : ''} found` : 'No clear auspicious window — pick another date'}
            </div>
            {m.description && <p style={{ fontSize: 14, lineHeight: 1.7, margin: '10px 0 0' }}>{m.description}</p>}
          </div>
          {panchang.tithi && (
            <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18, display: 'flex', gap: 18, flexWrap: 'wrap', fontSize: 13.5 }}>
              <span>Tithi: <strong>{panchang.tithi}</strong></span>
              <span>Nakshatra: <strong>{panchang.nakshatra}</strong></span>
              <span>Yoga: <strong>{panchang.yoga}</strong></span>
              {m.sunrise && <span>Sunrise <strong>{m.sunrise}</strong> · Sunset <strong>{m.sunset}</strong></span>}
            </div>
          )}
          {windows.length > 0 && (
            <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 20 }}>
              <div style={{ fontWeight: 800, fontSize: 13, letterSpacing: 0.8, textTransform: 'uppercase', color: COLORS.textDim, marginBottom: 12 }}>Choghadiya windows</div>
              {windows.map((w, i) => {
                const bad = (w.rating || '').toLowerCase() === 'avoid'
                return (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: `1px solid ${COLORS.border}`, fontSize: 13.5, flexWrap: 'wrap' }}>
                    <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ width: 9, height: 9, borderRadius: 99, background: bad ? '#d97706' : '#16a34a', display: 'inline-block' }} />
                      {w.name || w.choghadiya}
                    </span>
                    <span style={{ display: 'flex', gap: 14, alignItems: 'center', color: COLORS.textDim }}>
                      <strong style={{ color: COLORS.text }}>{w.startTime} – {w.endTime}</strong>
                      <span style={{ fontSize: 12 }}>{bad ? '⚠ avoid' : '✓ good'}</span>
                    </span>
                  </div>
                )
              })}
            </div>
          )}
          <button onClick={() => setResult(null)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 240 }}>Check another date</button>
        </motion.div>
      )}
    </ToolShell>
  )
}

// ─────────── LUCKY FINDER PAGE (#/lucky) ───────────
export function LuckyPage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [date, setDate] = useState('')
  const [lang, setLang] = useState('en')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    if (!date) return setError('Please select your birth date')
    setBusy(true); setError(null)
    try {
      setResult(await publicLuckyTool(resolve, { date, lang }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const u = (x) => x?.data || x
  const colors = u(result?.colors), numbers = u(result?.numbers), days = u(result?.days), metals = u(result?.metals)
  const Chip = ({ label, value }) => value ? (
    <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18, textAlign: 'center' }}>
      <div style={{ fontSize: 20, fontWeight: 900, color: theme.primaryColor }}>{value}</div>
      <div style={{ fontSize: 12, color: COLORS.textDim, marginTop: 4 }}>Your {label}</div>
    </div>
  ) : null
  const first = (v) => Array.isArray(v) ? v[0] : v

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} theme={theme} active="#/lucky" icon={Sparkles}
      title="Lucky Numbers & Colours" subtitle={`Your lucky numbers, colours, days and metals from numerology — quick guidance for important days. Presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div><label style={labelStyle}>Birth date *</label>
            <DateSelector value={date} onChange={setDate} /></div>
          <LangSelect value={lang} onChange={setLang} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: 14 }}>
            {busy ? 'Calculating…' : 'Find My Lucky Charms'}
          </button>
        </motion.form>
      ) : (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
            <Chip label="lucky number" value={first(numbers?.luckyNumbers || numbers?.luckyNumber)} />
            <Chip label="lucky colour" value={first(colors?.luckyColors || colors?.luckyColor)} />
            <Chip label="lucky day" value={first(days?.luckyDays || days?.luckyDay)} />
            <Chip label="lucky metal" value={first(metals?.luckyMetals || metals?.luckyMetal)} />
          </div>
          {(colors?.description || numbers?.description) && (
            <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 18, fontSize: 13.5, lineHeight: 1.8 }}>
              {colors?.description || numbers?.description}
            </div>
          )}
          <button onClick={() => setResult(null)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 240 }}>Check another birth date</button>
        </motion.div>
      )}
    </ToolShell>
  )
}

// ─────────── ABOUT / SERVICES / CONTACT SITE PAGES ───────────
export function AboutPage({ site, pages, theme, COLORS, slug }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const about = (pages?.about?.content) || {}
  const home = (pages?.home?.content) || {}
  const title = about.title || home.aboutTitle || `About ${site?.name || 'Us'}`
  const text = about.text || home.aboutText || 'A dedicated Vedic astrologer helping people find clarity through kundli analysis.'
  const socials = site?.settings || {}
  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <TenantHeader site={site} theme={theme} COLORS={COLORS} showStore active="#/about" />
      <main style={{ maxWidth: 760, margin: '0 auto', padding: '48px 20px 90px' }}>
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <div style={{ width: 84, height: 84, borderRadius: 26, background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 900, fontSize: 34, margin: '0 auto 18px' }}>
            {(site?.name || 'A').charAt(0)}
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 900, margin: '0 0 10px' }}>{title}</h1>
          <p style={{ color: COLORS.textDim, fontSize: 15, lineHeight: 1.8, whiteSpace: 'pre-line' }}>{text}</p>
        </div>
        {(home.statsYears || home.statsReadings || home.statsRating) && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 30 }}>
            {home.statsYears && <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 20, textAlign: 'center' }}><div style={{ fontSize: 24, fontWeight: 900, color: theme.primaryColor }}>{home.statsYears}</div><div style={{ fontSize: 12, color: COLORS.textDim }}>Years of practice</div></div>}
            {home.statsReadings && <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 20, textAlign: 'center' }}><div style={{ fontSize: 24, fontWeight: 900, color: theme.primaryColor }}>{home.statsReadings}</div><div style={{ fontSize: 12, color: COLORS.textDim }}>Kundlis read</div></div>}
            {home.statsRating && <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 20, textAlign: 'center' }}><div style={{ fontSize: 24, fontWeight: 900, color: theme.primaryColor }}>{home.statsRating}</div><div style={{ fontSize: 12, color: COLORS.textDim }}>Client rating</div></div>}
          </div>
        )}
        {Array.isArray(home.whyPoints) && home.whyPoints.length > 0 && (
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 24 }}>
            <div style={{ fontWeight: 800, marginBottom: 14 }}>Why clients choose {site?.name}</div>
            {home.whyPoints.map((w, i) => <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 10, fontSize: 14, lineHeight: 1.6 }}>✦ <span>{w}</span></div>)}
          </div>
        )}
        <div style={{ textAlign: 'center', marginTop: 34 }}>
          <a href="#services"><button style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, background: gradient, color: '#fff', border: 'none', padding: '13px 26px' }}>Explore services</button></a>
        </div>
      </main>
      <WhatsAppFab site={site} />
    </div>
  )
}

export function ServicesPage({ site, services, theme, COLORS, resolve }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <TenantHeader site={site} theme={theme} COLORS={COLORS} showStore active="#/services" />
      <main style={{ maxWidth: 900, margin: '0 auto', padding: '48px 20px 90px' }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <h1 style={{ fontSize: 32, fontWeight: 900, margin: '0 0 10px' }}>Services & Consultations</h1>
          <p style={{ color: COLORS.textDim, fontSize: 15 }}>Every session is prepared personally by {site?.name || 'your astrologer'} — pick a service below to see available times and book online.</p>
        </div>
        {(services || []).length === 0 ? (
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 40, textAlign: 'center', color: COLORS.textDim }}>
            Services are being updated — please check back soon, or <a href="#contact" style={{ color: theme.primaryColor }}>get in touch</a>.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
            {services.map((s) => (
              <div key={s.id} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 24, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontWeight: 800, fontSize: 16 }}>{s.name}</div>
                {s.description && <div style={{ fontSize: 13.5, color: COLORS.textDim, lineHeight: 1.7, flex: 1 }}>{s.description}</div>}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                  <span style={{ fontWeight: 900, fontSize: 18, color: theme.primaryColor }}>₹{s.price}</span>
                  <span style={{ fontSize: 12, color: COLORS.textDim }}>⏱ {s.duration_minutes} min</span>
                </div>
                <a href={`#book-${s.id}`}><button style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, background: gradient, color: '#fff', border: 'none', padding: 11 }}>Book this service</button></a>
              </div>
            ))}
          </div>
        )}
      </main>
      <WhatsAppFab site={site} />
    </div>
  )
}

export function ContactPage({ site, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const s = site?.settings || {}
  const rows = [
    ['Email', s.email, '✉️'],
    ['Phone / WhatsApp', s.phone, '📞'],
    ['City', s.city, '📍'],
    ['Website', s.websiteUrl, '🌐'],
  ].filter(([, v]) => !!v)
  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <TenantHeader site={site} theme={theme} COLORS={COLORS} showStore active="#/contact" />
      <main style={{ maxWidth: 640, margin: '0 auto', padding: '48px 20px 90px' }}>
        <div style={{ textAlign: 'center', marginBottom: 34 }}>
          <h1 style={{ fontSize: 32, fontWeight: 900, margin: '0 0 10px' }}>Get in Touch</h1>
          <p style={{ color: COLORS.textDim, fontSize: 15, lineHeight: 1.8 }}>Questions about a reading, booking or remedy? {site?.name || 'We'} usually reply the same day.</p>
        </div>
        {rows.length === 0 ? (
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 40, textAlign: 'center', color: COLORS.textDim }}>
            Contact details coming soon — meanwhile, use the booking form on the <a href="#services" style={{ color: theme.primaryColor }}>services page</a>.
          </div>
        ) : (
          <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, overflow: 'hidden' }}>
            {rows.map(([label, value, icon]) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 22px', borderBottom: `1px solid ${COLORS.border}`, gap: 12 }}>
                <span style={{ display: 'flex', gap: 8, alignItems: 'center', color: COLORS.textDim, fontSize: 13.5 }}>{icon} {label}</span>
                <span style={{ fontWeight: 700, fontSize: 14.5, wordBreak: 'break-all' }}>{value}</span>
              </div>
            ))}
          </div>
        )}
        <div style={{ textAlign: 'center', marginTop: 30 }}>
          <a href="#services"><button style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, background: gradient, color: '#fff', border: 'none', padding: '13px 26px' }}>Book a consultation</button></a>
        </div>
      </main>
      <WhatsAppFab site={site} />
    </div>
  )
}
