import { describe, it, expect, vi, beforeEach } from "vitest";
import { WordCloudViewModel } from "../WordCloudViewModel";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";
import type {
  WordCloudPollResults,
  WordFrequency,
} from "@domain/entities/Poll";

// --- Factories ---

function makeWordCloudResults(
  overrides: Partial<WordCloudPollResults> = {},
): WordCloudPollResults {
  return {
    poll_id: "poll-1",
    question: "What comes to mind?",
    total_responses: 5,
    frequencies: [
      { text: "hello", count: 3 },
      { text: "world", count: 2 },
    ],
    ...overrides,
  };
}

function createMockPollApi(): PollApiPort {
  return {
    createPoll: vi.fn().mockResolvedValue({}),
    listPolls: vi.fn().mockResolvedValue([]),
    getActivePoll: vi.fn().mockResolvedValue(null),
    activatePoll: vi.fn().mockResolvedValue(undefined),
    submitResponse: vi.fn().mockResolvedValue({
      id: "r1",
      poll_id: "poll-1",
      option_id: null,
      created_at: "2026-01-01T00:00:00Z",
    }),
    getResults: vi.fn().mockResolvedValue(makeWordCloudResults()),
  };
}

function createMockFingerprint(id: string = "fp-test-123"): FingerprintPort {
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

describe("WordCloudViewModel", () => {
  let api: PollApiPort;
  let fingerprint: FingerprintPort;
  let vm: WordCloudViewModel;

  beforeEach(() => {
    api = createMockPollApi();
    fingerprint = createMockFingerprint();
    vm = new WordCloudViewModel(api, fingerprint);
  });

  describe("initial state", () => {
    it("has empty inputText", () => {
      expect(vm.inputText).toBe("");
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

    it("has empty frequencies", () => {
      expect(vm.frequencies).toEqual([]);
    });

    it("has totalResponses of 0", () => {
      expect(vm.totalResponses).toBe(0);
    });
  });

  describe("wordCount computed", () => {
    it("returns 0 for empty string", () => {
      vm.setInputText("");
      expect(vm.wordCount).toBe(0);
    });

    it("returns 0 for whitespace only", () => {
      vm.setInputText("   ");
      expect(vm.wordCount).toBe(0);
    });

    it("returns 1 for a single word", () => {
      vm.setInputText("hello");
      expect(vm.wordCount).toBe(1);
    });

    it("returns 2 for two words", () => {
      vm.setInputText("hello world");
      expect(vm.wordCount).toBe(2);
    });

    it("returns 3 for three words", () => {
      vm.setInputText("one two three");
      expect(vm.wordCount).toBe(3);
    });

    it("counts correctly despite extra spaces between words", () => {
      vm.setInputText("one  two");
      expect(vm.wordCount).toBe(2);
    });
  });

  describe("isInputValid computed", () => {
    it("returns false for empty input", () => {
      vm.setInputText("");
      expect(vm.isInputValid).toBe(false);
    });

    it("returns false for whitespace only", () => {
      vm.setInputText("   ");
      expect(vm.isInputValid).toBe(false);
    });

    it("returns true for 1 word under 30 chars", () => {
      vm.setInputText("hello");
      expect(vm.isInputValid).toBe(true);
    });

    it("returns true for 2 words under 30 chars", () => {
      vm.setInputText("hello world");
      expect(vm.isInputValid).toBe(true);
    });

    it("returns true for 3 words under 30 chars", () => {
      vm.setInputText("one two three");
      expect(vm.isInputValid).toBe(true);
    });

    it("returns false for more than 3 words", () => {
      vm.setInputText("one two three four");
      expect(vm.isInputValid).toBe(false);
    });

    it("returns false when text exceeds 30 chars after trim", () => {
      // setInputText truncates to 30, so we directly set inputText via setInputText
      // But since setInputText slices at 30, text will already be truncated.
      // We test with exactly 30 chars (valid) vs > 30 (truncated by setter before validation).
      // The limit is enforced by setInputText, so isInputValid will only see <= 30 chars.
      // Test with 30 chars exactly (valid).
      vm.setInputText("a".repeat(30));
      expect(vm.isInputValid).toBe(true);
    });

    it("setInputText truncates text so isInputValid never sees >30 chars", () => {
      vm.setInputText("a".repeat(35));
      // After truncation to 30, it's one "word" of 30 chars — valid
      expect(vm.inputText.length).toBe(30);
      expect(vm.isInputValid).toBe(true);
    });
  });

  describe("isSubmitDisabled computed", () => {
    it("returns true when input is invalid (empty)", () => {
      expect(vm.isSubmitDisabled).toBe(true);
    });

    it("returns true when input has too many words", () => {
      vm.setInputText("one two three four");
      expect(vm.isSubmitDisabled).toBe(true);
    });

    it("returns true when isSubmitting is true", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );

      vm.setInputText("hello world");
      vm.submitResponse("poll-1"); // starts submitting, hangs
      await flushMicrotasks();

      expect(vm.isSubmitting).toBe(true);
      expect(vm.isSubmitDisabled).toBe(true);
    });

    it("returns true when hasSubmitted is true", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.hasSubmitted).toBe(true);
      expect(vm.isSubmitDisabled).toBe(true);
    });

    it("returns false when input is valid and not submitting or submitted", () => {
      vm.setInputText("hello world");
      expect(vm.isSubmitDisabled).toBe(false);
    });
  });

  describe("wordCountDisplay computed", () => {
    it("shows '0/3 words' initially", () => {
      expect(vm.wordCountDisplay).toBe("0/3 words");
    });

    it("shows '1/3 words' after entering one word", () => {
      vm.setInputText("hello");
      expect(vm.wordCountDisplay).toBe("1/3 words");
    });

    it("shows '2/3 words' after entering two words", () => {
      vm.setInputText("hello world");
      expect(vm.wordCountDisplay).toBe("2/3 words");
    });

    it("shows '3/3 words' after entering three words", () => {
      vm.setInputText("one two three");
      expect(vm.wordCountDisplay).toBe("3/3 words");
    });
  });

  describe("setInputText", () => {
    it("sets inputText to the provided value", () => {
      vm.setInputText("hello");
      expect(vm.inputText).toBe("hello");
    });

    it("truncates text at 30 characters", () => {
      const longText = "a".repeat(50);
      vm.setInputText(longText);
      expect(vm.inputText.length).toBe(30);
      expect(vm.inputText).toBe("a".repeat(30));
    });

    it("allows text of exactly 30 characters", () => {
      const exactText = "a".repeat(30);
      vm.setInputText(exactText);
      expect(vm.inputText).toBe(exactText);
    });

    it("allows empty string", () => {
      vm.setInputText("hello");
      vm.setInputText("");
      expect(vm.inputText).toBe("");
    });
  });

  describe("submitResponse", () => {
    it("calls fingerprint and submitResponse with correct params", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-42");

      expect(fingerprint.getFingerprint).toHaveBeenCalledTimes(1);
      expect(api.submitResponse).toHaveBeenCalledWith(
        "poll-42",
        "fp-test-123",
        null,
        "hello world",
      );
    });

    it("trims whitespace from inputText before submitting", async () => {
      vm.setInputText("  hello  ");
      await vm.submitResponse("poll-1");

      expect(api.submitResponse).toHaveBeenCalledWith(
        "poll-1",
        "fp-test-123",
        null,
        "hello",
      );
    });

    it("sets hasSubmitted to true after successful submission", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.hasSubmitted).toBe(true);
    });

    it("sets isSubmitting back to false after successful submission", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.isSubmitting).toBe(false);
    });

    it("fetches results after successful submission", async () => {
      const results = makeWordCloudResults({
        frequencies: [{ text: "test", count: 1 }],
        total_responses: 1,
      });
      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValue(results);

      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(api.getResults).toHaveBeenCalledWith("poll-1");
      expect(vm.frequencies).toEqual([{ text: "test", count: 1 }]);
      expect(vm.totalResponses).toBe(1);
    });

    it("updates frequencies and totalResponses from fetched results", async () => {
      const words: WordFrequency[] = [
        { text: "alpha", count: 5 },
        { text: "beta", count: 3 },
      ];
      const results = makeWordCloudResults({
        frequencies: words,
        total_responses: 8,
      });
      (api.getResults as ReturnType<typeof vi.fn>).mockResolvedValue(results);

      vm.setInputText("alpha beta");
      await vm.submitResponse("poll-1");

      expect(vm.frequencies).toEqual(words);
      expect(vm.totalResponses).toBe(8);
    });

    it("sets error message on fingerprint failure", async () => {
      (
        fingerprint.getFingerprint as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Fingerprint unavailable"));

      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.error).toBe("Fingerprint unavailable");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.hasSubmitted).toBe(false);
    });

    it("sets error message on submitResponse failure", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Already voted"),
      );

      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.error).toBe("Already voted");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.hasSubmitted).toBe(false);
    });

    it("sets generic error when non-Error is thrown", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValue(
        "some string error",
      );

      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.error).toBe("Failed to submit response");
    });

    it("does nothing when isSubmitDisabled is true (empty input)", async () => {
      await vm.submitResponse("poll-1");

      expect(fingerprint.getFingerprint).not.toHaveBeenCalled();
      expect(api.submitResponse).not.toHaveBeenCalled();
    });

    it("does nothing when already submitted", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      const submitCallCount = (api.submitResponse as ReturnType<typeof vi.fn>)
        .mock.calls.length;

      await vm.submitResponse("poll-1");

      expect(
        (api.submitResponse as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBe(submitCallCount);
    });

    it("clears previous error before submitting", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error("First error"),
      );

      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");
      expect(vm.error).toBe("First error");

      // Reset state manually so we can submit again
      vm.reset();
      vm.setInputText("new text");

      (api.submitResponse as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        id: "r2",
        poll_id: "poll-1",
        option_id: null,
        created_at: "2026-01-02T00:00:00Z",
      });

      await vm.submitResponse("poll-1");
      expect(vm.error).toBeNull();
    });
  });

  describe("handleWordCloudUpdated", () => {
    it("updates frequencies from WebSocket data", () => {
      const words = [
        { text: "apple", count: 4 },
        { text: "banana", count: 2 },
      ];
      vm.handleWordCloudUpdated({ total_responses: 6, frequencies: words });

      expect(vm.frequencies).toEqual(words);
    });

    it("updates totalResponses from WebSocket data", () => {
      vm.handleWordCloudUpdated({
        total_responses: 42,
        frequencies: [{ text: "foo", count: 42 }],
      });

      expect(vm.totalResponses).toBe(42);
    });

    it("handles empty words array", () => {
      vm.handleWordCloudUpdated({ total_responses: 0, frequencies: [] });

      expect(vm.frequencies).toEqual([]);
      expect(vm.totalResponses).toBe(0);
    });

    it("replaces existing frequencies with new data", () => {
      vm.handleWordCloudUpdated({
        total_responses: 3,
        frequencies: [{ text: "old", count: 3 }],
      });

      vm.handleWordCloudUpdated({
        total_responses: 5,
        frequencies: [
          { text: "new1", count: 3 },
          { text: "new2", count: 2 },
        ],
      });

      expect(vm.frequencies).toEqual([
        { text: "new1", count: 3 },
        { text: "new2", count: 2 },
      ]);
      expect(vm.totalResponses).toBe(5);
    });
  });

  describe("updateFromResults", () => {
    it("updates frequencies from API results", () => {
      const frequencies: WordFrequency[] = [
        { text: "cloud", count: 10 },
        { text: "data", count: 5 },
      ];
      const results = makeWordCloudResults({ frequencies, total_responses: 15 });

      vm.updateFromResults(results);

      expect(vm.frequencies).toEqual(frequencies);
    });

    it("updates totalResponses from API results", () => {
      const results = makeWordCloudResults({ total_responses: 99 });

      vm.updateFromResults(results);

      expect(vm.totalResponses).toBe(99);
    });

    it("handles empty frequencies in results", () => {
      const results = makeWordCloudResults({
        frequencies: [],
        total_responses: 0,
      });

      vm.updateFromResults(results);

      expect(vm.frequencies).toEqual([]);
      expect(vm.totalResponses).toBe(0);
    });

    it("replaces existing frequencies with new results", () => {
      vm.updateFromResults(
        makeWordCloudResults({
          frequencies: [{ text: "old", count: 3 }],
          total_responses: 3,
        }),
      );

      const newFrequencies: WordFrequency[] = [{ text: "fresh", count: 7 }];
      vm.updateFromResults(
        makeWordCloudResults({
          frequencies: newFrequencies,
          total_responses: 7,
        }),
      );

      expect(vm.frequencies).toEqual(newFrequencies);
      expect(vm.totalResponses).toBe(7);
    });
  });

  describe("reset", () => {
    it("resets inputText to empty string", async () => {
      vm.setInputText("some text");
      await vm.submitResponse("poll-1");

      vm.reset();

      expect(vm.inputText).toBe("");
    });

    it("resets isSubmitting to false", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );
      vm.setInputText("hello world");
      vm.submitResponse("poll-1");
      await flushMicrotasks();

      expect(vm.isSubmitting).toBe(true);

      vm.reset();

      expect(vm.isSubmitting).toBe(false);
    });

    it("resets hasSubmitted to false", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.hasSubmitted).toBe(true);

      vm.reset();

      expect(vm.hasSubmitted).toBe(false);
    });

    it("resets error to null", async () => {
      (api.submitResponse as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Some error"),
      );
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");

      expect(vm.error).toBe("Some error");

      vm.reset();

      expect(vm.error).toBeNull();
    });

    it("resets frequencies to empty array", () => {
      vm.updateFromResults(
        makeWordCloudResults({
          frequencies: [{ text: "word", count: 5 }],
        }),
      );

      vm.reset();

      expect(vm.frequencies).toEqual([]);
    });

    it("resets totalResponses to 0", () => {
      vm.updateFromResults(makeWordCloudResults({ total_responses: 42 }));

      vm.reset();

      expect(vm.totalResponses).toBe(0);
    });

    it("resets all state to initial values", async () => {
      vm.setInputText("hello world");
      await vm.submitResponse("poll-1");
      vm.updateFromResults(makeWordCloudResults({ total_responses: 10 }));

      vm.reset();

      expect(vm.inputText).toBe("");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.hasSubmitted).toBe(false);
      expect(vm.error).toBeNull();
      expect(vm.frequencies).toEqual([]);
      expect(vm.totalResponses).toBe(0);
    });
  });
});
