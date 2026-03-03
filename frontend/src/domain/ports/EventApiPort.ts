import type { Event } from "@domain/entities/Event";

export interface CreateEventRequest {
  readonly title: string;
  readonly description?: string;
  readonly start_date?: string;
  readonly end_date?: string;
  readonly creator_fingerprint?: string;
}

export interface CheckCreatorResponse {
  readonly is_creator: boolean;
}

export interface EventApiPort {
  createEvent(request: CreateEventRequest): Promise<Event>;
  getEventByCode(code: string): Promise<Event>;
  getEventById(id: string): Promise<Event>;
  checkCreator(
    eventId: string,
    creatorToken: string,
  ): Promise<CheckCreatorResponse>;
}
