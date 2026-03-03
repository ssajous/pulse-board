import { describe, it, expect, vi, beforeEach } from "vitest";
import { PollCreationViewModel } from "../PollCreationViewModel";
import type { Poll } from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";

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
    is_active: false,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function createMockPollApi(): PollApiPort {
  return {
    createPoll: vi.fn().mockResolvedValue(makePoll()),
    listPolls: vi.fn().mockResolvedValue([]),
    getActivePoll: vi.fn().mockResolvedValue(null),
    activatePoll: vi.fn().mockResolvedValue(undefined),
    submitResponse: vi.fn().mockResolvedValue({
      id: "r1",
      poll_id: "poll-1",
      option_id: "opt-1",
      created_at: "2026-01-01T00:00:00Z",
    }),
    getResults: vi.fn().mockResolvedValue({
      poll_id: "poll-1",
      question: "What is your favorite color?",
      total_votes: 0,
      options: [],
    }),
  };
}

/**
 * Helper to flush microtasks so async operations resolve before assertions.
 */
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

// --- Tests ---

describe("PollCreationViewModel", () => {
  let api: PollApiPort;
  let vm: PollCreationViewModel;

  beforeEach(() => {
    api = createMockPollApi();
    vm = new PollCreationViewModel(api);
  });

  describe("initial state", () => {
    it("has empty question", () => {
      expect(vm.question).toBe("");
    });

    it("has exactly 2 empty options", () => {
      expect(vm.options).toHaveLength(2);
      expect(vm.options[0]).toBe("");
      expect(vm.options[1]).toBe("");
    });

    it("is not submitting", () => {
      expect(vm.isSubmitting).toBe(false);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });

    it("has no created poll", () => {
      expect(vm.createdPoll).toBeNull();
    });
  });

  describe("isValid computed", () => {
    it("returns false when question is empty", () => {
      vm.setOptionText(0, "Option A");
      vm.setOptionText(1, "Option B");

      expect(vm.isValid).toBe(false);
    });

    it("returns false when question is only whitespace", () => {
      vm.setQuestion("   ");
      vm.setOptionText(0, "Option A");
      vm.setOptionText(1, "Option B");

      expect(vm.isValid).toBe(false);
    });

    it("returns false when question exceeds 500 characters", () => {
      vm.setQuestion("A".repeat(501));
      vm.setOptionText(0, "Option A");
      vm.setOptionText(1, "Option B");

      expect(vm.isValid).toBe(false);
    });

    it("returns true when question is exactly 500 characters", () => {
      vm.setQuestion("A".repeat(500));
      vm.setOptionText(0, "Option A");
      vm.setOptionText(1, "Option B");

      expect(vm.isValid).toBe(true);
    });

    it("returns false when any option text is empty", () => {
      vm.setQuestion("Valid question?");
      vm.setOptionText(0, "Option A");
      // option at index 1 is still empty

      expect(vm.isValid).toBe(false);
    });

    it("returns false when any option text is only whitespace", () => {
      vm.setQuestion("Valid question?");
      vm.setOptionText(0, "Option A");
      vm.setOptionText(1, "   ");

      expect(vm.isValid).toBe(false);
    });

    it("returns true when question and all options have text", () => {
      vm.setQuestion("Valid question?");
      vm.setOptionText(0, "Option A");
      vm.setOptionText(1, "Option B");

      expect(vm.isValid).toBe(true);
    });
  });

  describe("canAddOption computed", () => {
    it("returns true when fewer than 10 options", () => {
      expect(vm.options).toHaveLength(2);
      expect(vm.canAddOption).toBe(true);
    });

    it("returns true at 9 options", () => {
      // Start with 2, add 7 more to reach 9
      for (let i = 0; i < 7; i++) {
        vm.addOption();
      }
      expect(vm.options).toHaveLength(9);
      expect(vm.canAddOption).toBe(true);
    });

    it("returns false when at 10 options", () => {
      // Start with 2, add 8 more to reach 10
      for (let i = 0; i < 8; i++) {
        vm.addOption();
      }
      expect(vm.options).toHaveLength(10);
      expect(vm.canAddOption).toBe(false);
    });
  });

  describe("canRemoveOption computed", () => {
    it("returns false when at 2 options (minimum)", () => {
      expect(vm.options).toHaveLength(2);
      expect(vm.canRemoveOption).toBe(false);
    });

    it("returns true when more than 2 options", () => {
      vm.addOption();
      expect(vm.options).toHaveLength(3);
      expect(vm.canRemoveOption).toBe(true);
    });
  });

  describe("setQuestion", () => {
    it("updates the question", () => {
      vm.setQuestion("New question?");
      expect(vm.question).toBe("New question?");
    });

    it("allows setting empty string", () => {
      vm.setQuestion("Something");
      vm.setQuestion("");
      expect(vm.question).toBe("");
    });
  });

  describe("addOption", () => {
    it("adds an empty option string", () => {
      vm.addOption();
      expect(vm.options).toHaveLength(3);
      expect(vm.options[2]).toBe("");
    });

    it("does nothing when at max options", () => {
      for (let i = 0; i < 8; i++) {
        vm.addOption();
      }
      expect(vm.options).toHaveLength(10);

      vm.addOption();
      expect(vm.options).toHaveLength(10);
    });
  });

  describe("removeOption", () => {
    it("removes option at the given index", () => {
      vm.setOptionText(0, "Keep");
      vm.setOptionText(1, "Remove");
      vm.addOption();
      vm.setOptionText(2, "Also keep");

      vm.removeOption(1);

      expect(vm.options).toHaveLength(2);
      expect(vm.options[0]).toBe("Keep");
      expect(vm.options[1]).toBe("Also keep");
    });

    it("does nothing when at minimum options", () => {
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      vm.removeOption(0);

      expect(vm.options).toHaveLength(2);
      expect(vm.options[0]).toBe("A");
      expect(vm.options[1]).toBe("B");
    });
  });

  describe("setOptionText", () => {
    it("updates option text at the given index", () => {
      vm.setOptionText(0, "Updated");
      expect(vm.options[0]).toBe("Updated");
    });

    it("updates the last option", () => {
      vm.setOptionText(1, "Last option");
      expect(vm.options[1]).toBe("Last option");
    });

    it("ignores negative index", () => {
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      vm.setOptionText(-1, "Nope");

      expect(vm.options[0]).toBe("A");
      expect(vm.options[1]).toBe("B");
    });

    it("ignores out-of-bounds index", () => {
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      vm.setOptionText(5, "Nope");

      expect(vm.options).toHaveLength(2);
      expect(vm.options[0]).toBe("A");
      expect(vm.options[1]).toBe("B");
    });
  });

  describe("submit", () => {
    it("calls API with correct arguments and sets createdPoll", async () => {
      const expectedPoll = makePoll({ id: "new-poll" });
      (api.createPoll as ReturnType<typeof vi.fn>).mockResolvedValue(
        expectedPoll,
      );

      vm.setQuestion("  What is your favorite color?  ");
      vm.setOptionText(0, "  Red  ");
      vm.setOptionText(1, "  Blue  ");

      await vm.submit("event-1");

      expect(api.createPoll).toHaveBeenCalledWith("event-1", {
        question: "What is your favorite color?",
        options: ["Red", "Blue"],
      });
      expect(vm.createdPoll).toEqual(expectedPoll);
      expect(vm.isSubmitting).toBe(false);
      expect(vm.error).toBeNull();
    });

    it("sets isSubmitting during the API call", async () => {
      let resolvePromise: (value: Poll) => void;
      const pendingPromise = new Promise<Poll>((resolve) => {
        resolvePromise = resolve;
      });
      (api.createPoll as ReturnType<typeof vi.fn>).mockReturnValue(
        pendingPromise,
      );

      vm.setQuestion("Question?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      const submitPromise = vm.submit("event-1");
      expect(vm.isSubmitting).toBe(true);

      resolvePromise!(makePoll());
      await submitPromise;

      expect(vm.isSubmitting).toBe(false);
    });

    it("sets error on API failure", async () => {
      (api.createPoll as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Network error"),
      );

      vm.setQuestion("Question?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      await vm.submit("event-1");

      expect(vm.error).toBe("Network error");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.createdPoll).toBeNull();
    });

    it("sets generic error when non-Error is thrown", async () => {
      (api.createPoll as ReturnType<typeof vi.fn>).mockRejectedValue(
        "string error",
      );

      vm.setQuestion("Question?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      await vm.submit("event-1");

      expect(vm.error).toBe("Failed to create poll");
    });

    it("does nothing when form is invalid", async () => {
      // Question is empty, so isValid is false
      await vm.submit("event-1");

      expect(api.createPoll).not.toHaveBeenCalled();
      expect(vm.isSubmitting).toBe(false);
    });

    it("does nothing when already submitting", async () => {
      (api.createPoll as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );

      vm.setQuestion("Question?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      // Start first submit (will hang)
      vm.submit("event-1");
      expect(vm.isSubmitting).toBe(true);

      // Second submit should be a no-op
      await vm.submit("event-1");

      expect(api.createPoll).toHaveBeenCalledTimes(1);
    });

    it("clears previous error on new submission", async () => {
      // First call fails
      (api.createPoll as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("First fail"),
      );
      // Second call succeeds
      (api.createPoll as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        makePoll(),
      );

      vm.setQuestion("Question?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");

      await vm.submit("event-1");
      expect(vm.error).toBe("First fail");

      await vm.submit("event-1");
      expect(vm.error).toBeNull();
    });
  });

  describe("reset", () => {
    it("clears all state back to initial values", async () => {
      vm.setQuestion("Question?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");
      vm.addOption();
      vm.setOptionText(2, "C");

      await vm.submit("event-1");
      await flushMicrotasks();

      // Verify state was modified
      expect(vm.createdPoll).not.toBeNull();

      vm.reset();

      expect(vm.question).toBe("");
      expect(vm.options).toEqual(["", ""]);
      expect(vm.isSubmitting).toBe(false);
      expect(vm.error).toBeNull();
      expect(vm.createdPoll).toBeNull();
    });

    it("clears error state", async () => {
      (api.createPoll as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Fail"),
      );

      vm.setQuestion("Q?");
      vm.setOptionText(0, "A");
      vm.setOptionText(1, "B");
      await vm.submit("event-1");

      expect(vm.error).toBe("Fail");

      vm.reset();

      expect(vm.error).toBeNull();
    });
  });
});
