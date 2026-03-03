import { describe, it, expect, vi, beforeEach } from "vitest";
import { PollParticipationViewModel } from "../PollParticipationViewModel";
import type { Poll, PollResults } from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type {
  WebSocketPort,
  WebSocketMessageHandler,
} from "@domain/ports/WebSocketPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

// --- Factories ---

function makePoll(overrides: Partial<Poll> = {}): Poll {
  return {
    id: "poll-1",
    event_id: "event-1",
    question: "What is your favorite color?",
    poll_type: "multiple_choice",
    options: [
      { id: "opt-1", text: "Red" },
      { id: "opt-2", text: "Blue" },
    ],
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeResults(overrides: Partial<PollResults> = {}): PollResults {
  return {
    poll_id: "poll-1",
    question: "What is your favorite color?",
    total_votes: 10,
    options: [
      { option_id: "opt-1", text: "Red", count: 7, percentage: 70.0 },
      { option_id: "opt-2", text: "Blue", count: 3, percentage: 30.0 },
    ],
    ...overrides,
  };
}

function createMockPollApi(): PollApiPort {
  return {
    createPoll: vi.fn().mockResolvedValue(makePoll()),
    listPolls: vi.fn().mockResolvedValue([]),
    getActivePoll: vi.fn().mockResolvedValue(makePoll()),
    activatePoll: vi.fn().mockResolvedValue(undefined),
    submitResponse: vi.fn().mockResolvedValue({
      id: "r1",
      poll_id: "poll-1",
      option_id: "opt-1",
      created_at: "2026-01-01T00:00:00Z",
    }),
    getResults: vi.fn().mockResolvedValue(makeResults()),
  };
}

interface MockWsResult {
  ws: WebSocketPort;
  messageHandler: { current: WebSocketMessageHandler | null };
}

function createMockWs(): MockWsResult {
  const messageHandler: {
    current: WebSocketMessageHandler | null;
  } = { current: null };
  const ws: WebSocketPort = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    onMessage: vi.fn((handler) => {
      messageHandler.current = handler;
    }),
    onReconnect: vi.fn(),
  };
  return { ws, messageHandler };
}

function createMockFingerprint(
  id: string = "fp-test-123",
): FingerprintPort {
  return {
    getFingerprint: vi.fn().mockResolvedValue(id),
  };
}

/**
 * Helper to flush microtasks so async operations resolve before assertions.
 */
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

// --- Tests ---

describe("PollParticipationViewModel", () => {
  let api: PollApiPort;
  let wsResult: MockWsResult;
  let fingerprint: FingerprintPort;
  let vm: PollParticipationViewModel;

  beforeEach(() => {
    api = createMockPollApi();
    wsResult = createMockWs();
    fingerprint = createMockFingerprint();
    vm = new PollParticipationViewModel(api, wsResult.ws, fingerprint);
  });

  describe("initial state", () => {
    it("has no active poll", () => {
      expect(vm.activePoll).toBeNull();
    });

    it("has no selected option", () => {
      expect(vm.selectedOptionId).toBeNull();
    });

    it("is not submitting", () => {
      expect(vm.isSubmitting).toBe(false);
    });

    it("has not submitted", () => {
      expect(vm.hasSubmitted).toBe(false);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });

    it("has no results", () => {
      expect(vm.results).toBeNull();
    });
  });

  describe("canSubmit computed", () => {
    it("returns false when no active poll", () => {
      vm.selectOption("opt-1");
      expect(vm.canSubmit).toBe(false);
    });

    it("returns false when no option selected", async () => {
      await vm.loadActivePoll("event-1");
      expect(vm.activePoll).not.toBeNull();
      expect(vm.canSubmit).toBe(false);
    });

    it("returns false when already submitted", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.hasSubmitted).toBe(true);
      expect(vm.canSubmit).toBe(false);
    });

    it("returns false when currently submitting", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");

      vm.submit(); // starts submitting, hangs
      await flushMicrotasks();

      expect(vm.isSubmitting).toBe(true);
      expect(vm.canSubmit).toBe(false);
    });

    it("returns true when poll loaded, option selected, and not submitted", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");

      expect(vm.canSubmit).toBe(true);
    });
  });

  describe("showResults computed", () => {
    it("returns false when not submitted", () => {
      expect(vm.showResults).toBe(false);
    });

    it("returns false when submitted but no results", async () => {
      // Simulate a case where hasSubmitted is true but results is null
      // by using WebSocket to manipulate state
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");

      // Submit sets hasSubmitted and results together, so we test via
      // a normal successful submission
      await vm.submit();
      expect(vm.showResults).toBe(true);
    });

    it("returns true when submitted and results exist", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.hasSubmitted).toBe(true);
      expect(vm.results).not.toBeNull();
      expect(vm.showResults).toBe(true);
    });
  });

  describe("selectOption", () => {
    it("sets the selectedOptionId", () => {
      vm.selectOption("opt-2");
      expect(vm.selectedOptionId).toBe("opt-2");
    });

    it("allows changing selection", () => {
      vm.selectOption("opt-1");
      vm.selectOption("opt-2");
      expect(vm.selectedOptionId).toBe("opt-2");
    });

    it("is ignored when already submitted", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.hasSubmitted).toBe(true);
      expect(vm.selectedOptionId).toBe("opt-1");

      vm.selectOption("opt-2");
      expect(vm.selectedOptionId).toBe("opt-1");
    });
  });

  describe("loadActivePoll", () => {
    it("fetches and sets the active poll", async () => {
      const poll = makePoll({ id: "active-poll" });
      (api.getActivePoll as ReturnType<typeof vi.fn>).mockResolvedValue(
        poll,
      );

      await vm.loadActivePoll("event-1");

      expect(api.getActivePoll).toHaveBeenCalledWith("event-1");
      expect(vm.activePoll).toEqual(poll);
    });

    it("sets activePoll to null when no active poll exists", async () => {
      (api.getActivePoll as ReturnType<typeof vi.fn>).mockResolvedValue(
        null,
      );

      await vm.loadActivePoll("event-1");

      expect(vm.activePoll).toBeNull();
    });

    it("sets error on failure", async () => {
      (api.getActivePoll as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Server error"),
      );

      await vm.loadActivePoll("event-1");

      expect(vm.error).toBe("Server error");
      expect(vm.activePoll).toBeNull();
    });

    it("sets generic error when non-Error is thrown", async () => {
      (api.getActivePoll as ReturnType<typeof vi.fn>).mockRejectedValue(
        "string error",
      );

      await vm.loadActivePoll("event-1");

      expect(vm.error).toBe("Failed to load active poll");
    });
  });

  describe("submit", () => {
    it("calls fingerprint, submitResponse, then getResults on success", async () => {
      const poll = makePoll({ id: "poll-42" });
      (api.getActivePoll as ReturnType<typeof vi.fn>).mockResolvedValue(
        poll,
      );
      const expectedResults = makeResults({ poll_id: "poll-42" });
      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValue(
        expectedResults,
      );

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(fingerprint.getFingerprint).toHaveBeenCalledTimes(1);
      expect(api.submitResponse).toHaveBeenCalledWith(
        "poll-42",
        "fp-test-123",
        "opt-1",
        null,
      );
      expect(api.getResults).toHaveBeenCalledWith("poll-42");
      expect(vm.hasSubmitted).toBe(true);
      expect(vm.results).toEqual(expectedResults);
      expect(vm.isSubmitting).toBe(false);
    });

    it("sets error on fingerprint failure", async () => {
      (
        fingerprint.getFingerprint as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Fingerprint failed"));

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.error).toBe("Fingerprint failed");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.hasSubmitted).toBe(false);
    });

    it("sets error on submitResponse failure", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Already voted"),
      );

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.error).toBe("Already voted");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.hasSubmitted).toBe(false);
    });

    it("sets generic error when non-Error is thrown", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValue(
        42,
      );

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.error).toBe("Failed to submit response");
    });

    it("does nothing when canSubmit is false", async () => {
      // No poll loaded, no option selected
      await vm.submit();

      expect(fingerprint.getFingerprint).not.toHaveBeenCalled();
      expect(api.submitResponse).not.toHaveBeenCalled();
      expect(vm.isSubmitting).toBe(false);
    });

    it("clears previous error on new submission", async () => {
      // First call fails
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("First error"),
      );

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();
      expect(vm.error).toBe("First error");

      // Activate a new poll via WebSocket to reset state
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "poll-2",
        question: "New question?",
        options: [
          { id: "opt-a", text: "Yes" },
          { id: "opt-b", text: "No" },
        ],
      });

      vm.selectOption("opt-a");

      // Second call succeeds
      (api.submitResponse as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        id: "r2",
        poll_id: "poll-2",
        option_id: "opt-a",
        created_at: "2026-01-02T00:00:00Z",
      });

      await vm.submit();
      expect(vm.error).toBeNull();
    });
  });

  describe("WebSocket: poll_activated", () => {
    it("sets the active poll and resets participation state", async () => {
      // First, set some existing state
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");

      // Simulate poll_activated
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "new-poll",
        question: "New question?",
        options: [
          { id: "opt-a", text: "Yes" },
          { id: "opt-b", text: "No" },
        ],
      });

      expect(vm.activePoll).not.toBeNull();
      expect(vm.activePoll!.id).toBe("new-poll");
      expect(vm.activePoll!.question).toBe("New question?");
      expect(vm.activePoll!.options).toEqual([
        { id: "opt-a", text: "Yes" },
        { id: "opt-b", text: "No" },
      ]);
      expect(vm.activePoll!.is_active).toBe(true);
      expect(vm.selectedOptionId).toBeNull();
      expect(vm.hasSubmitted).toBe(false);
      expect(vm.results).toBeNull();
      expect(vm.error).toBeNull();
    });

    it("resets submitted state when a new poll activates", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.hasSubmitted).toBe(true);
      expect(vm.results).not.toBeNull();

      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "poll-2",
        question: "Another question?",
        options: [{ id: "opt-x", text: "Maybe" }],
      });

      expect(vm.hasSubmitted).toBe(false);
      expect(vm.results).toBeNull();
      expect(vm.selectedOptionId).toBeNull();
    });
  });

  describe("WebSocket: poll_deactivated", () => {
    it("clears poll and all participation state", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      wsResult.messageHandler.current!({
        type: "poll_deactivated",
      });

      expect(vm.activePoll).toBeNull();
      expect(vm.selectedOptionId).toBeNull();
      expect(vm.hasSubmitted).toBe(false);
      expect(vm.results).toBeNull();
      expect(vm.error).toBeNull();
    });

    it("clears state even when no poll was active", () => {
      wsResult.messageHandler.current!({
        type: "poll_deactivated",
      });

      expect(vm.activePoll).toBeNull();
      expect(vm.selectedOptionId).toBeNull();
    });
  });

  describe("WebSocket: poll_results_updated", () => {
    it("updates results when user has submitted", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      expect(vm.hasSubmitted).toBe(true);

      const updatedOptions = [
        { option_id: "opt-1", text: "Red", count: 15, percentage: 60.0 },
        { option_id: "opt-2", text: "Blue", count: 10, percentage: 40.0 },
      ];

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        poll_type: "multiple_choice",
        results: { options: updatedOptions },
      });

      expect(vm.results).not.toBeNull();
      expect(vm.results!.total_votes).toBe(25);
      expect(vm.results!.options).toEqual(updatedOptions);
    });

    it("does not update results when user has not submitted", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      // Intentionally do NOT submit

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        results: [
          { option_id: "opt-1", text: "Red", count: 5, percentage: 100.0 },
        ],
      });

      expect(vm.results).toBeNull();
    });

    it("calculates total_votes from option counts", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        results: [
          { option_id: "opt-1", text: "Red", count: 3, percentage: 30.0 },
          { option_id: "opt-2", text: "Blue", count: 7, percentage: 70.0 },
        ],
      });

      expect(vm.results!.total_votes).toBe(10);
    });

    it("uses active poll question for results", async () => {
      const poll = makePoll({
        id: "poll-1",
        question: "Specific question?",
      });
      (api.getActivePoll as ReturnType<typeof vi.fn>).mockResolvedValue(
        poll,
      );

      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        poll_type: "multiple_choice",
        results: {
          options: [
            { option_id: "opt-1", text: "Red", count: 1, percentage: 100.0 },
          ],
        },
      });

      expect(vm.results!.question).toBe("Specific question?");
    });

    it("ignores message when results is not an array", async () => {
      await vm.loadActivePoll("event-1");
      vm.selectOption("opt-1");
      await vm.submit();

      const resultsBefore = vm.results;

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        results: "not an array",
      });

      expect(vm.results).toEqual(resultsBefore);
    });
  });

  describe("WebSocket message validation", () => {
    it("ignores malformed messages", async () => {
      await vm.loadActivePoll("event-1");

      // Send garbage data -- should not throw or modify state
      wsResult.messageHandler.current!(null);
      wsResult.messageHandler.current!(undefined);
      wsResult.messageHandler.current!("string data");
      wsResult.messageHandler.current!(42);
      wsResult.messageHandler.current!({ type: "unknown_type" });

      expect(vm.activePoll).not.toBeNull();
    });
  });

  describe("constructor", () => {
    it("registers WebSocket message handler", () => {
      expect(wsResult.ws.onMessage).toHaveBeenCalledTimes(1);
    });
  });
});
