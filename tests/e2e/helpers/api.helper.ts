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

interface EventResponse {
  id: string;
  title: string;
  code: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  status: string;
  created_at: string;
  creator_token: string | null;
}

export interface PollOptionResponse {
  id: string;
  text: string;
}

export interface PollResponse {
  id: string;
  event_id: string;
  question: string;
  poll_type: string;
  options: PollOptionResponse[];
  is_active: boolean;
  created_at: string;
}

export interface PollOptionResultResponse {
  option_id: string;
  text: string;
  count: number;
  percentage: number;
}

export interface PollResultsResponse {
  poll_id: string;
  question: string;
  total_votes: number;
  options: PollOptionResultResponse[];
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

export async function createEventViaApi(
  title: string,
  description?: string
): Promise<EventResponse> {
  const response = await fetch(`${API_BASE}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description: description ?? null }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to create event: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<EventResponse>;
}

export async function joinEventViaApi(
  code: string
): Promise<EventResponse> {
  const response = await fetch(`${API_BASE}/events/join/${code}`);

  if (!response.ok) {
    throw new Error(
      `Failed to join event: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<EventResponse>;
}

export async function createEventTopicViaApi(
  eventId: string,
  content: string
): Promise<TopicResponse> {
  const response = await fetch(`${API_BASE}/events/${eventId}/topics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to create event topic: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<TopicResponse>;
}

export async function createPollViaApi(
  eventId: string,
  question: string,
  options: string[]
): Promise<PollResponse> {
  const response = await fetch(`${API_BASE}/events/${eventId}/polls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, options }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to create poll: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<PollResponse>;
}

export async function activatePollViaApi(
  pollId: string
): Promise<PollResponse> {
  const response = await fetch(`${API_BASE}/polls/${pollId}/activate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activate: true }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to activate poll: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<PollResponse>;
}

export async function deactivatePollViaApi(
  pollId: string
): Promise<PollResponse> {
  const response = await fetch(`${API_BASE}/polls/${pollId}/activate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activate: false }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to deactivate poll: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<PollResponse>;
}

export async function submitPollResponseViaApi(
  pollId: string,
  fingerprintId: string,
  optionId: string
): Promise<{ id: string; poll_id: string; option_id: string; created_at: string }> {
  const response = await fetch(`${API_BASE}/polls/${pollId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fingerprint_id: fingerprintId, option_id: optionId }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to submit poll response: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<{
    id: string;
    poll_id: string;
    option_id: string;
    created_at: string;
  }>;
}

export async function getPollResultsViaApi(
  pollId: string
): Promise<PollResultsResponse> {
  const response = await fetch(`${API_BASE}/polls/${pollId}/results`);

  if (!response.ok) {
    throw new Error(
      `Failed to get poll results: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<PollResultsResponse>;
}

export interface TopicStatusResponse {
  topic_id: string;
  new_status: string;
}

export interface CloseEventApiResponse {
  event_id: string;
  status: string;
}

export async function updateTopicStatusViaApi(
  eventId: string,
  topicId: string,
  status: string,
  creatorToken: string
): Promise<TopicStatusResponse> {
  const response = await fetch(
    `${API_BASE}/events/${eventId}/topics/${topicId}/status`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-Creator-Token": creatorToken,
      },
      body: JSON.stringify({ status }),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to update topic status: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<TopicStatusResponse>;
}

export async function closeEventViaApi(
  eventId: string,
  creatorToken: string
): Promise<CloseEventApiResponse> {
  const response = await fetch(`${API_BASE}/events/${eventId}/close`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-Creator-Token": creatorToken,
    },
  });

  if (!response.ok) {
    throw new Error(
      `Failed to close event: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<CloseEventApiResponse>;
}

export interface WordFrequency {
  text: string;
  count: number;
}

export interface WordCloudPollResultsResponse {
  poll_id: string;
  question: string;
  total_responses: number;
  frequencies: WordFrequency[];
}

export async function createWordCloudPollViaApi(
  eventId: string,
  question: string
): Promise<PollResponse> {
  const response = await fetch(`${API_BASE}/events/${eventId}/polls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, poll_type: "word_cloud", options: [] }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to create word cloud poll: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<PollResponse>;
}

export async function submitWordCloudResponseViaApi(
  pollId: string,
  fingerprintId: string,
  responseValue: string
): Promise<{ id: string; poll_id: string; option_id: null; created_at: string }> {
  const response = await fetch(`${API_BASE}/polls/${pollId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      fingerprint_id: fingerprintId,
      response_value: responseValue,
    }),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to submit word cloud response: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<{
    id: string;
    poll_id: string;
    option_id: null;
    created_at: string;
  }>;
}

export async function getWordCloudResultsViaApi(
  pollId: string
): Promise<WordCloudPollResultsResponse> {
  const response = await fetch(`${API_BASE}/polls/${pollId}/results`);

  if (!response.ok) {
    throw new Error(
      `Failed to get word cloud results: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<WordCloudPollResultsResponse>;
}
