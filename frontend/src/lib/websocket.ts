// ── WebSocket 连接管理 ───────────────────────────────────────────
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

type MessageHandler = (data: unknown) => void;

class WSClient {
  private socket: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private path = "";
  private disconnected = false;
  private retryCount = 0;
  private maxRetries = 10;

  connect(path: string, _token?: string) {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.disconnected = false;
    this.retryCount = 0;
    this.path = path;
    this._doConnect();
  }

  private _doConnect() {
    // 每次重连从 localStorage 读取最新 token
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;
    if (!token) {
      this.disconnected = true;
      return;
    }

    const url = `${WS_BASE}${this.path}?token=${token}`;
    this.socket = new WebSocket(url);

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
      if (this.disconnected) return;
      this.retryCount++;
      if (this.retryCount > this.maxRetries) {
        this.disconnected = true;
        return;
      }
      // 指数退避：3s, 6s, 12s, 24s... 最大 60s
      const delay = Math.min(3000 * Math.pow(2, this.retryCount - 1), 60000);
      this.reconnectTimer = setTimeout(() => this._doConnect(), delay);
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
    this.disconnected = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.socket?.close();
    this.socket = null;
    this.handlers.clear();
  }
}

export const wsClient = new WSClient();
