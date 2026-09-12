import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Star, Calendar, Clock, Check, Sparkles, Moon, ArrowRight,
  ChevronLeft, ChevronRight, Globe, BadgeCheck, Sparkle, Send,
  MapPin, Mail, Phone, ShoppingCart, Plus, Minus, ShoppingCart as CartIcon,
  ShieldCheck, HeartHandshake, Lock, UserCheck, Package, ShoppingBag, ScrollText, Heart,
} from 'lucide-react'

// Brand icons were dropped from newer lucide-react — inline the small SVG paths.
const brandIcon = (path, viewBox = '0 0 24 24') => {
  const Icon = ({ size = 17, color = 'currentColor' }) => (
    <svg width={size} height={size} viewBox={viewBox} fill={color}><path d={path} /></svg>
  )
  return Icon
}
const InstagramIcon = brandIcon('M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zm0 10.162a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z')
const YoutubeIcon = brandIcon('M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z')
const FacebookIcon = brandIcon('M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.985 4.388 10.974 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z')
const TwitterIcon = brandIcon('M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z')
const LinkedinIcon = brandIcon('M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z')
const TelegramIcon = brandIcon('M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.918-.9-1.066-.7-1.667-1.136-2.304-1.805-.916-.962-.322-1.486.224-2.076.344-.372 1.26-1.222 1.765-1.748.256-.264.17-.494-.129-.494-.14 0-.32.094-.5.28-.474.521-1.364 1.456-1.687 1.794-.457.48-.867.467-1.309.095-.611-.514-1.392-1.066-2.033-1.543-.684-.51-1.124-.757-.493-1.429.596-.635 3.48-3.395 4.79-4.677.502-.49.98-.377.98.32 0 1.047-.32 3.197-.72 5.907-.15 1.004-.27 1.42-.425 1.42-.273 0-.711-.508-1.68-1.452-.742-.726-1.947-1.014-2.604-.598-.342.217-.485.59-.423 1.055.09.673.69 1.408 1.413 2.187.384.414.81.87 1.267 1.393.899 1.028 1.65 1.6 2.575 1.914.81.276 1.617.354 2.26.28.524-.06.795-.36.86-.872.172-1.35.773-6.24 1.09-8.945.093-.79.034-1.306-.547-1.306z')
import toast from 'react-hot-toast'
import {
  getPublicSite, getPublicAvailability, publicBook, publicKundliTool, publicPanchangTool,
  publicHoroscopeTool, publicPlaceOrder,
} from '../lib/api.js'
import PlaceAutocomplete from '../components/PlaceAutocomplete.jsx'
import { KundliPage, MatchingPage } from './TenantTools.jsx'
import { tenantSiteUrl, tenantSubdomainLabel } from '../lib/tenant.js'

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const ZODIAC = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

const WHY_ICONS = [ShieldCheck, HeartHandshake, Lock, UserCheck]

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

    // LocalBusiness structured data — rich results for the astrologer's brand.
    const city = site.settings?.city || ''
    const ld = {
      '@context': 'https://schema.org', '@type': 'ProfessionalService',
      name: site.name, description, url: canonicalUrl,
      ...(site.settings?.phone ? { telephone: site.settings.phone } : {}),
      ...(city ? { address: { '@type': 'PostalAddress', addressLocality: city } } : {}),
    }
    let ldEl = document.getElementById('tenant-jsonld')
    if (!ldEl) { ldEl = document.createElement('script'); ldEl.setAttribute('type', 'application/ld+json'); ldEl.setAttribute('id', 'tenant-jsonld'); document.head.appendChild(ldEl) }
    ldEl.textContent = JSON.stringify(ld)
  }, [site.slug, site.name, site.tagline, site.custom_domain, home.heroSubtitle, site.settings])
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

// normalize social input: "@handle" → https://instagram.com/handle, bare host → https://…
const socialHref = (v, base) => {
  let s = (v || '').trim()
  if (!s) return null
  if (/^https?:\/\//i.test(s)) return s
  if (s.startsWith('@')) return `https://${base}/${s.slice(1)}`
  // Platform fields always build on the platform domain — handles may contain
  // dots ("pandit.sharma") and must not be mistaken for full URLs.
  if (base) return `https://${base}/${s.replace(/^https?:\/\/(www\.)?[^/]+\//i, '').replace(/^\//, '')}`
  return `https://${s}`
}

// ─── payment step after a booking is placed (visitor details are already captured) ───
function PaymentBox({ site, confirmed, service, inputStyle }) {
  const pay = site.settings?.paymentsMode || 'later'
  const amount = Number(confirmed.amount || service?.price || 0)
  const [payState, setPayState] = useState('idle') // idle | loading | done

  const openRazorpay = () => {
    setPayState('loading')
    const open = () => {
      const rz = new window.Razorpay({
        key: site.settings.razorpayKeyId,
        amount: Math.round(amount * 100),
        currency: 'INR',
        name: site.name,
        description: `Consultation — ${confirmed.date} ${confirmed.start_time}`,
        receipt: `booking:${confirmed.id}`,
        theme: { color: site.theme?.primaryColor || '#7c3aed' },
        modal: { ondismiss: () => setPayState('idle') },
        handler: () => setPayState('done'),
      })
      rz.open()
    }
    if (window.Razorpay) return open()
    const s = document.createElement('script')
    s.src = 'https://checkout.razorpay.com/v1/checkout.js'
    s.onload = open
    s.onerror = () => setPayState('idle')
    document.body.appendChild(s)
  }

  const box = { marginTop: 16, padding: 14, borderRadius: 12, border: '1px solid var(--border-color)', background: 'rgba(127,127,127,0.05)' }

  if (pay === 'upi' && site.settings?.upiId && amount > 0) {
    const upiLink = `upi://pay?pa=${encodeURIComponent(site.settings.upiId)}&pn=${encodeURIComponent(site.name)}&am=${amount}&cu=INR&tn=${encodeURIComponent(`Consultation ${confirmed.date} ${confirmed.start_time}`)}`
    return (
      <div style={box}>
        <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8 }}>Pay ₹{amount} via UPI</div>
        <a href={upiLink} style={{ ...inputStyle, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '11px 14px', cursor: 'pointer', fontWeight: 700, background: gradient_css(site), color: '#fff', border: 'none', textDecoration: 'none' }}>
          Open a UPI app — GPay, PhonePe, Paytm
        </a>
        <div style={{ fontSize: 12.5, opacity: 0.65, marginTop: 8, lineHeight: 1.55 }}>
          Paid? Send the payment screenshot on WhatsApp below and {site.name} will confirm your slot.
        </div>
      </div>
    )
  }

  if (pay === 'razorpay' && site.settings?.razorpayKeyId && amount > 0) {
    return (
      <div style={box}>
        <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8 }}>Consultation fee — ₹{amount}</div>
        {payState === 'done' ? (
          <div style={{ fontWeight: 700, color: '#16a34a', fontSize: 14 }}>Payment completed — thank you!</div>
        ) : (
          <>
            <button onClick={openRazorpay} disabled={payState === 'loading'} style={{ ...inputStyle, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '11px 14px', cursor: 'pointer', fontWeight: 700, background: gradient_css(site), color: '#fff', border: 'none' }}>
              {payState === 'loading' ? 'Opening…' : 'Pay online (cards, UPI, netbanking)'}
            </button>
            <div style={{ fontSize: 12.5, opacity: 0.65, marginTop: 8, lineHeight: 1.55 }}>
              Secure checkout by Razorpay. Your booking is already reserved — payment confirms it faster.
            </div>
          </>
        )}
      </div>
    )
  }

  // 'later'
  return (
    <div style={{ ...box, display: pay === 'later' ? undefined : 'none' }}>
      <div style={{ fontWeight: 700, fontSize: 13.5 }}>Pay later — no advance needed.</div>
      <div style={{ fontSize: 12.5, opacity: 0.65, marginTop: 4, lineHeight: 1.55 }}>
        {site.name} will share payment details while confirming your appointment.
      </div>
    </div>
  )
}
const gradient_css = (site) => `linear-gradient(135deg, ${site.theme?.primaryColor || '#7c3aed'}, ${site.theme?.accentColor || '#eab308'})`

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
          {site.name} has been notified and will contact you{confirmed.client_phone ? ` on ${confirmed.client_phone}` : ''}.
        </p>
        <PaymentBox site={site} confirmed={confirmed} service={service} inputStyle={inputStyle} />
        {site.settings?.whatsappNumber && (
          <a href={`https://wa.me/${String(site.settings.whatsappNumber).replace(/[^\d]/g, '')}?text=${encodeURIComponent(`Namaste, I just booked a consultation (${confirmed.date} at ${confirmed.start_time}).`)}`}
            target="_blank" rel="noopener noreferrer"
            style={{ ...inputStyle, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, maxWidth: 260, marginTop: 16, padding: '11px 14px', cursor: 'pointer', fontWeight: 600, background: '#16a34a', color: '#fff', border: 'none', textDecoration: 'none' }}>
            Message on WhatsApp
          </a>
        )}
        <div>
          <button onClick={() => { setConfirmed(null); setSelectedDate(null); setSelectedTime(null); setName(''); setPhone('') }}
            style={{ ...inputStyle, maxWidth: 220, marginTop: 12, padding: '11px 14px', cursor: 'pointer', fontWeight: 600, background: 'transparent', color: 'inherit', border: '1px solid var(--border-color)' }}>
            Book another
          </button>
        </div>
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

// ═══════════════ FULL KUNDLI SOFTWARE ═══════════════
// Basic mode shows a lead-gen snapshot; detail mode is the full software:
// North-Indian chart SVG, house table, planet table with degrees, and the
// Vimshottari dasha timeline — same Swiss-ephemeris engine as the platform.

// ═══════════════ DAILY HOROSCOPE WIDGET ═══════════════
function HoroscopeWidget({ resolve, theme, COLORS }) {
  const [sign, setSign] = useState(null)
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)

  const pick = (s) => {
    setSign(s); setData(null); setBusy(true)
    publicHoroscopeTool(resolve, s)
      .then((res) => setData(res?.horoscope || null))
      .catch(() => { toast.error('Could not load the horoscope — try again'); setBusy(false) })
      .finally(() => setBusy(false))
  }

  const card = {
    background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24,
  }

  const hor = data || {}

  return (
    <div style={card}>
      <h3 style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>Daily Rashifal</h3>
      <p style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 16 }}>
        Today's horoscope for your moon sign — updated every morning.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(74px, 1fr))', gap: 6, marginBottom: 20 }}>
        {ZODIAC.map((z) => (
          <button key={z} onClick={() => pick(z)} style={{
            padding: '8px 4px', borderRadius: 10, fontSize: 11, fontWeight: 700, cursor: 'pointer',
            border: `1.5px solid ${sign === z ? theme.primaryColor : COLORS.border}`,
            background: sign === z ? theme.primaryColor : 'transparent',
            color: sign === z ? '#fff' : COLORS.text,
          }}>{z}</button>
        ))}
      </div>

      {sign && busy && <div style={{ color: COLORS.textDim, fontSize: 14 }}>Reading the stars for {sign}…</div>}

      {sign && !busy && data && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <Moon size={20} style={{ color: theme.accentColor }} />
            <div>
              <div style={{ fontWeight: 800, fontSize: 17 }}>{hor.sign || sign}</div>
              <div style={{ fontSize: 12, color: COLORS.textDim }}>{hor.period}</div>
            </div>
          </div>
          <p style={{ fontSize: 14.5, lineHeight: 1.8, marginBottom: 18 }}>{hor.overview}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8, marginBottom: 14 }}>
            {[['Lucky Color', hor.luckyColor], ['Lucky Number', hor.luckyNumber], ['Lucky Direction', hor.luckyDirection]].map(([k, v]) => (
              <div key={k} style={{ padding: '10px 12px', background: 'rgba(127,127,127,0.06)', borderRadius: 10 }}>
                <div style={{ fontSize: 11, color: COLORS.textDim, fontWeight: 600 }}>{k}</div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{v || '—'}</div>
              </div>
            ))}
          </div>
          {hor.career?.positive && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
              {[['Career', hor.career], ['Love', hor.love], ['Finance', hor.finance], ['Health', hor.health]].map(([k, v]) => (
                <div key={k} style={{ padding: '12px', border: `1px solid ${COLORS.border}`, borderRadius: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: 0.5, marginBottom: 6, color: theme.primaryColor }}>{k.toUpperCase()}</div>
                  <div style={{ fontSize: 12.5, lineHeight: 1.6, color: COLORS.textDim }}>
                    {v?.positive} {v?.challenging ? <span style={{ opacity: 0.85 }}>Watch: {v.challenging}</span> : null}
                  </div>
                </div>
              ))}
            </div>
          )}
          {hor.remedy && (
            <div style={{ marginTop: 14, padding: '12px 14px', borderRadius: 10, background: `color-mix(in srgb, ${theme.primaryColor} 8%, transparent)`, fontSize: 13, lineHeight: 1.6 }}>
              <strong>Today's remedy:</strong> {hor.remedy}
            </div>
          )}
        </motion.div>
      )}

      {!sign && !busy && (
        <div style={{ color: COLORS.textDim, fontSize: 14 }}>👆 Tap your moon sign to read today's rashifal.</div>
      )}
    </div>
  )
}

// ═══════════════ PANCHANG CARD ═══════════════
function PanchangCard({ resolve, COLORS }) {
  const [panchang, setPanchang] = useState(null)
  useEffect(() => {
    publicPanchangTool(resolve).then(setPanchang).catch(() => setPanchang(null))
  }, [resolve])

  const card = {
    background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24,
  }

  return (
    <div style={card}>
      <h3 style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>Today's Panchang</h3>
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
            <div key={k} style={{ padding: '10px 12px', background: 'rgba(127,127,127,0.06)', borderRadius: 10 }}>
              <div style={{ fontSize: 11, color: COLORS.textDim, fontWeight: 600 }}>{k}</div>
              <div style={{ fontWeight: 700 }}>{v || '—'}</div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: COLORS.textDim, fontSize: 14 }}>Loading panchang…</div>
      )}
      <p style={{ fontSize: 12, color: COLORS.textDim, marginTop: 14 }}>
        Updated daily automatically — auspicious timings at a glance.
      </p>
    </div>
  )
}

// ═══════════════ STORE SECTION (cart + order, no online payment needed) ═══════════════
function StoreSection({ site, resolve, theme, COLORS }) {
  const products = site._products || []
  const [cart, setCart] = useState({})          // { product_id: qty }
  const [checkout, setCheckout] = useState(false)
  const [form, setForm] = useState({ name: '', phone: '', address: '', notes: '' })
  const [placing, setPlacing] = useState(false)
  const [placed, setPlaced] = useState(null)

  const setQty = (p, q) => setCart((c) => {
    const next = { ...c }
    const max = p.stock === -1 ? 99 : p.stock
    const val = Math.max(0, Math.min(max, q))
    if (val === 0) delete next[p.id]
    else next[p.id] = val
    return next
  })

  const items = Object.entries(cart).map(([id, qty]) => {
    const p = products.find((x) => String(x.id) === id)
    return p ? { p, qty } : null
  }).filter(Boolean)
  const total = items.reduce((s, { p, qty }) => s + p.price * qty, 0)

  const setF = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const placeOrder = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return toast.error('Please enter your name')
    setPlacing(true)
    try {
      const res = await publicPlaceOrder(resolve, {
        client_name: form.name.trim(),
        client_phone: form.phone.trim() || undefined,
        address: form.address.trim() || undefined,
        notes: form.notes.trim() || undefined,
        items: items.map(({ p, qty }) => ({ product_id: p.id, qty })),
      })
      setPlaced(res?.order || { id: '?', amount: total })
      toast.success(res?.message || 'Order placed!')
      setCart({}); setCheckout(false)
    } catch (err) {
      toast.error(errDetail(err))
    } finally { setPlacing(false) }
  }

  const inputStyle = {
    width: '100%', padding: '11px 14px', borderRadius: 10, fontSize: 14,
    border: `1px solid ${COLORS.border}`, background: 'rgba(127,127,127,0.05)',
    color: 'inherit', outline: 'none',
  }
  const grad = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`

  if (placed) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
        style={{ maxWidth: 480, margin: '0 auto', textAlign: 'center', padding: '36px 24px', background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 20 }}>
        <motion.div initial={{ scale: 0.5 }} animate={{ scale: 1 }}
          style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(34,197,94,0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
          <Check size={32} color="#22c55e" />
        </motion.div>
        <h3 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Order received!</h3>
        <p style={{ opacity: 0.75, marginBottom: 6, lineHeight: 1.6 }}>
          Order #{placed.id} · {placed.currency === 'INR' ? '₹' : ''}{placed.amount ?? total}
        </p>
        <p style={{ opacity: 0.6, fontSize: 14 }}>
          {site.name} will contact you to confirm payment and delivery.
        </p>
        {site.settings?.whatsappNumber && (
          <a href={`https://wa.me/${String(site.settings.whatsappNumber).replace(/[^\d]/g, '')}?text=${encodeURIComponent(`Namaste, I just placed order #${placed.id}.`)}`}
            target="_blank" rel="noopener noreferrer"
            style={{ ...inputStyle, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, maxWidth: 240, marginTop: 16, cursor: 'pointer', fontWeight: 700, background: '#16a34a', color: '#fff', border: 'none', textDecoration: 'none' }}>
            Confirm on WhatsApp
          </a>
        )}
        <div>
          <button onClick={() => setPlaced(null)} style={{ ...inputStyle, maxWidth: 200, marginTop: 12, cursor: 'pointer', background: 'transparent', color: 'inherit', border: `1px solid ${COLORS.border}` }}>
            Continue shopping
          </button>
        </div>
      </motion.div>
    )
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 16, marginBottom: 20 }}>
        {products.map((p) => {
          const qty = cart[p.id] || 0
          const outOfStock = p.stock !== -1 && p.stock <= 0
          return (
            <div key={p.id} style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              {p.image
                ? <img src={p.image} alt={p.name} style={{ width: '100%', height: 150, objectFit: 'cover' }} />
                : <div style={{ width: '100%', height: 150, background: 'rgba(127,127,127,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Package size={32} color={COLORS.textDim} /></div>}
              <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: 14.5 }}>{p.name}</div>
                {p.description && <div style={{ fontSize: 12, color: COLORS.textDim, lineHeight: 1.5 }}>{p.description}</div>}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                  <span style={{ fontWeight: 800, fontSize: 16 }}>₹{p.price}</span>
                  {outOfStock ? (
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#ef4444' }}>Out of stock</span>
                  ) : qty > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <button onClick={() => setQty(p, qty - 1)} style={{ width: 26, height: 26, borderRadius: 8, border: `1px solid ${COLORS.border}`, background: 'transparent', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Minus size={13} /></button>
                      <span style={{ fontWeight: 800, fontSize: 14 }}>{qty}</span>
                      <button onClick={() => setQty(p, qty + 1)} style={{ width: 26, height: 26, borderRadius: 8, border: 'none', background: grad, color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Plus size={13} /></button>
                    </div>
                  ) : (
                    <button onClick={() => setQty(p, 1)} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 14px', borderRadius: 9, border: 'none', background: grad, color: '#fff', fontWeight: 700, fontSize: 12.5, cursor: 'pointer' }}>
                      <ShoppingCart size={13} /> Add
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* cart / checkout */}
      {items.length > 0 && !checkout && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          style={{ maxWidth: 520, margin: '0 auto', background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 20, textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 10 }}>
            <CartIcon size={17} style={{ color: theme.accentColor }} />
            <span style={{ fontWeight: 700, fontSize: 15 }}>
              {items.reduce((s, { qty }) => s + qty, 0)} item{items.length > 1 ? 's' : ''} · ₹{total}
            </span>
          </div>
          <div style={{ fontSize: 12.5, color: COLORS.textDim, marginBottom: 14, lineHeight: 1.6 }}>
            {items.map(({ p, qty }) => `${p.name} × ${qty}`).join(' · ')}
          </div>
          <button onClick={() => setCheckout(true)} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: grad, color: '#fff' }}>
            Place Order
          </button>
          <p style={{ fontSize: 11.5, opacity: 0.55, marginTop: 8 }}>
            No online payment — {site.name} confirms your order personally on WhatsApp/phone.
          </p>
        </motion.div>
      )}

      {checkout && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          style={{ maxWidth: 520, margin: '0 auto', background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24 }}>
          <form onSubmit={placeOrder} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 800, letterSpacing: 0.5, opacity: 0.7, marginBottom: 2 }}>DELIVERY DETAILS</div>
            <input value={form.name} onChange={(e) => setF('name', e.target.value)} placeholder="Your name *" style={inputStyle} />
            <input value={form.phone} onChange={(e) => setF('phone', e.target.value)} placeholder="Phone (WhatsApp preferred)" style={inputStyle} />
            <textarea value={form.address} onChange={(e) => setF('address', e.target.value)} placeholder="Delivery address" rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
            <textarea value={form.notes} onChange={(e) => setF('notes', e.target.value)} placeholder="Any note for the astrologer (optional)" rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', border: `1px dashed ${COLORS.border}`, borderRadius: 10, fontSize: 13 }}>
              <span>{items.reduce((s, { qty }) => s + qty, 0)} item(s)</span>
              <span style={{ fontWeight: 800 }}>Total ₹{total}</span>
            </div>
            <button type="submit" disabled={placing} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: grad, color: '#fff', opacity: placing ? 0.7 : 1 }}>
              {placing ? 'Placing order…' : `Confirm Order · ₹${total}`}
            </button>
            <button type="button" onClick={() => setCheckout(false)} style={{ ...inputStyle, cursor: 'pointer', background: 'transparent', color: 'inherit', border: `1px solid ${COLORS.border}` }}>
              Back to cart
            </button>
          </form>
        </motion.div>
      )}
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
  const [route, setRoute] = useState(() => window.location.hash)

  useEffect(() => {
    const onHash = () => setRoute(window.location.hash)
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

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

  const site = { ...bundle.site, _products: bundle.products || [] }
  const theme = {
    primaryColor: site.theme?.primaryColor || '#7c3aed',
    accentColor: site.theme?.accentColor || '#eab308',
    bgStyle: site.theme?.bgStyle || 'dark',
    fontHeading: site.theme?.fontHeading,
  }
  const pages = bundle.pages || {}
  const home = pages.home?.content || {}
  const about = pages.about?.content || {}
  const services = bundle.services || []
  const settings = site.settings || {}
  const light = theme.bgStyle === 'light'

  const COLORS = light
    ? { bg: '#faf9f6', surface: '#ffffff', text: '#1c1917', textDim: 'rgba(28,25,23,0.6)', border: 'rgba(28,25,23,0.12)', heroOverlay: 'rgba(255,255,255,0.6)' }
    : { bg: '#0a0a1a', surface: 'rgba(255,255,255,0.04)', text: '#f1f0ff', textDim: 'rgba(241,240,255,0.6)', border: 'rgba(255,255,255,0.1)', heroOverlay: 'rgba(10,10,26,0.6)' }

  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`

  // Tool pages live on their own hash routes so the landing page stays clean.
  if (route.startsWith('#/kundli')) return <KundliPage site={site} resolve={resolve} theme={theme} COLORS={COLORS} />
  if (route.startsWith('#/matching')) return <MatchingPage site={site} resolve={resolve} theme={theme} COLORS={COLORS} />

  const sectionStyle = { maxWidth: 1000, margin: '0 auto', padding: '72px 20px' }
  const h2Style = { fontSize: 32, fontWeight: 800, marginBottom: 12, color: COLORS.text, textAlign: 'center' }
  const subStyle = { textAlign: 'center', color: COLORS.textDim, fontSize: 15, maxWidth: 620, margin: '0 auto 40px', lineHeight: 1.7 }

  const showStore = settings.showStore && (site._products || []).length > 0
  const showTestimonials = settings.showTestimonials !== false && Array.isArray(home.testimonials) && home.testimonials.length > 0
  const whyPoints = Array.isArray(home.whyPoints) ? home.whyPoints : []

  const socials = [
    ['instagram', InstagramIcon, socialHref(settings.instagram, 'instagram.com')],
    ['youtube', YoutubeIcon, socialHref(settings.youtube, 'youtube.com')],
    ['facebook', FacebookIcon, socialHref(settings.facebook, 'facebook.com')],
    ['twitter', TwitterIcon, socialHref(settings.twitter, 'x.com')],
    ['linkedin', LinkedinIcon, socialHref(settings.linkedin, 'linkedin.com')],
    ['telegram', TelegramIcon, socialHref(settings.telegram, 't.me')],
    ['website', Globe, socialHref(settings.websiteUrl, null)],
  ].filter(([, , href]) => !!href)

  const hasContact = settings.email || settings.phone || settings.city

  return (
    <div className="tenant-site" style={{ background: COLORS.bg, color: COLORS.text, minHeight: '100vh', fontFamily: "'Inter', system-ui, sans-serif" }}>
      <TenantHead site={site} home={home} />

      {/* heading font from theme (Cormorant/Playfair for the premium templates) */}
      <style>{theme.fontHeading
        ? `.tenant-site h1, .tenant-site h2, .tenant-site h3, .tenant-site .tenant-font { font-family: ${theme.fontHeading}; }`
          : ''}</style>

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
            {showStore && <a href="#shop" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Shop</a>}
            <a href="#/kundli" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Free Kundli</a>
            <a href="#/matching" style={{ color: COLORS.textDim, textDecoration: 'none' }}>Match Making</a>
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
                {showStore && (
                  <a href="#shop" style={{
                    padding: '14px 32px', borderRadius: 12, border: `1.5px solid ${COLORS.border}`, color: COLORS.text,
                    fontWeight: 700, fontSize: 16, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8,
                  }}><ShoppingBag size={18} /> Shop Remedies</a>
                )}
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

      {/* ─── stats band ─── */}
      {(home.statsYears || home.statsReadings || home.statsRating) && (
        <section style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)', borderBottom: `1px solid ${COLORS.border}` }}>
          <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 20px', display: 'flex', justifyContent: 'space-around', gap: 20, flexWrap: 'wrap' }}>
            {[
              [home.statsYears, 'Years of Practice'],
              [home.statsReadings, 'Kundlis Read'],
              [home.statsRating, 'Client Rating ★'],
            ].filter(([v]) => !!v).map(([v, k]) => (
              <div key={k} style={{ textAlign: 'center' }}>
                <div className="tenant-font" style={{ fontSize: 34, fontWeight: 900, background: gradient, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{v}</div>
                <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, color: COLORS.textDim, marginTop: 2 }}>{k.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ─── about ─── */}
      <section id="about">
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

      {/* ─── why choose me ─── */}
      {whyPoints.length > 0 && (
        <section style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)' }}>
          <div style={sectionStyle}>
            <h2 style={h2Style}>{home.whyTitle || 'Why Consult Me'}</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, maxWidth: 860, margin: '0 auto' }}>
              {whyPoints.map((w, i) => {
                const Icon = WHY_ICONS[i % WHY_ICONS.length]
                return (
                  <motion.div key={w.title} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24, textAlign: 'center' }}>
                    <div style={{
                      width: 46, height: 46, borderRadius: 14, margin: '0 auto 14px', display: 'flex',
                      alignItems: 'center', justifyContent: 'center', background: `color-mix(in srgb, ${theme.primaryColor} 14%, transparent)`,
                    }}>
                      <Icon size={21} style={{ color: theme.primaryColor }} />
                    </div>
                    <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 6 }}>{w.title}</h3>
                    <p style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.6 }}>{w.text}</p>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </section>
      )}

      {/* ─── services ─── */}
      <section id="services">
        <div style={sectionStyle}>
          <h2 style={h2Style}>Consultation Services</h2>
          <p style={subStyle}>Choose a reading — every consultation is done personally by {site.name}.</p>
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

      {/* ─── testimonials ─── */}
      {showTestimonials && (
        <section style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)' }}>
          <div style={sectionStyle}>
            <h2 style={h2Style}>{home.testimonialsTitle || 'What Clients Say'}</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, maxWidth: 860, margin: '0 auto' }}>
              {home.testimonials.map((t, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                  style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 24 }}>
                  <div style={{ display: 'flex', gap: 3, marginBottom: 12 }}>
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} size={15} fill={j < (t.rating || 5) ? theme.accentColor : 'transparent'} color={j < (t.rating || 5) ? theme.accentColor : COLORS.border} />
                    ))}
                  </div>
                  <p style={{ fontSize: 14, lineHeight: 1.7, color: COLORS.textDim, marginBottom: 14 }}>"{t.text}"</p>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>— {t.name}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ─── shop (products) ─── */}
      {showStore && (
        <section id="shop">
          <div style={sectionStyle}>
            <h2 style={h2Style}>{home.storeTitle || `Shop — Remedies & Products`}</h2>
            <p style={subStyle}>
              Gemstones, rudraksha and puja items recommended by {site.name}. Order now — pay on delivery or via UPI after confirmation.
            </p>
            <StoreSection site={site} resolve={resolve} theme={theme} COLORS={COLORS} />
          </div>
        </section>
      )}

      {/* ─── free tools (full kundli software + horoscope + panchang) ─── */}
      <section id="tools" style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)' }}>
        <div style={sectionStyle}>
          <h2 style={h2Style}>Free Astrology Tools</h2>
          <p style={subStyle}>
            A complete kundli, today's rashifal and daily panchang — free for every visitor, powered by a professional Vedic engine.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, alignItems: 'start' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <a href="#/kundli" style={{ textDecoration: 'none', color: 'inherit' }}>
                <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 26, height: '100%', cursor: 'pointer', transition: 'transform 0.15s' }}>
                  <ScrollText size={22} color={theme.primaryColor} />
                  <h3 style={{ fontSize: 18, fontWeight: 800, margin: '10px 0 6px' }}>Free Kundli</h3>
                  <p style={{ fontSize: 13.5, color: COLORS.textDim, lineHeight: 1.6, margin: 0 }}>
                    Your complete birth chart — lagna, planets, dasha timeline and dosha analysis in a detailed report.
                  </p>
                </div>
              </a>
              <a href="#/matching" style={{ textDecoration: 'none', color: 'inherit' }}>
                <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 16, padding: 26, height: '100%', cursor: 'pointer', transition: 'transform 0.15s' }}>
                  <Heart size={22} color={theme.accentColor} />
                  <h3 style={{ fontSize: 18, fontWeight: 800, margin: '10px 0 6px' }}>Match Making</h3>
                  <p style={{ fontSize: 13.5, color: COLORS.textDim, lineHeight: 1.6, margin: 0 }}>
                    Ashtakoota gun milan across all 36 gunas with manglik analysis for both partners.
                  </p>
                </div>
              </a>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <HoroscopeWidget resolve={resolve} theme={theme} COLORS={COLORS} />
              <PanchangCard resolve={resolve} COLORS={COLORS} />
            </div>
          </div>
        </div>
      </section>

      {/* ─── booking ─── */}
      <section id="book">
        <div style={sectionStyle}>
          <h2 style={h2Style}>Book Your Appointment</h2>
          <p style={subStyle}>Pick a service, choose an open slot — confirmation is instant.</p>
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

      {/* ─── contact ─── */}
      {hasContact && (
        <section id="contact" style={{ background: light ? '#f3f1ec' : 'rgba(255,255,255,0.02)' }}>
          <div style={sectionStyle}>
            <h2 style={h2Style}>Get in Touch</h2>
            <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
              {[
                [settings.phone, Phone, `tel:${(settings.phone || '').replace(/[^\d+]/g, '')}`],
                [settings.email, Mail, `mailto:${settings.email}`],
                [settings.city, MapPin, null],
              ].filter(([v]) => !!v).map(([v, Icon, href], i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 12, background: COLORS.surface,
                  border: `1px solid ${COLORS.border}`, borderRadius: 14, padding: '14px 22px', fontSize: 14, fontWeight: 600,
                }}>
                  <Icon size={17} style={{ color: theme.primaryColor }} />
                  {href ? <a href={href} style={{ color: COLORS.text, textDecoration: 'none' }}>{v}</a> : v}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ─── footer ─── */}
      <footer style={{ borderTop: `1px solid ${COLORS.border}`, padding: '48px 20px 32px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 10 }}>
            {site.logo_url
              ? <img src={site.logo_url} alt={site.name} style={{ width: 30, height: 30, borderRadius: 9, objectFit: 'cover' }} />
              : <div style={{ width: 30, height: 30, borderRadius: 9, background: gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 13 }}>
                  {(site.name || 'A').charAt(0)}
                </div>}
            <span style={{ fontWeight: 700 }}>{site.name}</span>
          </div>
          <div style={{ fontSize: 13, color: COLORS.textDim, marginBottom: 18, textAlign: 'center' }}>
            {site.custom_domain || tenantSubdomainLabel(site.slug)}
          </div>
          {socials.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginBottom: 22 }}>
              {socials.map(([key, Icon, href]) => (
                <a key={key} href={href} target="_blank" rel="noopener noreferrer" title={key}
                  style={{
                    width: 38, height: 38, borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    border: `1px solid ${COLORS.border}`, color: COLORS.textDim, textDecoration: 'none',
                  }}>
                  <Icon size={17} />
                </a>
              ))}
            </div>
          )}
          <div style={{ textAlign: 'center', fontSize: 12, opacity: 0.5 }}>
            <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>Powered by AstroVakta</Link>
          </div>
        </div>
      </footer>

      {/* ─── WhatsApp chat button (astrologer's number) ─── */}
      {settings.whatsappNumber && (
        <a href={`https://wa.me/${String(settings.whatsappNumber).replace(/[^\d]/g, '')}?text=${encodeURIComponent(`Namaste ${site.name}, I want to book a consultation.`)}`}
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
