import React, { useEffect, useRef, useState } from 'react'
import { useSimulation } from '../context/SimulationContext'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis } from 'recharts'

function MetricCard({ label, value, unit = '', color = '#00d4ff', delta }) {
  return (
    <div style={{
      background: '#0b1120',
      border: `1px solid #1a2744`,
      borderTop: `2px solid ${color}`,
      borderRadius: 4,
      padding: '14px 18px',
      minWidth: 140,
      flex: '1 1 140px',
    }}>
      <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, color, fontFamily: 'Orbitron, monospace', fontWeight: 700 }}>
        {typeof value === 'number' ? value.toFixed(2) : value}
        <span style={{ fontSize: 11, color: '#64748b', marginLeft: 3 }}>{unit}</span>
      </div>
      {delta !== undefined && (
        <div style={{ fontSize: 10, color: delta >= 0 ? '#00ff88' : '#ff3366', marginTop: 4 }}>
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta).toFixed(3)}
        </div>
      )}
    </div>
  )
}

const MAX_HISTORY = 60

export default function Dashboard() {
  const { state } = useSimulation()
  const { economy, simDate, events, tick, status, speed, formattedDate } = state
  const [history, setHistory] = useState([])
  const { emotionDistribution, behavioralModifiers, panicWaveActive } = state
  const prevEco = useRef(economy)

  useEffect(() => {
    if (tick === 0) return
    setHistory(prev => {
      const entry = {
        tick,
        gdp: economy.gdp,
        inflation: economy.inflation,
        unemployment: economy.unemployment,
        confidence: economy.marketConfidence,
        stability: economy.economicStability,
      }
      return [...prev, entry].slice(-MAX_HISTORY)
    })
    prevEco.current = economy
  }, [tick])

  const statusColor = { running: '#00ff88', paused: '#ffcc00', stopped: '#ff3366', idle: '#64748b' }[status] ?? '#64748b'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
            Command Dashboard
          </h1>
          <div style={{ color: '#64748b', fontSize: 11, marginTop: 3, fontFamily: 'Share Tech Mono, monospace' }}>
            {formattedDate}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, fontSize: 11, fontFamily: 'Share Tech Mono, monospace', color: '#64748b' }}>
          <span>Tick <span style={{ color: '#e2e8f0' }}>#{tick}</span></span>
          <span>Speed <span style={{ color: '#00d4ff' }}>{speed}x</span></span>
          <span>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: statusColor, display: 'inline-block', marginRight: 5, boxShadow: `0 0 6px ${statusColor}` }} />
            <span style={{ color: statusColor, textTransform: 'uppercase' }}>{status}</span>
          </span>
        </div>
      </div>

      {/* Economy Metrics */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
        <MetricCard label="GDP" value={economy.gdp} unit="$" color="#00d4ff" />
        <MetricCard label="Inflation" value={economy.inflation} unit="%" color="#ffcc00" />
        <MetricCard label="Unemployment" value={economy.unemployment} unit="%" color="#ff3366" />
        <MetricCard label="Market Confidence" value={economy.marketConfidence} unit="%" color="#00ff88" />
        <MetricCard label="Wealth Gini" value={economy.wealthGini} color="#a855f7" />
        <MetricCard label="Resource Index" value={economy.resourceIndex} color="#00d4ff" />
        <MetricCard label="Stability" value={economy.economicStability} unit="%" color="#00ff88" />
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
        {[
          { key: 'gdp', label: 'GDP', color: '#00d4ff' },
          { key: 'inflation', label: 'Inflation %', color: '#ffcc00' },
          { key: 'unemployment', label: 'Unemployment %', color: '#ff3366' },
          { key: 'confidence', label: 'Market Confidence', color: '#00ff88' },
        ].map(({ key, label, color }) => (
          <div key={key} style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: '12px 16px' }}>
            <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>{label}</div>
            <ResponsiveContainer width="100%" height={80}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="2 2" stroke="#1a2744" />
                <XAxis dataKey="tick" hide />
                <YAxis hide domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ background: '#0b1120', border: '1px solid #1a2744', fontSize: 11 }}
                  labelStyle={{ color: '#64748b' }}
                  itemStyle={{ color }}
                />
                <Line type="monotone" dataKey={key} stroke={color} dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      {/* Emotion & Behavior Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>

        {/* Emotion Distribution */}
        <div style={{ background: '#0b1120', border: `1px solid ${panicWaveActive ? '#ff3366' : '#1a2744'}`, borderRadius: 4, padding: '12px 16px', boxShadow: panicWaveActive ? '0 0 20px rgba(255,51,102,0.3)' : 'none' }}>
          <div style={{ fontSize: 9, color: panicWaveActive ? '#ff3366' : '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
            {panicWaveActive ? '⚠ PANIC WAVE ACTIVE' : 'Society Emotions'}
          </div>
          {Object.entries(emotionDistribution).filter(([, v]) => v > 0).map(([emotion, count]) => {
            const colors = { fearful: '#ff3366', greedy: '#ffcc00', trusting: '#00ff88', optimistic: '#00d4ff', stressed: '#a855f7', panic: '#ff0000', neutral: '#64748b' }
            const color = colors[emotion] || '#64748b'
            const pct = Math.round((count / 100) * 100)
            return (
              <div key={emotion} style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 2 }}>
                  <span style={{ color, textTransform: 'uppercase', letterSpacing: 1 }}>{emotion}</span>
                  <span style={{ color: '#e2e8f0' }}>{count} agents</span>
                </div>
                <div style={{ background: '#1a2744', borderRadius: 2, height: 4 }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.3s' }} />
                </div>
              </div>
            )
          })}
        </div>

        {/* Behavioral Modifiers */}
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: '12px 16px' }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
            Behavioral Modifiers
          </div>
          {Object.entries(behavioralModifiers).map(([key, val]) => {
            const label = key.replace(/_/g, ' ')
            const isLow = val < 0.7
            const isHigh = val > 1.3
            const color = isLow ? '#ff3366' : isHigh ? '#00ff88' : '#64748b'
            return (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>
                <span style={{ color: '#64748b', textTransform: 'uppercase', fontSize: 10 }}>{label}</span>
                <span style={{ color }}>{typeof val === 'number' ? val.toFixed(3) : val}</span>
              </div>
            )
          })}
        </div>

      </div>
      {/* Live Event Feed */}
      <div>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
          Live Event Feed
        </div>
        <div style={{
          background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4,
          padding: 14, maxHeight: 240, overflowY: 'auto',
          fontFamily: 'Share Tech Mono, monospace', fontSize: 11,
        }}>
          {events.length === 0
            ? <div style={{ color: '#64748b' }}>Awaiting simulation events...</div>
            : events.map((evt, i) => (
              <div key={i} style={{ padding: '3px 0', borderBottom: '1px solid #1a2744', color: evt.severity > 0.7 ? '#ff3366' : '#e2e8f0' }}>
                <span style={{ color: '#64748b' }}>[Y{evt.year} M{evt.month} D{evt.day}]</span>{' '}{evt.description}
              </div>
            ))
          }
        </div>
      </div>
    </div>
  )
}