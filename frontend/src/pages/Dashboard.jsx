import React, { useEffect, useRef, useState } from 'react'
import { useSimulation } from '../context/SimulationContext'
import MetricCard from '../components/shared/MetricCard'
import MiniChart from '../components/shared/MiniChart'
import AgentDeltaFeed from '../components/shared/AgentDeltaFeed'

const MAX_HISTORY = 120
const EVENT_COLORS = {
  recession: '#ff3366', market_crash: '#ff0000', panic_wave: '#ff3366',
  monopoly: '#a855f7', innovation_boom: '#00ff88', unemployment_crisis: '#ffcc00',
  shortage: '#ffcc00', recovery: '#00d4ff',
}
const EMOTION_COLORS = {
  fearful: '#ff3366', panic: '#ff0000', greedy: '#ffcc00',
  optimistic: '#00d4ff', trusting: '#00ff88', stressed: '#a855f7', neutral: '#64748b',
}

export default function Dashboard() {
  const { state } = useSimulation()
  const { economy, simDate, events, tick, status, speed, panicWaveActive, emotionDistribution, behavioralModifiers } = state
  const [history, setHistory] = useState([])
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
        gini: economy.wealthGini,
        resourceIndex: economy.resourceIndex,
      }
      return [...prev, entry].slice(-MAX_HISTORY)
    })
    prevEco.current = economy
  }, [tick])

  const statusColor = { running: '#00ff88', paused: '#ffcc00', stopped: '#ff3366', idle: '#64748b' }[status] ?? '#64748b'
  const activeEventCount = events.filter(e => e.tick >= tick - 48).length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 18, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
            Command Dashboard
          </h1>
          <div style={{ color: '#64748b', fontSize: 11, marginTop: 3, fontFamily: 'Share Tech Mono, monospace' }}>
            Year {simDate.year} — Month {simDate.month} — Day {simDate.day} — {String(simDate.hour).padStart(2, '0')}:00
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, fontSize: 11, fontFamily: 'Share Tech Mono, monospace', color: '#64748b', flexWrap: 'wrap' }}>
          <span>Tick <span style={{ color: '#e2e8f0' }}>#{tick}</span></span>
          <span>Speed <span style={{ color: '#00d4ff' }}>{speed}x</span></span>
          <span>Events <span style={{ color: '#ffcc00' }}>{activeEventCount}</span></span>
          <span>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: statusColor, display: 'inline-block', marginRight: 5, boxShadow: `0 0 6px ${statusColor}` }} />
            <span style={{ color: statusColor, textTransform: 'uppercase' }}>{status}</span>
          </span>
          {panicWaveActive && (
            <span style={{ color: '#ff3366', animation: 'pulse-soft 1s infinite', fontWeight: 700 }}>
              ⚠ PANIC WAVE
            </span>
          )}
        </div>
      </div>

      {/* Economy Metrics Row 1 */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
        <MetricCard label="GDP" value={economy.gdp} unit="$" color="#00d4ff" />
        <MetricCard label="Inflation" value={economy.inflation} unit="%" color="#ffcc00" />
        <MetricCard label="Unemployment" value={economy.unemployment} unit="%" color="#ff3366" />
        <MetricCard label="Market Confidence" value={economy.marketConfidence} unit="%" color="#00ff88" />
        <MetricCard label="Wealth Gini" value={economy.wealthGini} color="#a855f7" />
        <MetricCard label="Resource Index" value={economy.resourceIndex} color="#00d4ff" />
        <MetricCard label="Stability" value={economy.economicStability} unit="%" color="#00ff88" />
      </div>

      {/* 6 Live Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
        <MiniChart data={history} dataKey="gdp" color="#00d4ff" label="GDP Growth" />
        <MiniChart data={history} dataKey="inflation" color="#ffcc00" label="Inflation %" referenceValue={2} />
        <MiniChart data={history} dataKey="unemployment" color="#ff3366" label="Employment Rate" />
        <MiniChart data={history} dataKey="gini" color="#a855f7" label="Wealth Inequality (Gini)" />
        <MiniChart data={history} dataKey="resourceIndex" color="#00d4ff" label="Resource Index" />
        <MiniChart data={history} dataKey="confidence" color="#00ff88" label="Market Confidence" referenceValue={70} />
      </div>

      {/* Emotion + Behavioral + Agent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>

        {/* Society Emotions */}
        <div style={{ background: '#0b1120', border: `1px solid ${panicWaveActive ? '#ff3366' : '#1a2744'}`, borderRadius: 4, padding: '12px 16px', boxShadow: panicWaveActive ? '0 0 20px rgba(255,51,102,0.2)' : 'none' }}>
          <div style={{ fontSize: 9, color: panicWaveActive ? '#ff3366' : '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
            {panicWaveActive ? '⚠ PANIC WAVE ACTIVE' : 'Society Emotions'}
          </div>
          {Object.entries(emotionDistribution).filter(([, v]) => v > 0).map(([emotion, count]) => {
            const color = EMOTION_COLORS[emotion] || '#64748b'
            const pct = Math.round((count / 100) * 100)
            return (
              <div key={emotion} style={{ marginBottom: 7 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 2 }}>
                  <span style={{ color, textTransform: 'uppercase', letterSpacing: 1 }}>{emotion}</span>
                  <span style={{ color: '#e2e8f0' }}>{count} agents</span>
                </div>
                <div style={{ background: '#1a2744', borderRadius: 2, height: 4 }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.5s' }} />
                </div>
              </div>
            )
          })}
          {Object.keys(emotionDistribution).length === 0 && (
            <div style={{ color: '#1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>Awaiting data...</div>
          )}
        </div>

        {/* Behavioral Modifiers */}
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: '12px 16px' }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
            Behavioral Modifiers
          </div>
          {Object.entries(behavioralModifiers).map(([key, val]) => {
            const isLow = val < 0.7, isHigh = val > 1.3
            const color = isLow ? '#ff3366' : isHigh ? '#00ff88' : '#64748b'
            return (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>
                <span style={{ color: '#64748b', textTransform: 'uppercase', fontSize: 9 }}>{key.replace(/_/g, ' ')}</span>
                <span style={{ color }}>{typeof val === 'number' ? val.toFixed(3) : val}</span>
              </div>
            )
          })}
        </div>

        {/* Agent Activity */}
        <AgentDeltaFeed />
      </div>

      {/* Live Event Feed */}
      <div>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10, display: 'flex', justifyContent: 'space-between' }}>
          <span>Live Event Feed</span>
          <span style={{ color: '#1a2744' }}>{events.length} events logged</span>
        </div>
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14, maxHeight: 280, overflowY: 'auto', fontFamily: 'Share Tech Mono, monospace', fontSize: 11 }}>
          {events.length === 0
            ? <div style={{ color: '#64748b' }}>Awaiting simulation events...</div>
            : events.map((evt, i) => {
              const typeColor = EVENT_COLORS[evt.event_type] || '#64748b'
              const severityColor = evt.severity > 0.7 ? '#ff3366' : evt.severity > 0.4 ? '#ffcc00' : '#00ff88'
              return (
                <div key={i} style={{ padding: '5px 0', borderBottom: '1px solid #1a2744', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <span style={{ color: '#64748b', whiteSpace: 'nowrap', fontSize: 10 }}>
                    [Y{evt.year} M{evt.month} D{evt.day}]
                  </span>
                  <span style={{ background: `${typeColor}22`, color: typeColor, padding: '1px 6px', borderRadius: 2, fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, whiteSpace: 'nowrap' }}>
                    {evt.event_type?.replace(/_/g, ' ')}
                  </span>
                  <span style={{ color: '#e2e8f0', flex: 1 }}>{evt.description}</span>
                  <span style={{ color: severityColor, fontSize: 10, whiteSpace: 'nowrap' }}>
                    {evt.severity ? `sev ${Number(evt.severity).toFixed(2)}` : ''}
                  </span>
                </div>
              )
            })
          }
        </div>
      </div>
    </div>
  )
}