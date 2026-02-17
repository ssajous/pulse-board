const API_BASE = "http://localhost:8000/api";

interface TopicResponse {
  id: string;
  content: string;
  score: number;
  created_at: string;
}

interface VoteResponse {
  id: string;
  topic_id: string;
  fingerprint_id: string;
  direction: "up" | "down";
}

export async function resetDatabase(): Promise<void> {
  const response = await fetch(`${API_BASE}/test/reset`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to reset database: ${response.status} ${response.statusText}`
    );
  }
}

export async function createTopicViaApi(
  content: string
): Promise<TopicResponse> {
  const response = await fetch(`${API_BASE}/topics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to create topic: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<TopicResponse>;
}

export async function castVoteViaApi(
  topicId: string,
  fingerprintId: string,
  direction: "up" | "down"
): Promise<VoteResponse> {
  const response = await fetch(`${API_BASE}/topics/${topicId}/votes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      fingerprint_id: fingerprintId,
      direction,
    }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to cast vote: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<VoteResponse>;
}
