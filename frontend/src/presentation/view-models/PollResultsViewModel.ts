import { makeAutoObservable, runInAction } from "mobx";
import type {
  PollOptionResult,
  PollResults,
} from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";

export class PollResultsViewModel {
  results: PollResults | null = null;
  isLoading = false;
  error: string | null = null;

  private readonly _api: PollApiPort;

  constructor(api: PollApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get sortedOptions(): PollOptionResult[] {
    if (!this.results) return [];
    return [...this.results.options].sort(
      (a, b) => b.count - a.count,
    );
  }

  get hasVotes(): boolean {
    return (this.results?.total_votes ?? 0) > 0;
  }

  async loadResults(pollId: string): Promise<void> {
    this.isLoading = true;
    this.error = null;
    try {
      const results = await this._api.getResults(pollId);
      runInAction(() => {
        this.results = results as PollResults;
        this.isLoading = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error
            ? e.message
            : "Failed to load poll results";
        this.isLoading = false;
      });
    }
  }

  updateResults(results: PollResults): void {
    this.results = results;
  }

  dispose(): void {
    /* no-op for cleanup */
  }
}
