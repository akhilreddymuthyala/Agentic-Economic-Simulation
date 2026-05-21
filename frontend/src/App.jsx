import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { SimulationProvider } from './context/SimulationContext'
import Layout from './components/shared/Layout'
import ErrorBoundary from './components/shared/ErrorBoundary'
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
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<ErrorBoundary><Dashboard /></ErrorBoundary>} />
            <Route path="/control" element={<ErrorBoundary><SimulationControl /></ErrorBoundary>} />
            <Route path="/economy" element={<ErrorBoundary><EconomyPanel /></ErrorBoundary>} />
            <Route path="/agents" element={<ErrorBoundary><AgentVisualization /></ErrorBoundary>} />
            <Route path="/inspector" element={<ErrorBoundary><AgentInspector /></ErrorBoundary>} />
            <Route path="/analytics" element={<ErrorBoundary><Analytics /></ErrorBoundary>} />
          </Routes>
        </ErrorBoundary>
      </Layout>
    </SimulationProvider>
  )
}