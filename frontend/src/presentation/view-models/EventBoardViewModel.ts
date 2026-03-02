import { makeAutoObservable, runInAction } from "mobx";
import type { Event } from "@domain/entities/Event";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import { EventTopicApiClient } from "@infrastructure/api/eventTopicApiClient";
import { VoteApiClient } from "@infrastructure/api/voteApiClient";
import { FingerprintService } from "@infrastructure/fingerprint/fingerprintService";
import { WebSocketClient } from "@infrastructure/websocket";
import { TopicsViewModel } from "./TopicsViewModel";

function buildEventWebSocketUrl(code: string): string {
  const protocol =
    window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/events/${code}`;
}

export class EventBoardViewModel {
  event: Event | null = null;
  isLoading = true;
  error: string | null = null;
  topicsViewModel: TopicsViewModel | null = null;

  private readonly _api: EventApiPort;
  private _wsClient: WebSocketClient | null = null;

  constructor(api: EventApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  async resolveEvent(code: string): Promise<void> {
    this.isLoading = true;
    this.error = null;
    try {
      const event = await this._api.getEventByCode(code);
      runInAction(() => {
        this.event = event;
        this._wsClient = new WebSocketClient();
        this.topicsViewModel = new TopicsViewModel(
          new EventTopicApiClient(event.id),
          new VoteApiClient(),
          new FingerprintService(),
          this._wsClient,
        );
        this.isLoading = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to load event";
        this.isLoading = false;
      });
    }
  }

  connectWebSocket(): void {
    if (this.event && this._wsClient) {
      this._wsClient.connect(
        buildEventWebSocketUrl(this.event.code),
      );
    }
  }

  dispose(): void {
    this.topicsViewModel?.dispose();
    this._wsClient = null;
  }
}
