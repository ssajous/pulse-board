import type { Event } from "@domain/entities/Event";

export interface CreateEventRequest {
  readonly title: string;
  readonly description?: string;
  readonly start_date?: string;
  readonly end_date?: string;
}

export interface EventApiPort {
  createEvent(request: CreateEventRequest): Promise<Event>;
  getEventByCode(code: string): Promise<Event>;
  getEventById(id: string): Promise<Event>;
}
