export interface EventStats {
  readonly participant_count: number;
  readonly topic_count: number;
  readonly active_topic_count: number;
  readonly poll_count: number;
  readonly has_active_poll: boolean;
  readonly total_poll_responses: number;
}
