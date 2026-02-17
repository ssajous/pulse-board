export interface VoteResponse {
  readonly topic_id: string;
  readonly new_score: number;
  readonly vote_status: "created" | "toggled" | "cancelled";
  readonly user_vote: number | null;
  readonly censured: boolean;
}
