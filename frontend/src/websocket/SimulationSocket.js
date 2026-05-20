/**
 * SimulationSocket — manages the WebSocket connection lifecycle.
 * Exposes send() for imperative messages from outside React.
 * The actual state management lives in SimulationContext.
 */

let _ws = null
let _onMessage = null
let _reconnectTimer = null
const RECONNECT_DELAY = 3000

export function initSocket(onMessage) {
  _onMessage = onMessage
  _connect()
}

function _connect() {
  const host = window.location.hostname
  const url = `ws://${host}:8000/ws/simulation/`

  _ws = new WebSocket(url)

  _ws.onopen = () => {
    console.log('[WS] Connected')
    clearTimeout(_reconnectTimer)
    // Request full state on connect
    send({ type: 'request_state' })
  }

  _ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      if (_onMessage) _onMessage(msg)
    } catch (err) {
      console.warn('[WS] Parse error:', err)
    }
  }

  _ws.onclose = (e) => {
    console.log(`[WS] Disconnected (code=${e.code}). Reconnecting in ${RECONNECT_DELAY}ms...`)
    _reconnectTimer = setTimeout(_connect, RECONNECT_DELAY)
  }

  _ws.onerror = () => {
    _ws.close()
  }
}

export function send(payload) {
  if (_ws && _ws.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify(payload))
  }
}

export function requestEvents(limit = 100) {
  send({ type: 'request_events', limit })
}

export function ping() {
  send({ type: 'ping' })
}

export function getReadyState() {
  return _ws ? _ws.readyState : WebSocket.CLOSED
}

export function closeSocket() {
  clearTimeout(_reconnectTimer)
  if (_ws) _ws.close()
}