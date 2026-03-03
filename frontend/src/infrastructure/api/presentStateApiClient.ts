import type { PresentState } from "@domain/entities/PresentState";
import type { PresentStateApiPort } from "@domain/ports/PresentStateApiPort";

export class PresentStateApiClient implements PresentStateApiPort {
  async getPresentState(eventId: string): Promise<PresentState> {
    const response = await fetch(
      `/api/events/${eventId}/present-state`,
    );

    if (response.status === 404) {
      throw new Error("Event not found");
    }

    if (!response.ok) {
      throw new Error("Failed to fetch present state");
    }

    return response.json();
  }
}
