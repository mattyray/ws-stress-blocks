import type { ClientMessage, ServerMessage } from "./types";

type MessageHandler = (msg: ServerMessage) => void;
type CloseHandler = () => void;

let ws: WebSocket | null = null;
let messageHandler: MessageHandler | null = null;
let closeHandler: CloseHandler | null = null;
let reconnectDelay = 1000;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let intentionalClose = false;

function getWsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws`;
}

function attemptConnect(): void {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const url = getWsUrl();
  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectDelay = 1000; // Reset backoff on successful connect
  };

  ws.onmessage = (event: MessageEvent) => {
    try {
      const msg = JSON.parse(event.data) as ServerMessage;
      messageHandler?.(msg);
    } catch {
      // Ignore malformed messages
    }
  };

  ws.onclose = () => {
    ws = null;
    closeHandler?.();

    if (!intentionalClose) {
      scheduleReconnect();
    }
  };

  ws.onerror = () => {
    // onclose will fire after onerror, so reconnect is handled there
    ws?.close();
  };
}

function scheduleReconnect(): void {
  if (reconnectTimer) return;

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    attemptConnect();
    // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
    reconnectDelay = Math.min(reconnectDelay * 2, 10000);
  }, reconnectDelay);
}

export function connect(onMessage: MessageHandler, onClose: CloseHandler): void {
  messageHandler = onMessage;
  closeHandler = onClose;
  intentionalClose = false;
  attemptConnect();
}

export function send(message: ClientMessage): void {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
}

export function disconnect(): void {
  intentionalClose = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
  messageHandler = null;
  closeHandler = null;
}

export function isConnected(): boolean {
  return ws !== null && ws.readyState === WebSocket.OPEN;
}
