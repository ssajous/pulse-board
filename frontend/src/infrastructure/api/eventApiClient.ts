import type { Event } from "@domain/entities/Event";
import type {
  CreateEventRequest,
  EventApiPort,
} from "@domain/ports/EventApiPort";
import type { ErrorResponse } from "./types";

export class EventApiClient implements EventApiPort {
  async createEvent(request: CreateEventRequest): Promise<Event> {
    const response = await fetch("/api/events/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (response.status === 422) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }

    if (!response.ok) {
      throw new Error("Failed to create event");
    }

    return response.json();
  }

  async getEventByCode(code: string): Promise<Event> {
    const response = await fetch(`/api/events/join/${code}`);

    if (response.status === 404) {
      throw new Error("Event not found");
    }

    if (response.status === 409) {
      throw new Error("Event is no longer active");
    }

    if (!response.ok) {
      throw new Error("Failed to join event");
    }

    return response.json();
  }

  async getEventById(id: string): Promise<Event> {
    const response = await fetch(`/api/events/${id}`);

    if (response.status === 404) {
      throw new Error("Event not found");
    }

    if (!response.ok) {
      throw new Error("Failed to fetch event");
    }

    return response.json();
  }
}
