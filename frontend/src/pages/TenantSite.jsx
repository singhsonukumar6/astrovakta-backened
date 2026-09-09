import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Star, Calendar, Clock, Check, Sparkles, Moon, ArrowRight,
  ChevronLeft, ChevronRight, Globe, BadgeCheck, Sparkle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  getPublicSite, getPublicAvailability, publicBook, publicKundliTool, publicPanchangTool,
} from '../lib/api.js'
import { tenantSiteUrl, tenantSubdomainLabel } from '../lib/tenant.js'

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Tenant sites own their SEO (they're the astrologer's brand, not AstroVakta
// pages) — the platform SeoManager skips /s/ paths, so set meta directly.
function TenantHead({ site, home }) {
  useEffect(() => {
    const title = `${site.name}${site.tagline ? ` — ${site.tagline}` : ' · Vedic Astrologer'}`
    const description = (home.heroSubtitle || `${site.name}. ${site.tagline || 'Vedic astrology consultations'} — book online in minutes.`).slice(0, 300)
    const canonicalUrl = site.custom_domain ? `https://${site.custom_domain}` : tenantSiteUrl(site.slug)
    const upsert = (attr, key, content) => {
      let el = document.head.querySelector(`meta[${attr}="${key}"]`)
      if (!el) { el = document.createElement('meta'); el.setAttribute(attr, key); document.head.appendChild(el) }
      el.setAttribute('content', content)
    }
    document.title = title
    upsert('name', 'description', description)
    upsert('name', 'robots', 'index, follow, max-image-preview:large')
    upsert('property', 'og:title', title)
    upsert('property', 'og:description', description)
    upsert('property', 'og:type', 'website')
    upsert('property', 'og:site_name', site.name)
    upsert('property', 'og:url', canonicalUrl)
    let canonical = document.head.querySelector('link[rel="canonical"]')
    if (!canonical) { canonical = document.createElement('link'); canonical.setAttribute('rel', 'canonical'); document.head.appendChild(canonical) }
    canonical.setAttribute('href', canonicalUrl)
  }, [site.slug, site.name, site.tagline, site.custom_domain, home.heroSubtitle])
  return null
}

const errDetail = (e, fallback = 'Something went wrong — please try again') => {
  const d = e?.response?.data
  const msg = d?.detail || d?.data?.detail || d?.message
  return typeof msg === 'string' ? msg : fallback
}

const toMin = (t) => {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}
const toHHMM = (mins) => `${String(Math.floor(mins / 60)).padStart(2, '0')}:${String(mins % 60).padStart(2, '0')}`

// ═══════════════ BOOKING WIDGET ═══════════════
function BookingWidget({ site, resolve, services, theme }) {
  const [avail, setAvail] = useState(null)
  const [weekOffset, setWeekOffset] = useState(0)
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedTime, setSelectedTime] = useState(null)
  const [serviceId, setServiceId] = useState(services[0]?.id || null)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [confirmed, setConfirmed] = useState(null)

  const service = services.find((s) => s.id === serviceId) || null
  const duration = service?.duration_minutes || 30

  const loadAvail = (from) => {
    getPublicAvailability(resolve, from ? { weeks: 2, date_from: from } : { weeks: 2 })
      .then((a) => { setAvail(a) })
      .catch(() => setAvail({ days: [], weekly_hours: [], booked: [] }))
  }

  useEffect(() => { loadAvail(null) }, [resolve]) // eslint-disable-line

  // ── grid: one row per open weekday-rule, slots at 30-min boundaries ──
  const slotsByDate = useMemo(() => {
    if (!avail || !avail.days) return {}
    const rulesByDay = {}
    ;(avail.weekly_hours || []).forEach((r) => {
      rulesByDay[r.weekday] = rulesByDay[r.weekday] || []
      rulesByDay[r.weekday].push(r)
    })
    const booked = (avail.booked || []).filter((b) => b.date === selectedDate)
    const out = {}
    avail.days.forEach((d) => {
      const rules = rulesByDay[d.weekday] || []
      if (!rules.length) return
      const slots = []
      rules.forEach((r) => {
        const end = toMin(r.end_time) - duration
        for (let t = toMin(r.start_time); t <= end; t += 30) {
          const slotEnd = t + duration
          const taken = booked.some((b) => t < toMin(b.end_time) && toMin(b.start_time) < slotEnd)
          // don't offer slots on past dates/times
          const isPast = new Date(`${d.date}T${toHHMM(t)}:00`) < new Date()
          if (!taken && !isPast) slots.push(toHHMM(t))
        }
      })
      if (slots.length) out[d.date] = slots
    })
    return out
  }, [avail, selectedDate, duration])

  const visibleDays = useMemo(() => {
    if (!avail?.days) return []
    const start = weekOffset * 7
    return avail.days.slice(start, start + 7)
  }, [avail, weekOffset])

  useEffect(() => { setSelectedTime(null) }, [selectedDate, serviceId])

  const maxWeek = avail?.days ? Math.floor((avail.days.length - 1) / 7) - 1 : 0

  const book = async () => {
    if (!selectedDate || !selectedTime) return toast.error('Pick a date and time first')
    if (!name.trim()) return toast.error('Please enter your name')
    setConfirming(true)
    try {
      const res = await publicBook(resolve, {
        service_id: serviceId, client_name: name.trim(), client_phone: phone.trim() || undefined,
        notes: notes.trim() || undefined, date: selectedDate, start_time: selectedTime,
      })
      setConfirmed(res?.booking || {})
      toast.success(res?.message || 'Appointment confirmed!')
      loadAvail(selectedDate)
    } catch (e) {
      toast.error(errDetail(e))
      loadAvail(selectedDate)
    } finally { setConfirming(false) }
  }

  const inputStyle = {
    width: '100%', padding: '11px 14px', borderRadius: 10, fontSize: 14,
    border: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.15)',
    color: 'inherit', outline: 'none',
  }

  if (confirmed) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 16px' }}>
        <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
          style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(34,197,94,0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
          <Check size={32} color="#22c55e" />
        </motion.div>
        <h3 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Appointment confirmed!</h3>
        <p style={{ opacity: 0.75, marginBottom: 20, lineHeight: 1.6 }}>
          {confirmed.date} at {confirmed.start_time} — {confirmed.end_time}<br />
          {service ? `${service.name} · ${confirmed.amount ? `₹${confirmed.amount}` : ''}` : ''}
        </p>
        <p style={{ opacity: 0.6, fontSize: 14 }}>
          The astrologer has been notified and will contact you{confirmed.client_phone ? ` on ${confirmed.client_phone}` : ''}.
        </p>
        <button onClick={() => { setConfirmed(null); setSelectedDate(null); setSelectedTime(null); setName(''); setPhone('') }}
          style={{ ...inputStyle, maxWidth: 220, marginTop: 20, padding: '11px 14px', cursor: 'pointer', fontWeight: 600, background: 'var(--gradient-primary)', color: '#fff', border: 'none' }}>
          Book another
        </button>
      </div>
    )
  }

  return (
    <div>
      {/* Step 1: service */}
      <div style={{ fontSize: 13, fontWeight: 700, opacity: 0.6, marginBottom: 10, letterSpacing: 0.5 }}>1 · CHOOSE A SERVICE</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
        {services.map((s) => (
          <button key={s.id} onClick={() => setServiceId(s.id)} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10,
            padding: '12px 16px', borderRadius: 12, cursor: 'pointer', textAlign: 'left',
            border: `1.5px solid ${serviceId === s.id ? theme.primaryColor : 'var(--border-color)'}`,
            background: serviceId === s.id ? `color-mix(in srgb, ${theme.primaryColor} 12%, transparent)` : 'transparent',
            color: 'inherit',
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>{s.name}</div>
              <div style={{ fontSize: 12, opacity: 0.65 }}>{s.duration_minutes} min</div>
            </div>
            <div style={{ fontWeight: 800, fontSize: 15 }}>{s.price > 0 ? `₹${s.price}` : 'Free'}</div>
          </button>
        ))}
      </div>

      {/* Step 2: date */}
      <div style={{ fontSize: 13, fontWeight: 700, opacity: 0.6, marginBottom: 10, letterSpacing: 0.5 }}>2 · PICK A DATE</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 24 }}>
        <button onClick={() => setWeekOffset((w) => Math.max(0, w - 1))} disabled={weekOffset === 0}
          style={{ border: '1px solid var(--border-color)', background: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: 'inherit', opacity: weekOffset === 0 ? 0.3 : 1 }}>
          <ChevronLeft size={16} />
        </button>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 6, flex: 1 }}>
          {visibleDays.map((d) => {
            const dt = new Date(`${d.date}T00:00:00`)
            const open = !!(slotsByDate[d.date] || []).length
            const sel = selectedDate === d.date
            return (
              <button key={d.date} disabled={!open} onClick={() => setSelectedDate(d.date)} style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                padding: '8px 2px', borderRadius: 10, cursor: open ? 'pointer' : 'not-allowed',
                border: `1.5px solid ${sel ? theme.primaryColor : 'var(--border-color)'}`,
                background: sel ? theme.primaryColor : 'transparent',
                color: sel ? '#fff' : open ? 'inherit' : 'var(--border-color)',
                opacity: open ? 1 : 0.35,
              }}>
                <span style={{ fontSize: 10, fontWeight: 600, opacity: 0.7 }}>{DAY_LABELS[d.weekday]}</span>
                <span style={{ fontSize: 16, fontWeight: 800 }}>{dt.getDate()}</span>
              </button>
            )
          })}
        </div>
        <button onClick={() => setWeekOffset((w) => Math.min(maxWeek, w + 1))} disabled={weekOffset >= maxWeek}
          style={{ border: '1px solid var(--border-color)', background: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: 'inherit', opacity: weekOffset >= maxWeek ? 0.3 : 1 }}>
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Step 3: time */}
      {selectedDate && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ marginBottom: 24, overflow: 'hidden' }}>
          <div style={{ fontSize: 13, fontWeight: 700, opacity: 0.6, marginBottom: 10, letterSpacing: 0.5 }}>3 · PICK A TIME</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {(slotsByDate[selectedDate] || []).map((t) => (
              <button key={t} onClick={() => setSelectedTime(t)} style={{
                padding: '8px 14px', borderRadius: 10, cursor: 'pointer', fontSize: 13, fontWeight: 700,
                border: `1.5px solid ${selectedTime === t ? theme.primaryColor : 'var(--border-color)'}`,
                background: selectedTime === t ? theme.primaryColor : 'transparent',
                color: selectedTime === t ? '#fff' : 'inherit',
              }}>{t}</button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Step 4: details */}
      {selectedTime && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ overflow: 'hidden' }}>
          <div style={{ fontSize: 13, fontWeight: 700, opacity: 0.6, marginBottom: 10, letterSpacing: 0.5 }}>4 · YOUR DETAILS</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name *" style={inputStyle} />
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone (WhatsApp preferred)" style={inputStyle} />
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Birth date, time & place — helps the astrologer prepare (optional)" rows={3} style={{ ...inputStyle, resize: 'vertical' }} />
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px',
              border: '1px dashed var(--border-color)', borderRadius: 10, fontSize: 13, opacity: 0.8,
            }}>
              <span>{service?.name}</span>
              <span style={{ fontWeight: 700 }}>{selectedDate} · {selectedTime}–{toHHMM(toMin(selectedTime) + duration)}</span>
            </div>
            <button onClick={book} disabled={confirming} style={{
              ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, padding: '13px 14px', border: 'none',
              background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff',
              opacity: confirming ? 0.7 : 1,
            }}>
              {confirming ? 'Confirming…' : `Confirm booking${service?.price ? ` · ₹${service.price}` : ''}`}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center', fontSize: 12, opacity: 0.55 }}>
              <BadgeCheck size={13} /> No advance payment · You pay after the consultation
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

// ═══════════════ FREE TOOLS (kundli + panchang, powered by the platform engine) ═══════════════
function FreeTools({ site, resolve, theme, COLORS }) {
  const [panchang, setPanchang] = useState(null)
  const [form, setForm] = useState({ name: '', phone: '', date: '', time: '', place: '' })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    publicPanchangTool(resolve).then(setPanchang).catch(() => setPanchang(null))
  }, [resolve])

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.date || !form.time) { setError('Please enter your birth date and time'); return }
    setBusy(true); setError(null)
    try {
      const res = await publicKundliTool(resolve, {
        name: form.name.trim() || undefined,
        phone: form.phone.trim() || undefined,
        date: form.date, time: form.time,
        place: form.place.trim() || undefined,
      })
      setResult(res)
    } catch (err) {
      setError(errDetail(err))
    } finally { setBusy(false) }
  }

  const inputStyle = {
    width: '100%', padding: '11px 14px', borderRadius: 10, fontSize: 14,
    border: '1px solid var(--border-color)', background: 'rgba(127,127,127,0.05)',
    color: 'inherit', outline: 'none',
  }
  const card = {
    background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24,
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, alignItems: 'start' }}>
      {/* Today's panchang */}
      <div style={card}>
        <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 4 }}>Today's Panchang</h3>
        <p style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 16 }}>{panchang?.date || new Date().toISOString().slice(0, 10)}</p>
        {panchang ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 14 }}>
            {[
              ['Tithi', panchang.panchang?.tithi],
              ['Nakshatra', panchang.panchang?.nakshatra],
              ['Yoga', panchang.panchang?.yoga],
              ['Karana', panchang.panchang?.karana],
              ['Sunrise', panchang.panchang?.sunrise],
              ['Sunset', panchang.panchang?.sunset],
            ].map(([k, v]) => (
              <div key={k} style={{ padding: '8px 12px', background: 'rgba(127,127,127,0.06)', borderRadius: 10 }}>
                <div style={{ fontSize: 11, color: COLORS.textDim, fontWeight: 600 }}>{k}</div>
                <div style={{ fontWeight: 700 }}>{v || '—'}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: COLORS.textDim, fontSize: 14 }}>Loading panchang…</div>
        )}
        <p style={{ fontSize: 12, color: COLORS.textDim, marginTop: 14 }}>
          Updated daily automatically — a small taste of the Jyotish on this site.
        </p>
      </div>

      {/* Free kundli */}
      <div style={card}>
        <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 4 }}>Free Kundli Snapshot</h3>
        <p style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 16 }}>
          Enter birth details — get ascendant, moon sign, nakshatra & more instantly{` (${site.name} follows up personally if you leave your number).`}
        </p>
        {result ? (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
              {[
                ['Ascendant (Lagna)', result.ascendant?.sign],
                ['Lagna Lord', result.ascendant?.lord],
                ['Moon Sign', result.moonSign],
                ['Sun Sign', result.sunSign],
                ['Birth Nakshatra', result.moonNakshatra],
                ['Lucky Gemstone', result.gemstone?.stone],
              ].map(([k, v]) => (
                <div key={k} style={{ padding: '10px 12px', background: 'rgba(127,127,127,0.06)', borderRadius: 10 }}>
                  <div style={{ fontSize: 11, color: COLORS.textDim, fontWeight: 600 }}>{k}</div>
                  <div style={{ fontWeight: 800, fontSize: 15 }}>{v || '—'}</div>
                </div>
              ))}
            </div>
            <div style={{ maxHeight: 180, overflowY: 'auto', border: `1px solid ${COLORS.border}`, borderRadius: 10 }}>
              <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ textAlign: 'left', color: COLORS.textDim }}>
                    <th style={{ padding: '8px 12px', fontWeight: 600 }}>Planet</th>
                    <th style={{ padding: '8px 12px', fontWeight: 600 }}>Sign</th>
                    <th style={{ padding: '8px 12px', fontWeight: 600 }}>Nakshatra</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.planets || []).map((p) => (
                    <tr key={p.name} style={{ borderTop: `1px solid ${COLORS.border}` }}>
                      <td style={{ padding: '7px 12px', fontWeight: 700 }}>{p.name}{p.retrograde ? ' ℞' : ''}</td>
                      <td style={{ padding: '7px 12px' }}>{p.sign}</td>
                      <td style={{ padding: '7px 12px' }}>{p.nakshatra}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {result.leadCreated && (
              <div style={{ marginTop: 14, padding: '10px 14px', borderRadius: 10, background: 'rgba(5,150,105,0.08)', color: '#059669', fontSize: 13, fontWeight: 600 }}>
                ✓ {result.astrologer} has been notified — you'll be contacted personally.
              </div>
            )}
            <button onClick={() => setResult(null)} style={{ ...inputStyle, marginTop: 14, cursor: 'pointer', fontWeight: 700, background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff', border: 'none' }}>
              Check another birth details
            </button>
          </motion.div>
        ) : (
          <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Your name" style={inputStyle} />
            <input value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="Phone (get a personal follow-up)" style={inputStyle} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <input type="date" value={form.date} onChange={(e) => set('date', e.target.value)} style={inputStyle} />
              <input type="time" value={form.time} onChange={(e) => set('time', e.target.value)} style={inputStyle} />
            </div>
            <input value={form.place} onChange={(e) => set('place', e.target.value)} placeholder="Birth place (city)" style={inputStyle} />
            {error && <div style={{ color: '#dc2626', fontSize: 13 }}>{error}</div>}
            <button type="submit" disabled={busy} style={{
              ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none',
              background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, color: '#fff',
              opacity: busy ? 0.7 : 1,
            }}>
              {busy ? 'Reading the stars…' : 'Get My Free Kundli'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

// ═══════════════ MAIN PUBLIC SITE PAGE ═══════════════
// Resolves either by slug (/s/:slug route or tenant subdomain) or by custom
// domain (when the App shell renders it for a foreign hostname).
export default function TenantSite({ slug: slugProp, domain: domainProp }) {
  const { slug: slugParam } = useParams()
  const slug = slugProp || slugParam
  // `resolve` is { slug } or { domain } — threaded through every API call.
  const resolve = domainProp ? { domain: domainProp } : { slug }
  const [bundle, setBundle] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setBundle(null); setError(null)
    getPublicSite(resolve)
      .then((b) => setBundle(b))
      .catch(() => setError('not_found'))
  }, [slug, domainProp])

  if (error === 'not_found') {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, padding: 20 }}>
        <Globe size={48} color="#64748b" />
        <h2 style={{ fontSize: 22, fontWeight: 700 }}>Site not found</h2>
        <p style={{ color: '#94a3b8', fontSize: 14 }}>This astrologer's website doesn't exist or isn't published yet.</p>
        <Link to="/" style={{ color: '#a78bfa', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
          Powered by AstroVakta <ArrowRight size={14} />
        </Link>
      </div>
    )
  }

  if (!bundle) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="gradient-text" style={{ fontSize: 18, fontWeight: 600 }}>Loading…</div>
      </div>
    )
  }

  const site = bundle.site || {}
  const theme = {
    primaryColor: site.theme?.primaryColor || '#7c3aed',
    accentColor: site.theme?.accentColor || '#eab308',
    bgStyle: site.theme?.bgStyle || 'dark',
  }
  const pages = bundle.pages || {}
  const home = pages.home?.content || {}
  const about = pages.about?.content || {}
  const services = bundle.services || []
  const light = theme.bgStyle === 'light'

  const COLORS = light
    ? { bg: '#faf9f6', surface: '#ffffff', text: '#1c1917', textDim: 'rgba(28,25,23,0.6)', border: 'rgba(28,25,23,0.12)', heroOverlay: 'rgba(255,255,255,0.6)' }
    : { bg: '#0a0a1a', surface: 'rgba(255,255,255,0.04)', text: '#f1f0ff', textDim: 'rgba(241,240,255,0.6)', border: 'rgba(255,255,255,0.1)', heroOverlay: 'rgba(10,10,26,0.6)' }

  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`

  const sectionStyle = { maxWidth: 1000, margin: '0 auto', padding: '72px 20px' }
  const h2Style = { fontSize: 32, fontWeight: 800, marginBottom: 24, color: COLORS.text, textAlign: 'center' }

  return (
    <div style={{ background: COLORS.bg, color: COLORS.text, minHeight: '100vh', fontFamily: "'Inter', system-ui, sans-serif" }}>
      <TenantHead site={site} home={home} />

      {/* ─── header ─── */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: light ? 'rgba(255,255,255,0.85)' : 'rgba(10,10,26,0.85)',
        backdropFilter: 'blur(12px)', borderBottom: `1px solid ${COLORS.border}`,
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <a href="#top" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', color: COLORS.text }}>
            {site.logo_url
              ? <img src={site.logo_url} alt={site.name} style={{ width: 38, height: 38, borderRadius: 12, objectFit: 'cover', border: `1px solid ${COLORS.border}` }} />
              : <div style={{ width: 38, height: 38, borderRadius: 12, background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 16 }}>
                  {(site.name || 'A').charAt(0)}
                </div>}
            <div>
              <div style={{ fontWeight: 800, fontSize: 16 }}>{site.name}</div>
              {site.tagline && <div style={{ fontSize: 11, opacity: 0.6 }}>{site.tagline}</div>}
            </div>
          </a>
          <nav style={{ display: 'flex', gap: 18, alignItems: 'center', fontSize: 14, fontWeight: 600, flexWrap: 'wrap' }}>
            <a href="#about" style={{ color: COLORS.textDim, textDecoration: 'none' }}>About</a>
            <a href="#services" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Services</a>
            <a href="#tools" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Free Kundli</a>
            <a href="#book" style={{
              padding: '9px 20px', borderRadius: 10, background: gradient, color: '#fff', textDecoration: 'none',
              display: 'flex', alignItems: 'center', gap: 6,
            }}><Calendar size={15} /> Book Now</a>
          </nav>
        </div>
      </header>

      {/* ─── hero ─── */}
      <section id="top" style={{
        position: 'relative', overflow: 'hidden',
        background: `radial-gradient(ellipse 80% 60% at 50% -10%, color-mix(in srgb, ${theme.primaryColor} 30%, transparent), transparent), ${COLORS.bg}`,
      }}>
        {/* stars for dark theme */}
        {!light && (
          <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
            {Array.from({ length: 36 }).map((_, i) => (
              <Sparkle key={i} size={Math.random() * 2 + 1} color={theme.accentColor} opacity={Math.random() * 0.5 + 0.2}
                style={{ position: 'absolute', left: `${Math.random() * 100}%`, top: `${Math.random() * 60}%` }} />
            ))}
          </div>
        )}
        <div style={{ ...sectionStyle, paddingTop: 72, paddingBottom: 72, position: 'relative' }}>
          <div style={{ display: 'grid', gridTemplateColumns: site.hero_image ? '1.15fr 0.85fr' : '1fr', gap: 48, alignItems: 'center' }}>
            <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px', borderRadius: 20,
                border: `1px solid ${COLORS.border}`, fontSize: 13, fontWeight: 600, color: COLORS.textDim, marginBottom: 24,
              }}>
                <Moon size={14} color={theme.accentColor} /> {site.tagline || 'Vedic Astrologer'}
              </div>
              <h1 style={{
                fontSize: 'clamp(32px, 5.4vw, 52px)', fontWeight: 900, lineHeight: 1.15, marginBottom: 20,
                background: `linear-gradient(135deg, ${COLORS.text}, ${theme.primaryColor})`,
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>
                {home.heroTitle || `Consult ${site.name}`}
              </h1>
              <p style={{ fontSize: 'clamp(15px, 2.2vw, 18px)', color: COLORS.textDim, maxWidth: 560, marginBottom: 32, lineHeight: 1.7 }}>
                {home.heroSubtitle || 'Book a personal Vedic astrology consultation — kundli reading, career, marriage & remedies.'}
              </p>
              <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
                <a href="#book" style={{
                  padding: '14px 32px', borderRadius: 12, background: gradient, color: '#fff', fontWeight: 700,
                  fontSize: 16, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8,
                }}><Calendar size={18} /> Book a Consultation</a>
                <a href="#tools" style={{
                  padding: '14px 32px', borderRadius: 12, border: `1.5px solid ${COLORS.border}`, color: COLORS.text,
                  fontWeight: 700, fontSize: 16, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8,
                }}><Sparkles size={18} color={theme.accentColor} /> Free Kundli</a>
              </div>
            </motion.div>
            {site.hero_image && (
              <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.15 }}
                style={{ position: 'relative', maxWidth: 380, justifySelf: 'center', width: '100%' }}>
                <div style={{
                  position: 'absolute', inset: -14, borderRadius: 28, opacity: 0.35,
                  background: `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`, filter: 'blur(28px)',
                }} />
                <img src={site.hero_image} alt={site.name}
                  style={{ position: 'relative', width: '100%', aspectRatio: '4/4.6', objectFit: 'cover', objectPosition: 'top', borderRadius: 24, border: `1px solid ${COLORS.border}` }} />
              </motion.div>
            )}
          </div>
        </div>
      </section>

      {/* ─── about ─── */}
      <section id="about" style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)' }}>
        <div style={sectionStyle}>
          <h2 style={h2Style}>{home.aboutTitle || about.title || 'About'}</h2>
          <div style={{
            maxWidth: 720, margin: '0 auto', fontSize: 16, lineHeight: 1.8, color: COLORS.textDim, textAlign: 'center',
            whiteSpace: 'pre-line',
          }}>
            {home.aboutText || about.text || 'A dedicated Vedic astrologer helping people find clarity through kundli analysis.'}
          </div>
        </div>
      </section>

      {/* ─── services ─── */}
      <section id="services">
        <div style={sectionStyle}>
          <h2 style={h2Style}>Consultation Services</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
            {services.map((s) => (
              <div key={s.id} style={{
                background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24,
              }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12, background: gradient, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', marginBottom: 16, color: '#fff',
                }}><Star size={20} /></div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{s.name}</h3>
                {s.description && <p style={{ fontSize: 14, color: COLORS.textDim, lineHeight: 1.6, marginBottom: 16 }}>{s.description}</p>}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 14 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: COLORS.textDim }}><Clock size={14} /> {s.duration_minutes} min</span>
                  <span style={{ fontWeight: 800, fontSize: 17 }}>{s.price > 0 ? `₹${s.price}` : 'Free'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── free tools (kundli + panchang) ─── */}
      <section id="tools" style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)' }}>
        <div style={sectionStyle}>
          <h2 style={h2Style}>Free Astrology Tools</h2>
          <p style={{ textAlign: 'center', color: COLORS.textDim, fontSize: 15, maxWidth: 560, margin: '-12px auto 36px', lineHeight: 1.7 }}>
            Powered by a professional Vedic astrology engine — free for every visitor.
          </p>
          <FreeTools site={site} resolve={resolve} theme={theme} COLORS={COLORS} />
        </div>
      </section>

      {/* ─── booking ─── */}
      <section id="book">
        <div style={sectionStyle}>
          <h2 style={h2Style}>Book Your Appointment</h2>
          <div style={{
            maxWidth: 560, margin: '0 auto', background: COLORS.surface, border: `1px solid ${COLORS.border}`,
            borderRadius: 20, padding: '28px 24px',
          }}>
            {services.length > 0
              ? <BookingWidget site={site} resolve={resolve} services={services} theme={theme} />
              : <p style={{ textAlign: 'center', color: COLORS.textDim }}>Booking coming soon — please check back later.</p>}
          </div>
        </div>
      </section>

      {/* ─── footer ─── */}
      <footer style={{ borderTop: `1px solid ${COLORS.border}`, padding: '40px 20px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 12 }}>
          {site.logo_url
            ? <img src={site.logo_url} alt={site.name} style={{ width: 30, height: 30, borderRadius: 9, objectFit: 'cover' }} />
            : <div style={{ width: 30, height: 30, borderRadius: 9, background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 13 }}>
                {(site.name || 'A').charAt(0)}
              </div>}
          <span style={{ fontWeight: 700 }}>{site.name}</span>
        </div>
        <div style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 18 }}>
          {site.custom_domain || tenantSubdomainLabel(site.slug)}
        </div>
        <div style={{ fontSize: 12, opacity: 0.5 }}>
          <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>Powered by AstroVakta</Link>
        </div>
      </footer>

      {/* ─── WhatsApp chat button (astrologer's number) ─── */}
      {site.settings?.whatsappNumber && (
        <a href={`https://wa.me/${String(site.settings.whatsappNumber).replace(/[^\d]/g, '')}?text=${encodeURIComponent(`Namaste ${site.name}, I want to book a consultation.`)}`}
          target="_blank" rel="noopener noreferrer" title="Chat on WhatsApp"
          style={{
            position: 'fixed', bottom: 22, right: 22, zIndex: 60, width: 54, height: 54, borderRadius: '50%',
            background: '#16a34a', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(22,163,74,0.4)',
          }}>
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
        </a>
      )}
    </div>
  )
}
