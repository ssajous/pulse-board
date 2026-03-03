import type {
  Poll,
  AnyPollResults,
  PollSubmitResponse,
} from "@domain/entities/Poll";
import type { CreatePollRequest, PollApiPort } from "@domain/ports/PollApiPort";
import type { ErrorResponse } from "./types";

interface PollsResponse {
  polls: Poll[];
}

export class PollApiClient implements PollApiPort {
  async createPoll(
    eventId: string,
    request: CreatePollRequest,
  ): Promise<Poll> {
    const body: Record<string, unknown> = {
      question: request.question,
    };
    if (request.options !== undefined) body.options = request.options;
    if (request.poll_type !== undefined) body.poll_type = request.poll_type;

    const response = await fetch(`/api/events/${eventId}/polls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (response.status === 422) {
      const error: ErrorResponse = await response.json();
      throw new Error(error.detail);
    }

    if (!response.ok) {
      throw new Error("Failed to create poll");
    }

    return response.json();
  }

  async listPolls(eventId: string): Promise<Poll[]> {
    const response = await fetch(`/api/events/${eventId}/polls`);

    if (!response.ok) {
      throw new Error("Failed to fetch polls");
    }

    const data: PollsResponse = await response.json();
    return data.polls;
  }

  async getActivePoll(eventId: string): Promise<Poll | null> {
    const response = await fetch(
      `/api/events/${eventId}/polls/active`,
    );

    if (response.status === 204) {
      return null;
    }

    if (!response.ok) {
      throw new Error("Failed to fetch active poll");
    }

    return response.json();
  }

  async activatePoll(
    pollId: string,
    activate: boolean,
  ): Promise<void> {
    const response = await fetch(`/api/polls/${pollId}/activate`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activate }),
    });

    if (!response.ok) {
      throw new Error(
        activate
          ? "Failed to activate poll"
          : "Failed to deactivate poll",
      );
    }
  }

  async submitResponse(
    pollId: string,
    fingerprintId: string,
    optionId: string | null,
    responseValue?: number | string | null,
  ): Promise<PollSubmitResponse> {
    const response = await fetch(`/api/polls/${pollId}/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fingerprint_id: fingerprintId,
        option_id: optionId,
        response_value: responseValue ?? null,
      }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail =
        (body as ErrorResponse | null)?.detail
        ?? "Failed to submit response";
      throw new Error(detail);
    }

    return response.json();
  }

  async getResults(
    pollId: string,
    page?: number,
    pageSize?: number,
  ): Promise<AnyPollResults> {
    const params = new URLSearchParams();
    if (page !== undefined) params.set("page", String(page));
    if (pageSize !== undefined) params.set("page_size", String(pageSize));
    const qs = params.toString();
    const query = qs ? `?${qs}` : "";

    const response = await fetch(
      `/api/polls/${pollId}/results${query}`,
    );

    if (!response.ok) {
      throw new Error("Failed to fetch poll results");
    }

    return response.json();
  }
}
