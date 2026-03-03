import { memo } from "react";

interface PollResultsHeaderProps {
  question: string;
  totalVotes: number;
}

export const PollResultsHeader = memo(
  function PollResultsHeader({
    question,
    totalVotes,
  }: PollResultsHeaderProps) {
    return (
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-100">
          {question}
        </h3>
        <p className="text-sm text-slate-400">
          {totalVotes} {totalVotes === 1 ? "vote" : "votes"} total
        </p>
      </div>
    );
  },
);
