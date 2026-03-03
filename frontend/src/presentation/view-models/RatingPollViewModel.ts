import { makeAutoObservable, runInAction } from "mobx";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type { RatingPollResults } from "@domain/entities/Poll";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

export class RatingPollViewModel {
  selectedRating: number | null = null;
  hoveredRating: number | null = null;
  isSubmitting = false;
  hasSubmitted = false;
  error: string | null = null;
  results: RatingPollResults | null = null;

  private readonly _api: PollApiPort;
  private readonly _fingerprint: FingerprintPort;

  constructor(api: PollApiPort, fingerprint: FingerprintPort) {
    this._api = api;
    this._fingerprint = fingerprint;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get displayRating(): number {
    return this.hoveredRating ?? this.selectedRating ?? 0;
  }

  get canSubmit(): boolean {
    return (
      this.selectedRating !== null
      && !this.isSubmitting
      && !this.hasSubmitted
    );
  }

  get starStates(): boolean[] {
    return [1, 2, 3, 4, 5].map((n) => n <= this.displayRating);
  }

  setHoveredRating(rating: number | null): void {
    this.hoveredRating = rating;
  }

  selectRating(rating: number): void {
    if (this.hasSubmitted) return;
    this.selectedRating = rating;
  }

  async submitRating(pollId: string): Promise<void> {
    if (!this.canSubmit || this.selectedRating === null) return;
    this.isSubmitting = true;
    this.error = null;
    try {
      const fingerprintId = await this._fingerprint.getFingerprint();
      await this._api.submitResponse(
        pollId,
        fingerprintId,
        null,
        this.selectedRating,
      );
      const results = await this._api.getResults(pollId);
      runInAction(() => {
        this.hasSubmitted = true;
        this.results = results as RatingPollResults;
        this.isSubmitting = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to submit rating";
        this.isSubmitting = false;
      });
    }
  }

  updateResults(results: RatingPollResults): void {
    this.results = results;
  }

  reset(): void {
    this.selectedRating = null;
    this.hoveredRating = null;
    this.isSubmitting = false;
    this.hasSubmitted = false;
    this.error = null;
    this.results = null;
  }

  dispose(): void {
    /* no-op */
  }
}
