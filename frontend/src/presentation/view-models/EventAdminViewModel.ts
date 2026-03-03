import { makeAutoObservable, runInAction } from "mobx";
import type { Event } from "@domain/entities/Event";
import type { Poll, PollResults } from "@domain/entities/Poll";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { PollApiPort } from "@domain/ports/PollApiPort";

export class EventAdminViewModel {
  event: Event | null = null;
  polls: Poll[] = [];
  isLoading = true;
  error: string | null = null;
  pollResults: Map<string, PollResults> = new Map();
  activatingPollId: string | null = null;

  private readonly _eventApi: EventApiPort;
  private readonly _pollApi: PollApiPort;

  constructor(eventApi: EventApiPort, pollApi: PollApiPort) {
    this._eventApi = eventApi;
    this._pollApi = pollApi;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get eventId(): string | null {
    return this.event?.id ?? null;
  }

  get pollApi(): PollApiPort {
    return this._pollApi;
  }

  async loadEvent(code: string): Promise<void> {
    this.isLoading = true;
    this.error = null;
    try {
      const event = await this._eventApi.getEventByCode(code);
      runInAction(() => {
        this.event = event;
        this.isLoading = false;
      });
      await this.loadPolls();
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to load event";
        this.isLoading = false;
      });
    }
  }

  async loadPolls(): Promise<void> {
    if (!this.event) return;
    try {
      const polls = await this._pollApi.listPolls(this.event.id);
      runInAction(() => {
        this.polls = polls;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to load polls";
      });
    }
  }

  async togglePollActive(pollId: string): Promise<void> {
    const poll = this.polls.find((p) => p.id === pollId);
    if (!poll) return;

    this.activatingPollId = pollId;
    try {
      await this._pollApi.activatePoll(pollId, !poll.is_active);
      await this.loadPolls();
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error
            ? e.message
            : "Failed to toggle poll";
      });
    } finally {
      runInAction(() => {
        this.activatingPollId = null;
      });
    }
  }

  async loadPollResults(pollId: string): Promise<void> {
    try {
      const results = await this._pollApi.getResults(pollId);
      runInAction(() => {
        this.pollResults.set(pollId, results as PollResults);
      });
    } catch {
      /* results may not exist yet */
    }
  }

  onPollCreated(poll: Poll): void {
    this.polls = [...this.polls, poll];
  }

  dismissError(): void {
    this.error = null;
  }

  dispose(): void {
    /* no-op for cleanup */
  }
}
