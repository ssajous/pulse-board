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

export interface PollResults {
  readonly poll_id: string;
  readonly question: string;
  readonly total_votes: number;
  readonly options: PollOptionResult[];
}

export interface PollOptionResult {
  readonly option_id: string;
  readonly text: string;
  readonly count: number;
  readonly percentage: number;
}

export interface PollSubmitResponse {
  readonly id: string;
  readonly poll_id: string;
  readonly option_id: string;
  readonly created_at: string;
}
