// ── WebSocket 连接管理 ───────────────────────────────────────────
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

type MessageHandler = (data: unknown) => void;

class WSClient {
  private socket: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private url = "";

  connect(path: string, token: string) {
    this.url = `${WS_BASE}${path}?token=${token}`;
    this.socket = new WebSocket(this.url);

    this.socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const handlers = this.handlers.get("*");
        if (handlers) handlers.forEach((h) => h(msg));
        if (msg.action) {
          const actionHandlers = this.handlers.get(msg.action);
          if (actionHandlers) actionHandlers.forEach((h) => h(msg));
        }
      } catch {
        // ignore parse errors
      }
    };

    this.socket.onclose = () => {
      this.reconnectTimer = setTimeout(() => this.connect(path, token), 3000);
    };
  }

  on(action: string, handler: MessageHandler) {
    if (!this.handlers.has(action)) {
      this.handlers.set(action, new Set());
    }
    this.handlers.get(action)!.add(handler);
    return () => this.handlers.get(action)?.delete(handler);
  }

  send(data: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.socket?.close();
    this.socket = null;
    this.handlers.clear();
  }
}

export const wsClient = new WSClient();
