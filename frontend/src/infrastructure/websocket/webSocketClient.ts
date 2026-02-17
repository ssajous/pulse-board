import type {
  WebSocketPort,
  WebSocketMessageHandler,
} from "@domain/ports/WebSocketPort";

const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 5000;
const MAX_RECONNECT_ATTEMPTS = 10;

export class WebSocketClient implements WebSocketPort {
  private socket: WebSocket | null = null;
  private messageHandlers: WebSocketMessageHandler[] = [];
  private reconnectHandlers: (() => void)[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null =
    null;
  private url: string | null = null;
  private shouldReconnect = false;

  connect(url: string): void {
    this.url = url;
    this.shouldReconnect = true;
    this.createConnection();
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.clearReconnectTimer();

    if (this.socket) {
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      this.socket.onopen = null;
      this.socket.close();
      this.socket = null;
    }
  }

  onMessage(handler: WebSocketMessageHandler): void {
    this.messageHandlers.push(handler);
  }

  onReconnect(handler: () => void): void {
    this.reconnectHandlers.push(handler);
  }

  private createConnection(): void {
    if (!this.url) return;

    const isReconnect = this.reconnectAttempts > 0;
    console.log(
      isReconnect
        ? `WebSocket reconnecting (attempt ${this.reconnectAttempts})...`
        : "WebSocket connecting..."
    );

    this.socket = new WebSocket(this.url);

    this.socket.onopen = (): void => {
      console.log("WebSocket connected");
      const wasReconnect = this.reconnectAttempts > 0;
      this.reconnectAttempts = 0;

      if (wasReconnect) {
        this.reconnectHandlers.forEach((h) => h());
      }
    };

    this.socket.onmessage = (event: MessageEvent): void => {
      try {
        const data: unknown = JSON.parse(
          event.data as string
        );
        this.messageHandlers.forEach((h) => h(data));
      } catch {
        console.error(
          "WebSocket: failed to parse message",
          event.data
        );
      }
    };

    this.socket.onclose = (): void => {
      console.log("WebSocket disconnected");
      this.socket = null;
      this.scheduleReconnect();
    };

    this.socket.onerror = (event: Event): void => {
      console.error("WebSocket error", event);
    };
  }

  private scheduleReconnect(): void {
    if (!this.shouldReconnect) return;

    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log(
        "WebSocket: max reconnect attempts reached"
      );
      return;
    }

    this.reconnectAttempts += 1;
    const delay = Math.min(
      INITIAL_RECONNECT_DELAY_MS *
        Math.pow(2, this.reconnectAttempts - 1),
      MAX_RECONNECT_DELAY_MS
    );

    console.log(
      `WebSocket: reconnecting in ${delay}ms`
    );
    this.reconnectTimer = setTimeout(() => {
      this.createConnection();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
