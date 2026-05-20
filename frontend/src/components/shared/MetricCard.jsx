import React from 'react'

export default function MetricCard({ label, value, unit = '', color = '#00d4ff', delta, small = false }) {
  return (
    <div style={{
      background: '#0b1120',
      border: '1px solid #1a2744',
      borderTop: `2px solid ${color}`,
      borderRadius: 4,
      padding: small ? '10px 14px' : '14px 18px',
      flex: '1 1 120px',
      minWidth: 120,
    }}>
      <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: small ? 18 : 22, color, fontFamily: 'Orbitron, monospace', fontWeight: 700 }}>
        {typeof value === 'number' ? value.toLocaleString('en', { maximumFractionDigits: 2 }) : value}
        <span style={{ fontSize: 10, color: '#64748b', marginLeft: 3 }}>{unit}</span>
      </div>
      {delta !== undefined && (
        <div style={{ fontSize: 10, color: delta >= 0 ? '#00ff88' : '#ff3366', marginTop: 3 }}>
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta).toFixed(3)}
        </div>
      )}
    </div>
  )
}