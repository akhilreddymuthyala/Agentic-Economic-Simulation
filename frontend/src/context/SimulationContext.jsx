import React, { createContext, useContext, useReducer, useEffect, useRef } from 'react'

const SimulationContext = createContext(null)

const initialState = {
  status: 'idle',
  speed: 1,
  tick: 0,
  simDate: { year: 1, month: 1, week: 1, day: 1, hour: 0 },
  formattedDate: 'Year 1 — Month 1 — Day 1 — 00:00',
  tickIntervalSeconds: 12.5,
  economy: {
    gdp: 100000,
    gdpGrowthRate: 0,
    inflation: 2.0,
    unemployment: 5.0,
    marketConfidence: 70,
    wealthGini: 0.35,
    resourceIndex: 100,
    economicStability: 75,
  },
  events: [],
  agentUpdates: [],
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
          week: action.payload.week ?? state.simDate.week,
          day: action.payload.day ?? state.simDate.day,
          hour: action.payload.hour ?? state.simDate.hour,
        },
        economy: {
          gdp: action.payload.gdp ?? state.economy.gdp,
          gdpGrowthRate: action.payload.gdp_growth_rate ?? state.economy.gdpGrowthRate,
          inflation: action.payload.inflation ?? state.economy.inflation,
          unemployment: action.payload.unemployment ?? state.economy.unemployment,
          marketConfidence: action.payload.market_confidence ?? state.economy.marketConfidence,
          wealthGini: action.payload.wealth_gini ?? state.economy.wealthGini,
          resourceIndex: action.payload.resource_index ?? state.economy.resourceIndex,
          economicStability: action.payload.economic_stability ?? state.economy.economicStability,
        },
        agentUpdates: action.payload.agent_updates ?? [],
      }

    case 'NEW_EVENT':
      return {
        ...state,
        events: [action.payload, ...state.events].slice(0, 100),
      }

    case 'SIM_STATUS':
      return {
        ...state,
        status: action.payload.status ?? state.status,
        speed: action.payload.speed_multiplier ?? state.speed,
        tick: action.payload.current_tick ?? state.tick,
        tickIntervalSeconds: action.payload.tick_interval_seconds ?? state.tickIntervalSeconds,
        formattedDate: action.payload.formatted_date ?? state.formattedDate,
        simDate: {
          year: action.payload.current_year ?? state.simDate.year,
          month: action.payload.current_month ?? state.simDate.month,
          week: action.payload.current_week ?? state.simDate.week,
          day: action.payload.current_day ?? state.simDate.day,
          hour: action.payload.current_hour ?? state.simDate.hour,
        },
      }

    default:
      return state
  }
}

export function SimulationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const wsRef = useRef(null)

  // Fetch initial status from REST on mount
  useEffect(() => {
    fetch('/api/simulation/status/')
      .then(r => r.json())
      .then(data => dispatch({ type: 'SIM_STATUS', payload: data }))
      .catch(() => {})
  }, [])

  // WebSocket connection with auto-reconnect
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/simulation/`)
      wsRef.current = ws

      ws.onopen = () => dispatch({ type: 'WS_CONNECTED' })

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'tick_update') {
            dispatch({ type: 'TICK_UPDATE', payload: msg })
          } else if (msg.type === 'simulation_event') {
            dispatch({ type: 'NEW_EVENT', payload: msg })
          } else if (msg.type === 'status_update') {
            dispatch({ type: 'SIM_STATUS', payload: msg })
          }
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