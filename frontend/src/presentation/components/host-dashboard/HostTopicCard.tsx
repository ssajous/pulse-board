import { memo } from "react";
import { Star, CheckCircle, Archive, RotateCcw } from "lucide-react";
import type { Topic, TopicStatus } from "@domain/entities/Topic";

interface HostTopicCardProps {
  topic: Topic;
  isUpdating: boolean;
  onUpdateStatus: (topicId: string, status: TopicStatus) => void;
}

const STATUS_BADGE: Record<
  NonNullable<TopicStatus>,
  { label: string; className: string }
> = {
  active: {
    label: "Active",
    className:
      "border-slate-600 bg-slate-700 text-slate-300",
  },
  highlighted: {
    label: "Highlighted",
    className:
      "border-amber-500/30 bg-amber-500/20 text-amber-300",
  },
  answered: {
    label: "Answered",
    className:
      "border-green-500/30 bg-green-500/20 text-green-300",
  },
  archived: {
    label: "Archived",
    className:
      "border-slate-600 bg-slate-700/50 text-slate-500",
  },
};

export const HostTopicCard = memo(function HostTopicCard({
  topic,
  isUpdating,
  onUpdateStatus,
}: HostTopicCardProps) {
  const status = topic.status ?? "active";
  const badge = STATUS_BADGE[status];
  const isArchived = status === "archived";
  const isHighlighted = status === "highlighted";
  const isAnswered = status === "answered";

  const handleHighlight = () => onUpdateStatus(topic.id, "highlighted");
  const handleAnswer = () => onUpdateStatus(topic.id, "answered");
  const handleArchive = () => onUpdateStatus(topic.id, "archived");
  const handleRestore = () => onUpdateStatus(topic.id, "active");

  return (
    <div
      id={`host-topic-row-${topic.id}`}
      className={`flex items-start gap-3 rounded-xl border p-4 transition-all ${
        isHighlighted
          ? "border-amber-500/30 bg-amber-900/10"
          : isAnswered
            ? "border-green-500/20 bg-green-900/10"
            : isArchived
              ? "border-slate-700/50 bg-slate-800/50 opacity-60"
              : "border-slate-700 bg-slate-800"
      }`}
    >
      <div className="min-w-0 flex-1">
        <p
          className={`break-words text-sm leading-relaxed ${
            isArchived ? "text-slate-500" : "text-slate-200"
          }`}
        >
          {topic.content}
        </p>
        <div className="mt-2 flex items-center gap-3">
          <span
            id={`host-topic-status-${topic.id}`}
            className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${badge.className}`}
          >
            {badge.label}
          </span>
          <span className="text-xs text-slate-500">
            Score: {topic.score}
          </span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {!isHighlighted && !isArchived && (
          <button
            id={`host-topic-highlight-btn-${topic.id}`}
            onClick={handleHighlight}
            disabled={isUpdating}
            title="Highlight"
            className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-1.5 text-amber-400 transition-colors hover:bg-amber-500/20 disabled:opacity-40"
          >
            <Star size={14} />
          </button>
        )}
        {!isAnswered && !isArchived && (
          <button
            id={`host-topic-answered-btn-${topic.id}`}
            onClick={handleAnswer}
            disabled={isUpdating}
            title="Mark answered"
            className="rounded-lg border border-green-500/30 bg-green-500/10 p-1.5 text-green-400 transition-colors hover:bg-green-500/20 disabled:opacity-40"
          >
            <CheckCircle size={14} />
          </button>
        )}
        {!isArchived && (
          <button
            id={`host-topic-archive-btn-${topic.id}`}
            onClick={handleArchive}
            disabled={isUpdating}
            title="Archive"
            className="rounded-lg border border-slate-600 bg-slate-700/50 p-1.5 text-slate-400 transition-colors hover:bg-slate-700 disabled:opacity-40"
          >
            <Archive size={14} />
          </button>
        )}
        {isArchived && (
          <button
            id={`host-topic-restore-btn-${topic.id}`}
            onClick={handleRestore}
            disabled={isUpdating}
            title="Restore"
            className="rounded-lg border border-slate-600 bg-slate-700/50 p-1.5 text-slate-400 transition-colors hover:bg-slate-700 disabled:opacity-40"
          >
            <RotateCcw size={14} />
          </button>
        )}
      </div>
    </div>
  );
});
