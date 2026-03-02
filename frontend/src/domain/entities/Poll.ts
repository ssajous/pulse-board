export type PollType =
  | "multiple_choice"
  | "word_cloud"
  | "rating"
  | "open_text";

export interface PollOption {
  readonly id: string;
  readonly text: string;
}

export interface Poll {
  readonly id: string;
  readonly event_id: string;
  readonly question: string;
  readonly poll_type: PollType;
  readonly options: PollOption[];
  readonly is_active: boolean;
  readonly created_at: string;
}
