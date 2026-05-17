import React from 'react'
import axios from 'axios'
import { useSimulation } from '../context/SimulationContext'

const SPEEDS = [1, 5, 10, 25, 50]

export default function SimulationControl() {
  const { state } = useSimulation()

  const control = async (action, extra = {}) => {
    try {
      await axios.post('/api/simulation/control/', { action, ...extra })
    } catch (e) {
      console.error(e)
    }
  }

  const btnStyle = (active, color = '#00d4ff') => ({
    background: active ? `rgba(${color === '#00d4ff' ? '0,212,255' : '0,255,136'},0.12)` : '#0b1120',
    border: `1px solid ${active ? color : '#1a2744'}`,
    color: active ? color : '#64748b',
    padding: '10px 20px',
    borderRadius: 4,
    cursor: 'pointer',
    fontFamily: 'Share Tech Mono, monospace',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
    transition: 'all 0.15s',
  })

  return (
    <div>
      <h1
        style={{
          fontFamily: 'Orbitron, monospace',
          fontSize: 18,
          color: '#00d4ff',
          letterSpacing: 3,
          textTransform: 'uppercase',
          marginBottom: 32,
        }}
      >
        Simulation Control
      </h1>

      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 24, marginBottom: 24 }}>
        <div style={{ fontSize: 10, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 16 }}>
          Simulation State Controls
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button style={btnStyle(state.status === 'running', '#00ff88')} onClick={() => control('start')}>▶ Start</button>
          <button style={btnStyle(state.status === 'paused', '#ffcc00')} onClick={() => control('pause')}>⏸ Pause</button>
          <button style={btnStyle(state.status === 'stopped', '#ff3366')} onClick={() => control('stop')}>⏹ Stop</button>
          <button style={btnStyle(false)} onClick={() => control('reset')}>↺ Reset</button>
        </div>
      </div>

      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 24 }}>
        <div style={{ fontSize: 10, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 16 }}>
          Simulation Speed
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {SPEEDS.map((s) => (
            <button
              key={s}
              style={btnStyle(state.speed === s)}
              onClick={() => control('set_speed', { speed: s })}
            >
              {s}x
            </button>
          ))}
        </div>
        <div style={{ marginTop: 16, fontSize: 11, color: '#64748b', fontFamily: 'Share Tech Mono, monospace' }}>
          Current: {state.speed}x — 1 sim day = {(5 / state.speed).toFixed(2)} real minutes
        </div>
      </div>
    </div>
  )
}