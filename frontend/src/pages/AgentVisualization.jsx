import React, { useEffect, useRef, useState, useCallback } from 'react'
import axios from 'axios'
import * as d3 from 'd3'
import { useSimulation } from '../context/SimulationContext'

const EMOTION_COLORS = {
  panic: '#ff0000', fearful: '#ff3366', stressed: '#a855f7',
  greedy: '#ffcc00', optimistic: '#00d4ff', trusting: '#00ff88', neutral: '#334155',
}

const ROLE_FILTERS = [
  'all', 'consumer', 'worker', 'trader', 'investor',
  'business_owner', 'manufacturer', 'government', 'banker', 'influencer',
  'researcher', 'resource_supplier',
]

export default function AgentVisualization() {
  const svgRef = useRef(null)
  const simulationRef = useRef(null)
  const { state } = useSimulation()
  const [agents, setAgents] = useState([])
  const [relationships, setRelationships] = useState([])
  const [filter, setFilter] = useState('all')
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load agents and relationships once
  useEffect(() => {
    Promise.all([
      axios.get('/api/agents/?limit=100'),
      axios.get('/api/agents/1/relationships/').catch(() => ({ data: [] })),
    ]).then(([agentsRes]) => {
      setAgents(agentsRes.data.results || agentsRes.data)
      setLoading(false)
    }).catch(() => setLoading(false))

    // Load relationships for all agents
    axios.get('/api/agents/?limit=100').then(res => {
      const allAgents = res.data.results || res.data
      const relPromises = allAgents.slice(0, 20).map(a =>
        axios.get(`/api/agents/${a.id}/relationships/`).then(r => r.data).catch(() => [])
      )
      Promise.all(relPromises).then(allRels => {
        const flat = allRels.flat()
        const unique = []
        const seen = new Set()
        flat.forEach(r => {
          const key = [Math.min(r.agent_a, r.agent_b), Math.max(r.agent_a, r.agent_b)].join('-')
          if (!seen.has(key)) { seen.add(key); unique.push(r) }
        })
        setRelationships(unique)
      })
    })
  }, [])

  // Update node colors from live emotion data
  useEffect(() => {
    if (!svgRef.current || agents.length === 0) return
    const dist = state.emotionDistribution
    // Update is handled by D3 simulation re-render
  }, [state.emotionDistribution, state.tick])

  // Build D3 graph
  useEffect(() => {
    if (loading || agents.length === 0 || !svgRef.current) return

    const filtered = filter === 'all' ? agents : agents.filter(a => a.profession === filter)
    const agentIds = new Set(filtered.map(a => a.id))
    const filteredRels = relationships.filter(r => agentIds.has(r.agent_a) && agentIds.has(r.agent_b))

    const width = svgRef.current.clientWidth || 700
    const height = 500

    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    // Background
    svg.append('rect').attr('width', width).attr('height', height).attr('fill', '#050810')

    const g = svg.append('g')

    // Zoom
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => g.attr('transform', e.transform)))

    const nodes = filtered.map(a => ({
      id: a.id, name: a.name, profession: a.profession,
      wealth: a.wealth, emotion: a.dominant_emotion,
      influence: a.social_influence,
    }))

    const links = filteredRels.map(r => ({
      source: r.agent_a, target: r.agent_b,
      trust: r.trust_score, influence: r.influence_score,
    }))

    if (simulationRef.current) simulationRef.current.stop()

    simulationRef.current = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(60).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-80))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => nodeRadius(d) + 4))

    // Links
    const link = g.append('g').selectAll('line').data(links).enter().append('line')
      .attr('stroke', '#1a2744')
      .attr('stroke-opacity', d => d.trust * 0.8)
      .attr('stroke-width', 0.8)

    // Nodes
    const nodeGroup = g.append('g').selectAll('g').data(nodes).enter().append('g')
      .attr('cursor', 'pointer')
      .on('click', (event, d) => setSelectedAgent(d))
      .call(d3.drag()
        .on('start', (event, d) => { if (!event.active) simulationRef.current.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
        .on('end', (event, d) => { if (!event.active) simulationRef.current.alphaTarget(0); d.fx = null; d.fy = null })
      )

    nodeGroup.append('circle')
      .attr('r', d => nodeRadius(d))
      .attr('fill', d => EMOTION_COLORS[d.emotion] || '#334155')
      .attr('fill-opacity', 0.85)
      .attr('stroke', d => EMOTION_COLORS[d.emotion] || '#334155')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.5)

    // Pulse rings for high-influence agents
    nodeGroup.filter(d => d.influence > 0.7).append('circle')
      .attr('r', d => nodeRadius(d) + 4)
      .attr('fill', 'none')
      .attr('stroke', d => EMOTION_COLORS[d.emotion] || '#334155')
      .attr('stroke-width', 0.5)
      .attr('stroke-opacity', 0.3)

    nodeGroup.append('text')
      .attr('dy', d => -nodeRadius(d) - 3)
      .attr('text-anchor', 'middle')
      .attr('font-size', 8)
      .attr('fill', '#64748b')
      .attr('font-family', 'Share Tech Mono, monospace')
      .text(d => d.profession.substring(0, 4).toUpperCase())

    simulationRef.current.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => { if (simulationRef.current) simulationRef.current.stop() }
  }, [agents, relationships, filter, loading])

  function nodeRadius(d) {
    return Math.max(4, Math.min(20, Math.sqrt(d.wealth / 500) + 4))
  }

  const filterBtn = (f) => ({
    background: filter === f ? '#00d4ff18' : '#0b1120',
    border: `1px solid ${filter === f ? '#00d4ff' : '#1a2744'}`,
    color: filter === f ? '#00d4ff' : '#64748b',
    padding: '4px 10px', borderRadius: 4, cursor: 'pointer',
    fontFamily: 'Share Tech Mono, monospace', fontSize: 10,
    textTransform: 'uppercase', letterSpacing: 1,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00d4ff', letterSpacing: 3, textTransform: 'uppercase' }}>
        Agent Network
      </h1>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase' }}>Emotion:</span>
        {Object.entries(EMOTION_COLORS).map(([em, color]) => (
          <span key={em} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: '#64748b', fontFamily: 'Share Tech Mono, monospace' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
            {em}
          </span>
        ))}
        <span style={{ fontSize: 9, color: '#64748b', marginLeft: 12 }}>Node size = wealth</span>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {ROLE_FILTERS.map(f => (
          <button key={f} style={filterBtn(f)} onClick={() => setFilter(f)}>
            {f.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Graph */}
      <div style={{ background: '#050810', border: '1px solid #1a2744', borderRadius: 4, overflow: 'hidden', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontFamily: 'Share Tech Mono, monospace', fontSize: 12 }}>
            Loading agent network...
          </div>
        )}
        <svg ref={svgRef} style={{ width: '100%', height: 500, display: 'block' }} />
      </div>

      {/* Selected agent info */}
      {selectedAgent && (
        <div style={{ background: '#0b1120', border: '1px solid #00d4ff', borderRadius: 4, padding: 16, fontFamily: 'Share Tech Mono, monospace', fontSize: 11 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ color: '#00d4ff', fontFamily: 'Orbitron, monospace', fontSize: 13 }}>{selectedAgent.name}</span>
            <button onClick={() => setSelectedAgent(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 16 }}>×</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            {[
              ['Profession', selectedAgent.profession],
              ['Wealth', `$${Number(selectedAgent.wealth).toFixed(0)}`],
              ['Emotion', selectedAgent.emotion],
            ].map(([k, v]) => (
              <div key={k}>
                <div style={{ color: '#64748b', fontSize: 9, textTransform: 'uppercase', letterSpacing: 1 }}>{k}</div>
                <div style={{ color: '#e2e8f0', marginTop: 2 }}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}