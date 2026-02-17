export type WebSocketMessageHandler = (data: unknown) => void;

export interface WebSocketPort {
  connect(url: string): void;
  disconnect(): void;
  onMessage(handler: WebSocketMessageHandler): void;
  onReconnect(handler: () => void): void;
}
