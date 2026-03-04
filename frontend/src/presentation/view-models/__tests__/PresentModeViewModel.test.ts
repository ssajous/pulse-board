import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { PresentModeViewModel } from "../PresentModeViewModel";
import type { Event } from "@domain/entities/Event";
import type {
  PresentActivePoll,
  PresentState,
  PresentTopic,
} from "@domain/entities/PresentState";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { PresentStateApiPort } from "@domain/ports/PresentStateApiPort";
import type {
  WebSocketPort,
  WebSocketMessageHandler,
} from "@domain/ports/WebSocketPort";

// --- Browser globals mock (Node environment has no window/localStorage) ---

// Mock window.location so PresentModeViewModel.buildWebSocketUrl works in Node
Object.defineProperty(globalThis, "window", {
  value: {
    location: {
      protocol: "http:",
      host: "localhost",
    },
  },
  writable: true,
});

const localStorageStore: Record<string, string> = {};
const mockLocalStorage = {
  getItem: vi.fn((key: string): string | null => localStorageStore[key] ?? null),
  setItem: vi.fn((key: string, value: string): void => {
    localStorageStore[key] = value;
  }),
  removeItem: vi.fn((key: string): void => {
    delete localStorageStore[key];
  }),
  clear: vi.fn((): void => {
    Object.keys(localStorageStore).forEach((k) => delete localStorageStore[k]);
  }),
  length: 0,
  key: vi.fn((): string | null => null),
};

Object.defineProperty(globalThis, "localStorage", {
  value: mockLocalStorage,
  writable: true,
});

// --- Factories ---

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    id: "event-1",
    title: "Test Event",
    code: "ABC123",
    description: null,
    start_date: null,
    end_date: null,
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makePresentState(
  overrides: Partial<PresentState> = {},
): PresentState {
  return {
    active_poll: null,
    top_topics: [],
    participant_count: 0,
    ...overrides,
  };
}

function makePresentActivePoll(
  overrides: Partial<PresentActivePoll> = {},
): PresentActivePoll {
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

function makePresentTopic(overrides: Partial<PresentTopic> = {}): PresentTopic {
  return {
    id: "topic-1",
    content: "Sample topic",
    score: 5,
    ...overrides,
  };
}

function createMockEventApi(): EventApiPort {
  return {
    createEvent: vi.fn().mockResolvedValue(makeEvent()),
    getEventByCode: vi.fn().mockResolvedValue(makeEvent()),
    getEventById: vi.fn().mockResolvedValue(makeEvent()),
    checkCreator: vi.fn().mockResolvedValue({ is_creator: true }),
  };
}

function createMockPresentStateApi(): PresentStateApiPort {
  return {
    getPresentState: vi.fn().mockResolvedValue(makePresentState()),
  };
}

interface MockWsResult {
  ws: WebSocketPort;
  messageHandler: { current: WebSocketMessageHandler | null };
  reconnectHandler: { current: (() => void) | null };
}

function createMockWs(): MockWsResult {
  const messageHandler: { current: WebSocketMessageHandler | null } = {
    current: null,
  };
  const reconnectHandler: { current: (() => void) | null } = {
    current: null,
  };
  const ws: WebSocketPort = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    onMessage: vi.fn((handler) => {
      messageHandler.current = handler;
    }),
    onReconnect: vi.fn((handler) => {
      reconnectHandler.current = handler;
    }),
  };
  return { ws, messageHandler, reconnectHandler };
}

/**
 * Helper to flush microtasks so async operations resolve before assertions.
 */
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

// --- Tests ---

describe("PresentModeViewModel", () => {
  let eventApi: EventApiPort;
  let presentStateApi: PresentStateApiPort;
  let wsResult: MockWsResult;
  let vm: PresentModeViewModel;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear();
    // Reset getItem to return null by default (dark theme)
    mockLocalStorage.getItem.mockImplementation(
      (): string | null => null,
    );

    eventApi = createMockEventApi();
    presentStateApi = createMockPresentStateApi();
    wsResult = createMockWs();
    vm = new PresentModeViewModel(
      eventApi,
      presentStateApi,
      wsResult.ws,
    );
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("has no event", () => {
      expect(vm.event).toBeNull();
    });

    it("is not loading", () => {
      expect(vm.isLoading).toBe(false);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });

    it("has no active poll", () => {
      expect(vm.activePoll).toBeNull();
    });

    it("has empty top topics", () => {
      expect(vm.topTopics).toEqual([]);
    });

    it("has zero participant count", () => {
      expect(vm.participantCount).toBe(0);
    });

    it("defaults to dark theme when localStorage returns null", () => {
      expect(vm.isDarkTheme).toBe(true);
    });
  });

  describe("initialize(code)", () => {
    it("fetches event by code then present state by event id", async () => {
      const event = makeEvent({ id: "event-42", code: "XYZ" });
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockResolvedValue(event);

      await vm.initialize("XYZ");

      expect(eventApi.getEventByCode).toHaveBeenCalledWith("XYZ");
      expect(presentStateApi.getPresentState).toHaveBeenCalledWith("event-42");
    });

    it("sets event, activePoll, topTopics, participantCount from fetched data", async () => {
      const event = makeEvent({ id: "event-1" });
      const activePoll = makePresentActivePoll();
      const topics = [
        makePresentTopic({ id: "t1", score: 10 }),
        makePresentTopic({ id: "t2", score: 5 }),
      ];
      const state = makePresentState({
        active_poll: activePoll,
        top_topics: topics,
        participant_count: 42,
      });

      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockResolvedValue(event);
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      await vm.initialize("ABC123");

      expect(vm.event).toEqual(event);
      expect(vm.activePoll).toEqual(activePoll);
      expect(vm.topTopics).toEqual(topics);
      expect(vm.participantCount).toBe(42);
    });

    it("sets isLoading to false after success", async () => {
      await vm.initialize("ABC123");

      expect(vm.isLoading).toBe(false);
    });

    it("sets isLoading to true during fetch, false after", async () => {
      let loadingDuringFetch = false;
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockImplementation(async () => {
        loadingDuringFetch = vm.isLoading;
        return makeEvent();
      });

      await vm.initialize("ABC123");

      expect(loadingDuringFetch).toBe(true);
      expect(vm.isLoading).toBe(false);
    });

    it("sets error on failure", async () => {
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Network error"));

      await vm.initialize("ABC123");

      expect(vm.error).toBe("Network error");
      expect(vm.isLoading).toBe(false);
    });

    it("sets generic error message when non-Error is thrown", async () => {
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockRejectedValue("string error");

      await vm.initialize("ABC123");

      expect(vm.error).toBe("Failed to load present mode");
    });

    it("connects WebSocket to correct URL", async () => {
      // window.location is pre-mocked as http://localhost at module level
      await vm.initialize("ABC123");

      expect(wsResult.ws.connect).toHaveBeenCalledWith(
        "ws://localhost/ws/events/ABC123",
      );
    });

    it("registers onMessage and onReconnect handlers", async () => {
      await vm.initialize("ABC123");

      expect(wsResult.ws.onMessage).toHaveBeenCalledTimes(1);
      expect(wsResult.ws.onReconnect).toHaveBeenCalledTimes(1);
    });
  });

  describe("toggleTheme()", () => {
    it("flips isDarkTheme from true to false", () => {
      expect(vm.isDarkTheme).toBe(true);

      vm.toggleTheme();

      expect(vm.isDarkTheme).toBe(false);
    });

    it("flips isDarkTheme from false to true", () => {
      vm.toggleTheme(); // dark -> light
      expect(vm.isDarkTheme).toBe(false);

      vm.toggleTheme(); // light -> dark
      expect(vm.isDarkTheme).toBe(true);
    });

    it("writes 'light' to localStorage when dark to light", () => {
      expect(vm.isDarkTheme).toBe(true);

      vm.toggleTheme();

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "present-mode-theme",
        "light",
      );
    });

    it("writes 'dark' to localStorage when light to dark", () => {
      vm.toggleTheme(); // dark -> light, first call

      mockLocalStorage.setItem.mockClear();

      vm.toggleTheme(); // light -> dark

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "present-mode-theme",
        "dark",
      );
    });
  });

  describe("theme persistence", () => {
    it("defaults to dark theme when localStorage returns null", () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const freshVm = new PresentModeViewModel(
        createMockEventApi(),
        createMockPresentStateApi(),
      );

      expect(freshVm.isDarkTheme).toBe(true);
    });

    it("sets light theme when localStorage returns 'light'", () => {
      mockLocalStorage.getItem.mockReturnValue("light");

      const freshVm = new PresentModeViewModel(
        createMockEventApi(),
        createMockPresentStateApi(),
      );

      expect(freshVm.isDarkTheme).toBe(false);
    });

    it("sets dark theme when localStorage returns 'dark'", () => {
      mockLocalStorage.getItem.mockReturnValue("dark");

      const freshVm = new PresentModeViewModel(
        createMockEventApi(),
        createMockPresentStateApi(),
      );

      expect(freshVm.isDarkTheme).toBe(true);
    });
  });

  describe("dispose()", () => {
    it("calls ws.disconnect()", () => {
      vm.dispose();

      expect(wsResult.ws.disconnect).toHaveBeenCalledTimes(1);
    });

    it("does not throw when no WebSocket is provided", () => {
      const vmNoWs = new PresentModeViewModel(
        createMockEventApi(),
        createMockPresentStateApi(),
      );

      expect(() => vmNoWs.dispose()).not.toThrow();
    });
  });

  describe("hasActivePoll computed", () => {
    it("returns false when no active poll", () => {
      expect(vm.hasActivePoll).toBe(false);
    });

    it("returns true when active poll is set", async () => {
      const state = makePresentState({
        active_poll: makePresentActivePoll(),
      });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      await vm.initialize("ABC123");

      expect(vm.hasActivePoll).toBe(true);
    });
  });

  describe("WebSocket: poll_activated", () => {
    beforeEach(async () => {
      await vm.initialize("ABC123");
    });

    it("sets activePoll with poll_id, question, zero counts", () => {
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "poll-new",
        question: "Which option?",
        options: [
          { id: "opt-a", text: "Option A" },
          { id: "opt-b", text: "Option B" },
        ],
      });

      expect(vm.activePoll).not.toBeNull();
      expect(vm.activePoll!.poll_id).toBe("poll-new");
      expect(vm.activePoll!.question).toBe("Which option?");
      expect(vm.activePoll!.total_votes).toBe(0);
    });

    it("initializes options with count=0 and percentage=0", () => {
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "poll-new",
        question: "Which option?",
        options: [
          { id: "opt-a", text: "Option A" },
          { id: "opt-b", text: "Option B" },
        ],
      });

      expect(vm.activePoll!.options).toEqual([
        { option_id: "opt-a", text: "Option A", count: 0, percentage: 0 },
        { option_id: "opt-b", text: "Option B", count: 0, percentage: 0 },
      ]);
    });

    it("replaces an existing active poll", async () => {
      const state = makePresentState({
        active_poll: makePresentActivePoll({ poll_id: "old-poll" }),
      });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      const freshVm = new PresentModeViewModel(
        eventApi,
        presentStateApi,
        wsResult.ws,
      );
      await freshVm.initialize("ABC123");

      expect(freshVm.activePoll!.poll_id).toBe("old-poll");

      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "new-poll",
        question: "New question?",
        options: [],
      });

      expect(freshVm.activePoll!.poll_id).toBe("new-poll");
    });
  });

  describe("WebSocket: poll_deactivated", () => {
    beforeEach(async () => {
      await vm.initialize("ABC123");
    });

    it("sets activePoll to null", async () => {
      const state = makePresentState({
        active_poll: makePresentActivePoll(),
      });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      const freshVm = new PresentModeViewModel(
        eventApi,
        presentStateApi,
        wsResult.ws,
      );
      await freshVm.initialize("ABC123");
      expect(freshVm.activePoll).not.toBeNull();

      wsResult.messageHandler.current!({
        type: "poll_deactivated",
      });

      expect(freshVm.activePoll).toBeNull();
    });

    it("is a no-op when activePoll is already null", () => {
      expect(vm.activePoll).toBeNull();

      wsResult.messageHandler.current!({
        type: "poll_deactivated",
      });

      expect(vm.activePoll).toBeNull();
    });
  });

  describe("WebSocket: poll_results_updated", () => {
    beforeEach(async () => {
      await vm.initialize("ABC123");

      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "poll-1",
        question: "What is your favorite color?",
        options: [
          { id: "opt-1", text: "Red" },
          { id: "opt-2", text: "Blue" },
        ],
      });
    });

    it("updates activePoll options and total_votes", () => {
      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        results: [
          { option_id: "opt-1", text: "Red", count: 7, percentage: 70.0 },
          { option_id: "opt-2", text: "Blue", count: 3, percentage: 30.0 },
        ],
      });

      expect(vm.activePoll!.options).toEqual([
        { option_id: "opt-1", text: "Red", count: 7, percentage: 70.0 },
        { option_id: "opt-2", text: "Blue", count: 3, percentage: 30.0 },
      ]);
      expect(vm.activePoll!.total_votes).toBe(10);
    });

    it("uses total_votes from message when provided", () => {
      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        total_votes: 99,
        results: [
          { option_id: "opt-1", text: "Red", count: 7, percentage: 70.0 },
          { option_id: "opt-2", text: "Blue", count: 3, percentage: 30.0 },
        ],
      });

      expect(vm.activePoll!.total_votes).toBe(99);
    });

    it("calculates total_votes from option counts when not in message", () => {
      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        results: [
          { option_id: "opt-1", text: "Red", count: 4, percentage: 40.0 },
          { option_id: "opt-2", text: "Blue", count: 6, percentage: 60.0 },
        ],
      });

      expect(vm.activePoll!.total_votes).toBe(10);
    });

    it("ignores when activePoll is null", async () => {
      const vmNoPoll = new PresentModeViewModel(
        eventApi,
        presentStateApi,
        wsResult.ws,
      );
      await vmNoPoll.initialize("ABC123");
      expect(vmNoPoll.activePoll).toBeNull();

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "poll-1",
        results: [
          { option_id: "opt-1", text: "Red", count: 5, percentage: 100.0 },
        ],
      });

      expect(vmNoPoll.activePoll).toBeNull();
    });
  });

  describe("WebSocket: poll_activated with word_cloud type", () => {
    beforeEach(async () => {
      await vm.initialize("ABC123");
    });

    it("sets poll_type on activePoll when poll_type is 'word_cloud'", () => {
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "wc-poll",
        question: "What word comes to mind?",
        poll_type: "word_cloud",
        options: [],
      });

      expect(vm.activePoll).not.toBeNull();
      expect(vm.activePoll!.poll_type).toBe("word_cloud");
    });

    it("sets empty frequencies on activePoll for word_cloud poll", () => {
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "wc-poll",
        question: "What word comes to mind?",
        poll_type: "word_cloud",
        options: [],
      });

      expect(vm.activePoll!.frequencies).toEqual([]);
    });

    it("sets total_responses to 0 on activePoll for word_cloud poll", () => {
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "wc-poll",
        question: "What word comes to mind?",
        poll_type: "word_cloud",
        options: [],
      });

      expect(vm.activePoll!.total_responses).toBe(0);
    });

    it("sets poll_id and question correctly for word_cloud poll", () => {
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "wc-poll-99",
        question: "One word that describes the session?",
        poll_type: "word_cloud",
        options: [],
      });

      expect(vm.activePoll!.poll_id).toBe("wc-poll-99");
      expect(vm.activePoll!.question).toBe(
        "One word that describes the session?",
      );
    });
  });

  describe("WebSocket: poll_results_updated with word cloud data", () => {
    beforeEach(async () => {
      await vm.initialize("ABC123");

      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "wc-poll",
        question: "What word comes to mind?",
        poll_type: "word_cloud",
        options: [],
      });
    });

    it("updates frequencies when results has a 'words' array", () => {
      const words = [
        { text: "innovation", count: 10 },
        { text: "growth", count: 7 },
      ];

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "wc-poll",
        poll_type: "word_cloud",
        results: { total_responses: 17, words },
      });

      expect(vm.activePoll!.frequencies).toEqual(words);
    });

    it("updates total_responses when results has a 'words' array", () => {
      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "wc-poll",
        poll_type: "word_cloud",
        results: {
          total_responses: 42,
          words: [{ text: "cloud", count: 42 }],
        },
      });

      expect(vm.activePoll!.total_responses).toBe(42);
    });

    it("sets poll_type to 'word_cloud' on activePoll after results update", () => {
      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "wc-poll",
        poll_type: "word_cloud",
        results: {
          total_responses: 5,
          words: [{ text: "test", count: 5 }],
        },
      });

      expect(vm.activePoll!.poll_type).toBe("word_cloud");
    });

    it("handles empty words array in results", () => {
      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "wc-poll",
        poll_type: "word_cloud",
        results: { total_responses: 0, words: [] },
      });

      expect(vm.activePoll!.frequencies).toEqual([]);
      expect(vm.activePoll!.total_responses).toBe(0);
    });

    it("falls back to array-results behavior when results is a plain array (non-word-cloud)", () => {
      // Replace active poll with a multiple_choice one to test the fallback path
      wsResult.messageHandler.current!({
        type: "poll_activated",
        poll_id: "mc-poll",
        question: "Pick an option",
        poll_type: "multiple_choice",
        options: [
          { id: "opt-1", text: "Red" },
          { id: "opt-2", text: "Blue" },
        ],
      });

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "mc-poll",
        results: [
          { option_id: "opt-1", text: "Red", count: 5, percentage: 50.0 },
          { option_id: "opt-2", text: "Blue", count: 5, percentage: 50.0 },
        ],
      });

      expect(vm.activePoll!.options).toEqual([
        { option_id: "opt-1", text: "Red", count: 5, percentage: 50.0 },
        { option_id: "opt-2", text: "Blue", count: 5, percentage: 50.0 },
      ]);
      expect(vm.activePoll!.total_votes).toBe(10);
    });

    it("ignores results update when results is an object without 'words' and not an array", () => {
      const pollBefore = vm.activePoll;

      wsResult.messageHandler.current!({
        type: "poll_results_updated",
        poll_id: "wc-poll",
        results: { some_unknown_field: "data" },
      });

      // frequencies should remain unchanged since there's no 'words' field and it's not an array
      expect(vm.activePoll!.frequencies).toEqual(pollBefore!.frequencies);
    });
  });

  describe("WebSocket: score_update", () => {
    beforeEach(async () => {
      const topics = [
        makePresentTopic({ id: "t1", content: "Topic 1", score: 10 }),
        makePresentTopic({ id: "t2", content: "Topic 2", score: 5 }),
        makePresentTopic({ id: "t3", content: "Topic 3", score: 3 }),
      ];
      const state = makePresentState({ top_topics: topics });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      await vm.initialize("ABC123");
    });

    it("updates score of matching topic", () => {
      wsResult.messageHandler.current!({
        type: "score_update",
        topic_id: "t2",
        score: 15,
      });

      const t2 = vm.topTopics.find((t) => t.id === "t2");
      expect(t2).toBeDefined();
      expect(t2!.score).toBe(15);
    });

    it("re-sorts topTopics by score descending after update", () => {
      wsResult.messageHandler.current!({
        type: "score_update",
        topic_id: "t3",
        score: 20,
      });

      expect(vm.topTopics[0].id).toBe("t3");
      expect(vm.topTopics[1].id).toBe("t1");
      expect(vm.topTopics[2].id).toBe("t2");
    });

    it("does not change topTopics when topic_id not found", () => {
      const topicsBefore = [...vm.topTopics];

      wsResult.messageHandler.current!({
        type: "score_update",
        topic_id: "nonexistent",
        score: 100,
      });

      expect(vm.topTopics.map((t) => t.id)).toEqual(
        topicsBefore.map((t) => t.id),
      );
    });
  });

  describe("WebSocket: new_topic", () => {
    beforeEach(async () => {
      const topics = [
        makePresentTopic({ id: "t1", content: "Topic 1", score: 10 }),
        makePresentTopic({ id: "t2", content: "Topic 2", score: 5 }),
      ];
      const state = makePresentState({ top_topics: topics });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      await vm.initialize("ABC123");
    });

    it("inserts new topic", () => {
      wsResult.messageHandler.current!({
        type: "new_topic",
        topic: { id: "t3", content: "New Topic", score: 7 },
      });

      const t3 = vm.topTopics.find((t) => t.id === "t3");
      expect(t3).toBeDefined();
      expect(t3!.content).toBe("New Topic");
      expect(t3!.score).toBe(7);
    });

    it("keeps topics sorted by score descending after insert", () => {
      wsResult.messageHandler.current!({
        type: "new_topic",
        topic: { id: "t3", content: "New Topic", score: 7 },
      });

      expect(vm.topTopics[0].id).toBe("t1"); // score 10
      expect(vm.topTopics[1].id).toBe("t3"); // score 7
      expect(vm.topTopics[2].id).toBe("t2"); // score 5
    });

    it("keeps only top 10 topics after insert", async () => {
      const manyTopics = Array.from({ length: 10 }, (_, i) =>
        makePresentTopic({ id: `t${i + 1}`, score: 10 - i }),
      );
      const state = makePresentState({ top_topics: manyTopics });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      const freshVm = new PresentModeViewModel(
        eventApi,
        presentStateApi,
        wsResult.ws,
      );
      await freshVm.initialize("ABC123");
      expect(freshVm.topTopics).toHaveLength(10);

      wsResult.messageHandler.current!({
        type: "new_topic",
        topic: { id: "t-new", content: "New Top Topic", score: 100 },
      });

      expect(freshVm.topTopics).toHaveLength(10);
      expect(freshVm.topTopics[0].id).toBe("t-new");
    });

    it("ignores duplicate topics (same id)", () => {
      const countBefore = vm.topTopics.length;

      wsResult.messageHandler.current!({
        type: "new_topic",
        topic: { id: "t1", content: "Duplicate", score: 999 },
      });

      expect(vm.topTopics).toHaveLength(countBefore);
    });
  });

  describe("WebSocket: topic_censured", () => {
    beforeEach(async () => {
      const topics = [
        makePresentTopic({ id: "t1", content: "Topic 1", score: 10 }),
        makePresentTopic({ id: "t2", content: "Topic 2", score: 5 }),
        makePresentTopic({ id: "t3", content: "Topic 3", score: 3 }),
      ];
      const state = makePresentState({ top_topics: topics });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(state);

      await vm.initialize("ABC123");
    });

    it("removes topic from topTopics", () => {
      wsResult.messageHandler.current!({
        type: "topic_censured",
        topic_id: "t2",
      });

      expect(vm.topTopics.find((t) => t.id === "t2")).toBeUndefined();
      expect(vm.topTopics).toHaveLength(2);
    });

    it("leaves other topics intact", () => {
      wsResult.messageHandler.current!({
        type: "topic_censured",
        topic_id: "t2",
      });

      expect(vm.topTopics.find((t) => t.id === "t1")).toBeDefined();
      expect(vm.topTopics.find((t) => t.id === "t3")).toBeDefined();
    });

    it("is a no-op when topic_id not found", () => {
      const countBefore = vm.topTopics.length;

      wsResult.messageHandler.current!({
        type: "topic_censured",
        topic_id: "nonexistent",
      });

      expect(vm.topTopics).toHaveLength(countBefore);
    });
  });

  describe("WebSocket: reconnect handler", () => {
    it("re-fetches present state on reconnect", async () => {
      await vm.initialize("ABC123");

      const updatedState = makePresentState({
        active_poll: makePresentActivePoll({ poll_id: "poll-after-reconnect" }),
        top_topics: [makePresentTopic({ id: "t-new", score: 20 })],
        participant_count: 99,
      });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(updatedState);

      wsResult.reconnectHandler.current!();
      await flushMicrotasks();

      expect(presentStateApi.getPresentState).toHaveBeenCalledTimes(2);
    });

    it("updates activePoll, topTopics, participantCount on reconnect", async () => {
      const event = makeEvent({ id: "event-1" });
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockResolvedValue(event);

      await vm.initialize("ABC123");

      const updatedActivePoll = makePresentActivePoll({
        poll_id: "poll-reconnected",
      });
      const updatedTopics = [
        makePresentTopic({ id: "t-reconnected", score: 42 }),
      ];
      const updatedState = makePresentState({
        active_poll: updatedActivePoll,
        top_topics: updatedTopics,
        participant_count: 77,
      });
      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockResolvedValue(updatedState);

      wsResult.reconnectHandler.current!();
      await flushMicrotasks();

      expect(vm.activePoll).toEqual(updatedActivePoll);
      expect(vm.topTopics).toEqual(updatedTopics);
      expect(vm.participantCount).toBe(77);
    });

    it("does not crash when reconnect fails", async () => {
      await vm.initialize("ABC123");

      (
        presentStateApi.getPresentState as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Reconnect fetch failed"));

      await expect(async () => {
        wsResult.reconnectHandler.current!();
        await flushMicrotasks();
      }).not.toThrow();
    });
  });

  describe("WebSocket message validation", () => {
    beforeEach(async () => {
      await vm.initialize("ABC123");
    });

    it("ignores malformed messages", () => {
      const initialTopTopics = [...vm.topTopics];

      wsResult.messageHandler.current!(null);
      wsResult.messageHandler.current!(undefined);
      wsResult.messageHandler.current!("string data");
      wsResult.messageHandler.current!(42);
      wsResult.messageHandler.current!({ type: "unknown_type" });

      expect(vm.topTopics).toEqual(initialTopTopics);
    });
  });

  describe("constructor", () => {
    it("registers WebSocket message handler on initialize", async () => {
      await vm.initialize("ABC123");

      expect(wsResult.ws.onMessage).toHaveBeenCalledTimes(1);
    });

    it("registers WebSocket reconnect handler on initialize", async () => {
      await vm.initialize("ABC123");

      expect(wsResult.ws.onReconnect).toHaveBeenCalledTimes(1);
    });

    it("works without a WebSocket (no ws provided)", async () => {
      const vmNoWs = new PresentModeViewModel(
        createMockEventApi(),
        createMockPresentStateApi(),
      );

      await expect(vmNoWs.initialize("ABC123")).resolves.not.toThrow();
    });
  });
});
