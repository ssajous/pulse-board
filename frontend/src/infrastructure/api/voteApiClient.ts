import type { VoteResponse } from "@domain/entities/Vote";
import type { VoteApiPort } from "@domain/ports/VoteApiPort";

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
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail = body?.detail ?? "Failed to cast vote";
      throw new Error(detail);
    }
    return response.json();
  }
}
