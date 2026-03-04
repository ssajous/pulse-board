import { makeAutoObservable, runInAction } from "mobx";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type {
  WordFrequency,
  WordCloudPollResults,
} from "@domain/entities/Poll";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

const MAX_WORD_CLOUD_LENGTH = 30;

export class WordCloudViewModel {
  inputText = "";
  isSubmitting = false;
  hasSubmitted = false;
  error: string | null = null;
  frequencies: WordFrequency[] = [];
  totalResponses = 0;

  private readonly _api: PollApiPort;
  private readonly _fingerprint: FingerprintPort;

  constructor(api: PollApiPort, fingerprint: FingerprintPort) {
    this._api = api;
    this._fingerprint = fingerprint;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get wordCount(): number {
    const trimmed = this.inputText.trim();
    if (trimmed.length === 0) return 0;
    return trimmed.split(/\s+/).length;
  }

  get isInputValid(): boolean {
    const trimmed = this.inputText.trim();
    return (
      trimmed.length > 0
      && this.wordCount >= 1
      && this.wordCount <= 3
      && trimmed.length <= MAX_WORD_CLOUD_LENGTH
    );
  }

  get isSubmitDisabled(): boolean {
    return !this.isInputValid || this.isSubmitting || this.hasSubmitted;
  }

  get wordCountDisplay(): string {
    return `${this.wordCount}/3 words`;
  }

  setInputText(text: string): void {
    this.inputText = text.slice(0, MAX_WORD_CLOUD_LENGTH);
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
      )) as WordCloudPollResults;
      this.updateFromResults(results);
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to submit response";
        this.isSubmitting = false;
      });
    }
  }

  handleWordCloudUpdated(data: {
    total_responses: number;
    frequencies: Array<{ text: string; count: number }>;
  }): void {
    this.frequencies = data.frequencies;
    this.totalResponses = data.total_responses;
  }

  updateFromResults(results: WordCloudPollResults): void {
    runInAction(() => {
      this.frequencies = results.frequencies;
      this.totalResponses = results.total_responses;
    });
  }

  reset(): void {
    this.inputText = "";
    this.isSubmitting = false;
    this.hasSubmitted = false;
    this.error = null;
    this.frequencies = [];
    this.totalResponses = 0;
  }

  dispose(): void {
    /* no-op */
  }
}
