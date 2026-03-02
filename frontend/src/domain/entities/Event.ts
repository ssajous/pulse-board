export type EventStatus = "ACTIVE" | "CLOSED";

export interface Event {
  readonly id: string;
  readonly title: string;
  readonly code: string;
  readonly description: string | null;
  readonly start_date: string | null;
  readonly end_date: string | null;
  readonly status: EventStatus;
  readonly created_at: string;
}
