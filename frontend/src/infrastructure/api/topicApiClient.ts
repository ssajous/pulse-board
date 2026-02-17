import type { Topic } from "@domain/entities/Topic";
import type { TopicApiPort } from "@domain/ports/TopicApiPort";

interface TopicsResponse {
  topics: Topic[];
}

interface ErrorResponse {
  detail: string;
}

export class TopicApiClient implements TopicApiPort {
  async fetchTopics(): Promise<Topic[]> {
    const response = await fetch("/api/topics");

    if (!response.ok) {
      throw new Error("Failed to fetch topics");
    }

    const data: TopicsResponse = await response.json();
    return data.topics;
  }

  async createTopic(content: string): Promise<Topic> {
    const response = await fetch("/api/topics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });

    if (response.status === 422) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }

    if (!response.ok) {
      throw new Error("Failed to create topic");
    }

    return response.json();
  }
}
