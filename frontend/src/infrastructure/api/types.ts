import type { Topic } from "@domain/entities/Topic";

export interface TopicsResponse {
  topics: Topic[];
}

export interface ErrorResponse {
  detail: string;
}
