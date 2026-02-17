import type { VoteResponse } from "@domain/entities/Vote";

export interface VoteApiPort {
  castVote(
    topicId: string,
    fingerprintId: string,
    direction: "up" | "down"
  ): Promise<VoteResponse>;
}
