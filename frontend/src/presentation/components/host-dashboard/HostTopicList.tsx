import { observer } from "mobx-react-lite";
import type { Topic, TopicStatus } from "@domain/entities/Topic";
import { HostTopicCard } from "./HostTopicCard";

interface TopicSectionProps {
  title: string;
  topics: Topic[];
  updatingTopicId: string | null;
  onUpdateStatus: (topicId: string, status: TopicStatus) => void;
  emptyMessage?: string;
}

const TopicSection = observer(function TopicSection({
  title,
  topics,
  updatingTopicId,
  onUpdateStatus,
  emptyMessage,
}: TopicSectionProps) {
  if (topics.length === 0 && !emptyMessage) return null;

  return (
    <div className="mb-6">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        {title} ({topics.length})
      </h3>
      {topics.length === 0 && emptyMessage ? (
        <p className="rounded-xl border border-slate-700 bg-slate-800 p-4 text-sm text-slate-500">
          {emptyMessage}
        </p>
      ) : (
        <div className="space-y-3">
          {topics.map((topic) => (
            <HostTopicCard
              key={topic.id}
              topic={topic}
              isUpdating={updatingTopicId === topic.id}
              onUpdateStatus={onUpdateStatus}
            />
          ))}
        </div>
      )}
    </div>
  );
});

interface HostTopicListProps {
  highlightedTopics: Topic[];
  activeTopics: Topic[];
  answeredTopics: Topic[];
  archivedTopics: Topic[];
  updatingTopicId: string | null;
  onUpdateStatus: (topicId: string, status: TopicStatus) => void;
}

export const HostTopicList = observer(function HostTopicList({
  highlightedTopics,
  activeTopics,
  answeredTopics,
  archivedTopics,
  updatingTopicId,
  onUpdateStatus,
}: HostTopicListProps) {
  const total =
    highlightedTopics.length
    + activeTopics.length
    + answeredTopics.length
    + archivedTopics.length;

  return (
    <div id="host-topic-list">
      {total === 0 ? (
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-8 text-center">
          <p className="text-slate-400">
            No topics submitted yet.
          </p>
        </div>
      ) : (
        <>
          <TopicSection
            title="Highlighted"
            topics={highlightedTopics}
            updatingTopicId={updatingTopicId}
            onUpdateStatus={onUpdateStatus}
          />
          <TopicSection
            title="Active"
            topics={activeTopics}
            updatingTopicId={updatingTopicId}
            onUpdateStatus={onUpdateStatus}
            emptyMessage="No active topics."
          />
          <TopicSection
            title="Answered"
            topics={answeredTopics}
            updatingTopicId={updatingTopicId}
            onUpdateStatus={onUpdateStatus}
          />
          <TopicSection
            title="Archived"
            topics={archivedTopics}
            updatingTopicId={updatingTopicId}
            onUpdateStatus={onUpdateStatus}
          />
        </>
      )}
    </div>
  );
});
