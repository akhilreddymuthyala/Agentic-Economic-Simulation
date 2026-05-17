import React from 'react'

export default function EconomyPanel() {
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
        Economy &amp; Resource Controls
      </h1>
      <p style={{ color: '#64748b', fontFamily: 'Share Tech Mono, monospace', fontSize: 12 }}>
        Policy and resource sliders — implemented in Phase 4.
      </p>
    </div>
  )
}