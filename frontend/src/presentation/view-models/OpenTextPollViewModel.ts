import { makeAutoObservable, runInAction } from "mobx";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type {
  OpenTextResponse,
  OpenTextPollResults,
} from "@domain/entities/Poll";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

const MAX_TEXT_LENGTH = 500;
const AMBER_THRESHOLD = 450;
const RED_THRESHOLD = 490;

export class OpenTextPollViewModel {
  inputText = "";
  isSubmitting = false;
  hasSubmitted = false;
  error: string | null = null;
  responses: OpenTextResponse[] = [];
  totalResponses = 0;
  currentPage = 1;
  isLoadingMore = false;

  private readonly _api: PollApiPort;
  private readonly _fingerprint: FingerprintPort;

  constructor(api: PollApiPort, fingerprint: FingerprintPort) {
    this._api = api;
    this._fingerprint = fingerprint;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get charCount(): number {
    return this.inputText.length;
  }

  get isSubmitDisabled(): boolean {
    return (
      this.inputText.trim().length === 0
      || this.isSubmitting
      || this.hasSubmitted
    );
  }

  get counterColorClass(): string {
    if (this.charCount >= RED_THRESHOLD) return "text-red-400";
    if (this.charCount >= AMBER_THRESHOLD) return "text-amber-400";
    return "text-slate-400";
  }

  get hasMore(): boolean {
    return this.responses.length < this.totalResponses;
  }

  setInputText(text: string): void {
    this.inputText = text.slice(0, MAX_TEXT_LENGTH);
  }

  async submitResponse(pollId: string): Promise<void> {
    if (this.isSubmitDisabled) return;
    this.isSubmitting = true;
    this.error = null;
    try {
      const fingerprintId = await this._fingerprint.getFingerprint();
      await this._api.submitResponse(
        pollId,
        fingerprintId,
        null,
        this.inputText.trim(),
      );
      runInAction(() => {
        this.hasSubmitted = true;
        this.isSubmitting = false;
      });
      const results = (await this._api.getResults(
        pollId,
        1,
      )) as OpenTextPollResults;
      this.updateResults(results);
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to submit response";
        this.isSubmitting = false;
      });
    }
  }

  async loadMoreResponses(pollId: string): Promise<void> {
    if (!this.hasMore || this.isLoadingMore) return;
    this.isLoadingMore = true;
    try {
      const nextPage = this.currentPage + 1;
      const results = (await this._api.getResults(
        pollId,
        nextPage,
      )) as OpenTextPollResults;
      runInAction(() => {
        this.responses = [...this.responses, ...results.responses];
        this.currentPage = nextPage;
        this.totalResponses = results.total_responses;
        this.isLoadingMore = false;
      });
    } catch {
      runInAction(() => {
        this.isLoadingMore = false;
      });
    }
  }

  prependResponse(response: OpenTextResponse): void {
    this.responses = [response, ...this.responses];
    this.totalResponses += 1;
  }

  updateResults(results: OpenTextPollResults): void {
    runInAction(() => {
      this.responses = results.responses;
      this.totalResponses = results.total_responses;
      this.currentPage = results.page;
    });
  }

  reset(): void {
    this.inputText = "";
    this.isSubmitting = false;
    this.hasSubmitted = false;
    this.error = null;
    this.responses = [];
    this.totalResponses = 0;
    this.currentPage = 1;
    this.isLoadingMore = false;
  }

  dispose(): void {
    /* no-op */
  }
}
