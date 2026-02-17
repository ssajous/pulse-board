import { makeAutoObservable, runInAction } from "mobx";
import type { Topic } from "@domain/entities/Topic";
import type { TopicApiPort } from "@domain/ports/TopicApiPort";

export interface ToastMessage {
  message: string;
  type: "success" | "error";
}

export class TopicsViewModel {
  topics: Topic[] = [];
  isLoading = false;
  error: string | null = null;
  toast: ToastMessage | null = null;

  private readonly _api: TopicApiPort;

  constructor(api: TopicApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
    this.fetchTopics();
  }

  get sortedTopics(): Topic[] {
    return [...this.topics].sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    });
  }

  get isEmpty(): boolean {
    return this.topics.length === 0;
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
        this.error =
          e instanceof Error ? e.message : "Failed to fetch topics";
        this.isLoading = false;
      });
    }
  }

  async submitTopic(content: string): Promise<boolean> {
    try {
      await this._api.createTopic(content);
      await this.fetchTopics();
      this.showToast("Topic published successfully", "success");
      return true;
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Failed to create topic";
      this.showToast(message, "error");
      return false;
    }
  }

  showToast(message: string, type: "success" | "error"): void {
    this.toast = { message, type };
  }

  dismissToast(): void {
    this.toast = null;
  }
}
