// Standard loading state: a clean circular-arc spinner (the familiar
// border-arc pattern used by GitHub/Linear/Material) with an animated
// ellipsis on the label. Theme-neutral — no astrology motifs.

const CSS = `
@keyframes dl-rotate { to { transform: rotate(360deg); } }
@keyframes dl-blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
@keyframes dl-fade-in { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
.dl-spinner {
  border-radius: 50%;
  animation: dl-rotate 0.75s linear infinite;
  animation-fill-mode: forwards;
}
.dl-wrap { animation: dl-fade-in 0.25s ease-out; }
`

export default function DashboardLoader({ label = 'Loading', size = 48, full = false, light = false }) {
  const text = light ? 'rgba(241,240,255,0.75)' : '#64748b'
  const arc = light ? '#f1f0ff' : '#6d5bd0'          // the moving arc
  const track = light ? 'rgba(241,240,255,0.16)' : 'rgba(109,91,208,0.16)'  // the faint full ring
  const border = Math.max(2, Math.round(size * 0.07))
  return (
    <div className="dl-wrap" style={full
      ? { minHeight: '70vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18 }
      : { padding: 44, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14 }}>
      <style>{CSS}</style>
      <div className="dl-spinner" style={{
        width: size, height: size,
        border: `${border}px solid ${track}`,
        borderTopColor: arc,
      }} />
      <div style={{ color: text, fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'baseline', gap: 2 }}>
        {label}
        {[0, 1, 2].map((i) => (
          <span key={i} style={{ animation: `dl-blink 1.2s ${i * 0.2}s infinite` }}>.</span>
        ))}
      </div>
    </div>
  )
}
