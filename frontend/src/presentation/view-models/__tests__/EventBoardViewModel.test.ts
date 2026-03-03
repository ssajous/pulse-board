import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { EventBoardViewModel } from "../EventBoardViewModel";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { Event } from "@domain/entities/Event";

// --- Mock infrastructure dependencies ---
// The mocks must use function constructors (not arrow functions)
// so they work with the `new` keyword in the source code.

vi.mock("@infrastructure/api/eventTopicApiClient", () => ({
  EventTopicApiClient: vi.fn().mockImplementation(function () {
    return {
      fetchTopics: vi.fn().mockResolvedValue([]),
      createTopic: vi.fn(),
    };
  }),
}));

vi.mock("@infrastructure/api/voteApiClient", () => ({
  VoteApiClient: vi.fn().mockImplementation(function () {
    return {
      castVote: vi.fn(),
    };
  }),
}));

vi.mock("@infrastructure/api/pollApiClient", () => ({
  PollApiClient: vi.fn().mockImplementation(function () {
    return {
      createPoll: vi.fn(),
      listPolls: vi.fn().mockResolvedValue([]),
      getActivePoll: vi.fn().mockResolvedValue(null),
      activatePoll: vi.fn(),
      submitResponse: vi.fn(),
      getResults: vi.fn(),
    };
  }),
}));

vi.mock("@infrastructure/fingerprint/fingerprintService", () => ({
  FingerprintService: vi.fn().mockImplementation(function () {
    return {
      getFingerprint: vi.fn().mockResolvedValue("mock-fp-id"),
    };
  }),
}));

vi.mock("@infrastructure/websocket", () => ({
  WebSocketClient: vi.fn().mockImplementation(function () {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      onMessage: vi.fn(),
      onReconnect: vi.fn(),
    };
  }),
  buildWebSocketUrl: vi.fn().mockReturnValue("ws://localhost:8000/ws/test"),
}));

vi.mock("@infrastructure/logger", () => ({
  logger: {
    log: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@infrastructure/utils/typeGuards", () => ({
  isRecord: vi.fn().mockReturnValue(false),
  extractErrorMessage: vi.fn().mockReturnValue("error"),
}));

// Stub window.location for buildEventWebSocketUrl()
// and provide a default no-op localStorage for all tests.
beforeEach(() => {
  Object.defineProperty(globalThis, "window", {
    value: {
      location: {
        protocol: "http:",
        host: "localhost:8000",
      },
    },
    writable: true,
    configurable: true,
  });

  // Default localStorage stub: returns null for every key.
  // Individual tests override this with vi.stubGlobal as needed.
  vi.stubGlobal("localStorage", {
    getItem: vi.fn().mockReturnValue(null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// --- Factories ---

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    id: "evt-1",
    title: "Test Event",
    code: "123456",
    description: null,
    start_date: null,
    end_date: null,
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function createMockEventApi(): EventApiPort {
  return {
    createEvent: vi.fn().mockResolvedValue(makeEvent()),
    getEventByCode: vi.fn().mockResolvedValue(makeEvent()),
    getEventById: vi.fn().mockResolvedValue(makeEvent()),
    checkCreator: vi
      .fn()
      .mockResolvedValue({ is_creator: false }),
  };
}

/**
 * Helper to flush microtasks so async operations
 * (including chained .then() calls) resolve before assertions.
 */
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

// --- Tests ---

describe("EventBoardViewModel", () => {
  let api: EventApiPort;
  let vm: EventBoardViewModel;

  beforeEach(() => {
    api = createMockEventApi();
    vm = new EventBoardViewModel(api);
  });

  describe("initial state", () => {
    it("has null event", () => {
      expect(vm.event).toBeNull();
    });

    it("is loading", () => {
      expect(vm.isLoading).toBe(true);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });

    it("isCreator defaults to false", () => {
      expect(vm.isCreator).toBe(false);
    });

    it("has null topicsViewModel", () => {
      expect(vm.topicsViewModel).toBeNull();
    });

    it("has null pollParticipationViewModel", () => {
      expect(vm.pollParticipationViewModel).toBeNull();
    });
  });

  describe("resolveEvent", () => {
    it("sets event and stops loading on success", async () => {
      const event = makeEvent({ id: "evt-2", code: "654321" });
      (
        api.getEventByCode as ReturnType<typeof vi.fn>
      ).mockResolvedValue(event);

      await vm.resolveEvent("654321");

      expect(vm.event).toEqual(event);
      expect(vm.isLoading).toBe(false);
      expect(vm.error).toBeNull();
    });

    it("creates topicsViewModel on success", async () => {
      await vm.resolveEvent("123456");

      expect(vm.topicsViewModel).not.toBeNull();
    });

    it("creates pollParticipationViewModel on success", async () => {
      await vm.resolveEvent("123456");

      expect(vm.pollParticipationViewModel).not.toBeNull();
    });

    it("sets error on API failure", async () => {
      (
        api.getEventByCode as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Not found"));

      await vm.resolveEvent("bad-code");

      expect(vm.error).toBe("Not found");
      expect(vm.isLoading).toBe(false);
      expect(vm.event).toBeNull();
    });

    it("sets generic error when non-Error is thrown", async () => {
      (
        api.getEventByCode as ReturnType<typeof vi.fn>
      ).mockRejectedValue("string error");

      await vm.resolveEvent("bad-code");

      expect(vm.error).toBe("Failed to load event");
    });

    it("sets isCreator to true when checkCreator returns true", async () => {
      const mockLocalStorage = {
        getItem: vi.fn((key: string) =>
          key === "creator_token:123456"
            ? "stored-creator-token"
            : null,
        ),
      };
      vi.stubGlobal("localStorage", mockLocalStorage);

      (
        api.checkCreator as ReturnType<typeof vi.fn>
      ).mockResolvedValue({ is_creator: true });

      await vm.resolveEvent("123456");
      await flushMicrotasks();
      await flushMicrotasks();

      expect(api.checkCreator).toHaveBeenCalledWith(
        "evt-1",
        "stored-creator-token",
      );
      expect(vm.isCreator).toBe(true);
    });

    it("sets isCreator to false when checkCreator returns false", async () => {
      const mockLocalStorage = {
        getItem: vi.fn((key: string) =>
          key === "creator_token:123456"
            ? "stored-creator-token"
            : null,
        ),
      };
      vi.stubGlobal("localStorage", mockLocalStorage);

      (
        api.checkCreator as ReturnType<typeof vi.fn>
      ).mockResolvedValue({ is_creator: false });

      await vm.resolveEvent("123456");
      await flushMicrotasks();
      await flushMicrotasks();

      expect(vm.isCreator).toBe(false);
    });

    it("keeps isCreator false when checkCreator rejects", async () => {
      const mockLocalStorage = {
        getItem: vi.fn((key: string) =>
          key === "creator_token:123456"
            ? "stored-creator-token"
            : null,
        ),
      };
      vi.stubGlobal("localStorage", mockLocalStorage);

      (
        api.checkCreator as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Auth error"));

      await vm.resolveEvent("123456");
      await flushMicrotasks();
      await flushMicrotasks();

      expect(vm.isCreator).toBe(false);
    });

    it("keeps isCreator false when no creator_token in localStorage", async () => {
      // No token stored — checkCreator should never be called
      vi.stubGlobal("localStorage", {
        getItem: vi.fn().mockReturnValue(null),
      });

      await vm.resolveEvent("123456");
      await flushMicrotasks();
      await flushMicrotasks();

      expect(api.checkCreator).not.toHaveBeenCalled();
      expect(vm.isCreator).toBe(false);
    });

    it("calls getEventByCode with the code parameter", async () => {
      await vm.resolveEvent("999999");

      expect(api.getEventByCode).toHaveBeenCalledWith("999999");
    });
  });

  describe("dispose", () => {
    it("resets isCreator to false", async () => {
      vi.stubGlobal("localStorage", {
        getItem: vi.fn((key: string) =>
          key === "creator_token:123456"
            ? "stored-creator-token"
            : null,
        ),
      });
      (
        api.checkCreator as ReturnType<typeof vi.fn>
      ).mockResolvedValue({ is_creator: true });

      await vm.resolveEvent("123456");
      await flushMicrotasks();
      await flushMicrotasks();

      expect(vm.isCreator).toBe(true);

      vm.dispose();

      expect(vm.isCreator).toBe(false);
    });

    it("nullifies topicsViewModel", async () => {
      await vm.resolveEvent("123456");
      expect(vm.topicsViewModel).not.toBeNull();

      vm.dispose();

      expect(vm.topicsViewModel).toBeNull();
    });

    it("nullifies pollParticipationViewModel", async () => {
      await vm.resolveEvent("123456");
      expect(vm.pollParticipationViewModel).not.toBeNull();

      vm.dispose();

      expect(vm.pollParticipationViewModel).toBeNull();
    });

    it("is safe to call multiple times", () => {
      vm.dispose();
      vm.dispose();

      expect(vm.isCreator).toBe(false);
      expect(vm.topicsViewModel).toBeNull();
      expect(vm.pollParticipationViewModel).toBeNull();
    });
  });
});
