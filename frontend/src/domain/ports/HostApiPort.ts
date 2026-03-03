import type { Topic } from "@domain/entities/Topic";
import type { EventStats } from "@domain/entities/EventStats";

export interface UpdateTopicStatusResponse {
  readonly topic_id: string;
  readonly new_status: string;
}

export interface CloseEventResponse {
  readonly event_id: string;
  readonly status: string;
}

export interface HostApiPort {
  updateTopicStatus(
    eventId: string,
    topicId: string,
    status: string,
  ): Promise<UpdateTopicStatusResponse>;
  closeEvent(eventId: string): Promise<CloseEventResponse>;
  getEventStats(eventId: string): Promise<EventStats>;
  getAllTopics(eventId: string): Promise<Topic[]>;
}
