import { motion } from "motion/react";
import type { PresentTopic } from "@domain/entities/PresentState";

interface PresentTopicFeedProps {
  topics: PresentTopic[];
}

export const PresentTopicFeed = ({
  topics,
}: PresentTopicFeedProps) => {
  return (
    <div id="present-topic-feed" className="flex flex-col gap-3">
      <h2 className="text-2xl font-bold opacity-80">Top Topics</h2>
      {topics.length === 0 && (
        <p className="text-base opacity-50">
          No topics submitted yet.
        </p>
      )}
      {topics.map((topic, index) => (
        <motion.div
          key={topic.id}
          id={`present-topic-${topic.id}`}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex items-start gap-3 rounded-lg border border-current/10 bg-current/5 px-4 py-3"
        >
          <span className="mt-0.5 min-w-[1.75rem] text-base font-bold opacity-50">
            #{index + 1}
          </span>
          <span className="flex-1 text-2xl leading-snug">
            {topic.content}
          </span>
          <span className="mt-0.5 rounded bg-current/10 px-2 py-0.5 text-sm font-medium">
            {topic.score}
          </span>
        </motion.div>
      ))}
    </div>
  );
};
