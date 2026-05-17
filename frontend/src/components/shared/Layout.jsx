import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useSimulation } from '../../context/SimulationContext'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: '⬡' },
  { path: '/control', label: 'Simulation', icon: '⚙' },
  { path: '/economy', label: 'Economy', icon: '◈' },
  { path: '/agents', label: 'Agent Network', icon: '◉' },
  { path: '/inspector', label: 'Inspector', icon: '◎' },
  { path: '/analytics', label: 'Analytics', icon: '◧' },
]

export default function Layout({ children }) {
  const { state } = useSimulation()
  const [collapsed, setCollapsed] = useState(false)

  const statusColor = {
    running: '#00ff88',
    paused: '#ffcc00',
    stopped: '#ff3366',
    idle: '#64748b',
  }[state.status] ?? '#64748b'

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#050810' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: collapsed ? 56 : 220,
          minWidth: collapsed ? 56 : 220,
          background: '#0b1120',
          borderRight: '1px solid #1a2744',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.2s',
          overflow: 'hidden',
        }}
      >
        {/* Logo */}
        <div
          style={{
            padding: collapsed ? '20px 12px' : '20px 16px',
            borderBottom: '1px solid #1a2744',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span style={{ fontSize: 20, color: '#00d4ff' }}>⬡</span>
          {!collapsed && (
            <span
              style={{
                fontFamily: 'Orbitron, monospace',
                fontSize: 11,
                color: '#00d4ff',
                letterSpacing: 1,
                lineHeight: 1.3,
              }}
            >
              EMERGENT AI<br />ECONOMY
            </span>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '12px 0' }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: collapsed ? '10px 16px' : '10px 16px',
                color: isActive ? '#00d4ff' : '#64748b',
                textDecoration: 'none',
                fontFamily: 'Share Tech Mono, monospace',
                fontSize: 12,
                borderLeft: isActive ? '2px solid #00d4ff' : '2px solid transparent',
                background: isActive ? 'rgba(0,212,255,0.06)' : 'transparent',
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              })}
            >
              <span style={{ fontSize: 16, minWidth: 20, textAlign: 'center' }}>{item.icon}</span>
              {!collapsed && item.label}
            </NavLink>
          ))}
        </nav>

        {/* Status Footer */}
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid #1a2744',
            fontSize: 10,
            color: '#64748b',
            fontFamily: 'Share Tech Mono, monospace',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: statusColor,
                display: 'inline-block',
                boxShadow: `0 0 6px ${statusColor}`,
              }}
            />
            {!collapsed && (
              <span style={{ textTransform: 'uppercase', letterSpacing: 1 }}>
                {state.status}
              </span>
            )}
          </div>
          {!collapsed && (
            <div style={{ marginTop: 4, color: '#1a2744' }}>
              WS: {state.connected ? (
                <span style={{ color: '#00ff88' }}>connected</span>
              ) : (
                <span style={{ color: '#ff3366' }}>disconnected</span>
              )}
            </div>
          )}
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: 'none',
            border: 'none',
            borderTop: '1px solid #1a2744',
            color: '#64748b',
            cursor: 'pointer',
            padding: '8px',
            fontSize: 16,
            textAlign: 'center',
          }}
        >
          {collapsed ? '›' : '‹'}
        </button>
      </aside>

      {/* Main content */}
      <main
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 24,
          background: '#050810',
        }}
      >
        {children}
      </main>
    </div>
  )
}