import { observer } from "mobx-react-lite";
import type { Topic } from "@domain/entities/Topic";
import { useTopicsViewModel } from "@presentation/view-models";
import { TopicCardScore } from "./TopicCardScore";
import { TopicCardContent } from "./TopicCardContent";
import { TopicCardRemovalBar } from "./TopicCardRemovalBar";

interface TopicCardProps {
  topic: Topic;
}

export const TopicCard = observer(function TopicCard({ topic }: TopicCardProps) {
  const vm = useTopicsViewModel();

  return (
    <div
      id={`topic-card-${topic.id}`}
      className="flex animate-fade-in flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-800 shadow-lg shadow-slate-900/20 transition-all duration-200 hover:shadow-xl hover:shadow-slate-900/30 sm:flex-row"
    >
      <TopicCardScore
        topicId={topic.id}
        score={topic.score}
        userVote={vm.getUserVote(topic.id)}
        canVote={vm.canVote}
        isVoting={vm.isTopicVoting(topic.id)}
        onUpvote={() => vm.castVote(topic.id, "up")}
        onDownvote={() => vm.castVote(topic.id, "down")}
      />
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
