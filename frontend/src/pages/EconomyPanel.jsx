import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useSimulation } from '../context/SimulationContext'

function SliderControl({ label, value, min, max, step = 0.1, unit = '', color = '#00d4ff', onChange }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: '#64748b', fontFamily: 'Share Tech Mono, monospace', textTransform: 'uppercase', letterSpacing: 1 }}>
          {label}
        </span>
        <span style={{ fontSize: 12, color, fontFamily: 'Orbitron, monospace', fontWeight: 700 }}>
          {typeof value === 'number' ? value.toFixed(1) : value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{
          width: '100%',
          accentColor: color,
          background: 'transparent',
          cursor: 'pointer',
        }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#1a2744', marginTop: 2 }}>
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  )
}

function SectionCard({ title, children }) {
  return (
    <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20, marginBottom: 16 }}>
      <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 18, borderBottom: '1px solid #1a2744', paddingBottom: 8 }}>
        {title}
      </div>
      {children}
    </div>
  )
}

export default function EconomyPanel() {
  const { state } = useSimulation()

  const [policy, setPolicy] = useState({
    tax_rate: 20,
    interest_rate: 5,
    government_spending: 10000,
    subsidy_level: 0,
    stimulus_active: false,
    stimulus_amount: 0,
    market_regulation: 50,
  })

  const [resource, setResource] = useState({
    food_supply: 85,
    oil_supply: 80,
    energy_availability: 82,
    housing_supply: 75,
    water_resources: 90,
  })

  const [saving, setSaving] = useState(false)
  const [savedMsg, setSavedMsg] = useState('')

  useEffect(() => {
    axios.get('/api/policies/').then(r => setPolicy(r.data)).catch(() => {})
    axios.get('/api/resources/').then(r => setResource(r.data)).catch(() => {})
  }, [])

  const savePolicy = async (updates) => {
    const merged = { ...policy, ...updates }
    setPolicy(merged)
    setSaving(true)
    try {
      await axios.patch('/api/policies/', updates)
      setSavedMsg('Saved')
      setTimeout(() => setSavedMsg(''), 1500)
    } catch { setSavedMsg('Error') }
    finally { setSaving(false) }
  }

  const saveResource = async (updates) => {
    const merged = { ...resource, ...updates }
    setResource(merged)
    setSaving(true)
    try {
      await axios.patch('/api/resources/', updates)
      setSavedMsg('Saved')
      setTimeout(() => setSavedMsg(''), 1500)
    } catch { setSavedMsg('Error') }
    finally { setSaving(false) }
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
          Economy &amp; Resource Controls
        </h1>
        <div style={{ fontSize: 11, fontFamily: 'Share Tech Mono, monospace', color: savedMsg === 'Error' ? '#ff3366' : '#00ff88' }}>
          {saving ? 'Saving...' : savedMsg}
        </div>
      </div>

      {/* Live economy summary */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        {[
          { label: 'GDP', value: state.economy.gdp.toFixed(0), unit: '$', color: '#00d4ff' },
          { label: 'Inflation', value: state.economy.inflation.toFixed(2), unit: '%', color: '#ffcc00' },
          { label: 'Unemployment', value: state.economy.unemployment.toFixed(2), unit: '%', color: '#ff3366' },
          { label: 'Confidence', value: state.economy.marketConfidence.toFixed(1), unit: '%', color: '#00ff88' },
          { label: 'Resource Index', value: state.economy.resourceIndex.toFixed(1), color: '#a855f7' },
        ].map(m => (
          <div key={m.label} style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: '10px 16px', flex: '1 1 100px' }}>
            <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase' }}>{m.label}</div>
            <div style={{ fontSize: 18, color: m.color, fontFamily: 'Orbitron, monospace', fontWeight: 700, marginTop: 4 }}>
              {m.value}<span style={{ fontSize: 10, color: '#64748b', marginLeft: 2 }}>{m.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>

        {/* Economic Policy Controls */}
        <SectionCard title="Economic Policy">
          <SliderControl label="Tax Rate" value={policy.tax_rate} min={0} max={80} unit="%" color="#ffcc00"
            onChange={v => savePolicy({ tax_rate: v })} />
          <SliderControl label="Interest Rate" value={policy.interest_rate} min={0} max={25} unit="%" color="#ff3366"
            onChange={v => savePolicy({ interest_rate: v })} />
          <SliderControl label="Government Spending" value={policy.government_spending} min={0} max={200000} step={1000} unit="$" color="#00d4ff"
            onChange={v => savePolicy({ government_spending: v })} />
          <SliderControl label="Subsidy Level" value={policy.subsidy_level} min={0} max={50000} step={500} unit="$" color="#00ff88"
            onChange={v => savePolicy({ subsidy_level: v })} />
          <SliderControl label="Market Regulation" value={policy.market_regulation} min={0} max={100} unit="%" color="#a855f7"
            onChange={v => savePolicy({ market_regulation: v })} />

          {/* Stimulus toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
            <button
              onClick={() => savePolicy({ stimulus_active: !policy.stimulus_active })}
              style={{
                background: policy.stimulus_active ? 'rgba(0,255,136,0.12)' : '#0b1120',
                border: `1px solid ${policy.stimulus_active ? '#00ff88' : '#1a2744'}`,
                color: policy.stimulus_active ? '#00ff88' : '#64748b',
                padding: '8px 16px', borderRadius: 4, cursor: 'pointer',
                fontFamily: 'Share Tech Mono, monospace', fontSize: 11,
                textTransform: 'uppercase', letterSpacing: 1,
              }}
            >
              {policy.stimulus_active ? '● Stimulus ON' : '○ Stimulus OFF'}
            </button>
            {policy.stimulus_active && (
              <SliderControl label="Stimulus Amount" value={policy.stimulus_amount} min={0} max={500000} step={5000} unit="$" color="#00ff88"
                onChange={v => savePolicy({ stimulus_amount: v })} />
            )}
          </div>
        </SectionCard>

        {/* Resource Controls */}
        <SectionCard title="Resource Supply Controls">
          <SliderControl label="Food Supply" value={resource.food_supply} min={0} max={100} unit="%" color="#00ff88"
            onChange={v => saveResource({ food_supply: v })} />
          <SliderControl label="Oil Supply" value={resource.oil_supply} min={0} max={100} unit="%" color="#ffcc00"
            onChange={v => saveResource({ oil_supply: v })} />
          <SliderControl label="Energy Availability" value={resource.energy_availability} min={0} max={100} unit="%" color="#00d4ff"
            onChange={v => saveResource({ energy_availability: v })} />
          <SliderControl label="Housing Supply" value={resource.housing_supply} min={0} max={100} unit="%" color="#a855f7"
            onChange={v => saveResource({ housing_supply: v })} />
          <SliderControl label="Water Resources" value={resource.water_resources} min={0} max={100} unit="%" color="#ff3366"
            onChange={v => saveResource({ water_resources: v })} />
        </SectionCard>

      </div>
    </div>
  )
}