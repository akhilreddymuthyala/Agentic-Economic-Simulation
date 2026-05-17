import React from 'react'

export default function AgentInspector() {
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
        Agent Inspector
      </h1>
      <p style={{ color: '#64748b', fontFamily: 'Share Tech Mono, monospace', fontSize: 12 }}>
        Per-agent drill-down panel — implemented in Phase 9.
      </p>
    </div>
  )
}