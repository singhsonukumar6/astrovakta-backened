import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Heart, ScrollText, Sparkles, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'
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

function BirthFields({ id, value, onChange, COLORS }) {
  const set = (k, v) => onChange({ ...value, [k]: v })
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
      <div>
        <label style={labelStyle}>Birth date *</label>
        <input type="date" value={value.date} onChange={(e) => set('date', e.target.value)} style={inputStyle} />
      </div>
      <div>
        <label style={labelStyle}>Birth time *</label>
        <input type="time" value={value.time} onChange={(e) => set('time', e.target.value)} style={inputStyle} />
      </div>
      <div style={{ gridColumn: '1 / -1' }}>
        <label style={labelStyle}>Birth place</label>
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

  const submit = async (e) => {
    e.preventDefault()
    if (!form.date || !form.time) { setError('Please enter your birth date and time'); return }
    setBusy(true); setError(null)
    try {
      const payload = {
        name: form.name.trim() || undefined,
        phone: form.phone.trim() || undefined,
        date: form.date, time: form.time,
        place: (form.place || undefined),
        lat: form.lat ?? undefined, lon: form.lon ?? undefined, tz: form.tz || undefined,
        detail: true,
        chart_theme: theme.bgStyle === 'dark' ? 'dark' : 'light',
      }
      const res = await publicKundliFull(resolve, payload)
      setResult(res.core)
      setFull(res)
      if (form.date && form.time) {
        publicDoshaTool(resolve, {
          date: form.date, time: form.time,
          lat: form.lat ?? undefined, lon: form.lon ?? undefined, tz: form.tz || undefined,
        }).then(setDosha).catch(() => setDosha(null))
      }
    } catch (err) { setError(errText(err)) } finally { setBusy(false) }
  }

  return (
    <ToolShell site={site} COLORS={COLORS} gradient={gradient} icon={ScrollText}
      title="Free Kundli" subtitle={`Complete Vedic birth chart with lagna, planets, dasha and dosha analysis — computed on a professional Swiss-ephemeris engine, presented by ${site?.name || 'our astrologer'}.`}>
      {!result ? (
        <motion.form onSubmit={submit} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 18, padding: 28, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div><label style={labelStyle}>Your name</label>
              <input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Full name" style={inputStyle} /></div>
            <div><label style={labelStyle}>Phone (WhatsApp)</label>
              <input value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="For a personal follow-up" style={inputStyle} /></div>
          </div>
          <BirthFields value={form} onChange={setForm} COLORS={COLORS} />
          {error && <div style={{ color: '#dc2626', fontSize: 13.5 }}>{error}</div>}
          <button type="submit" disabled={busy} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, fontSize: 15, border: 'none', background: gradient, color: '#fff', opacity: busy ? 0.7 : 1, padding: '14px' }}>
            {busy ? 'Calculating…' : 'Generate Detailed Kundli'}
          </button>
        </motion.form>
      ) : (
        <KundliResult result={result} dosha={dosha} full={full} theme={theme} COLORS={COLORS} onBack={() => { setResult(null); setFull(null); setDosha(null) }} site={site} />
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

function KundliResult({ result, dosha, full, theme, COLORS, onBack, site }) {
  const [view, setView] = useState('summary')
  const gradient = `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
  const tabBtn = (id, label) => (
    <button onClick={() => setView(id)} style={{
      padding: '8px 16px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer',
      border: `1.5px solid ${view === id ? theme.primaryColor : COLORS.border}`,
      background: view === id ? theme.primaryColor : 'transparent',
      color: view === id ? '#fff' : COLORS.text,
    }}>{label}</button>
  )
  const dashaColor = (lord) => ({ Ketu: '#8b5cf6', Venus: '#f472b6', Sun: '#f59e0b', Moon: '#94a3b8', Mars: '#ef4444', Rahu: '#3b82f6', Jupiter: '#eab308', Saturn: '#64748b', Mercury: '#10b981' }[lord] || theme.primaryColor)
  const wa = String(site?.settings?.whatsappNumber || '').replace(/[^\d]/g, '')

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
        {[['Date', result.birthDate], ['Time', result.birthTime], ['Place', result.birthPlace]].filter(([, v]) => v).map(([k, v]) => (
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
        {result.dasha && tabBtn('dasha', 'Dasha')}
        {dosha && tabBtn('dosha', 'Dosha Report')}
        {full && tabBtn('dasha-systems', 'All Dasha Systems')}
        {full && tabBtn('kp', 'KP & Extras')}
        {(full?.divisionalD9?.svg || full?.divisionalD10?.svg) && tabBtn('varga', 'Divisional Charts')}
        {full?.lalKitab && tabBtn('lal', 'Lal Kitab')}
      </div>

      {view === 'summary' && (
        <Section title="Chart Summary" COLORS={COLORS}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
            {[
              ['Ascendant (Lagna)', result.ascendant?.sign],
              ['Lagna Lord', result.ascendant?.lord],
              ['Moon Sign (Rashi)', result.moonSign],
              ['Birth Nakshatra', result.moonNakshatra],
              ['Sun Sign', result.sunSign],
              ['Lucky Gemstone', result.gemstone?.stone],
            ].map(([k, v]) => (
              <div key={k} style={{ padding: 12, background: 'rgba(127,127,127,0.06)', borderRadius: 10 }}>
                <div style={{ fontSize: 11, color: COLORS.textDim, fontWeight: 600 }}>{k}</div>
                <div style={{ fontWeight: 800, fontSize: 15 }}>{v || '—'}</div>
              </div>
            ))}
          </div>
          {result.currentDasha?.mahadasha && (
            <div style={{ marginTop: 14, padding: '13px 16px', borderRadius: 12, background: `color-mix(in srgb, ${dashaColor(result.currentDasha.mahadasha)} 12%, transparent)`, border: `1px solid ${dashaColor(result.currentDasha.mahadasha)}44` }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.5, opacity: 0.7, marginBottom: 3 }}>RUNNING MAHADASHA</div>
              <div style={{ fontWeight: 800, fontSize: 16 }}>
                {result.currentDasha.mahadasha}
                {result.currentDasha.antardasha && <> → <span style={{ fontSize: 14 }}>{result.currentDasha.antardasha} antardasha</span></>}
                <span style={{ fontSize: 12, fontWeight: 600, opacity: 0.65 }}> · till {result.currentDasha.to}</span>
              </div>
            </div>
          )}
        </Section>
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

      {view === 'dasha' && result.dasha && (
        <Section title="Vimshottari Mahadasha Timeline" COLORS={COLORS}>
          {result.dasha.map((d, i) => {
            const today = new Date().toISOString().slice(0, 10)
            const active = result.currentDasha?.mahadasha && result.currentDasha.mahadasha === d.lord && d.from <= today
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderRadius: 10, marginBottom: 6, border: `1px solid ${active ? dashaColor(d.lord) : COLORS.border}`, background: active ? `color-mix(in srgb, ${dashaColor(d.lord)} 12%, transparent)` : 'transparent' }}>
                <div style={{ width: 30, height: 30, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: dashaColor(d.lord), color: '#fff', fontWeight: 800, fontSize: 11 }}>{d.lord?.slice(0, 2)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>{d.lord} Mahadasha {active && <span style={{ fontSize: 11, color: dashaColor(d.lord) }}>· running now</span>}</div>
                  <div style={{ fontSize: 12, color: COLORS.textDim }}>{d.from} → {d.to}</div>
                </div>
              </div>
            )
          })}
        </Section>
      )}

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
                <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.65 }}>{Array.isArray(dosha.manglik.remedies) ? dosha.manglik.remedies.join(' · ') : String(dosha.manglik.remedies)}</div>
              </div>
            )}
            <div style={{ fontSize: 12.5, color: COLORS.textDim }}>For a detailed personal reading of these yogas, book a consultation with {site?.name || 'the astrologer'}.</div>
          </div>
        </Section>
      )}

      {view === 'dasha-systems' && full && (
        <Section title="Complete Dasha Analysis — all systems" COLORS={COLORS}>
          <JsonReport data={full} skip={['core', 'divisional', 'doshaCompute']} COLORS={COLORS} />
        </Section>
      )}

      {view === 'kp' && full && (
        <Section title="KP Astrology & Additional Analysis" COLORS={COLORS}>
          <JsonReport data={full} only={['kpRulingPlanets', 'doshaCompute', 'dhaiya']} COLORS={COLORS} />
        </Section>
      )}

      {view === 'varga' && full && (
        <Section title="Divisional Charts (Varga)" COLORS={COLORS}>
          {['divisionalD9', 'divisionalD10'].map((k) => full[k]?.svg ? (
            <div key={k} style={{ marginBottom: 18 }}>
              <div style={{ fontSize: 13, fontWeight: 800, marginBottom: 6 }}>{k === 'divisionalD9' ? 'D9 — Navamsa (marriage & fortune)' : 'D10 — Dashamsa (career & profession)'}</div>
              <div style={{ maxWidth: 560 }} dangerouslySetInnerHTML={{ __html: full[k].svg }} />
            </div>
          ) : null)}
        </Section>
      )}

      {view === 'lal' && full?.lalKitab && (
        <Section title="Lal Kitab Analysis" COLORS={COLORS}>
          <JsonReport data={full.lalKitab} COLORS={COLORS} />
        </Section>
      )}

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 6 }}>
        <button onClick={onBack} style={{ ...inputStyle, cursor: 'pointer', fontWeight: 700, maxWidth: 260 }}>Generate another kundli</button>
        <a href="#/" style={{ textDecoration: 'none', flex: 1, minWidth: 200 }}>
          <button style={{ ...inputStyle, cursor: 'pointer', fontWeight: 800, background: gradient, color: '#fff', border: 'none' }}>
            <Sparkles size={14} style={{ verticalAlign: '-2px', marginRight: 6 }} />Book a detailed consultation
          </button>
        </a>
      </div>
    </motion.div>
  )
}
const grahan_present = (g) => g?.grahanPresent ?? g?.present ?? false
const shrapit_present = (s) => s?.shrapitPresent ?? s?.present ?? false

function JsonReport({ data, skip = [], only = null, COLORS, depth = 0 }) {
  const entries = Array.isArray(data)
    ? data.map((v, i) => [String(i + 1), v])
    : Object.entries(data || {}).filter(([k]) => !skip.includes(k) && (!only || only.includes(k)))
  if (!entries.length) return null
  return (
    <div style={{ marginLeft: depth ? 14 : 0 }}>
      {entries.map(([k, v]) => {
        if (v == null || v === '') return null
        const isObj = typeof v === 'object'
        return (
          <div key={k} style={{ marginBottom: depth ? 6 : 14 }}>
            <div style={{ fontSize: depth ? 12.5 : 13.5, fontWeight: 800, color: COLORS.textDim }}>{k.replace(/([A-Z])/g, ' $1').replace(/^./, (c) => c.toUpperCase())}</div>
            {isObj
              ? <JsonReport data={v} skip={skip} COLORS={COLORS} depth={depth + 1} />
              : <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>{String(v).slice(0, 400)}</div>}
          </div>
        )
      })}
    </div>
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
