/**
 * Builds a WebSocket URL using the current page's protocol and host.
 *
 * @param path - Optional path appended after the host (e.g. "events/ABC123").
 *               When omitted the base "/ws" endpoint is returned.
 */
export function buildWebSocketUrl(path?: string): string {
  const protocol =
    window.location.protocol === "https:" ? "wss:" : "ws:";
  const suffix = path ? `/ws/${path}` : "/ws";
  return `${protocol}//${window.location.host}${suffix}`;
}
