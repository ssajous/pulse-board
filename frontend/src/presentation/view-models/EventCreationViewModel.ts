import { makeAutoObservable, runInAction } from "mobx";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

export class EventCreationViewModel {
  title = "";
  description = "";
  startDate = "";
  endDate = "";
  isSubmitting = false;
  error: string | null = null;
  createdCode: string | null = null;

  private readonly _api: EventApiPort;
  private readonly _fingerprint: FingerprintPort;

  constructor(api: EventApiPort, fingerprint: FingerprintPort) {
    this._api = api;
    this._fingerprint = fingerprint;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get isValid(): boolean {
    return this.title.trim().length > 0 && this.title.length <= 200;
  }

  get isComplete(): boolean {
    return this.createdCode !== null;
  }

  setTitle(value: string): void {
    this.title = value;
  }

  setDescription(value: string): void {
    this.description = value;
  }

  setStartDate(value: string): void {
    this.startDate = value;
  }

  setEndDate(value: string): void {
    this.endDate = value;
  }

  async submit(): Promise<void> {
    if (!this.isValid || this.isSubmitting) return;
    this.isSubmitting = true;
    this.error = null;
    try {
      const fingerprint = await this._fingerprint.getFingerprint();
      const event = await this._api.createEvent({
        title: this.title.trim(),
        description: this.description.trim() || undefined,
        start_date: this.startDate || undefined,
        end_date: this.endDate || undefined,
        creator_fingerprint: fingerprint,
      });
      if (event.creator_token) {
        localStorage.setItem(
          `creator_token:${event.code}`,
          event.creator_token,
        );
      }
      runInAction(() => {
        this.createdCode = event.code;
        this.isSubmitting = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to create event";
        this.isSubmitting = false;
      });
    }
  }

  reset(): void {
    this.title = "";
    this.description = "";
    this.startDate = "";
    this.endDate = "";
    this.isSubmitting = false;
    this.error = null;
    this.createdCode = null;
  }
}
