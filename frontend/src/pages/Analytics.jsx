import React from 'react'

export default function Analytics() {
  return (
    <div>
      <h1
        style={{
          fontFamily: 'Orbitron, monospace',
          fontSize: 18,
          color: '#00d4ff',
          letterSpacing: 3,
          textTransform: 'uppercase',
          marginBottom: 12,
        }}
      >
        Analytics &amp; Replay
      </h1>
      <p style={{ color: '#64748b', fontFamily: 'Share Tech Mono, monospace', fontSize: 12 }}>
        Historical timeline, replay controls, and trend analysis — implemented in Phase 6.
      </p>
    </div>
  )
}