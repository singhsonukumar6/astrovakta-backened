import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, ChevronDown, ChevronRight, Heart, ScrollText, Sparkles, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'
import PlaceAutocomplete from '../components/PlaceAutocomplete.jsx'
import { signUpWithEmailAndVerify } from '../lib/firebase.js'
import { publicKundliTool, publicKundliFull, publicMatchingTool, publicDoshaTool } from '../lib/api.js'

// ─────────── shared bits for tenant tool pages ───────────
const errText = (e) => {
  const d = e?.response?.data
  const msg = d?.data?.detail || d?.detail || d?.message
  return (typeof msg === 'string' && msg) || 'Something went wrong — please try again'
}

function ToolShell({ site, COLORS, gradient, title, subtitle, icon: Icon, children }) {
  return (
    <div style={{ minHeight: '100vh', background: COLORS.bg, color: COLORS.text }}>
      <header style={{ background: COLORS.surface, borderBottom: `1px solid ${COLORS.border}`, padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <a href="#/" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none', color: COLORS.text, fontWeight: 800, fontSize: 15 }}>
          <ArrowLeft size={16} /> {site?.name || 'Home'}
        </a>
        <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontWeight: 700, fontSize: 14 }}>
          <Icon size={16} color={theme_color(gradient)} /> {title}
        </span>
      </header>
      <main style={{ maxWidth: 900, margin: '0 auto', padding: '36px 18px 90px' }}>
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <h1 style={{ fontSize: 32, fontWeight: 900, letterSpacing: '-0.5px', margin: '0 0 10px' }}>{title}</h1>
          <p style={{ color: COLORS.textDim, fontSize: 15, lineHeight: 1.7, maxWidth: 560, margin: '0 auto' }}>{subtitle}</p>
        </div>
        {children}
      </main>
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

function DateSelector({ value, onChange }) {
  const [y, m, d] = value ? value.split('-').map(Number) : [null, null, null]
  const thisYear = new Date().getFullYear()
  const years = []
  for (let v = thisYear; v >= 1900; v--) years.push(v)
  const maxDay = y && m ? new Date(y, m, 0).getDate() : 31
  const set = (ny, nm, nd) => {
    if (!ny || !nm || !nd) return onChange('')
    const day = Math.min(nd, new Date(ny, nm, 0).getDate())
    onChange(`${ny}-${String(nm).padStart(2, '0')}-${String(day).padStart(2, '0')}`)
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr 1.1fr', gap: 8 }}>
      <Sel placeholder="Day" value={d || ''} options={Array.from({ length: maxDay }, (_, i) => ({ value: i + 1, label: i + 1 }))} onChange={(v) => set(y, m, Number(v))} />
      <Sel placeholder="Month" value={m || ''} options={MONTHS_FULL.map((nm, i) => ({ value: i + 1, label: nm }))} onChange={(v) => set(y, Number(v), d)} />
      <Sel placeholder="Year" value={y || ''} options={years.map((v) => ({ value: v, label: v }))} onChange={(v) => set(Number(v), m, d)} />
    </div>
  )
}

function TimeSelector({ value, onChange }) {
  const [h24, mn] = value ? value.split(':').map(Number) : [null, null]
  const h12 = h24 == null ? null : (h24 % 12 || 12)
  const ap = h24 == null ? '' : (h24 < 12 ? 'AM' : 'PM')
  const set = (nh, nm, nap) => {
    if (nh == null || nm == null || !nap) return onChange('')
    const h = nap === 'PM' ? (nh % 12) + 12 : nh % 12
    onChange(`${String(h).padStart(2, '0')}:${String(nm).padStart(2, '0')}`)
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.1fr', gap: 8 }}>
      <Sel placeholder="Hour" value={h12 || ''} options={Array.from({ length: 12 }, (_, i) => ({ value: i + 1, label: String(i + 1).padStart(2, '0') }))} onChange={(v) => set(Number(v), mn, ap || 'AM')} />
      <Sel placeholder="Min" value={mn == null ? '' : mn} options={Array.from({ length: 60 }, (_, i) => ({ value: i, label: String(i).padStart(2, '0') }))} onChange={(v) => set(h12, Number(v), ap || 'AM')} />
      <Sel placeholder="AM/PM" value={ap} options={[{ value: 'AM', label: 'AM' }, { value: 'PM', label: 'PM' }]} onChange={(v) => set(h12, mn, v)} />
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

// ─────────── DETAILED KUNDLI PAGE (#/kundli) ───────────
export function KundliPage({ site, resolve, theme, COLORS }) {
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const [form, setForm] = useState({ name: '', phone: '', date: '', time: '', place: '', lat: null, lon: null, tz: null })
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
      }
      const res = await publicKundliFull(resolve, payload)
      setResult(res.core)
      setFull(res)
      publicDoshaTool(resolve, {
        date: form.date, time: form.time,
        lat: form.lat ?? undefined, lon: form.lon ?? undefined, tz: form.tz || undefined,
      }).then(setDosha).catch(() => setDosha(null))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} icon={ScrollText}
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
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    if (!boy.date || !boy.time || !girl.date || !girl.time) { setError('Please enter birth date and time for both partners'); return }
    setBusy(true); setError(null)
    try {
      const clean = (p) => ({ date: p.date, time: p.time, lat: p.lat ?? undefined, lon: p.lon ?? undefined, tz: p.tz || undefined, place: p.place || undefined })
      setResult(await publicMatchingTool(resolve, { boy: clean(boy), girl: clean(girl) }))
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  const scorePct = result ? Math.round((result.summary?.totalScore || 0) / 36 * 100) : 0

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} icon={Heart}
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
    window.location.hash = '#/'
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
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} icon={Heart}
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
