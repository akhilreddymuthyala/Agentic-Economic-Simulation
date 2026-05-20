import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useSimulation } from '../context/SimulationContext'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const SPEEDS = [1, 5, 10, 25, 50]
const SPEED_DESC = { 1: '5 min/day', 5: '1 min/day', 10: '30s/day', 25: '12s/day', 50: '6s/day' }

export default function SimulationControl() {
  const { state, dispatch } = useSimulation()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [agentCount, setAgentCount] = useState(100)

  useEffect(() => {
    axios.get('/api/agents/summary/').then(r => {
      setAgentCount(r.data.totals?.total || 100)
    }).catch(() => {})
  }, [])

  const control = async (action, extra = {}) => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post('/api/simulation/control/', { action, ...extra })
      dispatch({ type: 'SIM_STATUS', payload: res.data })
    } catch (e) {
      setError(e?.response?.data?.error || 'Request failed')
    } finally { setLoading(false) }
  }

  const isRunning = state.status === 'running'
  const isPaused = state.status === 'paused'

  const btnStyle = (active, color = '#00d4ff') => ({
    background: active ? `${color}18` : '#0b1120',
    border: `1px solid ${active ? color : '#1a2744'}`,
    color: active ? color : '#64748b',
    padding: '10px 22px', borderRadius: 4,
    cursor: loading ? 'not-allowed' : 'pointer',
    fontFamily: 'Share Tech Mono, monospace', fontSize: 12,
    letterSpacing: 1, textTransform: 'uppercase',
    transition: 'all 0.15s', opacity: loading ? 0.6 : 1,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
        Simulation Control
      </h1>

      {error && (
        <div style={{ background: '#ff336618', border: '1px solid #ff3366', borderRadius: 4, padding: '8px 14px', color: '#ff3366', fontSize: 12 }}>
          {error}
        </div>
      )}

      {/* Live Status Bar */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 16, display: 'flex', gap: 24, flexWrap: 'wrap', fontFamily: 'Share Tech Mono, monospace', fontSize: 11, color: '#64748b' }}>
        <span>Status: <span style={{ color: isRunning ? '#00ff88' : '#ffcc00', textTransform: 'uppercase' }}>{state.status}</span></span>
        <span>Tick: <span style={{ color: '#e2e8f0' }}>#{state.tick}</span></span>
        <span>Date: <span style={{ color: '#e2e8f0' }}>Y{state.simDate.year} M{state.simDate.month} D{state.simDate.day} {String(state.simDate.hour).padStart(2,'0')}:00</span></span>
        <span>Speed: <span style={{ color: '#00d4ff' }}>{state.speed}x</span></span>
        <span>Interval: <span style={{ color: '#00d4ff' }}>{state.tickIntervalSeconds}s/tick</span></span>
        <span>Agents: <span style={{ color: '#e2e8f0' }}>{agentCount}</span></span>
      </div>

      {/* State Controls */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 14 }}>Simulation State</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button style={btnStyle(isRunning, '#00ff88')} onClick={() => control('start')} disabled={loading || isRunning}>▶ Start</button>
          <button style={btnStyle(isPaused, '#ffcc00')} onClick={() => control('pause')} disabled={loading || !isRunning}>⏸ Pause</button>
          <button style={btnStyle(state.status === 'stopped', '#ff3366')} onClick={() => control('stop')} disabled={loading}>⏹ Stop</button>
          <button style={btnStyle(false)} onClick={() => control('reset')} disabled={loading || isRunning}>↺ Reset</button>
          <button
                  style={{
                  background: '#ff336618',
                  border: '1px solid #ff3366',
                  color: '#ff3366',
                  padding: '10px 22px', borderRadius: 4,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontFamily: 'Share Tech Mono, monospace', fontSize: 12,
                  letterSpacing: 1, textTransform: 'uppercase',
                  opacity: loading ? 0.6 : 1,
                }}
                onClick={async () => {
                  if (!window.confirm('Full reset will restore all agents, economy, and resources to baseline. Continue?')) return
                  setLoading(true)
                  try {
                    const res = await axios.post('/api/simulation/control/', { action: 'reset_full' })
                    dispatch({ type: 'SIM_STATUS', payload: res.data })
                    alert('Full reset complete. All agents and economy restored to baseline.')
                  } catch (e) {
                    setError('Reset failed: ' + (e?.response?.data?.error || e.message))
                  } finally { setLoading(false) }
                }}
                disabled={loading || isRunning}
              >
                ⚠ Full Reset
              </button>
        </div>
      </div>

      {/* Speed */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 14 }}>Simulation Speed</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {SPEEDS.map(s => (
            <button key={s} style={btnStyle(state.speed === s)} onClick={() => control('set_speed', { speed: s })} disabled={loading}>
              {s}x
            </button>
          ))}
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: '#64748b', fontFamily: 'Share Tech Mono, monospace' }}>
          Current: <span style={{ color: '#00d4ff' }}>{state.speed}x</span> — {SPEED_DESC[state.speed]}
        </div>
      </div>

      {/* Snapshot */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 14 }}>Snapshot Manager</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            style={btnStyle(false, '#a855f7')}
            onClick={async () => {
              try {
                await axios.post('/api/snapshots/', { label: `Manual tick ${state.tick}` })
                alert(`Snapshot saved at tick ${state.tick}`)
              } catch { alert('Snapshot failed') }
            }}
          >◈ Save Snapshot</button>
        </div>
        <div style={{ marginTop: 10, fontSize: 10, color: '#64748b', fontFamily: 'Share Tech Mono, monospace' }}>
          Current tick: #{state.tick} — Y{state.simDate.year} M{state.simDate.month} D{state.simDate.day}
        </div>
      </div>
    </div>
  )
}