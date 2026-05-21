import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('Component error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          background: '#0b1120', border: '1px solid #ff3366',
          borderRadius: 4, padding: 24, margin: 16,
          fontFamily: 'Share Tech Mono, monospace',
        }}>
          <div style={{ color: '#ff3366', fontSize: 12, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
            Component Error
          </div>
          <div style={{ color: '#64748b', fontSize: 11, marginBottom: 16 }}>
            {this.state.error?.message}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              background: '#ff336618', border: '1px solid #ff3366',
              color: '#ff3366', padding: '6px 14px', borderRadius: 4,
              cursor: 'pointer', fontFamily: 'Share Tech Mono, monospace', fontSize: 11,
            }}
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}