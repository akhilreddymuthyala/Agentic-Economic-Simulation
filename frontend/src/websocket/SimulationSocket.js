// Utility for imperative WebSocket sends from outside React tree
let _ws = null

export function setSocket(ws) {
  _ws = ws
}

export function sendMessage(payload) {
  if (_ws && _ws.readyState === WebSocket.OPEN) {
    _ws.send(JSON.stringify(payload))
  }
}