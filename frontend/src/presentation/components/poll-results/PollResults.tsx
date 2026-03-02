import { memo } from "react";
import { BarChart3 } from "lucide-react";
import type { PollResults as PollResultsType } from "@domain/entities/Poll";
import { PollResultsHeader } from "./PollResultsHeader";
import { PollResultsBar } from "./PollResultsBar";

interface PollResultsProps {
  results: PollResultsType;
}

export const PollResults = memo(function PollResults({
  results,
}: PollResultsProps) {
  const sortedOptions = [...results.options].sort(
    (a, b) => b.count - a.count,
  );

  return (
    <div
      id="poll-results"
      className="mb-8 rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
    >
      <div className="mb-2 flex items-center gap-2 text-sm font-medium text-indigo-400">
        <BarChart3 size={16} />
        Poll Results
      </div>
      <PollResultsHeader
        question={results.question}
        totalVotes={results.total_votes}
      />
      <div>
        {sortedOptions.map((option) => (
          <PollResultsBar key={option.option_id} option={option} />
        ))}
      </div>
    </div>
  );
});
