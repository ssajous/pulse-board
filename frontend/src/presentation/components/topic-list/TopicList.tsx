import { observer } from "mobx-react-lite";
import { useTopicsViewModel } from "@presentation/view-models";
import { TopicCard } from "@presentation/components/topic-card";
import { TopicListEmpty } from "./TopicListEmpty";

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
    </div>
  );
}

export const TopicList = observer(function TopicList() {
  const vm = useTopicsViewModel();

  if (vm.isLoading) return <LoadingSpinner />;
  if (vm.isEmpty) return <TopicListEmpty />;

  return (
    <div id="topic-list" className="space-y-4">
      {vm.sortedTopics.map((topic) => (
        <TopicCard key={topic.id} topic={topic} />
      ))}
    </div>
  );
});
