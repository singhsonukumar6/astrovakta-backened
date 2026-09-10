import { useEffect, useRef, useState } from 'react'
import { MapPin, Loader2 } from 'lucide-react'
import { searchLocations, getLocationTimezone } from '../lib/api.js'

// Debounced birth-place search backed by /api/location/search.
// onSelect receives { label, lat, lon, tz } once coordinates (and, a moment
// later, the resolved IANA timezone) are known — everything kundli math needs.
export default function PlaceAutocomplete({ value, onSelect, placeholder = 'Birth place (city)', inputStyle, countrycode }) {
  const [query, setQuery] = useState(value || '')
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const boxRef = useRef(null)
  const timer = useRef(null)
  const pickedRef = useRef(null)

  useEffect(() => {
    const close = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const handleChange = (e) => {
    const q = e.target.value
    setQuery(q)
    pickedRef.current = null
    onSelect(null)
    setOpen(false)
    clearTimeout(timer.current)
    if (q.trim().length < 2) { setItems([]); setBusy(false); return }
    setBusy(true)
    timer.current = setTimeout(async () => {
      try {
        const list = await searchLocations(q.trim(), countrycode)
        setItems(list)
        setOpen(list.length > 0)
      } catch { setItems([]) }
      finally { setBusy(false) }
    }, 400)
  }

  const pick = (loc) => {
    const a = loc.address || {}
    const label = [a.city || loc.name, a.state, a.country].filter(Boolean).join(', ') || loc.displayName
    setQuery(label)
    setItems([])
    setOpen(false)
    const sel = { label, lat: loc.latitude, lon: loc.longitude, tz: null }
    pickedRef.current = sel
    onSelect(sel)
    // Resolve the IANA timezone from the coordinates (India resolves instantly)
    getLocationTimezone(loc.latitude, loc.longitude).then((tz) => {
      if (pickedRef.current === sel) onSelect({ ...sel, tz: tz || 'UTC' })
    })
  }

  return (
    <div ref={boxRef} style={{ position: 'relative' }}>
      <input
        value={query}
        onChange={handleChange}
        onFocus={() => { if (items.length > 0) setOpen(true) }}
        placeholder={placeholder}
        autoComplete="off"
        style={inputStyle}
      />
      {busy && (
        <Loader2 size={15} color="#94a3b8" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)' }} className="spin" />
      )}
      {open && items.length > 0 && (
        <div style={{
          position: 'absolute', left: 0, right: 0, top: 'calc(100% + 4px)', zIndex: 30,
          background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12,
          boxShadow: '0 12px 30px rgba(15,23,42,0.14)', overflow: 'hidden',
        }}>
          {items.map((loc, i) => (
            <button key={i} type="button" onClick={() => pick(loc)} style={{
              display: 'flex', alignItems: 'flex-start', gap: 9, width: '100%', padding: '10px 12px',
              border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left',
            }}
              onMouseDown={(e) => e.preventDefault()}>
              <MapPin size={14} color="#4f46e5" style={{ flexShrink: 0, marginTop: 2 }} />
              <span style={{ minWidth: 0 }}>
                <span style={{ display: 'block', fontSize: 13.5, fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {(loc.address?.city || loc.name || loc.displayName || '').slice(0, 40)}
                </span>
                <span style={{ display: 'block', fontSize: 11.5, color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {loc.displayName}
                </span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
