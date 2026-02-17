import { ThumbsUp, ThumbsDown } from "lucide-react";

interface TopicCardScoreProps {
  topicId: string;
  score: number;
  userVote: number | null;
  canVote: boolean;
  isVoting: boolean;
  onUpvote: () => void;
  onDownvote: () => void;
}

const BTN_CLASS =
  "flex h-10 w-10 items-center justify-center rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-slate-900";

function getUpvoteClasses(userVote: number | null, canVote: boolean, isVoting: boolean): string {
  if (!canVote || isVoting) {
    return `${BTN_CLASS} text-slate-600 cursor-not-allowed opacity-50`;
  }
  if (userVote === 1) {
    return `${BTN_CLASS} bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30`;
  }
  return `${BTN_CLASS} text-slate-500 hover:bg-emerald-500/10 hover:text-emerald-400`;
}

function getDownvoteClasses(userVote: number | null, canVote: boolean, isVoting: boolean): string {
  if (!canVote || isVoting) {
    return `${BTN_CLASS} text-slate-600 cursor-not-allowed opacity-50`;
  }
  if (userVote === -1) {
    return `${BTN_CLASS} bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30`;
  }
  return `${BTN_CLASS} text-slate-500 hover:bg-rose-500/10 hover:text-rose-400`;
}

export function TopicCardScore({
  topicId,
  score,
  userVote,
  canVote,
  isVoting,
  onUpvote,
  onDownvote,
}: TopicCardScoreProps) {
  let scoreColor = "text-slate-500";
  if (score > 0) scoreColor = "text-emerald-400";
  else if (score < 0) scoreColor = "text-rose-400";

  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-700 bg-slate-900/30 p-4 sm:w-20 sm:flex-col sm:justify-center sm:border-b-0 sm:border-r">
      <button
        id={`topic-upvote-${topicId}`}
        className={getUpvoteClasses(userVote, canVote, isVoting)}
        aria-label="Upvote"
        disabled={!canVote || isVoting}
        onClick={onUpvote}
      >
        <ThumbsUp size={20} />
      </button>
      <span
        className={`text-lg font-bold tabular-nums transition-colors duration-300 ${scoreColor}`}
      >
        {score}
      </span>
      <button
        id={`topic-downvote-${topicId}`}
        className={getDownvoteClasses(userVote, canVote, isVoting)}
        aria-label="Downvote"
        disabled={!canVote || isVoting}
        onClick={onDownvote}
      >
        <ThumbsDown size={20} />
      </button>
    </div>
  );
}
