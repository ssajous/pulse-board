import { observer } from "mobx-react-lite";
import { AnimatePresence, motion } from "motion/react";
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

  if (vm.isLoading) {
    return (
      <div id="topic-list">
        <LoadingSpinner />
      </div>
    );
  }

  if (vm.isEmpty) {
    return (
      <div id="topic-list">
        <TopicListEmpty />
      </div>
    );
  }

  return (
    <div id="topic-list" className="space-y-4">
      <AnimatePresence mode="popLayout">
        {vm.sortedTopics.map((topic) => (
          <motion.div
            key={topic.id}
            layout
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{
              layout: { type: "spring", stiffness: 350, damping: 30 },
              opacity: { duration: 0.2 },
            }}
          >
            <TopicCard topic={topic} />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
});
