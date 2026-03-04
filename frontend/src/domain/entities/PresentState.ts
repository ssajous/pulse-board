import type { PollOptionResult, PollType, WordFrequency } from "./Poll";

export interface PresentActivePoll {
  readonly poll_id: string;
  readonly question: string;
  readonly total_votes: number;
  readonly options: PollOptionResult[];
  readonly poll_type?: PollType;
  readonly frequencies?: WordFrequency[];
  readonly total_responses?: number;
}

export interface PresentTopic {
  readonly id: string;
  readonly content: string;
  readonly score: number;
}

export interface PresentState {
  readonly active_poll: PresentActivePoll | null;
  readonly top_topics: PresentTopic[];
  readonly participant_count: number;
}
