import React, { createContext, useContext, useReducer, useEffect, useRef } from 'react'

const SimulationContext = createContext(null)

const initialState = {
  status: 'idle',
  speed: 1,
  tick: 0,
  simDate: { year: 1, month: 1, day: 1, hour: 0 },
  economy: {
    gdp: 100000,
    inflation: 2.0,
    unemployment: 5.0,
    marketConfidence: 70,
    wealthGini: 0.35,
    resourceIndex: 100,
    economicStability: 75,
  },
  events: [],
  connected: false,
}

function reducer(state, action) {
  switch (action.type) {
    case 'WS_CONNECTED':
      return { ...state, connected: true }
    case 'WS_DISCONNECTED':
      return { ...state, connected: false }
    case 'TICK_UPDATE':
      return {
        ...state,
        tick: action.payload.tick_number ?? state.tick,
        simDate: {
          year: action.payload.year ?? state.simDate.year,
          month: action.payload.month ?? state.simDate.month,
          day: action.payload.day ?? state.simDate.day,
          hour: action.payload.hour ?? state.simDate.hour,
        },
        economy: {
          gdp: action.payload.gdp ?? state.economy.gdp,
          inflation: action.payload.inflation ?? state.economy.inflation,
          unemployment: action.payload.unemployment ?? state.economy.unemployment,
          marketConfidence: action.payload.market_confidence ?? state.economy.marketConfidence,
          wealthGini: action.payload.wealth_gini ?? state.economy.wealthGini,
          resourceIndex: action.payload.resource_index ?? state.economy.resourceIndex,
          economicStability: action.payload.economic_stability ?? state.economy.economicStability,
        },
      }
    case 'NEW_EVENT':
      return {
        ...state,
        events: [action.payload, ...state.events].slice(0, 100),
      }
    case 'SIM_STATUS':
      return { ...state, status: action.payload.status, speed: action.payload.speed ?? state.speed }
    default:
      return state
  }
}

export function SimulationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const wsRef = useRef(null)

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/simulation/`)
      wsRef.current = ws

      ws.onopen = () => dispatch({ type: 'WS_CONNECTED' })

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'tick_update') dispatch({ type: 'TICK_UPDATE', payload: msg })
          else if (msg.type === 'simulation_event') dispatch({ type: 'NEW_EVENT', payload: msg })
          else if (msg.type === 'status_update') dispatch({ type: 'SIM_STATUS', payload: msg })
        } catch (_) {}
      }

      ws.onclose = () => {
        dispatch({ type: 'WS_DISCONNECTED' })
        setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  return (
    <SimulationContext.Provider value={{ state, dispatch }}>
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulation() {
  const ctx = useContext(SimulationContext)
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider')
  return ctx
}