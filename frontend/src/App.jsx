import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { SimulationProvider } from './context/SimulationContext'
import Layout from './components/shared/Layout'
import Dashboard from './pages/Dashboard'
import SimulationControl from './pages/SimulationControl'
import EconomyPanel from './pages/EconomyPanel'
import AgentVisualization from './pages/AgentVisualization'
import AgentInspector from './pages/AgentInspector'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <SimulationProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/control" element={<SimulationControl />} />
          <Route path="/economy" element={<EconomyPanel />} />
          <Route path="/agents" element={<AgentVisualization />} />
          <Route path="/inspector" element={<AgentInspector />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
    </SimulationProvider>
  )
}