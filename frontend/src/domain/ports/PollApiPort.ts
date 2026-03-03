import type { Poll, PollResults, PollSubmitResponse } from "@domain/entities/Poll";

export interface CreatePollRequest {
  readonly question: string;
  readonly options: string[];
}

export interface PollApiPort {
  createPoll(eventId: string, request: CreatePollRequest): Promise<Poll>;
  listPolls(eventId: string): Promise<Poll[]>;
  getActivePoll(eventId: string): Promise<Poll | null>;
  activatePoll(pollId: string, activate: boolean): Promise<void>;
  submitResponse(
    pollId: string,
    fingerprintId: string,
    optionId: string,
  ): Promise<PollSubmitResponse>;
  getResults(pollId: string): Promise<PollResults>;
}
