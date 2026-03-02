import type { Poll } from "@domain/entities/Poll";

export interface PollApiPort {
  listPolls(eventId: string): Promise<Poll[]>;
  getActivePoll(eventId: string): Promise<Poll | null>;
}
