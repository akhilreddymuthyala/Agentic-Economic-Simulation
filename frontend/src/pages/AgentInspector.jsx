import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useSimulation } from '../context/SimulationContext'

const EMOTION_COLORS = {
  panic: '#ff0000', fearful: '#ff3366', stressed: '#a855f7',
  greedy: '#ffcc00', optimistic: '#00d4ff', trusting: '#00ff88', neutral: '#64748b',
}

function EmotionBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 3 }}>
        <span style={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</span>
        <span style={{ color }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div style={{ background: '#1a2744', borderRadius: 2, height: 5 }}>
        <div style={{ width: `${value * 100}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.3s' }} />
      </div>
    </div>
  )
}

function AgentCard({ agent, selected, onClick }) {
  const emotionColor = EMOTION_COLORS[agent.dominant_emotion] || '#64748b'
  return (
    <div
      onClick={() => onClick(agent)}
      style={{
        background: selected ? '#00d4ff10' : '#0b1120',
        border: `1px solid ${selected ? '#00d4ff' : '#1a2744'}`,
        borderRadius: 4, padding: '10px 12px', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6,
        transition: 'all 0.15s',
      }}
    >
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: emotionColor, display: 'inline-block', flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, color: '#e2e8f0', fontFamily: 'Share Tech Mono, monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{agent.name}</div>
        <div style={{ fontSize: 9, color: '#64748b', textTransform: 'uppercase' }}>{agent.profession?.replace(/_/g, ' ')}</div>
      </div>
      <div style={{ fontSize: 10, color: '#64748b', fontFamily: 'Orbitron, monospace', flexShrink: 0 }}>
        ${Number(agent.wealth).toLocaleString('en', { maximumFractionDigits: 0 })}
      </div>
    </div>
  )
}

export default function AgentInspector() {
  const { state } = useSimulation()
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState(null)
  const [memories, setMemories] = useState([])
  const [relationships, setRelationships] = useState([])
  const [neuralLogs, setNeuralLogs] = useState([])
  const [view, setView] = useState('single') // 'single' | 'society'
  const [search, setSearch] = useState('')
  const [profFilter, setProfFilter] = useState('all')

  useEffect(() => {
    axios.get('/api/agents/?limit=100').then(r => {
      setAgents(r.data.results || r.data)
    }).catch(() => {})
  }, [state.tick])

  const selectAgent = async (agent) => {
    setSelected(agent)
    setView('single')
    const [memRes, relRes, logRes] = await Promise.all([
      axios.get(`/api/agents/${agent.id}/memories/?top_k=10`).catch(() => ({ data: [] })),
      axios.get(`/api/agents/${agent.id}/relationships/`).catch(() => ({ data: [] })),
      axios.get(`/api/ai/neural-logs/?agent_id=${agent.id}&limit=5`).catch(() => ({ data: [] })),
    ])
    setMemories(memRes.data)
    setRelationships(relRes.data)
    setNeuralLogs(logRes.data)
  }

  const professions = ['all', ...new Set(agents.map(a => a.profession))]
  const filtered = agents.filter(a =>
    (profFilter === 'all' || a.profession === profFilter) &&
    (search === '' || a.name.toLowerCase().includes(search.toLowerCase()))
  )

  const tabBtn = (active) => ({
    background: active ? '#00d4ff18' : '#0b1120',
    border: `1px solid ${active ? '#00d4ff' : '#1a2744'}`,
    color: active ? '#00d4ff' : '#64748b',
    padding: '6px 14px', borderRadius: 4, cursor: 'pointer',
    fontFamily: 'Share Tech Mono, monospace', fontSize: 11,
    textTransform: 'uppercase', letterSpacing: 1,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>Agent Inspector</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={tabBtn(view === 'single')} onClick={() => setView('single')}>Single Agent</button>
          <button style={tabBtn(view === 'society')} onClick={() => setView('society')}>Society View</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16, alignItems: 'start' }}>

        {/* Agent List */}
        <div>
          <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
            <input
              placeholder="Search agents..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ flex: 1, background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: '6px 10px', color: '#e2e8f0', fontSize: 11, fontFamily: 'Share Tech Mono, monospace', outline: 'none' }}
            />
          </div>
          <select
            value={profFilter}
            onChange={e => setProfFilter(e.target.value)}
            style={{ width: '100%', background: '#0b1120', border: '1px solid #1a2744', color: '#64748b', padding: '6px 10px', borderRadius: 4, fontSize: 11, fontFamily: 'Share Tech Mono, monospace', marginBottom: 10, cursor: 'pointer' }}
          >
            {professions.map(p => <option key={p} value={p}>{p.replace(/_/g, ' ')}</option>)}
          </select>
          <div style={{ maxHeight: 520, overflowY: 'auto', paddingRight: 4 }}>
            {filtered.map(a => (
              <AgentCard key={a.id} agent={a} selected={selected?.id === a.id} onClick={selectAgent} />
            ))}
          </div>
        </div>

        {/* Inspector Panel */}
        <div>
          {view === 'society' ? (
            <SocietyView agents={agents} state={state} />
          ) : selected ? (
            <SingleAgentView agent={selected} memories={memories} relationships={relationships} neuralLogs={neuralLogs} />
          ) : (
            <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 40, textAlign: 'center', color: '#64748b', fontFamily: 'Share Tech Mono, monospace', fontSize: 12 }}>
              Select an agent from the list to inspect
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function SingleAgentView({ agent, memories, relationships, neuralLogs }) {
  const tierLabel = { 1: 'LLM Elite', 2: 'Neural', 3: 'Rule-Based' }
  const emotionColor = EMOTION_COLORS[agent.dominant_emotion] || '#64748b'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Header */}
      <div style={{ background: '#0b1120', border: `1px solid ${emotionColor}`, borderRadius: 4, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontFamily: 'Orbitron, monospace', fontSize: 15, color: '#e2e8f0' }}>{agent.name}</div>
            <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginTop: 3 }}>
              {agent.profession?.replace(/_/g, ' ')} — {tierLabel[agent.intelligence_tier] || 'Rule-Based'}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'Orbitron, monospace', fontSize: 18, color: '#00d4ff' }}>
              ${Number(agent.wealth).toLocaleString('en', { maximumFractionDigits: 0 })}
            </div>
            <div style={{ fontSize: 9, color: '#64748b', marginTop: 2 }}>wealth</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginTop: 14 }}>
          {[
            ['Risk Score', (agent.risk_score * 100).toFixed(0) + '%'],
            ['Strategy', agent.strategy],
            ['Last Action', agent.last_action],
            ['Dominant Emotion', agent.dominant_emotion],
          ].map(([k, v]) => (
            <div key={k}>
              <div style={{ fontSize: 9, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>{k}</div>
              <div style={{ fontSize: 11, color: '#e2e8f0', marginTop: 2, fontFamily: 'Share Tech Mono, monospace', textTransform: 'capitalize' }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {/* Emotion Vector */}
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Emotion Vector</div>
          <EmotionBar label="Fear" value={agent.emotion_fear || 0} color="#ff3366" />
          <EmotionBar label="Greed" value={agent.emotion_greed || 0} color="#ffcc00" />
          <EmotionBar label="Trust" value={agent.emotion_trust || 0} color="#00ff88" />
          <EmotionBar label="Optimism" value={agent.emotion_optimism || 0} color="#00d4ff" />
          <EmotionBar label="Stress" value={agent.emotion_stress || 0} color="#a855f7" />
          <EmotionBar label="Panic" value={agent.emotion_panic || 0} color="#ff0000" />
        </div>

        {/* Relationships */}
        <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
          <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>
            Relationships ({relationships.length})
          </div>
          <div style={{ maxHeight: 200, overflowY: 'auto' }}>
            {relationships.slice(0, 10).map((r, i) => {
              const other = r.agent_a === agent.id
                ? { id: r.agent_b, name: r.agent_b_name, prof: r.agent_b_profession }
                : { id: r.agent_a, name: r.agent_a_name, prof: r.agent_a_profession }
              return (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #1a2744', fontSize: 10, fontFamily: 'Share Tech Mono, monospace' }}>
                  <span style={{ color: '#e2e8f0' }}>{other.name}</span>
                  <span style={{ color: '#64748b', fontSize: 9 }}>{other.prof?.substring(0, 8)}</span>
                  <span style={{ color: '#00ff88' }}>trust {(r.trust_score * 100).toFixed(0)}%</span>
                </div>
              )
            })}
            {relationships.length === 0 && <div style={{ color: '#1a2744', fontSize: 11 }}>No relationships found</div>}
          </div>
        </div>
      </div>

      {/* Memory Log */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Memory Log</div>
        {memories.length === 0
          ? <div style={{ color: '#1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>No memories recorded</div>
          : memories.map((m, i) => (
            <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #1a2744' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <span style={{ fontSize: 9, color: '#64748b', textTransform: 'uppercase' }}>{m.memory_type}</span>
                <span style={{ fontSize: 9, color: '#a855f7' }}>imp {m.importance?.toFixed(2)}</span>
              </div>
              <div style={{ fontSize: 11, color: '#e2e8f0', fontFamily: 'Share Tech Mono, monospace', lineHeight: 1.5 }}>{m.memory_text}</div>
            </div>
          ))
        }
      </div>

      {/* Reasoning Log (LLM agents) */}
      {agent.intelligence_tier === 1 && neuralLogs.length > 0 && (
        <div style={{ background: '#0b1120', border: '1px solid #a855f7', borderRadius: 4, padding: 14 }}>
          <div style={{ fontSize: 9, color: '#a855f7', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>LLM Reasoning Log</div>
          {neuralLogs.map((log, i) => (
            <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #1a2744' }}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 3, fontSize: 9 }}>
                <span style={{ color: '#64748b' }}>Tick #{log.tick_number}</span>
                <span style={{ color: '#00d4ff', textTransform: 'uppercase' }}>{log.decision_output}</span>
                <span style={{ color: '#a855f7' }}>conf {(log.confidence * 100).toFixed(0)}%</span>
              </div>
              <div style={{ fontSize: 11, color: '#e2e8f0', fontFamily: 'Share Tech Mono, monospace' }}>{log.reasoning}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SocietyView({ agents, state }) {
  const totalWealth = agents.reduce((s, a) => s + (a.wealth || 0), 0)
  const avgWealth = agents.length ? totalWealth / agents.length : 0
  const employed = agents.filter(a => a.is_employed).length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
        {[
          ['Total Agents', agents.length, '#00d4ff'],
          ['Employed', employed, '#00ff88'],
          ['Unemployed', agents.length - employed, '#ff3366'],
          ['Total Wealth', `$${totalWealth.toLocaleString('en', { maximumFractionDigits: 0 })}`, '#00d4ff'],
          ['Avg Wealth', `$${avgWealth.toLocaleString('en', { maximumFractionDigits: 0 })}`, '#ffcc00'],
          ['Gini', state.economy.wealthGini.toFixed(3), '#a855f7'],
        ].map(([k, v, c]) => (
          <div key={k} style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 12 }}>
            <div style={{ fontSize: 9, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>{k}</div>
            <div style={{ fontSize: 18, color: c, fontFamily: 'Orbitron, monospace', fontWeight: 700, marginTop: 4 }}>{v}</div>
          </div>
        ))}
      </div>

      {/* Emotion Distribution */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Society Emotion Distribution</div>
        {Object.entries(state.emotionDistribution).filter(([, v]) => v > 0).map(([em, count]) => {
          const color = EMOTION_COLORS[em] || '#64748b'
          return (
            <div key={em} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 2 }}>
                <span style={{ color, textTransform: 'uppercase' }}>{em}</span>
                <span style={{ color: '#e2e8f0' }}>{count} / {agents.length}</span>
              </div>
              <div style={{ background: '#1a2744', borderRadius: 2, height: 5 }}>
                <div style={{ width: `${(count / agents.length) * 100}%`, height: '100%', background: color, borderRadius: 2 }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Profession breakdown */}
      <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: 14 }}>
        <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Profession Wealth Ranking</div>
        {Object.entries(
          agents.reduce((acc, a) => {
            if (!acc[a.profession]) acc[a.profession] = { total: 0, count: 0 }
            acc[a.profession].total += a.wealth || 0
            acc[a.profession].count++
            return acc
          }, {})
        ).sort(([, a], [, b]) => b.total - a.total).map(([prof, data]) => (
          <div key={prof} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #1a2744', fontSize: 11, fontFamily: 'Share Tech Mono, monospace' }}>
            <span style={{ color: '#64748b', textTransform: 'capitalize' }}>{prof.replace(/_/g, ' ')}</span>
            <span style={{ color: '#64748b' }}>×{data.count}</span>
            <span style={{ color: '#00d4ff' }}>${(data.total / data.count).toLocaleString('en', { maximumFractionDigits: 0 })} avg</span>
          </div>
        ))}
      </div>
    </div>
  )
}