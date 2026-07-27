import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Copy, ChevronDown, Clock, CheckCircle2, XCircle, Code, Globe, Maximize2, X, Settings, Search, MapPin, Loader2, ToggleLeft, ToggleRight } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api.js'
import { endpointCategories } from './sandbox_endpoints.js'

// ──── Location Search Autocomplete ────
function LocationSearch({ value, onSelect, label = 'Location', prefix = '', apiKey = '' }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(value || '')
  const debounceRef = useRef(null)
  const wrapperRef = useRef(null)

  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const search = (q) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!q || q.length < 2) { setResults([]); return }
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const headers = {}
        if (apiKey) headers['X-API-Key'] = apiKey
        const res = await api.get('/api/location/search', { params: { q, limit: 5 }, headers })
        setResults(res.data?.locations || [])
        setOpen(true)
      } catch { setResults([]) }
      setLoading(false)
    }, 300)
  }

  const handleSelect = async (loc) => {
    setSelected(loc.displayName)
    setQuery('')
    setResults([])
    setOpen(false)
    let tz = 'Asia/Kolkata'
    try {
      const h = {}
      if (apiKey) h['X-API-Key'] = apiKey
      const tzRes = await api.get('/api/location/timezone', { params: { lat: loc.latitude, lon: loc.longitude }, headers: h })
      tz = tzRes.data?.timezone || tz
    } catch {}
    onSelect({
      [`${prefix}latitude`]: loc.latitude,
      [`${prefix}longitude`]: loc.longitude,
      [`${prefix}timezone`]: tz,
      locationName: loc.displayName,
    })
  }

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
        <MapPin size={12} /> {label}
      </label>
      {selected && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'rgba(124,58,237,0.1)', borderRadius: 8, marginBottom: 6 }}>
          <MapPin size={14} color="#a78bfa" />
          <span style={{ flex: 1, fontSize: 13, color: '#e2e8f0' }}>{selected}</span>
          <button onClick={() => { setSelected(''); onSelect({ [`${prefix}latitude`]: null, [`${prefix}longitude`]: null, [`${prefix}timezone`]: null, locationName: '' }) }}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 2 }}>
            <X size={14} />
          </button>
        </div>
      )}
      <div style={{ position: 'relative' }}>
        <input
          className="input-field"
          placeholder="Search city or place..."
          value={query}
          onChange={(e) => { setQuery(e.target.value); search(e.target.value) }}
          onFocus={() => { if (results.length) setOpen(true) }}
          style={{ fontSize: 13, paddingRight: 32 }}
        />
        {loading && <Loader2 size={14} color="#64748b" style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', animation: 'spin 1s linear infinite' }} />}
      </div>
      <AnimatePresence>
        {open && results.length > 0 && (
          <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
            style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50, background: '#12122a', border: '1px solid rgba(124,58,237,0.25)', borderRadius: 10, marginTop: 4, overflow: 'hidden', boxShadow: '0 12px 40px rgba(0,0,0,0.5)' }}>
            {results.map((loc, i) => (
              <button key={i} onClick={() => handleSelect(loc)}
                style={{ display: 'flex', alignItems: 'flex-start', gap: 10, width: '100%', padding: '10px 14px', background: 'transparent', border: 'none', color: '#e2e8f0', cursor: 'pointer', textAlign: 'left', borderBottom: i < results.length - 1 ? '1px solid rgba(100,116,139,0.15)' : 'none' }}
                onMouseEnter={(e) => e.target.style.background = 'rgba(124,58,237,0.08)'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}>
                <MapPin size={14} color="#a78bfa" style={{ marginTop: 2, flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{loc.displayName}</div>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                    {loc.latitude?.toFixed(4)}, {loc.longitude?.toFixed(4)}
                  </div>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ──── Dynamic Form Fields ────
function DynamicForm({ fields, values, onChange, apiKey }) {
  // Group fields by their group property
  const groups = useMemo(() => {
    const g = {}
    for (const f of fields) {
      const grp = f.group || 'Other'
      if (!g[grp]) g[grp] = []
      g[grp].push(f)
    }
    return g
  }, [fields])

  const updateVal = (key, val) => {
    onChange({ ...values, [key]: val })
  }

  const handleLocationSelect = (prefix, locData) => {
    const newVals = { ...values, ...locData }
    onChange(newVals)
  }

  const locationPrefixMap = LOCATION_PREFIX_MAP

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {Object.entries(groups).map(([groupName, groupFields]) => (
        <div key={groupName}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#7c3aed', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
            {groupName}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {groupFields.map((field) => {
              // Location autocomplete fields
              if (field.type === 'location') {
                const prefix = locationPrefixMap[field.key] || ''
                return (
                  <LocationSearch
                    key={field.key}
                    label={field.label}
                    prefix={prefix}
                    value={values.locationName || ''}
                    onSelect={(locData) => handleLocationSelect(prefix, locData)}
                    apiKey={apiKey}
                  />
                )
              }

              // Hidden fields (auto-filled by location)
              if (field.type === 'hidden') return null

              // Text/number/date/time inputs
              const val = values[field.key] ?? ''
              const inputStyle = { fontSize: 13 }

              return (
                <div key={field.key}>
                  <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>{field.label}</label>
                  {field.type === 'textarea' ? (
                    <textarea
                      className="input-field"
                      value={val}
                      placeholder={field.placeholder || ''}
                      onChange={(e) => updateVal(field.key, e.target.value)}
                      rows={3}
                      style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.6 }}
                    />
                  ) : field.type === 'select' ? (
                    <div style={{ position: 'relative' }}>
                      <select
                        className="input-field"
                        value={val}
                        onChange={(e) => updateVal(field.key, e.target.value)}
                        style={{ appearance: 'none', paddingRight: 36, cursor: 'pointer', ...inputStyle }}>
                        <option value="">Select...</option>
                        {field.options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                      </select>
                      <ChevronDown size={14} color="#64748b" style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
                    </div>
                  ) : (
                    <input
                      className="input-field"
                      type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : field.type === 'time' ? 'time' : 'text'}
                      value={val}
                      placeholder={field.placeholder || ''}
                      min={field.min}
                      max={field.max}
                      onChange={(e) => updateVal(field.key, field.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                      style={inputStyle}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

// ──── Curl Generator ────
function CurlGenerator({ method, path, body, apiKey }) {
  const curlPath = path.split('?')[0]
  const curl = `curl -X ${method} "http://localhost:5000${curlPath}" \\
  -H "X-API-Key: ${apiKey || 'YOUR_API_KEY'}" \\
  -H "Content-Type: application/json"${
    method === 'POST' && body ? ` \\
  -d '${body.replace(/\n/g, '').replace(/  +/g, ' ')}'` : ''
  }`

  return (
    <div style={{ background: '#0d0d24', borderRadius: 'var(--radius)', padding: 16, position: 'relative' }}>
      <button
        onClick={() => { navigator.clipboard.writeText(curl).then(() => toast.success('Copied!')).catch(() => toast.error('Failed to copy')) }}
        style={{ position: 'absolute', top: 12, right: 12, background: 'rgba(124,58,237,0.15)', border: 'none', borderRadius: 6, padding: 6, color: '#a78bfa', cursor: 'pointer' }}>
        <Copy size={14} />
      </button>
      <pre style={{ fontSize: 12, lineHeight: 1.7, color: '#94a3b8', fontFamily: 'var(--font-mono)', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
        {curl}
      </pre>
    </div>
  )
}

// ──── SVG Helpers ────
function isSvgString(str) {
  if (typeof str !== 'string') return false
  const trimmed = str.trim()
  return trimmed.startsWith('<svg') || trimmed.startsWith('<?xml') || trimmed.startsWith('\\n<svg') || trimmed.startsWith('\\n<?xml')
}

function isSvgResponse(data) {
  if (typeof data === 'string' && isSvgString(data)) return true
  if (data?.svg && typeof data.svg === 'string' && isSvgString(data.svg)) return true
  if (data?.data?.svg && typeof data.data.svg === 'string' && isSvgString(data.data.svg)) return true
  return false
}

function getSvgString(data) {
  let svg = null
  if (typeof data === 'string' && isSvgString(data)) svg = data
  else if (data?.svg && typeof data.svg === 'string' && isSvgString(data.svg)) svg = data.svg
  else if (data?.data?.svg && typeof data.data.svg === 'string' && isSvgString(data.data.svg)) svg = data.data.svg
  if (!svg) return null
  return svg.replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\t/g, '\t')
}

function SvgViewer({ svgString }) {
  const [fullscreen, setFullscreen] = useState(false)
  const dataUrl = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgString)))}`
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

const planetEmoji = { Sun: '\u2609', Moon: '\u263D', Mars: '\u2642', Mercury: '\u263F', Jupiter: '\u2643', Venus: '\u2640', Saturn: '\u2644', Rahu: '\u2641', Ketu: '\u2642' }
const signEmoji = { Aries: '\u2648', Taurus: '\u2649', Gemini: '\u264A', Cancer: '\u264B', Leo: '\u264C', Virgo: '\u264D', Libra: '\u264E', Scorpio: '\u264F', Sagittarius: '\u2650', Capricorn: '\u2651', Aquarius: '\u2652', Pisces: '\u2653' }

// ──── Response Views ────
function WebKundliView({ data }) {
  const kundli = data?.data || data
  const planets = kundli?.planets || []
  const houses = kundli?.houses || []
  const basic = kundli?.basicDetails || {}
  const doshas = kundli?.doshas
  const yogas = kundli?.yogas

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {basic && Object.keys(basic).length > 0 && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: '#a78bfa' }}>Basic Details</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
            {Object.entries(basic).filter(([k]) => !['longitude','latitude'].includes(k)).map(([key, val]) => (
              <div key={key} style={{ fontSize: 13 }}>
                <span style={{ color: '#64748b' }}>{key.replace(/([A-Z])/g, ' $1').trim()}: </span>
                <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{typeof val === 'object' ? JSON.stringify(val) : String(val)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {planets.length > 0 && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: '#a78bfa' }}>Planets</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
            {planets.map((p) => (
              <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'rgba(10,10,26,0.5)', borderRadius: 10, borderLeft: `3px solid ${p.isRetrograde ? '#ef4444' : '#7c3aed'}` }}>
                <span style={{ fontSize: 20, width: 28, textAlign: 'center' }}>{planetEmoji[p.name] || '\u2B50'}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0' }}>{p.name}</span>
                    {p.isRetrograde && <span style={{ fontSize: 10, color: '#ef4444', fontWeight: 700 }}>R</span>}
                    {p.isCombust && <span style={{ fontSize: 10, color: '#f59e0b', fontWeight: 700 }}>C</span>}
                  </div>
                  <div style={{ fontSize: 12, color: '#94a3b8' }}>{signEmoji[p.sign] || ''} {p.sign} {p.degreeDMS || ''}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>House {p.house} \u00B7 {p.nakshatra} {p.nakshatraPada ? `P${p.nakshatraPada}` : ''} \u00B7 {p.houseStatus}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {houses.length > 0 && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: '#a78bfa' }}>Houses (Bhava)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
            {houses.map((h) => (
              <div key={h.house || h.number} style={{ padding: '10px 14px', background: 'rgba(10,10,26,0.5)', borderRadius: 10 }}>
                <div style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0', marginBottom: 4 }}>House {h.house || h.number}</div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>{signEmoji[h.sign] || ''} {h.sign} \u00B7 Lord: {h.signLord}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {doshas && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: '#a78bfa' }}>Doshas</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(Array.isArray(doshas) ? doshas : Object.entries(doshas).map(([name, val]) => ({ name, ...val }))).map((d, i) => {
              const name = d.name || d
              const present = d.present ?? d.hasDosha ?? false
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                  <span style={{ color: present ? '#ef4444' : '#22c55e', fontWeight: 700 }}>{present ? '\u26A0' : '\u2713'}</span>
                  <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{typeof name === 'string' ? name : JSON.stringify(name)}</span>
                  {d.severity && <span className="badge" style={{ fontSize: 10, padding: '2px 8px', background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}>{d.severity}</span>}
                </div>
              )
            })}
          </div>
        </div>
      )}
      {yogas && (
        <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: '#a78bfa' }}>Yogas</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {(Array.isArray(yogas) ? yogas : Object.entries(yogas).map(([name, val]) => ({ name, ...val })))
              .filter(y => typeof y === 'object' && y !== null).slice(0, 20)
              .map((y, i) => (
                <div key={i} style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: '#7c3aed' }}>\u25C6</span>
                  <span style={{ color: '#e2e8f0' }}>{y.name || y.yoga || JSON.stringify(y)}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

function WebGenericView({ data }) {
  if (data === null || data === undefined) return <p style={{ color: '#64748b' }}>No data</p>
  const renderValue = (val, depth = 0) => {
    if (val === null || val === undefined) return <span style={{ color: '#64748b' }}>null</span>
    if (typeof val === 'boolean') return <span style={{ color: val ? '#22c55e' : '#ef4444' }}>{String(val)}</span>
    if (typeof val === 'number') return <span style={{ color: '#3b82f6' }}>{val}</span>
    if (typeof val === 'string') {
      if (val.length > 200) return <div style={{ background: 'rgba(10,10,26,0.5)', borderRadius: 8, padding: 12, marginTop: 6 }}><span style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{val}</span></div>
      return <span style={{ color: '#e2e8f0' }}>"{val}"</span>
    }
    if (Array.isArray(val)) {
      if (val.length === 0) return <span style={{ color: '#64748b' }}>[]</span>
      return <div style={{ marginLeft: depth * 16 }}><span style={{ color: '#64748b' }}>[{val.length} items]</span><div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>{val.map((item, i) => <div key={i} style={{ paddingLeft: 12, borderLeft: '1px solid rgba(124,58,237,0.2)' }}>{renderValue(item, depth + 1)}</div>)}</div></div>
    }
    if (typeof val === 'object') {
      const entries = Object.entries(val)
      if (entries.length === 0) return <span style={{ color: '#64748b' }}>{'{}'}</span>
      return <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginLeft: depth * 16 }}>{entries.map(([k, v]) => <div key={k}><span style={{ color: '#a78bfa', fontWeight: 500 }}>{k}: </span>{renderValue(v, depth + 1)}</div>)}</div>
    }
    return <span style={{ color: '#e2e8f0' }}>{String(val)}</span>
  }
  const rootData = data?.data || data
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>{Object.entries(rootData).map(([key, val]) => <div key={key} className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 16 }}><h4 style={{ fontSize: 14, fontWeight: 700, color: '#a78bfa', marginBottom: 10 }}>{key.replace(/([A-Z])/g, ' $1').trim()}</h4>{renderValue(val, 0)}</div>)}</div>
}

function WebTextView({ text }) {
  return <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20, fontSize: 14, lineHeight: 1.8, color: '#e2e8f0', whiteSpace: 'pre-wrap' }}>{text}</div>
}

function WebResponseView({ data, status }) {
  if (status >= 400) {
    const errorMsg = data?.detail || data?.error || data?.message || JSON.stringify(data)
    return <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 20, borderLeft: '3px solid #ef4444' }}><h4 style={{ fontSize: 14, fontWeight: 700, color: '#ef4444', marginBottom: 8 }}>Error {status}</h4><p style={{ color: '#94a3b8', fontSize: 14 }}>{typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg)}</p></div>
  }
  if (isSvgResponse(data)) return <SvgViewer svgString={getSvgString(data)} />
  const rootData = data?.data || data
  if ((Array.isArray(rootData?.planets) && rootData.planets.length > 0) || (Array.isArray(rootData?.houses) && rootData.houses.length > 0)) return <WebKundliView data={data} />
  if (typeof data === 'string') return <WebTextView text={data} />
  return <WebGenericView data={data} />
}

// ──── Location Prefix Map ────
const LOCATION_PREFIX_MAP = {
  '_location': '',
  '_partnerLocation': 'partner',
  '_maleLocation': 'male',
  '_femaleLocation': 'female',
}

// ──── Main Sandbox Component ────
const DEFAULT_LOCATION = { dateOfBirth: '1990-05-15', timeOfBirth: '10:30', latitude: 28.6139, longitude: 77.209, timezone: 'Asia/Kolkata' }

export default function Sandbox() {
  const [selectedEndpoint, setSelectedEndpoint] = useState('/api/kundli')
  const [formValues, setFormValues] = useState(DEFAULT_LOCATION)
  const [jsonMode, setJsonMode] = useState(false)
  const [rawBody, setRawBody] = useState(JSON.stringify(DEFAULT_LOCATION, null, 2))
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [responseTime, setResponseTime] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [viewMode, setViewMode] = useState('web')
  const [searchQuery, setSearchQuery] = useState('')
  const [showAiConfig, setShowAiConfig] = useState(false)
  const [aiProviderUrl, setAiProviderUrl] = useState('')
  const [aiProviderKey, setAiProviderKey] = useState('')

  const allEndpoints = useMemo(() => Object.values(endpointCategories).flat(), [])
  const currentEndpoint = useMemo(() => allEndpoints.find(e => e.path === selectedEndpoint), [allEndpoints, selectedEndpoint])
  const isAiEndpoint = currentEndpoint?.ai === true

  const filteredCategories = useMemo(() => {
    if (!searchQuery) return endpointCategories
    const q = searchQuery.toLowerCase()
    const result = {}
    for (const [cat, eps] of Object.entries(endpointCategories)) {
      const matched = eps.filter(ep => ep.label.toLowerCase().includes(q) || ep.path.toLowerCase().includes(q))
      if (matched.length > 0) result[cat] = matched
    }
    return result
  }, [searchQuery])

  const endpointCount = useMemo(() => Object.values(filteredCategories).reduce((s, arr) => s + arr.length, 0), [filteredCategories])

  // Build body from form values (strips internal keys like _location, locationName)
  const buildBody = useCallback((vals) => {
    const body = {}
    for (const [k, v] of Object.entries(vals)) {
      if (k.startsWith('_') || k === 'locationName') continue
      if (v !== null && v !== undefined && v !== '') body[k] = v
    }
    return body
  }, [])

  const handleEndpointChange = (path) => {
    const ep = allEndpoints.find(e => e.path === path)
    setSelectedEndpoint(path)
    const initVals = { ...DEFAULT_LOCATION }
    if (ep?.fields) {
      for (const f of ep.fields) {
        if (f.type === 'location') {
          const prefix = LOCATION_PREFIX_MAP[f.key] || ''
          if (prefix) {
            initVals[`${prefix}latitude`] = DEFAULT_LOCATION.latitude
            initVals[`${prefix}longitude`] = DEFAULT_LOCATION.longitude
            initVals[`${prefix}timezone`] = DEFAULT_LOCATION.timezone
          }
          continue
        }
        if (f.type === 'hidden') continue
        if (f.key === 'year') initVals[f.key] = 2026
        else if (f.key === 'month') initVals[f.key] = 7
        else if (f.type === 'number') initVals[f.key] = f.min ?? (f.default ?? '')
        else if (f.type === 'select' && f.options?.length) initVals[f.key] = f.options[0]
        else if (f.type === 'date') initVals[f.key] = initVals[f.key] || '1990-05-15'
        else if (f.type === 'time') initVals[f.key] = initVals[f.key] || '10:30'
        else initVals[f.key] = initVals[f.key] || ''
      }
    }
    setFormValues(initVals)
    setRawBody(JSON.stringify(buildBody(initVals), null, 2))
    setResponse(null)
    setStatus(null)
    setResponseTime(null)
  }

  // Sync form changes to raw JSON
  useEffect(() => {
    if (!jsonMode) {
      setRawBody(JSON.stringify(buildBody(formValues), null, 2))
    }
  }, [formValues, jsonMode, buildBody])

  const handleFormChange = (newVals) => {
    setFormValues(newVals)
  }

  const handleRawChange = (newBody) => {
    setRawBody(newBody)
    try {
      const parsed = JSON.parse(newBody)
      setFormValues(prev => ({ ...prev, ...parsed }))
    } catch {}
  }

  const sendRequest = useCallback(async () => {
    setLoading(true)
    setResponse(null)
    setStatus(null)
    setResponseTime(null)
    const start = performance.now()
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (apiKey) headers['X-API-Key'] = apiKey

      let requestData = undefined
      if (currentEndpoint?.method === 'POST') {
        const bodyStr = jsonMode ? rawBody : JSON.stringify(buildBody(formValues), null, 2)
        requestData = JSON.parse(bodyStr || '{}')
        if (isAiEndpoint) {
          if (!aiProviderUrl) {
            toast.error('Configure AI Provider URL first (Settings icon)')
            setLoading(false)
            return
          }
          requestData._aiProviderUrl = aiProviderUrl
          requestData._aiProviderKey = aiProviderKey
        }
      }

      const isPdfEndpoint = currentEndpoint?.pdf
      const apiUrl = selectedEndpoint.split('?')[0]

      // For GET endpoints, build query params from rawBody
      let params = undefined
      if (currentEndpoint?.get) {
        const bodyStr = jsonMode ? rawBody : JSON.stringify(buildBody(formValues), null, 2)
        try {
          const parsed = JSON.parse(bodyStr || '{}')
          params = parsed
        } catch {
          params = undefined
        }
      }

      const res = await api.request({
        method: currentEndpoint?.method || 'POST',
        url: apiUrl,
        params,
        data: requestData,
        headers,
        validateStatus: () => true,
        responseType: isPdfEndpoint ? 'blob' : 'json',
      })

      if (isPdfEndpoint && res.status === 200) {
        const blob = new Blob([res.data], { type: 'application/pdf' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = (formValues.clientName || 'Report').replace(/\s+/g, '_') + '_Kundli_Report.pdf'
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        setResponse({ success: true, message: 'PDF downloaded successfully!', fileName: a.download })
        setStatus(200)
        toast.success('PDF report downloaded!')
      } else {
        setStatus(res.status)
        setResponse(res.data)
      }
      setResponseTime(Math.round(performance.now() - start))
    } catch (err) {
      setStatus(err.response?.status || 500)
      setResponse({ error: err.message })
      setResponseTime(Math.round(performance.now() - start))
    } finally {
      setLoading(false)
    }
  }, [selectedEndpoint, formValues, rawBody, jsonMode, apiKey, currentEndpoint, isAiEndpoint, aiProviderUrl, aiProviderKey, buildBody])

  const copyResponse = () => {
    navigator.clipboard.writeText(JSON.stringify(response, null, 2)).then(() => toast.success('Response copied!')).catch(() => toast.error('Failed to copy'))
  }

  const hasFields = currentEndpoint?.fields && currentEndpoint.fields.length > 0

  return (
    <div style={{ minHeight: '100vh', paddingTop: 96, paddingLeft: 24, paddingRight: 24 }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ maxWidth: 1400, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 800 }}>API <span className="gradient-text">Sandbox</span></h1>
            <p style={{ color: '#94a3b8' }}>{endpointCount} endpoints available</p>
          </div>
        </div>

        {/* Search */}
        <div style={{ position: 'relative', marginBottom: 20 }}>
          <Search size={16} color="#64748b" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
          <input className="input-field" placeholder="Search endpoints..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: 40, width: '100%', maxWidth: 400 }} />
        </div>

        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {/* Left Panel */}
          <div style={{ flex: '1 1 400px', minWidth: 0 }}>
            <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24 }}>
              {/* API Key */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>X-API-Key</label>
                <input className="input-field" placeholder="avk_xxxxxxxxxxxx" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }} />
              </div>

              {/* Endpoint Selector */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <label style={{ fontSize: 13, color: '#94a3b8' }}>Endpoint</label>
                  {isAiEndpoint && (
                    <button onClick={() => setShowAiConfig(!showAiConfig)} style={{ display: 'flex', alignItems: 'center', gap: 4, background: showAiConfig ? 'rgba(251,191,36,0.2)' : 'rgba(100,116,139,0.2)', border: 'none', borderRadius: 6, padding: '4px 8px', color: showAiConfig ? '#fbbf24' : '#94a3b8', fontSize: 11, cursor: 'pointer' }}>
                        <Settings size={12} /> AI Provider
                    </button>
                  )}
                </div>
                <div style={{ position: 'relative' }}>
                  <select className="input-field" value={selectedEndpoint} onChange={(e) => handleEndpointChange(e.target.value)} style={{ appearance: 'none', paddingRight: 36, cursor: 'pointer' }}>
                    {Object.entries(filteredCategories).map(([cat, eps]) => (
                      <optgroup key={cat} label={`${cat} (${eps.length})`}>
                        {eps.map(ep => <option key={ep.path} value={ep.path}>[{ep.method}] {ep.label}</option>)}
                      </optgroup>
                    ))}
                  </select>
                  <ChevronDown size={16} color="#64748b" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
                </div>
              </div>

              {/* AI Provider Config */}
              {isAiEndpoint && showAiConfig && (
                <div style={{ marginBottom: 16, padding: 14, background: 'rgba(251,191,36,0.05)', borderRadius: 10, border: '1px solid rgba(251,191,36,0.15)' }}>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#fbbf24', marginBottom: 10 }}>AI Provider Configuration</label>
                  <div style={{ marginBottom: 10 }}>
                    <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>Provider URL</label>
                    <input className="input-field" placeholder="https://api.openai.com/v1/chat/completions" value={aiProviderUrl} onChange={(e) => setAiProviderUrl(e.target.value)} style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>API Key</label>
                    <input className="input-field" placeholder="sk-..." type="password" value={aiProviderKey} onChange={(e) => setAiProviderKey(e.target.value)} style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }} />
                  </div>
                </div>
              )}

              {/* Form / JSON Toggle */}
              {currentEndpoint?.method === 'POST' && hasFields && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <button onClick={() => setJsonMode(false)} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, border: 'none', background: !jsonMode ? 'rgba(124,58,237,0.25)' : 'rgba(100,116,139,0.1)', color: !jsonMode ? '#a78bfa' : '#64748b', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                      {jsonMode ? <ToggleLeft size={14} /> : <ToggleRight size={14} color="#22c55e" />} Form
                    </button>
                    <button onClick={() => setJsonMode(true)} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, border: 'none', background: jsonMode ? 'rgba(124,58,237,0.25)' : 'rgba(100,116,139,0.1)', color: jsonMode ? '#a78bfa' : '#64748b', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                      {jsonMode ? <ToggleRight size={14} color="#22c55e" /> : <ToggleLeft size={14} />} JSON
                    </button>
                  </div>
                </div>
              )}

              {/* Form Fields or JSON Editor */}
              {currentEndpoint?.method === 'POST' && (
                <>
                  {jsonMode || !hasFields ? (
                    <div style={{ marginBottom: 16 }}>
                      <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Request Body</label>
                      <textarea className="input-field" value={rawBody} onChange={(e) => handleRawChange(e.target.value)} rows={12}
                        style={{ fontFamily: 'var(--font-mono)', fontSize: 13, resize: 'vertical', lineHeight: 1.6 }} />
                    </div>
                  ) : (
                    <div style={{ marginBottom: 16, maxHeight: 480, overflowY: 'auto', paddingRight: 4 }}>
                      <DynamicForm fields={currentEndpoint.fields} values={formValues} onChange={handleFormChange} apiKey={apiKey} />
                    </div>
                  )}
                </>
              )}

              {/* GET endpoint query params */}
              {currentEndpoint?.get && (
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Query Parameters</label>
                  {hasFields && !jsonMode ? (
                    <div style={{ maxHeight: 300, overflowY: 'auto', paddingRight: 4 }}>
                      <DynamicForm fields={currentEndpoint.fields} values={formValues} onChange={handleFormChange} apiKey={apiKey} />
                    </div>
                  ) : (
                    <textarea className="input-field" value={rawBody} onChange={(e) => handleRawChange(e.target.value)} rows={4}
                      style={{ fontFamily: 'var(--font-mono)', fontSize: 13, resize: 'vertical', lineHeight: 1.6 }} />
                  )}
                </div>
              )}

              {/* cURL */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>cURL</label>
                <CurlGenerator method={currentEndpoint?.method || 'POST'} path={selectedEndpoint} body={currentEndpoint?.method === 'POST' ? rawBody : null} apiKey={apiKey} />
              </div>

              <button className="btn-primary" onClick={sendRequest} disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
                {loading ? 'Sending...' : <><Play size={16} /> Send Request</>}
              </button>
            </div>
          </div>

          {/* Right Panel */}
          <div style={{ flex: '1 1 400px', minWidth: 0 }}>
            <div className="glass" style={{ borderRadius: 'var(--radius-lg)', padding: 24, minHeight: 400 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Response</span>
                  {status && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600, background: status < 400 ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: status < 400 ? '#22c55e' : '#ef4444' }}>
                        {status < 400 ? <CheckCircle2 size={12} /> : <XCircle size={12} />} {status}
                      </span>
                      {responseTime && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#64748b' }}><Clock size={12} /> {responseTime}ms</span>}
                    </div>
                  )}
                </div>
                {response && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'rgba(10,10,26,0.5)', borderRadius: 8, padding: 2 }}>
                    <button onClick={() => setViewMode('web')} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, border: 'none', background: viewMode === 'web' ? 'rgba(124,58,237,0.25)' : 'transparent', color: viewMode === 'web' ? '#a78bfa' : '#64748b', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}><Globe size={13} /> Web</button>
                    <button onClick={() => setViewMode('json')} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 6, border: 'none', background: viewMode === 'json' ? 'rgba(124,58,237,0.25)' : 'transparent', color: viewMode === 'json' ? '#a78bfa' : '#64748b', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}><Code size={13} /> JSON</button>
                  </div>
                )}
              </div>

              {response ? (
                viewMode === 'web' ? <WebResponseView data={response} status={status} /> : (
                  <div style={{ position: 'relative' }}>
                    <button onClick={copyResponse} style={{ position: 'absolute', top: 8, right: 8, background: 'rgba(124,58,237,0.15)', border: 'none', borderRadius: 6, padding: 6, color: '#a78bfa', cursor: 'pointer', zIndex: 5 }}><Copy size={13} /></button>
                    <pre style={{ background: '#0d0d24', borderRadius: 'var(--radius)', padding: 20, fontSize: 13, lineHeight: 1.7, fontFamily: 'var(--font-mono)', color: '#e2e8f0', overflow: 'auto', maxHeight: 600, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(response, null, 2)}
                    </pre>
                  </div>
                )
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: '#475569', fontSize: 15 }}>Send a request to see the response</div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
