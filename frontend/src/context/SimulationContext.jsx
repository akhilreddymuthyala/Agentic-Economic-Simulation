import React, {
  createContext, useContext, useReducer,
  useEffect, useRef, useCallback,
} from 'react'
import { initSocket, closeSocket, requestEvents } from '../websocket/SimulationSocket'

const SimulationContext = createContext(null)

const initialState = {
  // Connection
  connected: false,
  lastHeartbeat: null,

  // Simulation clock
  status: 'idle',
  speed: 1,
  tick: 0,
  simDate: { year: 1, month: 1, week: 1, day: 1, hour: 0 },
  formattedDate: 'Year 1 — Month 1 — Day 1 — 00:00',
  tickIntervalSeconds: 12.5,

  // Economy
  economy: {
    gdp: 100000,
    gdpGrowthRate: 0,
    inflation: 2.0,
    unemployment: 5.0,
    marketConfidence: 70,
    wealthGini: 0.35,
    resourceIndex: 100,
    economicStability: 75,
    totalWealth: 500000,
  },

  policyControls: {
    tax_rate: 20,
    interest_rate: 5,
    government_spending: 10000,
    subsidy_level: 0,
    stimulus_active: false,
    stimulus_amount: 0,
    market_regulation: 50,
  },
  resourceControls: {
    food_supply: 85,
    oil_supply: 80,
    energy_availability: 82,
    housing_supply: 75,
    water_resources: 90,
  },

  // Agents
  agentDeltas: [],
  emotionDistribution: {},
  behavioralModifiers: {},
  panicWaveActive: false,
  herdActive: false,

  // Resources
  resourceShortages: [],
  resourcePrices: {},

  // Events
  events: [],

  // Policy
  policy: {},
  socialControls: {
    fear_sensitivity: 1.0,
    greed_level: 0.15,
    trust_level: 0.5,
    cooperation_rate: 0.5,
    social_influence_strength: 0.5,
  },
}

function applyEconomyFromPayload(payload, current) {
  return {
    gdp: payload.gdp ?? current.gdp,
    gdpGrowthRate: payload.gdp_growth_rate ?? current.gdpGrowthRate,
    inflation: payload.inflation ?? current.inflation,
    unemployment: payload.unemployment ?? current.unemployment,
    marketConfidence: payload.market_confidence ?? current.marketConfidence,
    wealthGini: payload.wealth_gini ?? current.wealthGini,
    resourceIndex: payload.resource_index ?? current.resourceIndex,
    economicStability: payload.economic_stability ?? current.economicStability,
    totalWealth: payload.total_wealth ?? current.totalWealth,
  }
}

function reducer(state, action) {
  switch (action.type) {

    case 'WS_CONNECTED':
      return { ...state, connected: true, lastHeartbeat: Date.now() }

    case 'WS_DISCONNECTED':
      return { ...state, connected: false }

    case 'HEARTBEAT':
      return { ...state, lastHeartbeat: Date.now() }
    
    case 'SET_POLICY_CONTROLS':
      return { ...state, policyControls: { ...state.policyControls, ...action.payload } }

    case 'SET_RESOURCE_CONTROLS':
      return { ...state, resourceControls: { ...state.resourceControls, ...action.payload } }

    case 'SET_SOCIAL_CONTROLS':
      return { ...state, socialControls: { ...state.socialControls, ...action.payload } }  

    case 'INITIAL_STATE': {
      const p = action.payload
      return {
        ...state,
        status: p.status ?? state.status,
        speed: p.speed_multiplier ?? state.speed,
        tick: p.current_tick ?? state.tick,
        simDate: {
          year: p.current_year ?? state.simDate.year,
          month: p.current_month ?? state.simDate.month,
          week: state.simDate.week,
          day: p.current_day ?? state.simDate.day,
          hour: p.current_hour ?? state.simDate.hour,
        },
        economy: p.economy
          ? applyEconomyFromPayload(p.economy, state.economy)
          : state.economy,
        emotionDistribution: p.emotion_distribution ?? state.emotionDistribution,
        events: p.recent_events
          ? [...p.recent_events, ...state.events].slice(0, 200)
          : state.events,
        policy: p.policy ?? state.policy,
      }
    }

    case 'TICK_UPDATE': {
      const p = action.payload
      const newEvents = p.events?.length
        ? [...p.events, ...state.events].slice(0, 200)
        : state.events

      return {
        ...state,
        tick: p.tick_number ?? state.tick,
        simDate: {
          year: p.year ?? state.simDate.year,
          month: p.month ?? state.simDate.month,
          week: state.simDate.week,
          day: p.day ?? state.simDate.day,
          hour: p.hour ?? state.simDate.hour,
        },
        economy: applyEconomyFromPayload(p, state.economy),
        agentDeltas: p.agent_deltas ?? [],
        emotionDistribution: p.emotion_distribution ?? state.emotionDistribution,
        behavioralModifiers: p.behavioral_modifiers ?? state.behavioralModifiers,
        panicWaveActive: p.panic_wave_active ?? false,
        herdActive: p.herd_active ?? false,
        resourceShortages: p.resource_shortages ?? [],
        resourcePrices: p.resource_prices ?? state.resourcePrices,
        events: newEvents,
        policy: p.policy ?? state.policy,
        lastHeartbeat: Date.now(),
      }
    }

    case 'NEW_EVENT': {
      const evt = action.payload
      const already = state.events.some(
        e => e.tick === evt.tick && e.event_type === evt.event_type
      )
      if (already) return state
      return {
        ...state,
        events: [evt, ...state.events].slice(0, 200),
      }
    }

    case 'STATUS_UPDATE':
      return {
        ...state,
        status: action.payload.status ?? state.status,
        speed: action.payload.speed_multiplier ?? state.speed,
        tick: action.payload.current_tick ?? state.tick,
        formattedDate: action.payload.formatted_date ?? state.formattedDate,
        simDate: {
          year: action.payload.current_year ?? state.simDate.year,
          month: action.payload.current_month ?? state.simDate.month,
          week: state.simDate.week,
          day: action.payload.current_day ?? state.simDate.day,
          hour: action.payload.current_hour ?? state.simDate.hour,
        },
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
  const dispatchRef = useRef(dispatch)
  dispatchRef.current = dispatch

  const handleMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'connection_established':
        dispatchRef.current({ type: 'WS_CONNECTED' })
        break

      case 'initial_state':
      case 'full_state':
        dispatchRef.current({ type: 'INITIAL_STATE', payload: msg })
        break

      case 'tick_update':
        dispatchRef.current({ type: 'TICK_UPDATE', payload: msg })
        break

      case 'simulation_event':
        dispatchRef.current({ type: 'NEW_EVENT', payload: msg })
        break

      case 'status_update':
        dispatchRef.current({ type: 'STATUS_UPDATE', payload: msg })
        break

      case 'pong':
        dispatchRef.current({ type: 'HEARTBEAT' })
        break

      case 'event_history':
        if (msg.events) {
          msg.events.forEach(evt =>
            dispatchRef.current({ type: 'NEW_EVENT', payload: evt })
          )
        }
        break

      default:
        break
    }
  }, [])

  useEffect(() => {
    // Fetch REST status on mount as fallback
    fetch('/api/simulation/status/')
      .then(r => r.json())
      .then(data => dispatch({ type: 'SIM_STATUS', payload: data }))
      .catch(() => {})  

    // Init WebSocket
    initSocket(handleMessage)

    // Heartbeat — ping every 30s to keep connection alive
    const heartbeat = setInterval(() => {
      import('../websocket/SimulationSocket').then(({ ping }) => ping())
    }, 30000)

    return () => {
      clearInterval(heartbeat)
      closeSocket()
    }
  }, [handleMessage])

  useEffect(() => {
    fetch('/api/policies/')
      .then(r => r.json())
      .then(data => dispatch({ type: 'SET_POLICY_CONTROLS', payload: data }))
      .catch(() => {})

    fetch('/api/resources/')
      .then(r => r.json())
      .then(data => dispatch({ type: 'SET_RESOURCE_CONTROLS', payload: data }))
      .catch(() => {})
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