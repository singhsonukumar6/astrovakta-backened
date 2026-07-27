import { useMemo } from 'react'

export default function Starfield() {
  const stars = useMemo(() => {
    return Array.from({ length: 120 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: `${Math.random() * 2 + 1}px`,
      duration: `${Math.random() * 4 + 2}s`,
      delay: `${Math.random() * 4}s`,
      maxOpacity: Math.random() * 0.7 + 0.3,
    }))
  }, [])

  return (
    <div className="starfield">
      {stars.map((s) => (
        <div
          key={s.id}
          className="star"
          style={{
            left: s.left,
            top: s.top,
            width: s.size,
            height: s.size,
            '--duration': s.duration,
            animationDelay: s.delay,
            '--max-opacity': s.maxOpacity,
          }}
        />
      ))}
    </div>
  )
}
