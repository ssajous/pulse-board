import { makeAutoObservable, runInAction } from "mobx";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { Event } from "@domain/entities/Event";

export class EventJoinViewModel {
  code = "";
  isJoining = false;
  error: string | null = null;
  joinedEvent: Event | null = null;

  private readonly _api: EventApiPort;

  constructor(api: EventApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get isValid(): boolean {
    return /^\d{6}$/.test(this.code);
  }

  setCode(value: string): void {
    this.code = value.replace(/\D/g, "").slice(0, 6);
  }

  async join(): Promise<void> {
    if (!this.isValid || this.isJoining) return;
    this.isJoining = true;
    this.error = null;
    try {
      const event = await this._api.getEventByCode(this.code);
      runInAction(() => {
        this.joinedEvent = event;
        this.isJoining = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to join event";
        this.isJoining = false;
      });
    }
  }

  reset(): void {
    this.code = "";
    this.isJoining = false;
    this.error = null;
    this.joinedEvent = null;
  }
}
