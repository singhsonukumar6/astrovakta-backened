// Astrology-themed loading animation for the dashboard: a slowly rotating
// zodiac wheel, a fast-orbiting moon, and a pulsing planet. Used wherever a
// dashboard tab waits on data.

const ZODIAC_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']

const CSS = `
@keyframes dl-spin { to { transform: rotate(360deg); } }
@keyframes dl-spin-rev { to { transform: rotate(-360deg); } }
@keyframes dl-pulse { 0%,100% { transform: scale(1); box-shadow: 0 0 14px rgba(124,58,237,0.45); } 50% { transform: scale(1.12); box-shadow: 0 0 26px rgba(124,58,237,0.75); } }
@keyframes dl-blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
.dl-wheel { position: relative; }
.dl-ring { position: absolute; inset: 0; border-radius: 50%; border: 1.5px dashed rgba(124,58,237,0.4); animation: dl-spin 14s linear infinite; }
.dl-glyph { position: absolute; left: 50%; top: 50%; font-size: 11px; color: #a78bfa; margin: -7px; line-height: 14px; }
.dl-orbit { position: absolute; inset: 12%; border-radius: 50%; animation: dl-spin-rev 2.6s linear infinite; }
.dl-moon { position: absolute; top: -4px; left: 50%; width: 8px; height: 8px; margin-left: -4px; border-radius: 50%; background: linear-gradient(135deg, #eab308, #f59e0b); box-shadow: 0 0 10px rgba(234,179,8,0.8); }
.dl-planet { position: absolute; left: 50%; top: 50%; border-radius: 50%; background: linear-gradient(135deg, #7c3aed, #a78bfa); animation: dl-pulse 1.6s ease-in-out infinite; }
`

export default function DashboardLoader({ label = 'Loading', size = 64, full = false, light = false }) {
  const text = light ? '#f1f0ff' : '#64748b'
  return (
    <div style={full
      ? { minHeight: '70vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18 }
      : { padding: 44, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14 }}>
      <style>{CSS}</style>
      <div className="dl-wheel" style={{ width: size, height: size }}>
        <div className="dl-ring">
          {ZODIAC_GLYPHS.map((g, i) => (
            <span key={i} className="dl-glyph"
              style={{ transform: `rotate(${i * 30}deg) translateY(-${Math.round(size / 2) - 8}px)` }}>{g}</span>
          ))}
        </div>
        <div className="dl-orbit"><span className="dl-moon" /></div>
        <div className="dl-planet"
          style={{ width: Math.round(size * 0.3), height: Math.round(size * 0.3), marginLeft: -Math.round(size * 0.15), marginTop: -Math.round(size * 0.15) }} />
      </div>
      <div style={{ color: text, fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'baseline', gap: 2 }}>
        {label}
        {[0, 1, 2].map((i) => (
          <span key={i} style={{ animation: `dl-blink 1.2s ${i * 0.2}s infinite` }}>.</span>
        ))}
      </div>
    </div>
  )
}
