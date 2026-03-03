import { makeAutoObservable, runInAction } from "mobx";
import type { Event } from "@domain/entities/Event";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import { EventTopicApiClient } from "@infrastructure/api/eventTopicApiClient";
import { VoteApiClient } from "@infrastructure/api/voteApiClient";
import { PollApiClient } from "@infrastructure/api/pollApiClient";
import { FingerprintService } from "@infrastructure/fingerprint/fingerprintService";
import { WebSocketClient, buildWebSocketUrl } from "@infrastructure/websocket";
import { TopicsViewModel } from "./TopicsViewModel";
import { PollParticipationViewModel } from "./PollParticipationViewModel";

export class EventBoardViewModel {
  event: Event | null = null;
  isLoading = true;
  error: string | null = null;
  isCreator: boolean = false;
  topicsViewModel: TopicsViewModel | null = null;
  pollParticipationViewModel: PollParticipationViewModel | null =
    null;

  private readonly _api: EventApiPort;
  private _wsClient: WebSocketClient | null = null;

  constructor(api: EventApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  async resolveEvent(code: string): Promise<void> {
    this.dispose();
    this.isLoading = true;
    this.error = null;

    const fingerprintSvc = new FingerprintService();

    try {
      const event = await this._api.getEventByCode(code);
      runInAction(() => {
        this.event = event;
        this._wsClient = new WebSocketClient();
        this.topicsViewModel = new TopicsViewModel(
          new EventTopicApiClient(event.id),
          new VoteApiClient(),
          fingerprintSvc,
          this._wsClient,
        );
        this.pollParticipationViewModel =
          new PollParticipationViewModel(
            new PollApiClient(),
            this._wsClient,
            fingerprintSvc,
          );
        this._wsClient.connect(
          buildWebSocketUrl(`events/${event.code}`),
        );
        this.pollParticipationViewModel.loadActivePoll(event.id);
        this.isLoading = false;
      });

      const creatorToken = localStorage.getItem(`creator_token:${code}`);
      if (creatorToken) {
        try {
          const result = await this._api.checkCreator(
            event.id,
            creatorToken,
          );
          runInAction(() => {
            this.isCreator = result.is_creator;
          });
        } catch {
          // Creator check failure is non-critical; isCreator stays false
        }
      }
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to load event";
        this.isLoading = false;
      });
    }
  }

  get isEventClosed(): boolean {
    return this.topicsViewModel?.isEventClosed ?? false;
  }

  dispose(): void {
    this.topicsViewModel?.dispose();
    this.topicsViewModel = null;
    this.pollParticipationViewModel?.dispose();
    this.pollParticipationViewModel = null;
    this._wsClient = null;
    this.isCreator = false;
  }
}
