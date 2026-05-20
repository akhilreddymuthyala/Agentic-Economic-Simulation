import React, { useEffect, useState } from 'react'
import { useSimulation } from '../../context/SimulationContext'

export default function ConnectionStatus() {
  const { state } = useSimulation()
  const [lag, setLag] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      if (state.lastHeartbeat) {
        setLag(Math.round((Date.now() - state.lastHeartbeat) / 1000))
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [state.lastHeartbeat])

  const isStale = lag > 30
  const color = !state.connected ? '#ff3366'
    : isStale ? '#ffcc00'
    : '#00ff88'

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 10,
      fontFamily: 'Share Tech Mono, monospace',
      color: '#64748b',
    }}>
      <span style={{
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 6px ${color}`,
        display: 'inline-block',
        animation: state.connected && !isStale ? 'pulse-soft 2s infinite' : 'none',
      }} />
      <span style={{ color }}>
        {!state.connected ? 'DISCONNECTED'
          : isStale ? `STALE (${lag}s)`
          : 'LIVE'}
      </span>
      {state.connected && (
        <span style={{ color: '#1a2744' }}>
          tick #{state.tick}
        </span>
      )}
    </div>
  )
}