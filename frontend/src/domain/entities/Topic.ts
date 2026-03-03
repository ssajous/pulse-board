export type TopicStatus =
  | "active"
  | "highlighted"
  | "answered"
  | "archived";

export interface Topic {
  readonly id: string;
  readonly content: string;
  readonly score: number;
  readonly created_at: string;
  readonly status?: TopicStatus;
}
