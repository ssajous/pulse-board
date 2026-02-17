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

const BTN_BASE =
  "flex h-10 w-10 items-center justify-center rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-slate-900";

const DISABLED_CLASS = `${BTN_BASE} text-slate-600 cursor-not-allowed opacity-50`;

interface VoteColorScheme {
  active: string;
  hover: string;
}

const UPVOTE_COLORS: VoteColorScheme = {
  active: "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30",
  hover: "text-slate-500 hover:bg-emerald-500/10 hover:text-emerald-400",
};

const DOWNVOTE_COLORS: VoteColorScheme = {
  active: "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30",
  hover: "text-slate-500 hover:bg-rose-500/10 hover:text-rose-400",
};

function getVoteButtonClasses(
  isActive: boolean,
  canVote: boolean,
  isVoting: boolean,
  colors: VoteColorScheme
): string {
  if (!canVote || isVoting) return DISABLED_CLASS;
  if (isActive) return `${BTN_BASE} ${colors.active}`;
  return `${BTN_BASE} ${colors.hover}`;
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
        className={getVoteButtonClasses(userVote === 1, canVote, isVoting, UPVOTE_COLORS)}
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
        className={getVoteButtonClasses(userVote === -1, canVote, isVoting, DOWNVOTE_COLORS)}
        aria-label="Downvote"
        disabled={!canVote || isVoting}
        onClick={onDownvote}
      >
        <ThumbsDown size={20} />
      </button>
    </div>
  );
}
