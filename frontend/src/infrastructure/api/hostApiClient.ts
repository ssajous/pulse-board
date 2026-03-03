import type { Topic } from "@domain/entities/Topic";
import type { EventStats } from "@domain/entities/EventStats";
import type {
  HostApiPort,
  UpdateTopicStatusResponse,
  CloseEventResponse,
} from "@domain/ports/HostApiPort";

export class HostApiClient implements HostApiPort {
  private readonly creatorToken: string;

  constructor(creatorToken: string) {
    this.creatorToken = creatorToken;
  }

  private get headers(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-Creator-Token": this.creatorToken,
    };
  }

  async updateTopicStatus(
    eventId: string,
    topicId: string,
    status: string,
  ): Promise<UpdateTopicStatusResponse> {
    const response = await fetch(
      `/api/events/${eventId}/topics/${topicId}/status`,
      {
        method: "PATCH",
        headers: this.headers,
        body: JSON.stringify({ status }),
      },
    );

    if (response.status === 403) {
      throw new Error("Not authorized to manage this event");
    }

    if (response.status === 404) {
      throw new Error("Topic not found");
    }

    if (!response.ok) {
      throw new Error("Failed to update topic status");
    }

    return response.json();
  }

  async closeEvent(eventId: string): Promise<CloseEventResponse> {
    const response = await fetch(`/api/events/${eventId}/close`, {
      method: "POST",
      headers: this.headers,
    });

    if (response.status === 403) {
      throw new Error("Not authorized to close this event");
    }

    if (response.status === 404) {
      throw new Error("Event not found");
    }

    if (!response.ok) {
      throw new Error("Failed to close event");
    }

    return response.json();
  }

  async getEventStats(eventId: string): Promise<EventStats> {
    const response = await fetch(`/api/events/${eventId}/stats`, {
      headers: this.headers,
    });

    if (response.status === 403) {
      throw new Error("Not authorized to view event stats");
    }

    if (response.status === 404) {
      throw new Error("Event not found");
    }

    if (!response.ok) {
      throw new Error("Failed to fetch event stats");
    }

    return response.json();
  }

  async getAllTopics(eventId: string): Promise<Topic[]> {
    const response = await fetch(
      `/api/events/${eventId}/topics/all`,
      {
        headers: this.headers,
      },
    );

    if (response.status === 403) {
      throw new Error("Not authorized to view all topics");
    }

    if (response.status === 404) {
      throw new Error("Event not found");
    }

    if (!response.ok) {
      throw new Error("Failed to fetch topics");
    }

    return response.json();
  }
}
