import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import { useSimulation } from '../context/SimulationContext'

const EVENT_COLORS = {
  recession: '#ff3366', market_crash: '#ff0000', panic_wave: '#ff3366',
  monopoly: '#a855f7', innovation_boom: '#00ff88', unemployment_crisis: '#ffcc00',
  shortage: '#ffcc00', recovery: '#00d4ff',
}

export default function Analytics() {
  const { state } = useSimulation()
  const [events, setEvents] = useState([])
  const [eventSummary, setEventSummary] = useState([])
  const [history, setHistory] = useState([])
  const [snapshots, setSnapshots] = useState([])
  const [selectedSnapshot, setSelectedSnapshot] = useState(null)
  const [restoring, setRestoring] = useState(false)
  const [activeLines, setActiveLines] = useState({ gdp: true, inflation: true, unemployment: true, market_confidence: true })

  useEffect(() => {
    Promise.all([
      axios.get('/api/events/?limit=100'),
      axios.get('/api/events/summary/'),
      axios.get('/api/economy/state/history/?limit=200'),
      axios.get('/api/snapshots/'),
    ]).then(([evtRes, sumRes, histRes, snapRes]) => {
      setEvents(evtRes.data)
      setEventSummary(sumRes.data)
      setHistory((histRes.data || []).reverse())
      setSnapshots(snapRes.data)
    }).catch(() => {})
  }, [state.tick % 48 === 0])

  const restoreSnapshot = async (id) => {
    setRestoring(true)
    try {
      await axios.post(`/api/snapshots/${id}/restore/`)
      alert(`Snapshot ${id} restored. Restart simulation to continue from this point.`)
    } catch { alert('Restore failed') }
    setRestoring(false)
  }

  const chartData = history.map(h => ({
    tick: h.tick_number,
    day: `Y${h.simulation_year}M${h.simulation_month}D${h.simulation_day}`,
    gdp: h.gdp,
    inflation: h.inflation,
    unemployment: h.unemployment,
    market_confidence: h.market_confidence,
    stability: h.economic_stability,
    gini: h.wealth_gini,
  }))

  const toggleLine = (key) => setActiveLines(l => ({ ...l, [key]: !l[key] }))

  const lineBtn = (key, color, label) => (
    <button
      onClick={() => toggleLine(key)}
      style={{
        background: activeLines[key] ? `${color}18` : '#0b1120',
        border: `1px solid ${activeLines[key] ? color : '#1a2744'}`,
        color: activeLines[key] ? color : '#64748b',
        padding: '4px 10px', borderRadius: 4, cursor: 'pointer',
        fontFamily: 'Share Tech Mono, monospace', fontSize: 10,
        textTransform: 'uppercase', letterSpacing: 1,
      }}
    >{label}</button>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
        Analytics &amp; Replay
      </h1>

      {/* Economic History Chart */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase' }}>Economic History — {chartData.length} snapshots</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {lineBtn('gdp', '#00d4ff', 'GDP')}
            {lineBtn('inflation', '#ffcc00', 'Inflation')}
            {lineBtn('unemployment', '#ff3366', 'Unemployment')}
            {lineBtn('market_confidence', '#00ff88', 'Confidence')}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="2 2" stroke="#1a2744" />
            <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 9 }} interval={Math.floor(chartData.length / 8)} />
            <YAxis tick={{ fill: '#64748b', fontSize: 9 }} />
            <Tooltip contentStyle={{ background: '#0b1120', border: '1px solid #1a2744', fontSize: 10 }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {activeLines.gdp && <Line type="monotone" dataKey="gdp" stroke="#00d4ff" dot={false} strokeWidth={1.5} isAnimationActive={false} />}
            {activeLines.inflation && <Line type="monotone" dataKey="inflation" stroke="#ffcc00" dot={false} strokeWidth={1.5} isAnimationActive={false} />}
            {activeLines.unemployment && <Line type="monotone" dataKey="unemployment" stroke="#ff3366" dot={false} strokeWidth={1.5} isAnimationActive={false} />}
            {activeLines.market_confidence && <Line type="monotone" dataKey="market_confidence" stroke="#00ff88" dot={false} strokeWidth={1.5} isAnimationActive={false} />}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>

        {/* Event Summary */}
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Event Summary</div>
          {eventSummary.length === 0
            ? <div style={{ color: '#1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>No events yet</div>
            : eventSummary.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>
                <span style={{ color: EVENT_COLORS[s.event_type] || '#64748b', textTransform: 'uppercase', fontSize: 9 }}>{s.event_type?.replace(/_/g, ' ')}</span>
                <span style={{ color: '#e2e8f0' }}>×{s.count}</span>
                <span style={{ color: '#64748b' }}>avg sev {Number(s.avg_severity).toFixed(2)}</span>
              </div>
            ))
          }
        </div>

        {/* Snapshot Manager */}
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Snapshots — Replay System</div>
          {snapshots.length === 0
            ? <div style={{ color: '#1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>No snapshots saved yet</div>
            : snapshots.slice(0, 10).map(s => (
              <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #1a2744' }}>
                <div>
                  <div style={{ fontSize: 11, color: '#e2e8f0', fontFamily: 'Share Tech Mono, monospace' }}>{s.label}</div>
                  <div style={{ fontSize: 9, color: '#64748b' }}>Y{s.simulation_year} M{s.simulation_month} D{s.simulation_day} — Tick #{s.tick_number}</div>
                </div>
                <button
                  onClick={() => restoreSnapshot(s.id)}
                  disabled={restoring}
                  style={{ background: '#0b1120', border: '1px solid #a855f7', color: '#a855f7', padding: '4px 10px', borderRadius: 4, cursor: 'pointer', fontFamily: 'Share Tech Mono, monospace', fontSize: 10 }}
                >
                  Restore
                </button>
              </div>
            ))
          }
        </div>
      </div>

      {/* Full Event Timeline */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>
          Event Timeline — {events.length} events
        </div>
        <div style={{ maxHeight: 320, overflowY: 'auto', fontFamily: 'Share Tech Mono, monospace', fontSize: 11 }}>
          {events.length === 0
            ? <div style={{ color: '#1a2744' }}>No events recorded</div>
            : events.map((evt, i) => {
              const color = EVENT_COLORS[evt.event_type] || '#64748b'
              const severityColor = evt.severity > 0.7 ? '#ff3366' : evt.severity > 0.4 ? '#ffcc00' : '#00ff88'
              return (
                <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #1a2744', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <span style={{ color: '#64748b', whiteSpace: 'nowrap', fontSize: 10 }}>
                    Y{evt.simulation_year} M{evt.simulation_month} D{evt.simulation_day}
                  </span>
                  <span style={{ background: `${color}22`, color, padding: '1px 6px', borderRadius: 2, fontSize: 9, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                    {evt.event_type?.replace(/_/g, ' ')}
                  </span>
                  <span style={{ color: '#e2e8f0', flex: 1 }}>{evt.description}</span>
                  <span style={{ color: severityColor, whiteSpace: 'nowrap', fontSize: 10 }}>
                    sev {Number(evt.severity).toFixed(2)}
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