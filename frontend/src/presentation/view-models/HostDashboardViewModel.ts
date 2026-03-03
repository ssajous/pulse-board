import { makeAutoObservable, observable, runInAction } from "mobx";
import type { Event } from "@domain/entities/Event";
import type { Topic, TopicStatus } from "@domain/entities/Topic";
import type { Poll, PollResults } from "@domain/entities/Poll";
import type { EventStats } from "@domain/entities/EventStats";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import type { HostApiPort } from "@domain/ports/HostApiPort";
import type { WebSocketPort } from "@domain/ports/WebSocketPort";
import { logger } from "@infrastructure/logger";
import {
  isRecord,
  extractErrorMessage,
} from "@infrastructure/utils/typeGuards";
import { buildWebSocketUrl } from "@infrastructure/websocket/buildWebSocketUrl";

export class HostDashboardViewModel {
  event: Event | null = null;
  topics: Topic[] = [];
  polls: Poll[] = [];
  stats: EventStats | null = null;
  isLoading = true;
  error: string | null = null;
  updatingTopicId: string | null = null;
  isClosingEvent = false;
  codeCopied = false;
  pollResults: Map<string, PollResults> = observable.map();
  activatingPollId: string | null = null;

  private readonly _eventApi: EventApiPort;
  private readonly _pollApi: PollApiPort;
  private readonly _hostApi: HostApiPort;
  private readonly _ws: WebSocketPort | null;
  private _copyTimerId: ReturnType<typeof setTimeout> | null = null;

  constructor(
    eventApi: EventApiPort,
    pollApi: PollApiPort,
    hostApi: HostApiPort,
    ws?: WebSocketPort,
  ) {
    this._eventApi = eventApi;
    this._pollApi = pollApi;
    this._hostApi = hostApi;
    this._ws = ws ?? null;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get isClosed(): boolean {
    return this.event?.status === "closed";
  }

  get activeTopics(): Topic[] {
    return this.topics.filter(
      (t) => !t.status || t.status === "active",
    );
  }

  get highlightedTopics(): Topic[] {
    return this.topics.filter((t) => t.status === "highlighted");
  }

  get answeredTopics(): Topic[] {
    return this.topics.filter((t) => t.status === "answered");
  }

  get archivedTopics(): Topic[] {
    return this.topics.filter((t) => t.status === "archived");
  }

  get activePoll(): Poll | null {
    return this.polls.find((p) => p.is_active) ?? null;
  }

  get eventId(): string | null {
    return this.event?.id ?? null;
  }

  get pollApi(): PollApiPort {
    return this._pollApi;
  }

  async loadDashboard(code: string): Promise<void> {
    this.isLoading = true;
    this.error = null;

    try {
      const event = await this._eventApi.getEventByCode(code);
      runInAction(() => {
        this.event = event;
      });

      await Promise.all([
        this.loadTopics(),
        this.loadPolls(),
        this.loadStats(),
      ]);

      if (this._ws) {
        this._ws.connect(buildWebSocketUrl(`events/${event.code}`));
        this._ws.onMessage(this.handleWebSocketMessage);
        this._ws.onReconnect(this.handleReconnect);
      }

      runInAction(() => {
        this.isLoading = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to load dashboard");
        this.isLoading = false;
      });
    }
  }

  private async loadTopics(): Promise<void> {
    if (!this.event) return;
    try {
      const topics = await this._hostApi.getAllTopics(this.event.id);
      runInAction(() => {
        this.topics = topics;
      });
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to load topics");
      });
    }
  }

  private async loadPolls(): Promise<void> {
    if (!this.event) return;
    try {
      const polls = await this._pollApi.listPolls(this.event.id);
      runInAction(() => {
        this.polls = polls;
      });
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to load polls");
      });
    }
  }

  private async loadStats(): Promise<void> {
    if (!this.event) return;
    try {
      const stats = await this._hostApi.getEventStats(this.event.id);
      runInAction(() => {
        this.stats = stats;
      });
    } catch (e) {
      logger.error("Failed to load event stats", e);
    }
  }

  async updateTopicStatus(
    topicId: string,
    status: TopicStatus,
  ): Promise<void> {
    if (!this.event || this.updatingTopicId) return;

    this.updatingTopicId = topicId;
    try {
      await this._hostApi.updateTopicStatus(
        this.event.id,
        topicId,
        status,
      );
      runInAction(() => {
        this.topics = this.topics.map((t) =>
          t.id === topicId ? { ...t, status } : t,
        );
        this.updatingTopicId = null;
      });
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(
          e,
          "Failed to update topic status",
        );
        this.updatingTopicId = null;
      });
    }
  }

  async closeEvent(): Promise<void> {
    if (!this.event || this.isClosingEvent) return;

    this.isClosingEvent = true;
    try {
      await this._hostApi.closeEvent(this.event.id);
      runInAction(() => {
        if (this.event) {
          this.event = { ...this.event, status: "closed" };
        }
        this.isClosingEvent = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to close event");
        this.isClosingEvent = false;
      });
    }
  }

  copyEventCode(): void {
    if (!this.event) return;
    navigator.clipboard.writeText(this.event.code).then(() => {
      runInAction(() => {
        this.codeCopied = true;
      });
      this._copyTimerId = setTimeout(() => {
        runInAction(() => {
          this.codeCopied = false;
        });
      }, 2000);
    });
  }

  async togglePollActive(pollId: string): Promise<void> {
    const poll = this.polls.find((p) => p.id === pollId);
    if (!poll) return;

    this.activatingPollId = pollId;
    try {
      await this._pollApi.activatePoll(pollId, !poll.is_active);
      await this.loadPolls();
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to toggle poll");
      });
    } finally {
      runInAction(() => {
        this.activatingPollId = null;
      });
    }
  }

  async loadPollResults(pollId: string): Promise<void> {
    try {
      const results = await this._pollApi.getResults(pollId);
      runInAction(() => {
        this.pollResults.set(pollId, results as PollResults);
      });
    } catch {
      /* results may not exist yet */
    }
  }

  onPollCreated(_poll: Poll): void {
    this.loadPolls();
  }

  dismissError(): void {
    this.error = null;
  }

  dispose(): void {
    if (this._copyTimerId) {
      clearTimeout(this._copyTimerId);
    }
    this._ws?.disconnect();
  }

  private handleWebSocketMessage(data: unknown): void {
    if (!isRecord(data)) return;

    switch (data.type as string) {
      case "score_update":
        this.handleScoreUpdate(data);
        break;
      case "new_topic":
        this.handleNewTopic(data);
        break;
      case "topic_censured":
        this.handleTopicCensured(data);
        break;
      case "topic_status_changed":
        this.handleTopicStatusChanged(data);
        break;
      case "event_closed":
        if (this.event) {
          this.event = { ...this.event, status: "closed" };
        }
        break;
      case "poll_activated":
      case "poll_deactivated":
        this.loadPolls();
        break;
      case "poll_results_updated":
        this.handlePollResultsUpdated(data);
        break;
    }
  }

  private handleScoreUpdate(data: Record<string, unknown>): void {
    if (
      typeof data.topic_id !== "string"
      || typeof data.score !== "number"
    ) {
      return;
    }
    this.topics = this.topics.map((t) =>
      t.id === data.topic_id
        ? { ...t, score: data.score as number }
        : t,
    );
  }

  private handleNewTopic(data: Record<string, unknown>): void {
    if (!isRecord(data.topic)) return;
    const t = data.topic;
    if (
      typeof t.id !== "string"
      || typeof t.content !== "string"
      || typeof t.score !== "number"
      || typeof t.created_at !== "string"
    ) {
      return;
    }
    if (this.topics.some((topic) => topic.id === t.id)) return;

    const newTopic: Topic = {
      id: t.id,
      content: t.content,
      score: t.score,
      created_at: t.created_at,
      status: "active",
    };
    this.topics = [...this.topics, newTopic];
  }

  private handleTopicCensured(data: Record<string, unknown>): void {
    if (typeof data.topic_id !== "string") return;
    this.topics = this.topics.filter((t) => t.id !== data.topic_id);
  }

  private handleTopicStatusChanged(
    data: Record<string, unknown>,
  ): void {
    if (
      typeof data.topic_id !== "string"
      || typeof data.new_status !== "string"
    ) {
      return;
    }
    this.topics = this.topics.map((t) =>
      t.id === data.topic_id
        ? { ...t, status: data.new_status as TopicStatus }
        : t,
    );
  }

  private handlePollResultsUpdated(
    data: Record<string, unknown>,
  ): void {
    if (
      typeof data.poll_id !== "string"
      || !Array.isArray(data.results)
    ) {
      return;
    }
    const options = data.results as Array<{
      option_id: string;
      text: string;
      count: number;
      percentage: number;
    }>;
    const totalVotes = options.reduce(
      (sum, opt) => sum + opt.count,
      0,
    );
    const existing = this.pollResults.get(data.poll_id);
    if (!existing) return;
    this.pollResults.set(data.poll_id, {
      ...existing,
      total_votes:
        typeof data.total_votes === "number"
          ? data.total_votes
          : totalVotes,
      options,
    });
  }

  private async handleReconnect(): Promise<void> {
    if (!this.event) return;
    await Promise.all([
      this.loadTopics(),
      this.loadPolls(),
      this.loadStats(),
    ]);
  }
}
