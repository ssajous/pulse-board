import { memo } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";

interface TopicCardScoreProps {
  score: number;
}

const BTN_CLASS =
  "flex h-10 w-10 items-center justify-center rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-slate-900";

export const TopicCardScore = memo(function TopicCardScore({
  score,
}: TopicCardScoreProps) {
  const scoreColor =
    score > 0
      ? "text-emerald-400"
      : score < 0
        ? "text-rose-400"
        : "text-slate-500";

  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-700 bg-slate-900/30 p-4 sm:w-20 sm:flex-col sm:justify-center sm:border-b-0 sm:border-r">
      <button
        className={`${BTN_CLASS} text-slate-500 hover:bg-emerald-500/10 hover:text-emerald-400`}
        aria-label="Upvote"
      >
        <ThumbsUp size={20} />
      </button>
      <span
        className={`text-lg font-bold tabular-nums transition-colors duration-300 ${scoreColor}`}
      >
        {score}
      </span>
      <button
        className={`${BTN_CLASS} text-slate-500 hover:bg-rose-500/10 hover:text-rose-400`}
        aria-label="Downvote"
      >
        <ThumbsDown size={20} />
      </button>
    </div>
  );
});
