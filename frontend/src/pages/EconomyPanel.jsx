import React, { useState } from 'react'
import axios from 'axios'
import { useSimulation } from '../context/SimulationContext'
import MetricCard from '../components/shared/MetricCard'

function SliderRow({ label, value, min, max, step = 0.1, unit = '', color = '#00d4ff', onChange }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 10, color: '#64748b', fontFamily: 'Share Tech Mono, monospace', textTransform: 'uppercase', letterSpacing: 1 }}>
          {label}
        </span>
        <span style={{ fontSize: 12, color, fontFamily: 'Orbitron, monospace', fontWeight: 700 }}>
          {typeof value === 'number' ? value.toFixed(1) : value}{unit}
        </span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: color, cursor: 'pointer' }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#1a2744', marginTop: 2 }}>
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  )
}

function Panel({ title, children }) {
  return (
    <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 20 }}>
      <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 18, borderBottom: '1px solid #1a2744', paddingBottom: 8 }}>
        {title}
      </div>
      {children}
    </div>
  )
}

export default function EconomyPanel() {
  const { state, dispatch } = useSimulation()

  // All state lives in context — persists across page navigation
  const policy = state.policyControls
  const resource = state.resourceControls
  const social = state.socialControls

  const [savedMsg, setSavedMsg] = useState('')

  const showSaved = (ok) => {
    setSavedMsg(ok ? 'Saved' : 'Error')
    setTimeout(() => setSavedMsg(''), 1500)
  }

  const savePolicy = async (updates) => {
    dispatch({ type: 'SET_POLICY_CONTROLS', payload: updates })
    try {
      await axios.patch('/api/policies/', updates)
      showSaved(true)
    } catch { showSaved(false) }
  }

  const saveResource = async (updates) => {
    dispatch({ type: 'SET_RESOURCE_CONTROLS', payload: updates })
    try {
      await axios.patch('/api/resources/', updates)
      showSaved(true)
    } catch { showSaved(false) }
  }

  const updateSocial = (updates) => {
    dispatch({ type: 'SET_SOCIAL_CONTROLS', payload: updates })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
          Economy &amp; Resource Controls
        </h1>
        <div style={{ fontSize: 11, fontFamily: 'Share Tech Mono, monospace', color: savedMsg === 'Error' ? '#ff3366' : '#00ff88' }}>
          {savedMsg}
        </div>
      </div>

      {/* Live Metrics */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <MetricCard small label="GDP" value={state.economy.gdp} unit="$" color="#00d4ff" />
        <MetricCard small label="Inflation" value={state.economy.inflation} unit="%" color="#ffcc00" />
        <MetricCard small label="Unemployment" value={state.economy.unemployment} unit="%" color="#ff3366" />
        <MetricCard small label="Confidence" value={state.economy.marketConfidence} unit="%" color="#00ff88" />
        <MetricCard small label="Resource Index" value={state.economy.resourceIndex} color="#a855f7" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>

        <Panel title="Economic Policy Controls">
          <SliderRow label="Tax Rate" value={policy.tax_rate ?? 20} min={0} max={80} unit="%" color="#ffcc00"
            onChange={v => savePolicy({ tax_rate: v })} />
          <SliderRow label="Interest Rate" value={policy.interest_rate ?? 5} min={0} max={25} unit="%" color="#ff3366"
            onChange={v => savePolicy({ interest_rate: v })} />
          <SliderRow label="Government Spending" value={policy.government_spending ?? 10000} min={0} max={200000} step={1000} unit="$" color="#00d4ff"
            onChange={v => savePolicy({ government_spending: v })} />
          <SliderRow label="Subsidy Level" value={policy.subsidy_level ?? 0} min={0} max={50000} step={500} unit="$" color="#00ff88"
            onChange={v => savePolicy({ subsidy_level: v })} />
          <SliderRow label="Market Regulation" value={policy.market_regulation ?? 50} min={0} max={100} unit="%" color="#a855f7"
            onChange={v => savePolicy({ market_regulation: v })} />
          <div style={{ marginTop: 10 }}>
            <button
              onClick={() => savePolicy({ stimulus_active: !policy.stimulus_active })}
              style={{
                background: policy.stimulus_active ? '#00ff8818' : '#0b1120',
                border: `1px solid ${policy.stimulus_active ? '#00ff88' : '#1a2744'}`,
                color: policy.stimulus_active ? '#00ff88' : '#64748b',
                padding: '8px 16px', borderRadius: 4, cursor: 'pointer',
                fontFamily: 'Share Tech Mono, monospace', fontSize: 11, textTransform: 'uppercase',
              }}
            >
              {policy.stimulus_active ? '● Stimulus ON' : '○ Stimulus OFF'}
            </button>
          </div>
          {policy.stimulus_active && (
            <div style={{ marginTop: 12 }}>
              <SliderRow label="Stimulus Amount" value={policy.stimulus_amount ?? 0} min={0} max={500000} step={5000} unit="$" color="#00ff88"
                onChange={v => savePolicy({ stimulus_amount: v })} />
            </div>
          )}
        </Panel>

        <Panel title="Resource Supply Controls">
          <SliderRow label="Food Supply" value={resource.food_supply ?? 85} min={0} max={100} unit="%" color="#00ff88"
            onChange={v => saveResource({ food_supply: v })} />
          <SliderRow label="Oil Supply" value={resource.oil_supply ?? 80} min={0} max={100} unit="%" color="#ffcc00"
            onChange={v => saveResource({ oil_supply: v })} />
          <SliderRow label="Energy Availability" value={resource.energy_availability ?? 82} min={0} max={100} unit="%" color="#00d4ff"
            onChange={v => saveResource({ energy_availability: v })} />
          <SliderRow label="Housing Supply" value={resource.housing_supply ?? 75} min={0} max={100} unit="%" color="#a855f7"
            onChange={v => saveResource({ housing_supply: v })} />
          <SliderRow label="Water Resources" value={resource.water_resources ?? 90} min={0} max={100} unit="%" color="#ff3366"
            onChange={v => saveResource({ water_resources: v })} />
        </Panel>

        <Panel title="Social Controls">
          <SliderRow label="Fear Sensitivity" value={social?.fear_sensitivity ?? 1.0} min={0} max={3} step={0.05} color="#ff3366"
            onChange={v => updateSocial({ fear_sensitivity: v })} />
          <SliderRow label="Greed Level" value={social?.greed_level ?? 0.15} min={0} max={1} step={0.01} color="#ffcc00"
            onChange={v => updateSocial({ greed_level: v })} />
          <SliderRow label="Trust Level" value={social?.trust_level ?? 0.5} min={0} max={1} step={0.01} color="#00ff88"
            onChange={v => updateSocial({ trust_level: v })} />
          <SliderRow label="Cooperation Rate" value={social?.cooperation_rate ?? 0.5} min={0} max={1} step={0.01} color="#00d4ff"
            onChange={v => updateSocial({ cooperation_rate: v })} />
          <SliderRow label="Social Influence Strength" value={social?.social_influence_strength ?? 0.5} min={0} max={2} step={0.05} color="#a855f7"
            onChange={v => updateSocial({ social_influence_strength: v })} />
        </Panel>

      </div>
    </div>
  )
}