import type { Topic } from "@domain/entities/Topic";

export interface TopicApiPort {
  fetchTopics(): Promise<Topic[]>;
  createTopic(content: string): Promise<Topic>;
}
