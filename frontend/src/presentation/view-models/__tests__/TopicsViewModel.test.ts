import { describe, it, expect, vi, beforeEach } from "vitest";
import { TopicsViewModel } from "../TopicsViewModel";
import type { Topic } from "@domain/entities/Topic";
import type { TopicApiPort } from "@domain/ports/TopicApiPort";
import type {
  WebSocketPort,
  WebSocketMessageHandler,
} from "@domain/ports/WebSocketPort";
import type { VoteApiPort } from "@domain/ports/VoteApiPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

// --- Stub window.location for buildWebSocketUrl() ---
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

// --- Factories ---

function makeTopic(overrides: Partial<Topic> = {}): Topic {
  return {
    id: "t1",
    content: "Test topic",
    score: 0,
    created_at: "2026-02-17T10:00:00Z",
    ...overrides,
  };
}

function createMockApi(topics: Topic[] = []): TopicApiPort {
  return {
    fetchTopics: vi.fn().mockResolvedValue(topics),
    createTopic: vi
      .fn()
      .mockImplementation(async (content: string) => ({
        id: "new-id",
        content,
        score: 0,
        created_at: "2026-02-17T12:00:00Z",
      })),
  };
}

function createMockVoteApi(): VoteApiPort {
  return {
    castVote: vi.fn().mockResolvedValue({
      topic_id: "t1",
      new_score: 1,
      vote_status: "created" as const,
      user_vote: 1,
      censured: false,
    }),
  };
}

function createMockFingerprint(
  id: string = "fp-abc123"
): FingerprintPort {
  return {
    getFingerprint: vi.fn().mockResolvedValue(id),
  };
}

interface MockWsResult {
  ws: WebSocketPort;
  messageHandler: { current: WebSocketMessageHandler | null };
  reconnectHandler: { current: (() => void) | null };
}

function createMockWs(): MockWsResult {
  const messageHandler: {
    current: WebSocketMessageHandler | null;
  } = { current: null };
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
 * Helper to flush microtasks so the constructor's
 * fetchTopics() promise resolves before assertions.
 */
async function flushMicrotasks(): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
}

// --- Tests ---

describe("TopicsViewModel", () => {
  describe("constructor", () => {
    it("calls fetchTopics on construction", async () => {
      const api = createMockApi([makeTopic()]);
      const _vm = new TopicsViewModel(api);

      await flushMicrotasks();

      expect(api.fetchTopics).toHaveBeenCalledTimes(1);
    });

    it("registers WebSocket handlers when ws is provided", () => {
      const api = createMockApi();
      const { ws } = createMockWs();

      const _vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );

      expect(ws.onMessage).toHaveBeenCalledTimes(1);
      expect(ws.onReconnect).toHaveBeenCalledTimes(1);
      expect(ws.connect).toHaveBeenCalledTimes(1);
    });
  });

  describe("handleNewTopic (via WebSocket)", () => {
    it("adds a topic from a new_topic WebSocket message", async () => {
      const existingTopic = makeTopic({ id: "existing" });
      const api = createMockApi([existingTopic]);
      const { ws, messageHandler } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      expect(vm.topics).toHaveLength(1);

      messageHandler.current!({
        type: "new_topic",
        topic: {
          id: "ws-new",
          content: "From WebSocket",
          score: 3,
          created_at: "2026-02-17T11:00:00Z",
        },
      });

      expect(vm.topics).toHaveLength(2);
      expect(vm.topics.find((t) => t.id === "ws-new")).toEqual({
        id: "ws-new",
        content: "From WebSocket",
        score: 3,
        created_at: "2026-02-17T11:00:00Z",
      });
    });

    it("deduplicates topics already in the list", async () => {
      const existingTopic = makeTopic({ id: "existing-id" });
      const api = createMockApi([existingTopic]);
      const { ws, messageHandler } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      expect(vm.topics).toHaveLength(1);

      messageHandler.current!({
        type: "new_topic",
        topic: {
          id: "existing-id",
          content: "Duplicate",
          score: 10,
          created_at: "2026-02-17T11:00:00Z",
        },
      });

      expect(vm.topics).toHaveLength(1);
    });
  });

  describe("handleScoreUpdate (via WebSocket)", () => {
    it("updates score for an existing topic", async () => {
      const topic = makeTopic({ id: "t1", score: 0 });
      const api = createMockApi([topic]);
      const { ws, messageHandler } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      expect(vm.topics[0].score).toBe(0);

      messageHandler.current!({
        type: "score_update",
        topic_id: "t1",
        score: 5,
      });

      expect(vm.topics[0].score).toBe(5);
    });

    it("ignores score updates for topics being voted on", async () => {
      const topic = makeTopic({ id: "t1", score: 0 });
      const api = createMockApi([topic]);
      const voteApi = createMockVoteApi();
      const fingerprint = createMockFingerprint();
      const { ws, messageHandler } = createMockWs();

      // Make castVote hang so isVoting stays true
      (voteApi.castVote as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {})
      );

      const vm = new TopicsViewModel(
        api,
        voteApi,
        fingerprint,
        ws
      );
      await flushMicrotasks();

      // Start a vote to put "t1" into the isVoting set
      vm.castVote("t1", "up");

      // The topic should now be in the isVoting set
      expect(vm.isTopicVoting("t1")).toBe(true);

      // The optimistic update will have changed the score to 1
      const scoreAfterOptimistic = vm.topics.find(
        (t) => t.id === "t1"
      )!.score;

      // Now send a WS score_update -- it should be ignored
      messageHandler.current!({
        type: "score_update",
        topic_id: "t1",
        score: 99,
      });

      expect(vm.topics.find((t) => t.id === "t1")!.score).toBe(
        scoreAfterOptimistic
      );
    });
  });

  describe("handleTopicCensured (via WebSocket)", () => {
    it("removes topic and shows toast", async () => {
      const topic = makeTopic({ id: "t1" });
      const api = createMockApi([topic]);
      const { ws, messageHandler } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      expect(vm.topics).toHaveLength(1);

      messageHandler.current!({
        type: "topic_censured",
        topic_id: "t1",
      });

      expect(vm.topics).toHaveLength(0);
      expect(vm.toast).toEqual({
        message: "Topic has been censured by the community",
        type: "success",
      });
    });
  });

  describe("submitTopic", () => {
    it("adds topic from API response without calling fetchTopics again", async () => {
      const api = createMockApi([makeTopic({ id: "initial" })]);

      const vm = new TopicsViewModel(api);
      await flushMicrotasks();

      expect(api.fetchTopics).toHaveBeenCalledTimes(1);
      expect(vm.topics).toHaveLength(1);

      const result = await vm.submitTopic("new content");

      expect(result).toBe(true);
      expect(api.createTopic).toHaveBeenCalledWith("new content");
      // fetchTopics should NOT have been called a second time
      expect(api.fetchTopics).toHaveBeenCalledTimes(1);
      expect(vm.topics).toHaveLength(2);
      expect(
        vm.topics.find((t) => t.id === "new-id")
      ).toBeDefined();
    });

    it("returns false and shows error toast on failure", async () => {
      const api = createMockApi([]);
      (
        api.createTopic as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Network error"));

      const vm = new TopicsViewModel(api);
      await flushMicrotasks();

      const result = await vm.submitTopic("will fail");

      expect(result).toBe(false);
      expect(vm.toast).toEqual({
        message: "Network error",
        type: "error",
      });
    });
  });

  describe("handleReconnect (via WebSocket)", () => {
    it("triggers a full refresh of topics", async () => {
      const api = createMockApi([makeTopic({ id: "t1" })]);
      const { ws, reconnectHandler } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      expect(api.fetchTopics).toHaveBeenCalledTimes(1);

      // Return different data on the second fetch
      (
        api.fetchTopics as ReturnType<typeof vi.fn>
      ).mockResolvedValue([
        makeTopic({ id: "t2", content: "Refreshed" }),
      ]);

      reconnectHandler.current!();
      await flushMicrotasks();

      expect(api.fetchTopics).toHaveBeenCalledTimes(2);
      expect(vm.topics).toHaveLength(1);
      expect(vm.topics[0].id).toBe("t2");
    });
  });

  describe("WebSocket message validation", () => {
    it("ignores malformed messages", async () => {
      const api = createMockApi([makeTopic({ id: "t1" })]);
      const { ws, messageHandler } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      // Send garbage data -- should not throw or modify state
      messageHandler.current!(null);
      messageHandler.current!(undefined);
      messageHandler.current!("string data");
      messageHandler.current!(42);
      messageHandler.current!({ type: "unknown_type" });
      messageHandler.current!({ type: "score_update" }); // missing fields
      messageHandler.current!({
        type: "new_topic",
        topic: { id: 123 },
      }); // wrong field types

      expect(vm.topics).toHaveLength(1);
      expect(vm.topics[0].id).toBe("t1");
    });
  });

  describe("dispose", () => {
    it("disconnects the WebSocket", async () => {
      const api = createMockApi();
      const { ws } = createMockWs();

      const vm = new TopicsViewModel(
        api,
        undefined,
        undefined,
        ws
      );
      await flushMicrotasks();

      vm.dispose();

      expect(ws.disconnect).toHaveBeenCalledTimes(1);
    });
  });

  describe("sortedTopics", () => {
    it("sorts by score descending, then by created_at descending", async () => {
      const topics = [
        makeTopic({
          id: "a",
          score: 1,
          created_at: "2026-02-17T10:00:00Z",
        }),
        makeTopic({
          id: "b",
          score: 5,
          created_at: "2026-02-17T09:00:00Z",
        }),
        makeTopic({
          id: "c",
          score: 5,
          created_at: "2026-02-17T11:00:00Z",
        }),
      ];
      const api = createMockApi(topics);

      const vm = new TopicsViewModel(api);
      await flushMicrotasks();

      const sorted = vm.sortedTopics;
      expect(sorted.map((t) => t.id)).toEqual(["c", "b", "a"]);
    });
  });

  describe("fetchTopics error handling", () => {
    it("sets error state on fetch failure", async () => {
      const api = createMockApi();
      (
        api.fetchTopics as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Server down"));

      const vm = new TopicsViewModel(api);
      await flushMicrotasks();

      expect(vm.error).toBe("Server down");
      expect(vm.isLoading).toBe(false);
    });
  });

  describe("initFingerprint", () => {
    it("sets fingerprintId on success", async () => {
      const api = createMockApi();
      const fingerprint = createMockFingerprint("fp-xyz");

      const vm = new TopicsViewModel(
        api,
        undefined,
        fingerprint
      );
      await flushMicrotasks();

      expect(vm.fingerprintId).toBe("fp-xyz");
      expect(vm.fingerprintError).toBe(false);
    });

    it("sets fingerprintError on failure", async () => {
      const api = createMockApi();
      const fingerprint: FingerprintPort = {
        getFingerprint: vi
          .fn()
          .mockRejectedValue(new Error("FP failed")),
      };

      const vm = new TopicsViewModel(
        api,
        undefined,
        fingerprint
      );
      await flushMicrotasks();

      expect(vm.fingerprintId).toBeNull();
      expect(vm.fingerprintError).toBe(true);
    });
  });
});
