import React from 'react'
import { useSimulation } from '../../context/SimulationContext'

const EMOTION_COLORS = {
  panic: '#ff0000',
  fearful: '#ff3366',
  stressed: '#a855f7',
  greedy: '#ffcc00',
  optimistic: '#00d4ff',
  trusting: '#00ff88',
  neutral: '#64748b',
}

const ACTION_COLORS = {
  panic: '#ff0000',
  sell: '#ff3366',
  buy: '#00ff88',
  invest: '#00d4ff',
  save: '#64748b',
  work: '#ffcc00',
  cooperate: '#a855f7',
}

const TIER_LABELS = { 1: 'LLM', 2: 'NET', 3: 'RULE' }

export default function AgentDeltaFeed() {
  const { state } = useSimulation()
  const deltas = state.agentDeltas || []

  return (
    <div style={{
      background: '#0b1120',
      border: '1px solid #1a2744',
      borderRadius: 4,
      padding: '12px 16px',
    }}>
      <div style={{
        fontSize: 9, color: '#64748b', letterSpacing: 2,
        textTransform: 'uppercase', marginBottom: 10,
      }}>
        Agent Activity — Tick #{state.tick}
      </div>

      {deltas.length === 0 ? (
        <div style={{ color: '#1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>
          No agent activity this tick
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {deltas.map((delta, i) => {
            const emotionColor = EMOTION_COLORS[delta.dominant_emotion] || '#64748b'
            const actionColor = ACTION_COLORS[delta.last_action] || '#64748b'
            const tierLabel = TIER_LABELS[delta.tier] || 'RULE'

            return (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '3px 0',
                borderBottom: '1px solid #0b1120',
                fontFamily: 'Share Tech Mono, monospace',
                fontSize: 10,
              }}>
                <span style={{
                  background: '#1a2744',
                  color: '#64748b',
                  padding: '1px 4px',
                  borderRadius: 2,
                  fontSize: 8,
                  minWidth: 32,
                  textAlign: 'center',
                }}>
                  {tierLabel}
                </span>
                <span style={{ color: '#64748b', minWidth: 80, textTransform: 'capitalize' }}>
                  {delta.profession?.replace(/_/g, ' ')}
                </span>
                <span style={{
                  color: actionColor,
                  textTransform: 'uppercase',
                  minWidth: 60,
                  fontWeight: 700,
                  fontSize: 9,
                }}>
                  {delta.last_action}
                </span>
                <span style={{ color: emotionColor, minWidth: 70, textTransform: 'capitalize', fontSize: 9 }}>
                  {delta.dominant_emotion}
                </span>
                <span style={{ color: '#e2e8f0', marginLeft: 'auto' }}>
                  ${delta.wealth?.toLocaleString('en', { maximumFractionDigits: 0 })}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}