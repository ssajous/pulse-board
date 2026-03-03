import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { HostDashboardViewModel } from "../HostDashboardViewModel";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type { HostApiPort } from "@domain/ports/HostApiPort";
import type {
  WebSocketPort,
  WebSocketMessageHandler,
} from "@domain/ports/WebSocketPort";
import type { Event } from "@domain/entities/Event";
import type { Topic } from "@domain/entities/Topic";
import type { EventStats } from "@domain/entities/EventStats";
import type { Poll } from "@domain/entities/Poll";

// --- Browser globals mock (Node environment has no window) ---

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
});

afterEach(() => {
  vi.clearAllMocks();
});

// --- Factories ---

const mockEvent: Event = {
  id: "event-1",
  title: "Test Event",
  code: "ABC123",
  description: null,
  start_date: null,
  end_date: null,
  status: "active",
  created_at: "2026-03-03T00:00:00Z",
};

const mockTopics: Topic[] = [
  {
    id: "t1",
    content: "Topic 1",
    score: 5,
    created_at: "2026-03-03T00:00:00Z",
    status: "active",
  },
  {
    id: "t2",
    content: "Topic 2",
    score: 3,
    created_at: "2026-03-03T01:00:00Z",
    status: "highlighted",
  },
  {
    id: "t3",
    content: "Topic 3",
    score: 1,
    created_at: "2026-03-03T02:00:00Z",
    status: "archived",
  },
];

const mockStats: EventStats = {
  participant_count: 10,
  topic_count: 3,
  active_topic_count: 1,
  poll_count: 1,
  has_active_poll: false,
  total_poll_responses: 5,
};

function makePoll(overrides: Partial<Poll> = {}): Poll {
  return {
    id: "poll-1",
    event_id: "event-1",
    question: "Test question?",
    poll_type: "multiple_choice",
    options: [
      { id: "opt-1", text: "Option A" },
      { id: "opt-2", text: "Option B" },
    ],
    is_active: false,
    created_at: "2026-03-03T00:00:00Z",
    ...overrides,
  };
}

function createMockEventApi(): EventApiPort {
  return {
    createEvent: vi.fn(),
    getEventByCode: vi.fn().mockResolvedValue(mockEvent),
    getEventById: vi.fn().mockResolvedValue(mockEvent),
    checkCreator: vi.fn(),
  };
}

function createMockPollApi(): PollApiPort {
  return {
    listPolls: vi.fn().mockResolvedValue([]),
    createPoll: vi.fn(),
    activatePoll: vi.fn().mockResolvedValue(undefined),
    submitResponse: vi.fn(),
    getResults: vi.fn(),
    getActivePoll: vi.fn(),
  };
}

function createMockHostApi(): HostApiPort {
  return {
    updateTopicStatus: vi
      .fn()
      .mockResolvedValue({ topic_id: "t1", new_status: "highlighted" }),
    closeEvent: vi
      .fn()
      .mockResolvedValue({ event_id: "event-1", status: "closed" }),
    getEventStats: vi.fn().mockResolvedValue(mockStats),
    getAllTopics: vi.fn().mockResolvedValue(mockTopics),
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

describe("HostDashboardViewModel", () => {
  let vm: HostDashboardViewModel;
  let eventApi: EventApiPort;
  let pollApi: PollApiPort;
  let hostApi: HostApiPort;

  beforeEach(() => {
    eventApi = createMockEventApi();
    pollApi = createMockPollApi();
    hostApi = createMockHostApi();
    vm = new HostDashboardViewModel(eventApi, pollApi, hostApi);
  });

  describe("initial state", () => {
    it("has null event", () => {
      expect(vm.event).toBeNull();
    });

    it("has empty topics array", () => {
      expect(vm.topics).toEqual([]);
    });

    it("is loading", () => {
      expect(vm.isLoading).toBe(true);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });

    it("is not closed", () => {
      expect(vm.isClosed).toBe(false);
    });

    it("has null stats", () => {
      expect(vm.stats).toBeNull();
    });

    it("has empty polls array", () => {
      expect(vm.polls).toEqual([]);
    });
  });

  describe("loadDashboard", () => {
    it("loads event, topics, and stats from API", async () => {
      await vm.loadDashboard("ABC123");

      expect(vm.event).toEqual(mockEvent);
      expect(vm.topics).toEqual(mockTopics);
      expect(vm.stats).toEqual(mockStats);
      expect(vm.isLoading).toBe(false);
    });

    it("calls getEventByCode with the provided code", async () => {
      await vm.loadDashboard("ABC123");

      expect(eventApi.getEventByCode).toHaveBeenCalledWith("ABC123");
    });

    it("calls getAllTopics with the event id", async () => {
      await vm.loadDashboard("ABC123");

      expect(hostApi.getAllTopics).toHaveBeenCalledWith("event-1");
    });

    it("calls getEventStats with the event id", async () => {
      await vm.loadDashboard("ABC123");

      expect(hostApi.getEventStats).toHaveBeenCalledWith("event-1");
    });

    it("calls listPolls with the event id", async () => {
      await vm.loadDashboard("ABC123");

      expect(pollApi.listPolls).toHaveBeenCalledWith("event-1");
    });

    it("sets isClosed to true when event status is closed", async () => {
      const closedEvent: Event = { ...mockEvent, status: "closed" };
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockResolvedValue(closedEvent);

      await vm.loadDashboard("ABC123");

      expect(vm.isClosed).toBe(true);
    });

    it("sets error on failed event fetch", async () => {
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Network error"));

      await vm.loadDashboard("ABC123");

      expect(vm.error).toBe("Network error");
      expect(vm.isLoading).toBe(false);
    });

    it("sets generic error when non-Error is thrown", async () => {
      (
        eventApi.getEventByCode as ReturnType<typeof vi.fn>
      ).mockRejectedValue("string error");

      await vm.loadDashboard("ABC123");

      expect(vm.error).toBe("Failed to load dashboard");
      expect(vm.isLoading).toBe(false);
    });

    it("connects WebSocket when ws is provided", async () => {
      const { ws } = createMockWs();
      const vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        ws,
      );

      await vmWithWs.loadDashboard("ABC123");

      expect(ws.connect).toHaveBeenCalledWith(
        "ws://localhost:8000/ws/events/ABC123",
      );
    });

    it("registers onMessage and onReconnect when ws is provided", async () => {
      const { ws } = createMockWs();
      const vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        ws,
      );

      await vmWithWs.loadDashboard("ABC123");

      expect(ws.onMessage).toHaveBeenCalledTimes(1);
      expect(ws.onReconnect).toHaveBeenCalledTimes(1);
    });
  });

  describe("computed topic groups", () => {
    beforeEach(async () => {
      await vm.loadDashboard("ABC123");
    });

    it("filters active topics correctly", () => {
      expect(vm.activeTopics).toHaveLength(1);
      expect(vm.activeTopics[0].id).toBe("t1");
    });

    it("filters highlighted topics correctly", () => {
      expect(vm.highlightedTopics).toHaveLength(1);
      expect(vm.highlightedTopics[0].id).toBe("t2");
    });

    it("filters archived topics correctly", () => {
      expect(vm.archivedTopics).toHaveLength(1);
      expect(vm.archivedTopics[0].id).toBe("t3");
    });

    it("returns empty answered topics when none present", () => {
      expect(vm.answeredTopics).toHaveLength(0);
    });
  });

  describe("updateTopicStatus", () => {
    beforeEach(async () => {
      await vm.loadDashboard("ABC123");
    });

    it("updates topic status in local state", async () => {
      (hostApi.updateTopicStatus as ReturnType<typeof vi.fn>).mockResolvedValue(
        { topic_id: "t1", new_status: "answered" },
      );

      await vm.updateTopicStatus("t1", "answered");

      const t = vm.topics.find((t) => t.id === "t1");
      expect(t?.status).toBe("answered");
    });

    it("calls updateTopicStatus API with correct arguments", async () => {
      await vm.updateTopicStatus("t1", "highlighted");

      expect(hostApi.updateTopicStatus).toHaveBeenCalledWith(
        "event-1",
        "t1",
        "highlighted",
      );
    });

    it("sets error on failed status update", async () => {
      (
        hostApi.updateTopicStatus as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Update failed"));

      await vm.updateTopicStatus("t1", "highlighted");

      expect(vm.error).toBe("Update failed");
    });

    it("clears updatingTopicId after success", async () => {
      await vm.updateTopicStatus("t1", "highlighted");

      expect(vm.updatingTopicId).toBeNull();
    });

    it("clears updatingTopicId after failure", async () => {
      (
        hostApi.updateTopicStatus as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Failed"));

      await vm.updateTopicStatus("t1", "highlighted");

      expect(vm.updatingTopicId).toBeNull();
    });

    it("does nothing when event is not loaded", async () => {
      const freshVm = new HostDashboardViewModel(eventApi, pollApi, hostApi);

      await freshVm.updateTopicStatus("t1", "highlighted");

      expect(hostApi.updateTopicStatus).not.toHaveBeenCalled();
    });
  });

  describe("closeEvent", () => {
    beforeEach(async () => {
      await vm.loadDashboard("ABC123");
    });

    it("sets isClosed to true after successful close", async () => {
      await vm.closeEvent();

      expect(vm.isClosed).toBe(true);
    });

    it("calls closeEvent API with event id", async () => {
      await vm.closeEvent();

      expect(hostApi.closeEvent).toHaveBeenCalledWith("event-1");
    });

    it("sets error on failed close", async () => {
      (hostApi.closeEvent as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Close failed"),
      );

      await vm.closeEvent();

      expect(vm.error).toBe("Close failed");
    });

    it("clears isClosingEvent after success", async () => {
      await vm.closeEvent();

      expect(vm.isClosingEvent).toBe(false);
    });

    it("clears isClosingEvent after failure", async () => {
      (hostApi.closeEvent as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Failed"),
      );

      await vm.closeEvent();

      expect(vm.isClosingEvent).toBe(false);
    });

    it("does nothing when event is not loaded", async () => {
      const freshVm = new HostDashboardViewModel(eventApi, pollApi, hostApi);

      await freshVm.closeEvent();

      expect(hostApi.closeEvent).not.toHaveBeenCalled();
    });
  });

  describe("togglePollActive", () => {
    beforeEach(async () => {
      (pollApi.listPolls as ReturnType<typeof vi.fn>).mockResolvedValue([
        makePoll({ id: "poll-1", is_active: false }),
      ]);
      await vm.loadDashboard("ABC123");
    });

    it("calls activatePoll to activate an inactive poll", async () => {
      await vm.togglePollActive("poll-1");

      expect(pollApi.activatePoll).toHaveBeenCalledWith("poll-1", true);
    });

    it("calls activatePoll to deactivate an active poll", async () => {
      (pollApi.listPolls as ReturnType<typeof vi.fn>).mockResolvedValue([
        makePoll({ id: "poll-1", is_active: true }),
      ]);
      const freshVm = new HostDashboardViewModel(eventApi, pollApi, hostApi);
      await freshVm.loadDashboard("ABC123");

      await freshVm.togglePollActive("poll-1");

      expect(pollApi.activatePoll).toHaveBeenCalledWith("poll-1", false);
    });

    it("does nothing when poll id not found", async () => {
      await vm.togglePollActive("nonexistent");

      expect(pollApi.activatePoll).not.toHaveBeenCalled();
    });

    it("sets error on failed toggle", async () => {
      (pollApi.activatePoll as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("Toggle failed"),
      );

      await vm.togglePollActive("poll-1");

      expect(vm.error).toBe("Toggle failed");
    });
  });

  describe("onPollCreated", () => {
    beforeEach(async () => {
      await vm.loadDashboard("ABC123");
    });

    it("reloads polls from the server", async () => {
      const newPoll = makePoll({ id: "poll-new" });

      vm.onPollCreated(newPoll);
      await flushMicrotasks();

      expect(pollApi.listPolls).toHaveBeenCalledTimes(2); // once on load, once on create
    });
  });

  describe("activePoll computed", () => {
    beforeEach(async () => {
      await vm.loadDashboard("ABC123");
    });

    it("returns null when no poll is active", () => {
      expect(vm.activePoll).toBeNull();
    });

    it("returns the active poll", async () => {
      (pollApi.listPolls as ReturnType<typeof vi.fn>).mockResolvedValue([
        makePoll({ id: "poll-1", is_active: true }),
        makePoll({ id: "poll-2", is_active: false }),
      ]);
      const freshVm = new HostDashboardViewModel(eventApi, pollApi, hostApi);
      await freshVm.loadDashboard("ABC123");

      expect(freshVm.activePoll).not.toBeNull();
      expect(freshVm.activePoll!.id).toBe("poll-1");
    });
  });

  describe("dismissError", () => {
    beforeEach(async () => {
      await vm.loadDashboard("ABC123");
    });

    it("clears the error", () => {
      vm.error = "Test error";

      vm.dismissError();

      expect(vm.error).toBeNull();
    });

    it("is safe to call when error is already null", () => {
      expect(vm.error).toBeNull();

      vm.dismissError();

      expect(vm.error).toBeNull();
    });
  });

  describe("dispose", () => {
    it("disconnects the WebSocket when one is provided", async () => {
      const { ws } = createMockWs();
      const vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        ws,
      );
      await vmWithWs.loadDashboard("ABC123");

      vmWithWs.dispose();

      expect(ws.disconnect).toHaveBeenCalledTimes(1);
    });

    it("does not throw when no WebSocket is provided", () => {
      expect(() => vm.dispose()).not.toThrow();
    });
  });

  describe("WebSocket: topic_status_changed", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("updates topic status in local state", () => {
      wsResult.messageHandler.current!({
        type: "topic_status_changed",
        topic_id: "t1",
        new_status: "answered",
      });

      const t = vmWithWs.topics.find((t) => t.id === "t1");
      expect(t?.status).toBe("answered");
    });

    it("leaves other topics unchanged", () => {
      wsResult.messageHandler.current!({
        type: "topic_status_changed",
        topic_id: "t1",
        new_status: "answered",
      });

      const t2 = vmWithWs.topics.find((t) => t.id === "t2");
      expect(t2?.status).toBe("highlighted");
    });

    it("ignores message when topic_id is missing", () => {
      const topicsBefore = vmWithWs.topics.map((t) => ({ ...t }));

      wsResult.messageHandler.current!({
        type: "topic_status_changed",
        new_status: "answered",
      });

      expect(vmWithWs.topics.map((t) => t.status)).toEqual(
        topicsBefore.map((t) => t.status),
      );
    });

    it("ignores message when new_status is missing", () => {
      const topicsBefore = vmWithWs.topics.map((t) => ({ ...t }));

      wsResult.messageHandler.current!({
        type: "topic_status_changed",
        topic_id: "t1",
      });

      expect(vmWithWs.topics.map((t) => t.status)).toEqual(
        topicsBefore.map((t) => t.status),
      );
    });
  });

  describe("WebSocket: event_closed", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("sets isClosed to true", () => {
      expect(vmWithWs.isClosed).toBe(false);

      wsResult.messageHandler.current!({
        type: "event_closed",
        event_id: "event-1",
      });

      expect(vmWithWs.isClosed).toBe(true);
    });
  });

  describe("WebSocket: score_update", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("updates score for a matching topic", () => {
      wsResult.messageHandler.current!({
        type: "score_update",
        topic_id: "t1",
        score: 99,
      });

      const t = vmWithWs.topics.find((t) => t.id === "t1");
      expect(t?.score).toBe(99);
    });

    it("ignores when topic_id not found", () => {
      const scoresBefore = vmWithWs.topics.map((t) => t.score);

      wsResult.messageHandler.current!({
        type: "score_update",
        topic_id: "nonexistent",
        score: 99,
      });

      expect(vmWithWs.topics.map((t) => t.score)).toEqual(scoresBefore);
    });
  });

  describe("WebSocket: new_topic", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("adds new topic from WebSocket message", () => {
      const countBefore = vmWithWs.topics.length;

      wsResult.messageHandler.current!({
        type: "new_topic",
        topic: {
          id: "t-new",
          content: "Brand new topic",
          score: 0,
          created_at: "2026-03-03T10:00:00Z",
        },
      });

      expect(vmWithWs.topics.length).toBe(countBefore + 1);
      const newTopic = vmWithWs.topics.find((t) => t.id === "t-new");
      expect(newTopic?.content).toBe("Brand new topic");
      expect(newTopic?.status).toBe("active");
    });

    it("deduplicates topics already in the list", () => {
      const countBefore = vmWithWs.topics.length;

      wsResult.messageHandler.current!({
        type: "new_topic",
        topic: {
          id: "t1",
          content: "Duplicate",
          score: 100,
          created_at: "2026-03-03T10:00:00Z",
        },
      });

      expect(vmWithWs.topics.length).toBe(countBefore);
    });
  });

  describe("WebSocket: topic_censured", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("removes the censured topic from the list", () => {
      expect(vmWithWs.topics.find((t) => t.id === "t1")).toBeDefined();

      wsResult.messageHandler.current!({
        type: "topic_censured",
        topic_id: "t1",
      });

      expect(vmWithWs.topics.find((t) => t.id === "t1")).toBeUndefined();
    });

    it("leaves other topics intact", () => {
      wsResult.messageHandler.current!({
        type: "topic_censured",
        topic_id: "t1",
      });

      expect(vmWithWs.topics.find((t) => t.id === "t2")).toBeDefined();
    });
  });

  describe("WebSocket: poll_activated and poll_deactivated", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("calls listPolls on poll_activated", async () => {
      const callsBefore = (pollApi.listPolls as ReturnType<typeof vi.fn>).mock
        .calls.length;

      wsResult.messageHandler.current!({ type: "poll_activated" });
      await flushMicrotasks();

      expect(
        (pollApi.listPolls as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBeGreaterThan(callsBefore);
    });

    it("calls listPolls on poll_deactivated", async () => {
      const callsBefore = (pollApi.listPolls as ReturnType<typeof vi.fn>).mock
        .calls.length;

      wsResult.messageHandler.current!({ type: "poll_deactivated" });
      await flushMicrotasks();

      expect(
        (pollApi.listPolls as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBeGreaterThan(callsBefore);
    });
  });

  describe("WebSocket message validation", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("ignores malformed messages without throwing", () => {
      const topicsCountBefore = vmWithWs.topics.length;

      wsResult.messageHandler.current!(null);
      wsResult.messageHandler.current!(undefined);
      wsResult.messageHandler.current!("string data");
      wsResult.messageHandler.current!(42);
      wsResult.messageHandler.current!({ type: "unknown_type" });

      expect(vmWithWs.topics.length).toBe(topicsCountBefore);
      expect(vmWithWs.isClosed).toBe(false);
    });
  });

  describe("WebSocket: reconnect handler", () => {
    let wsResult: MockWsResult;
    let vmWithWs: HostDashboardViewModel;

    beforeEach(async () => {
      wsResult = createMockWs();
      vmWithWs = new HostDashboardViewModel(
        eventApi,
        pollApi,
        hostApi,
        wsResult.ws,
      );
      await vmWithWs.loadDashboard("ABC123");
    });

    it("re-fetches topics, polls, and stats on reconnect", async () => {
      const topicsCallsBefore = (
        hostApi.getAllTopics as ReturnType<typeof vi.fn>
      ).mock.calls.length;
      const pollsCallsBefore = (pollApi.listPolls as ReturnType<typeof vi.fn>)
        .mock.calls.length;
      const statsCallsBefore = (
        hostApi.getEventStats as ReturnType<typeof vi.fn>
      ).mock.calls.length;

      wsResult.reconnectHandler.current!();
      await flushMicrotasks();

      expect(
        (hostApi.getAllTopics as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBeGreaterThan(topicsCallsBefore);
      expect(
        (pollApi.listPolls as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBeGreaterThan(pollsCallsBefore);
      expect(
        (hostApi.getEventStats as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBeGreaterThan(statsCallsBefore);
    });
  });
});
