import { makeAutoObservable, observable, runInAction } from "mobx";
import type { Topic } from "@domain/entities/Topic";
import type { TopicApiPort } from "@domain/ports/TopicApiPort";
import type { VoteApiPort } from "@domain/ports/VoteApiPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";
import type { WebSocketPort } from "@domain/ports/WebSocketPort";
import { computeScoreDelta } from "@application/use-cases/computeScoreDelta";
import { logger } from "@infrastructure/logger";

function extractErrorMessage(
  error: unknown,
  fallback: string
): string {
  return error instanceof Error ? error.message : fallback;
}

function buildWebSocketUrl(): string {
  const protocol =
    window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

interface ScoreUpdateMessage {
  type: "score_update";
  topic_id: string;
  score: number;
}

interface TopicCensuredMessage {
  type: "topic_censured";
  topic_id: string;
}

interface NewTopicMessage {
  type: "new_topic";
  topic: {
    id: string;
    content: string;
    score: number;
    created_at: string;
  };
}

type WebSocketMessage =
  | ScoreUpdateMessage
  | TopicCensuredMessage
  | NewTopicMessage;

function isRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    typeof value === "object"
    && value !== null
    && !Array.isArray(value)
  );
}

function isWebSocketMessage(
  data: unknown
): data is WebSocketMessage {
  if (!isRecord(data)) return false;

  if (data.type === "score_update") {
    return (
      typeof data.topic_id === "string"
      && typeof data.score === "number"
    );
  }
  if (data.type === "topic_censured") {
    return typeof data.topic_id === "string";
  }
  if (data.type === "new_topic") {
    if (!isRecord(data.topic)) return false;
    const t = data.topic;
    return (
      typeof t.id === "string"
      && typeof t.content === "string"
      && typeof t.score === "number"
      && typeof t.created_at === "string"
    );
  }
  return false;
}

export interface ToastMessage {
  message: string;
  type: "success" | "error";
}

export class TopicsViewModel {
  topics: Topic[] = [];
  isLoading = false;
  error: string | null = null;
  toast: ToastMessage | null = null;

  userVotes: Map<string, number> = observable.map();
  fingerprintId: string | null = null;
  fingerprintError = false;
  isVoting: Set<string> = observable.set();

  private readonly _api: TopicApiPort;
  private readonly _voteApi: VoteApiPort | null;
  private readonly _fingerprint: FingerprintPort | null;
  private readonly _ws: WebSocketPort | null;

  constructor(
    api: TopicApiPort,
    voteApi?: VoteApiPort,
    fingerprint?: FingerprintPort,
    ws?: WebSocketPort
  ) {
    this._api = api;
    this._voteApi = voteApi ?? null;
    this._fingerprint = fingerprint ?? null;
    this._ws = ws ?? null;
    makeAutoObservable(this, {}, { autoBind: true });
    this.fetchTopics();
    if (this._fingerprint) {
      this.initFingerprint();
    }
    if (this._ws) {
      this._ws.onMessage(this.handleWebSocketMessage);
      this._ws.onReconnect(this.handleReconnect);
    }
  }

  connectWebSocket(): void {
    this._ws?.connect(buildWebSocketUrl());
  }

  get sortedTopics(): Topic[] {
    return [...this.topics].sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (
        new Date(b.created_at).getTime()
        - new Date(a.created_at).getTime()
      );
    });
  }

  get isEmpty(): boolean {
    return this.topics.length === 0;
  }

  get canVote(): boolean {
    return (
      this.fingerprintId !== null
      && !this.fingerprintError
    );
  }

  async initFingerprint(): Promise<void> {
    if (!this._fingerprint) return;
    try {
      const id = await this._fingerprint.getFingerprint();
      runInAction(() => {
        this.fingerprintId = id;
      });
    } catch {
      runInAction(() => {
        this.fingerprintError = true;
      });
    }
  }

  getUserVote(topicId: string): number | null {
    return this.userVotes.get(topicId) ?? null;
  }

  isTopicVoting(topicId: string): boolean {
    return this.isVoting.has(topicId);
  }

  private setTopicScore(topicId: string, score: number): void {
    this.topics = this.topics.map((t) =>
      t.id === topicId ? { ...t, score } : t
    );
  }

  private setUserVote(topicId: string, vote: number | null): void {
    if (vote !== null) {
      this.userVotes.set(topicId, vote);
    } else {
      this.userVotes.delete(topicId);
    }
  }

  async castVote(
    topicId: string,
    direction: "up" | "down"
  ): Promise<void> {
    if (
      !this.canVote
      || !this._voteApi
      || this.isVoting.has(topicId)
    ) {
      return;
    }

    const prevVote = this.userVotes.get(topicId) ?? null;
    const topic = this.topics.find((t) => t.id === topicId);
    if (!topic) return;
    const prevScore = topic.score;

    const delta = computeScoreDelta(prevVote, direction);
    const newValue = direction === "up" ? 1 : -1;
    const optimisticVote = prevVote === newValue ? null : newValue;

    // Optimistic update
    this.isVoting.add(topicId);
    this.setTopicScore(topicId, topic.score + delta);
    this.setUserVote(topicId, optimisticVote);

    try {
      const response = await this._voteApi.castVote(
        topicId,
        this.fingerprintId!,
        direction
      );
      runInAction(() => {
        this.setTopicScore(topicId, response.new_score);
        this.setUserVote(topicId, response.user_vote);
        this.isVoting.delete(topicId);

        if (response.censured) {
          setTimeout(() => {
            runInAction(() => {
              this.topics = this.topics.filter(
                (t) => t.id !== topicId
              );
              this.showToast(
                "Topic has been censured by the community",
                "success"
              );
            });
          }, 300);
        }
      });
    } catch (e) {
      runInAction(() => {
        this.setTopicScore(topicId, prevScore);
        this.setUserVote(topicId, prevVote);
        this.isVoting.delete(topicId);
        this.showToast(
          extractErrorMessage(e, "Failed to cast vote"),
          "error"
        );
      });
    }
  }

  async fetchTopics(): Promise<void> {
    this.isLoading = true;
    this.error = null;
    try {
      const topics = await this._api.fetchTopics();
      runInAction(() => {
        this.topics = topics;
        this.isLoading = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to fetch topics");
        this.isLoading = false;
      });
    }
  }

  async submitTopic(content: string): Promise<boolean> {
    try {
      const newTopic = await this._api.createTopic(content);
      runInAction(() => {
        if (!this.topics.some((t) => t.id === newTopic.id)) {
          this.topics = [...this.topics, newTopic];
        }
      });
      this.showToast(
        "Topic published successfully",
        "success"
      );
      return true;
    } catch (e) {
      this.showToast(
        extractErrorMessage(e, "Failed to create topic"),
        "error"
      );
      return false;
    }
  }

  showToast(
    message: string,
    type: "success" | "error"
  ): void {
    this.toast = { message, type };
  }

  dismissToast(): void {
    this.toast = null;
  }

  private handleWebSocketMessage(data: unknown): void {
    logger.log("WebSocket message received:", data);
    if (!isWebSocketMessage(data)) return;

    switch (data.type) {
      case "score_update":
        this.handleScoreUpdate(data.topic_id, data.score);
        break;
      case "topic_censured":
        this.handleTopicCensured(data.topic_id);
        break;
      case "new_topic":
        this.handleNewTopic(data.topic);
        break;
    }
  }

  private handleScoreUpdate(
    topicId: string,
    score: number
  ): void {
    if (this.isVoting.has(topicId)) return;
    this.setTopicScore(topicId, score);
  }

  private handleTopicCensured(topicId: string): void {
    this.topics = this.topics.filter(
      (t) => t.id !== topicId
    );
    this.showToast(
      "Topic has been censured by the community",
      "success"
    );
  }

  private handleNewTopic(topic: NewTopicMessage["topic"]): void {
    if (this.topics.some((t) => t.id === topic.id)) return;

    this.topics = [...this.topics, topic];
  }

  private handleReconnect(): void {
    this.fetchTopics();
  }

  dispose(): void {
    this._ws?.disconnect();
  }
}
