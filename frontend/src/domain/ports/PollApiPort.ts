import type {
  Poll,
  AnyPollResults,
  PollSubmitResponse,
} from "@domain/entities/Poll";

export interface CreatePollRequest {
  readonly question: string;
  readonly options?: string[];
  readonly poll_type?: string;
}

export interface PollApiPort {
  createPoll(eventId: string, request: CreatePollRequest): Promise<Poll>;
  listPolls(eventId: string): Promise<Poll[]>;
  getActivePoll(eventId: string): Promise<Poll | null>;
  activatePoll(pollId: string, activate: boolean): Promise<void>;
  submitResponse(
    pollId: string,
    fingerprintId: string,
    optionId: string | null,
    responseValue?: number | string | null,
  ): Promise<PollSubmitResponse>;
  getResults(
    pollId: string,
    page?: number,
    pageSize?: number,
  ): Promise<AnyPollResults>;
}
