import React, { useState } from 'react'

export default function SectionCard({ title, children, defaultOpen = true, accent = '#1a2744' }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div style={{ background: '#0b1120', border: `1px solid ${accent}`, borderRadius: 4, marginBottom: 16, overflow: 'hidden' }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          padding: '10px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          borderBottom: open ? `1px solid ${accent}` : 'none',
        }}
      >
        <span style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase' }}>{title}</span>
        <span style={{ color: '#1a2744', fontSize: 12 }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && <div style={{ padding: 16 }}>{children}</div>}
    </div>
  )
}