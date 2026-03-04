import { makeAutoObservable, runInAction } from "mobx";
import type { Event } from "@domain/entities/Event";
import type {
  PresentActivePoll,
  PresentTopic,
} from "@domain/entities/PresentState";
import type { PollType, WordFrequency } from "@domain/entities/Poll";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { PresentStateApiPort } from "@domain/ports/PresentStateApiPort";
import type { WebSocketPort } from "@domain/ports/WebSocketPort";
import { logger } from "@infrastructure/logger";
import { isRecord, extractErrorMessage } from "@infrastructure/utils/typeGuards";
import { buildWebSocketUrl } from "@infrastructure/websocket/buildWebSocketUrl";

const TOP_TOPICS_LIMIT = 10;
const PRESENT_THEME_KEY = "present-mode-theme";

export class PresentModeViewModel {
  event: Event | null = null;
  isLoading = false;
  error: string | null = null;
  activePoll: PresentActivePoll | null = null;
  topTopics: PresentTopic[] = [];
  participantCount = 0;
  isDarkTheme = true;

  private readonly _eventApi: EventApiPort;
  private readonly _presentStateApi: PresentStateApiPort;
  private readonly _ws: WebSocketPort | null;

  constructor(
    eventApi: EventApiPort,
    presentStateApi: PresentStateApiPort,
    ws?: WebSocketPort,
  ) {
    this._eventApi = eventApi;
    this._presentStateApi = presentStateApi;
    this._ws = ws ?? null;
    this.isDarkTheme =
      localStorage.getItem(PRESENT_THEME_KEY) !== "light";
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get hasActivePoll(): boolean {
    return this.activePoll !== null;
  }

  async initialize(code: string): Promise<void> {
    runInAction(() => {
      this.isLoading = true;
      this.error = null;
    });

    try {
      const event = await this._eventApi.getEventByCode(code);
      const presentState =
        await this._presentStateApi.getPresentState(event.id);

      runInAction(() => {
        this.event = event;
        this.activePoll = presentState.active_poll;
        this.topTopics = presentState.top_topics;
        this.participantCount = presentState.participant_count;
        this.isLoading = false;
      });

      if (this._ws) {
        this._ws.connect(buildWebSocketUrl(`events/${code}`));
        this._ws.onMessage(this.handleWebSocketMessage);
        this._ws.onReconnect(this.handleReconnect);
      }
    } catch (e) {
      runInAction(() => {
        this.error = extractErrorMessage(e, "Failed to load present mode");
        this.isLoading = false;
      });
    }
  }

  toggleTheme(): void {
    this.isDarkTheme = !this.isDarkTheme;
    localStorage.setItem(
      PRESENT_THEME_KEY,
      this.isDarkTheme ? "dark" : "light",
    );
  }

  dispose(): void {
    this._ws?.disconnect();
  }

  private handleWebSocketMessage(data: unknown): void {
    logger.log("PresentMode WebSocket message:", data);
    if (!isRecord(data)) return;

    switch (data.type as string) {
      case "poll_activated":
        this.handlePollActivated(data);
        break;
      case "poll_deactivated":
        this.activePoll = null;
        break;
      case "poll_results_updated":
        this.handlePollResultsUpdated(data);
        break;
      case "score_update":
        this.handleScoreUpdate(data);
        break;
      case "new_topic":
        this.handleNewTopic(data);
        break;
      case "topic_censured":
        this.handleTopicCensured(data);
        break;
    }
  }

  private handlePollActivated(
    data: Record<string, unknown>,
  ): void {
    if (
      typeof data.poll_id !== "string"
      || typeof data.question !== "string"
      || !Array.isArray(data.options)
    ) {
      return;
    }

    const options = data.options.map(
      (opt: Record<string, unknown>) => ({
        option_id: opt.id as string,
        text: opt.text as string,
        count: 0,
        percentage: 0,
      }),
    );

    this.activePoll = {
      poll_id: data.poll_id,
      question: data.question,
      total_votes: 0,
      options,
      poll_type: (data.poll_type as PollType) ?? "multiple_choice",
      frequencies: [],
      total_responses: 0,
    };
  }

  private handlePollResultsUpdated(
    data: Record<string, unknown>,
  ): void {
    if (!this.activePoll) return;

    if (data.poll_type === "word_cloud" && isRecord(data.results)) {
      const resultsObj = data.results as Record<string, unknown>;
      this.activePoll = {
        ...this.activePoll,
        poll_type: "word_cloud",
        frequencies: (resultsObj.words as WordFrequency[]) ?? [],
        total_responses:
          (resultsObj.total_responses as number) ?? 0,
      };
      return;
    }

    if (!Array.isArray(data.results)) return;

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

    this.activePoll = {
      ...this.activePoll,
      total_votes: typeof data.total_votes === "number"
        ? data.total_votes
        : totalVotes,
      options,
    };
  }

  private handleScoreUpdate(
    data: Record<string, unknown>,
  ): void {
    if (
      typeof data.topic_id !== "string"
      || typeof data.score !== "number"
    ) {
      return;
    }

    const updated = this.topTopics.map((t) =>
      t.id === data.topic_id
        ? { ...t, score: data.score as number }
        : t,
    );

    this.topTopics = this.sortAndLimitTopics(updated);
  }

  private handleNewTopic(data: Record<string, unknown>): void {
    if (!isRecord(data.topic)) return;
    const t = data.topic;
    if (
      typeof t.id !== "string"
      || typeof t.content !== "string"
      || typeof t.score !== "number"
    ) {
      return;
    }

    const alreadyExists = this.topTopics.some(
      (topic) => topic.id === t.id,
    );
    if (alreadyExists) return;

    const newTopic: PresentTopic = {
      id: t.id,
      content: t.content,
      score: t.score,
    };

    this.topTopics = this.sortAndLimitTopics([
      ...this.topTopics,
      newTopic,
    ]);
  }

  private sortAndLimitTopics(topics: PresentTopic[]): PresentTopic[] {
    return [...topics]
      .sort((a, b) => b.score - a.score)
      .slice(0, TOP_TOPICS_LIMIT);
  }

  private handleTopicCensured(
    data: Record<string, unknown>,
  ): void {
    if (typeof data.topic_id !== "string") return;
    this.topTopics = this.topTopics.filter(
      (t) => t.id !== data.topic_id,
    );
  }

  private async handleReconnect(): Promise<void> {
    if (!this.event) return;
    try {
      const presentState =
        await this._presentStateApi.getPresentState(
          this.event.id,
        );
      runInAction(() => {
        this.activePoll = presentState.active_poll;
        this.topTopics = presentState.top_topics;
        this.participantCount = presentState.participant_count;
      });
    } catch (e) {
      logger.error("Failed to refresh present state on reconnect", e);
    }
  }
}
