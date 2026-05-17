import React, { useState } from 'react'
import axios from 'axios'
import { useSimulation } from '../context/SimulationContext'

const SPEEDS = [1, 5, 10, 25, 50]

const SPEED_DESC = {
  1: '5 min / sim day',
  5: '1 min / sim day',
  10: '30 sec / sim day',
  25: '12 sec / sim day',
  50: '6 sec / sim day',
}

export default function SimulationControl() {
  const { state, dispatch } = useSimulation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const control = async (action, extra = {}) => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post('/api/simulation/control/', { action, ...extra })
      dispatch({ type: 'SIM_STATUS', payload: res.data })
    } catch (e) {
      setError(e?.response?.data?.error || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const isRunning = state.status === 'running'
  const isPaused = state.status === 'paused'

  const btnStyle = (active, color = '#00d4ff') => ({
    background: active ? `rgba(0,212,255,0.1)` : '#0b1120',
    border: `1px solid ${active ? color : '#1a2744'}`,
    color: active ? color : '#64748b',
    padding: '10px 22px',
    borderRadius: 4,
    cursor: loading ? 'not-allowed' : 'pointer',
    fontFamily: 'Share Tech Mono, monospace',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
    transition: 'all 0.15s',
    opacity: loading ? 0.6 : 1,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
        Simulation Control
      </h1>

      {error && (
        <div style={{ background: 'rgba(255,51,102,0.1)', border: '1px solid #ff3366', borderRadius: 4, padding: '8px 14px', color: '#ff3366', fontSize: 12 }}>
          {error}
        </div>
      )}

      {/* State display */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 16, fontFamily: 'Share Tech Mono, monospace', fontSize: 11, color: '#64748b', display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        <span>Status: <span style={{ color: isRunning ? '#00ff88' : '#ffcc00', textTransform: 'uppercase' }}>{state.status}</span></span>
        <span>Tick: <span style={{ color: '#e2e8f0' }}>#{state.tick}</span></span>
        <span>Date: <span style={{ color: '#e2e8f0' }}>Y{state.simDate.year} M{state.simDate.month} D{state.simDate.day} {String(state.simDate.hour).padStart(2,'0')}:00</span></span>
        <span>Interval: <span style={{ color: '#00d4ff' }}>{state.tickIntervalSeconds}s / tick</span></span>
      </div>

      {/* Controls */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 14 }}>
          Simulation State
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button style={btnStyle(isRunning, '#00ff88')} onClick={() => control('start')} disabled={loading || isRunning}>
            ▶ Start
          </button>
          <button style={btnStyle(isPaused, '#ffcc00')} onClick={() => control('pause')} disabled={loading || !isRunning}>
            ⏸ Pause
          </button>
          <button style={btnStyle(state.status === 'stopped', '#ff3366')} onClick={() => control('stop')} disabled={loading}>
            ⏹ Stop
          </button>
          <button style={btnStyle(false)} onClick={() => control('reset')} disabled={loading || isRunning}>
            ↺ Reset
          </button>
        </div>
      </div>

      {/* Speed */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 14 }}>
          Simulation Speed
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {SPEEDS.map(s => (
            <button
              key={s}
              style={btnStyle(state.speed === s)}
              onClick={() => control('set_speed', { speed: s })}
              disabled={loading}
            >
              {s}x
            </button>
          ))}
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: '#64748b', fontFamily: 'Share Tech Mono, monospace' }}>
          Current: <span style={{ color: '#00d4ff' }}>{state.speed}x</span> — {SPEED_DESC[state.speed]}
        </div>
      </div>

      {/* Snapshot controls */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 14 }}>
          Snapshot Manager
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            style={btnStyle(false, '#a855f7')}
            onClick={async () => {
              try {
                await axios.post('/api/snapshots/', { label: `Manual snapshot tick ${state.tick}` })
                alert('Snapshot saved.')
              } catch { alert('Snapshot failed.') }
            }}
          >
            ◈ Save Snapshot
          </button>
        </div>
        <div style={{ marginTop: 10, fontSize: 10, color: '#64748b', fontFamily: 'Share Tech Mono, monospace' }}>
          View and restore snapshots in the Analytics page.
        </div>
      </div>
    </div>
  )
}