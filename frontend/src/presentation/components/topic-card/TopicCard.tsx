import { memo } from "react";
import type { Topic } from "@domain/entities/Topic";
import { TopicCardScore } from "./TopicCardScore";
import { TopicCardContent } from "./TopicCardContent";
import { TopicCardRemovalBar } from "./TopicCardRemovalBar";

interface TopicCardProps {
  topic: Topic;
}

export const TopicCard = memo(function TopicCard({ topic }: TopicCardProps) {
  return (
    <div
      id={`topic-card-${topic.id}`}
      className="flex animate-fade-in flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-800 shadow-lg shadow-slate-900/20 transition-all duration-200 hover:shadow-xl hover:shadow-slate-900/30 sm:flex-row"
    >
      <TopicCardScore score={topic.score} />
      <div className="flex flex-1 flex-col">
        <TopicCardContent
          content={topic.content}
          createdAt={topic.created_at}
          score={topic.score}
        />
        <TopicCardRemovalBar score={topic.score} />
      </div>
    </div>
  );
});
