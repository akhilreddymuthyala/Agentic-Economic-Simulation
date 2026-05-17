import React from 'react'
import { useSimulation } from '../context/SimulationContext'

function MetricCard({ label, value, unit = '', color = '#00d4ff' }) {
  return (
    <div
      style={{
        background: '#0b1120',
        border: '1px solid #1a2744',
        borderRadius: 4,
        padding: '16px 20px',
        minWidth: 140,
      }}
    >
      <div style={{ fontSize: 10, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, color, fontFamily: 'Orbitron, monospace', fontWeight: 700 }}>
        {typeof value === 'number' ? value.toFixed(1) : value}
        <span style={{ fontSize: 12, color: '#64748b', marginLeft: 4 }}>{unit}</span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { state } = useSimulation()
  const { economy, simDate, events, tick, status, speed } = state

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontFamily: 'Orbitron, monospace',
            fontSize: 18,
            color: '#00d4ff',
            letterSpacing: 3,
            textTransform: 'uppercase',
          }}
        >
          Command Dashboard
        </h1>
        <div style={{ color: '#64748b', fontSize: 11, marginTop: 4, fontFamily: 'Share Tech Mono, monospace' }}>
          Year {simDate.year} — Month {simDate.month} — Day {simDate.day} — {String(simDate.hour).padStart(2, '0')}:00 &nbsp;|&nbsp;
          Tick #{tick} &nbsp;|&nbsp; Speed {speed}x &nbsp;|&nbsp;
          Status <span style={{ color: status === 'running' ? '#00ff88' : '#ffcc00', textTransform: 'uppercase' }}>{status}</span>
        </div>
      </div>

      {/* Economy Metrics */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 32 }}>
        <MetricCard label="GDP" value={economy.gdp} unit="$" color="#00d4ff" />
        <MetricCard label="Inflation" value={economy.inflation} unit="%" color="#ffcc00" />
        <MetricCard label="Unemployment" value={economy.unemployment} unit="%" color="#ff3366" />
        <MetricCard label="Market Confidence" value={economy.marketConfidence} unit="%" color="#00ff88" />
        <MetricCard label="Wealth Gini" value={economy.wealthGini} color="#a855f7" />
        <MetricCard label="Resource Index" value={economy.resourceIndex} color="#00d4ff" />
        <MetricCard label="Stability" value={economy.economicStability} unit="%" color="#00ff88" />
      </div>

      {/* Live Event Feed */}
      <div>
        <div
          style={{
            fontSize: 10,
            color: '#64748b',
            letterSpacing: 2,
            textTransform: 'uppercase',
            marginBottom: 12,
          }}
        >
          Live Event Feed
        </div>
        <div
          style={{
            background: '#0b1120',
            border: '1px solid #1a2744',
            borderRadius: 4,
            padding: 16,
            maxHeight: 320,
            overflowY: 'auto',
            fontFamily: 'Share Tech Mono, monospace',
            fontSize: 12,
          }}
        >
          {events.length === 0 ? (
            <div style={{ color: '#64748b' }}>Awaiting simulation events...</div>
          ) : (
            events.map((evt, i) => (
              <div
                key={i}
                style={{
                  padding: '4px 0',
                  borderBottom: '1px solid #1a2744',
                  color: evt.severity > 0.7 ? '#ff3366' : '#e2e8f0',
                }}
              >
                <span style={{ color: '#64748b' }}>
                  [Y{evt.year} M{evt.month} D{evt.day}]
                </span>{' '}
                {evt.description}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}