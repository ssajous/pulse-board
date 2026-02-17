import type { VoteResponse } from "@domain/entities/Vote";
import type { VoteApiPort } from "@domain/ports/VoteApiPort";

interface ErrorResponse {
  detail: string;
}

export class VoteApiClient implements VoteApiPort {
  async castVote(
    topicId: string,
    fingerprintId: string,
    direction: "up" | "down"
  ): Promise<VoteResponse> {
    const response = await fetch(`/api/topics/${topicId}/votes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fingerprint_id: fingerprintId, direction }),
    });
    if (response.status === 404) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }
    if (response.status === 422) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }
    if (!response.ok) throw new Error("Failed to cast vote");
    return response.json();
  }
}
