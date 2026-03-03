import { makeAutoObservable, runInAction } from "mobx";
import type {
  Poll,
  PollResults,
  PollType,
  RatingPollResults,
} from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type { WebSocketPort } from "@domain/ports/WebSocketPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";
import { logger } from "@infrastructure/logger";
import { isRecord } from "@infrastructure/utils/typeGuards";
import { RatingPollViewModel } from "./RatingPollViewModel";
import { OpenTextPollViewModel } from "./OpenTextPollViewModel";

export class PollParticipationViewModel {
  activePoll: Poll | null = null;
  selectedOptionId: string | null = null;
  isSubmitting = false;
  hasSubmitted = false;
  error: string | null = null;
  results: PollResults | null = null;
  ratingVm: RatingPollViewModel | null = null;
  openTextVm: OpenTextPollViewModel | null = null;

  private readonly _api: PollApiPort;
  private readonly _ws: WebSocketPort;
  private readonly _fingerprint: FingerprintPort;

  constructor(
    api: PollApiPort,
    ws: WebSocketPort,
    fingerprint: FingerprintPort,
  ) {
    this._api = api;
    this._ws = ws;
    this._fingerprint = fingerprint;
    makeAutoObservable(this, {}, { autoBind: true });
    this.setupWebSocketHandlers();
  }

  get canSubmit(): boolean {
    return (
      this.activePoll !== null
      && this.selectedOptionId !== null
      && !this.isSubmitting
      && !this.hasSubmitted
    );
  }

  get showResults(): boolean {
    return this.hasSubmitted && this.results !== null;
  }

  selectOption(id: string): void {
    if (this.hasSubmitted) return;
    this.selectedOptionId = id;
  }

  async loadActivePoll(eventId: string): Promise<void> {
    try {
      const poll = await this._api.getActivePoll(eventId);
      runInAction(() => {
        this.activePoll = poll;
        if (poll) {
          this.initSubVm(poll);
        }
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error
            ? e.message
            : "Failed to load active poll";
      });
    }
  }

  async submit(): Promise<void> {
    if (!this.canSubmit || !this.activePoll || !this.selectedOptionId) {
      return;
    }
    this.isSubmitting = true;
    this.error = null;
    try {
      const fingerprintId =
        await this._fingerprint.getFingerprint();
      await this._api.submitResponse(
        this.activePoll.id,
        fingerprintId,
        this.selectedOptionId,
        null,
      );
      const results = await this._api.getResults(this.activePoll.id);
      runInAction(() => {
        this.hasSubmitted = true;
        this.results = results as PollResults;
        this.isSubmitting = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error
            ? e.message
            : "Failed to submit response";
        this.isSubmitting = false;
      });
    }
  }

  private initSubVm(poll: Poll): void {
    this.ratingVm?.dispose();
    this.openTextVm?.dispose();
    this.ratingVm = null;
    this.openTextVm = null;

    if (poll.poll_type === "rating") {
      this.ratingVm = new RatingPollViewModel(
        this._api,
        this._fingerprint,
      );
    } else if (poll.poll_type === "open_text") {
      this.openTextVm = new OpenTextPollViewModel(
        this._api,
        this._fingerprint,
      );
    }
  }

  private setupWebSocketHandlers(): void {
    this._ws.onMessage((data: unknown) => {
      logger.log("Poll WebSocket message received:", data);
      if (!isRecord(data)) return;

      switch (data.type as string) {
        case "poll_activated": {
          const poll: Poll = {
            id: data.poll_id as string,
            event_id: "",
            question: data.question as string,
            poll_type:
              ((data.poll_type as string) as PollType)
              ?? "multiple_choice",
            options: (data.options as Poll["options"]) ?? [],
            is_active: true,
            created_at: new Date().toISOString(),
          };
          this.handlePollActivated(poll);
          break;
        }
        case "poll_deactivated":
          this.handlePollDeactivated();
          break;
        case "poll_results_updated": {
          const pollType = data.poll_type as string | undefined;
          if (pollType === "rating" && this.ratingVm) {
            this.ratingVm.updateResults(
              data.results as RatingPollResults,
            );
          } else if (pollType === "open_text") {
            // Open text results are loaded on demand, not pushed
          } else {
            if (!isRecord(data.results)) break;
            const optionsData = (
              data.results as Record<string, unknown>
            ).options;
            if (!Array.isArray(optionsData)) break;
            const options = optionsData as PollResults["options"];
            const totalVotes = options.reduce(
              (sum, opt) => sum + opt.count,
              0,
            );
            this.handleResultsUpdated({
              poll_id: data.poll_id as string,
              question: this.activePoll?.question ?? "",
              total_votes: totalVotes,
              options,
            });
          }
          break;
        }
      }
    });
  }

  private resetPollState(poll: Poll | null): void {
    this.activePoll = poll;
    this.selectedOptionId = null;
    this.hasSubmitted = false;
    this.results = null;
    this.error = null;
  }

  private handlePollActivated(poll: Poll): void {
    this.initSubVm(poll);
    this.resetPollState(poll);
  }

  private handlePollDeactivated(): void {
    this.ratingVm?.dispose();
    this.openTextVm?.dispose();
    this.ratingVm = null;
    this.openTextVm = null;
    this.resetPollState(null);
  }

  private handleResultsUpdated(results: PollResults): void {
    if (this.hasSubmitted) {
      this.results = results;
    }
  }

  dispose(): void {
    this.ratingVm?.dispose();
    this.openTextVm?.dispose();
  }
}
