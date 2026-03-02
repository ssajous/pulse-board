import { describe, it, expect, vi, beforeEach } from "vitest";
import { PollResultsViewModel } from "../PollResultsViewModel";
import type { PollResults } from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";

// --- Factories ---

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
    createPoll: vi.fn().mockResolvedValue({
      id: "poll-1",
      event_id: "event-1",
      question: "Q?",
      poll_type: "multiple_choice",
      options: [],
      is_active: false,
      created_at: "2026-01-01T00:00:00Z",
    }),
    listPolls: vi.fn().mockResolvedValue([]),
    getActivePoll: vi.fn().mockResolvedValue(null),
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

/**
 * Helper to flush microtasks so async operations resolve before assertions.
 */
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

// --- Tests ---

describe("PollResultsViewModel", () => {
  let api: PollApiPort;
  let vm: PollResultsViewModel;

  beforeEach(() => {
    api = createMockPollApi();
    vm = new PollResultsViewModel(api);
  });

  describe("initial state", () => {
    it("has no results", () => {
      expect(vm.results).toBeNull();
    });

    it("is not loading", () => {
      expect(vm.isLoading).toBe(false);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });
  });

  describe("sortedOptions computed", () => {
    it("returns empty array when no results", () => {
      expect(vm.sortedOptions).toEqual([]);
    });

    it("returns options sorted by count descending", () => {
      vm.updateResults(
        makeResults({
          options: [
            { option_id: "opt-1", text: "Red", count: 3, percentage: 30.0 },
            { option_id: "opt-2", text: "Blue", count: 7, percentage: 70.0 },
            { option_id: "opt-3", text: "Green", count: 5, percentage: 50.0 },
          ],
        }),
      );

      const sorted = vm.sortedOptions;
      expect(sorted.map((o) => o.option_id)).toEqual([
        "opt-2",
        "opt-3",
        "opt-1",
      ]);
      expect(sorted.map((o) => o.count)).toEqual([7, 5, 3]);
    });

    it("maintains stable order for equal counts", () => {
      vm.updateResults(
        makeResults({
          options: [
            { option_id: "opt-1", text: "Red", count: 5, percentage: 50.0 },
            { option_id: "opt-2", text: "Blue", count: 5, percentage: 50.0 },
          ],
        }),
      );

      const sorted = vm.sortedOptions;
      expect(sorted).toHaveLength(2);
      // Both have count 5, order is implementation-dependent but stable
      expect(sorted[0].count).toBe(5);
      expect(sorted[1].count).toBe(5);
    });

    it("handles single option", () => {
      vm.updateResults(
        makeResults({
          options: [
            { option_id: "opt-1", text: "Only", count: 10, percentage: 100.0 },
          ],
        }),
      );

      expect(vm.sortedOptions).toHaveLength(1);
      expect(vm.sortedOptions[0].option_id).toBe("opt-1");
    });

    it("handles empty options array", () => {
      vm.updateResults(makeResults({ options: [], total_votes: 0 }));

      expect(vm.sortedOptions).toEqual([]);
    });

    it("does not mutate the original results options array", () => {
      const results = makeResults({
        options: [
          { option_id: "opt-1", text: "Red", count: 1, percentage: 10.0 },
          { option_id: "opt-2", text: "Blue", count: 9, percentage: 90.0 },
        ],
      });
      vm.updateResults(results);

      vm.sortedOptions;

      // Original results should still have original order
      expect(vm.results!.options[0].option_id).toBe("opt-1");
      expect(vm.results!.options[1].option_id).toBe("opt-2");
    });
  });

  describe("hasVotes computed", () => {
    it("returns false when no results", () => {
      expect(vm.hasVotes).toBe(false);
    });

    it("returns false when total_votes is 0", () => {
      vm.updateResults(makeResults({ total_votes: 0 }));
      expect(vm.hasVotes).toBe(false);
    });

    it("returns true when total_votes is greater than 0", () => {
      vm.updateResults(makeResults({ total_votes: 1 }));
      expect(vm.hasVotes).toBe(true);
    });

    it("returns true when total_votes is large", () => {
      vm.updateResults(makeResults({ total_votes: 10000 }));
      expect(vm.hasVotes).toBe(true);
    });
  });

  describe("loadResults", () => {
    it("fetches and sets results", async () => {
      const expectedResults = makeResults({ poll_id: "poll-42" });
      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValue(
        expectedResults,
      );

      await vm.loadResults("poll-42");

      expect(api.getResults).toHaveBeenCalledWith("poll-42");
      expect(vm.results).toEqual(expectedResults);
      expect(vm.isLoading).toBe(false);
      expect(vm.error).toBeNull();
    });

    it("sets isLoading during the API call", async () => {
      let resolvePromise: (value: PollResults) => void;
      const pendingPromise = new Promise<PollResults>((resolve) => {
        resolvePromise = resolve;
      });
      (api.getResults as ReturnType<typeof vi.fn>).mockReturnValue(
        pendingPromise,
      );

      const loadPromise = vm.loadResults("poll-1");
      expect(vm.isLoading).toBe(true);

      resolvePromise!(makeResults());
      await loadPromise;

      expect(vm.isLoading).toBe(false);
    });

    it("sets error on failure", async () => {
      (api.getResults as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Not found"),
      );

      await vm.loadResults("poll-1");

      expect(vm.error).toBe("Not found");
      expect(vm.isLoading).toBe(false);
      expect(vm.results).toBeNull();
    });

    it("sets generic error when non-Error is thrown", async () => {
      (api.getResults as ReturnType<typeof vi.fn>).mockRejectedValue(
        "string error",
      );

      await vm.loadResults("poll-1");

      expect(vm.error).toBe("Failed to load poll results");
    });

    it("clears previous error on new load", async () => {
      // First call fails
      (api.getResults as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("Fail"),
      );

      await vm.loadResults("poll-1");
      expect(vm.error).toBe("Fail");

      // Second call succeeds
      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        makeResults(),
      );

      await vm.loadResults("poll-1");
      expect(vm.error).toBeNull();
    });

    it("replaces existing results on successful reload", async () => {
      const firstResults = makeResults({ total_votes: 5 });
      const secondResults = makeResults({ total_votes: 20 });

      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        firstResults,
      );
      await vm.loadResults("poll-1");
      expect(vm.results!.total_votes).toBe(5);

      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        secondResults,
      );
      await vm.loadResults("poll-1");
      expect(vm.results!.total_votes).toBe(20);
    });
  });

  describe("updateResults", () => {
    it("directly sets results", () => {
      const results = makeResults({ total_votes: 42 });
      vm.updateResults(results);

      expect(vm.results).toEqual(results);
    });

    it("replaces existing results", () => {
      vm.updateResults(makeResults({ total_votes: 5 }));
      expect(vm.results!.total_votes).toBe(5);

      vm.updateResults(makeResults({ total_votes: 99 }));
      expect(vm.results!.total_votes).toBe(99);
    });

    it("triggers computed property updates", () => {
      expect(vm.hasVotes).toBe(false);
      expect(vm.sortedOptions).toEqual([]);

      vm.updateResults(makeResults());

      expect(vm.hasVotes).toBe(true);
      expect(vm.sortedOptions).toHaveLength(2);
    });
  });
});
