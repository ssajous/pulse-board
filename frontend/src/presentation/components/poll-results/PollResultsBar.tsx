import { memo } from "react";
import type { PollOptionResult } from "@domain/entities/Poll";

interface PollResultsBarProps {
  option: PollOptionResult;
}

export const PollResultsBar = memo(function PollResultsBar({
  option,
}: PollResultsBarProps) {
  return (
    <div
      id={`poll-results-bar-${option.option_id}`}
      className="mb-3"
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="text-sm text-slate-200">{option.text}</span>
        <span className="text-sm text-slate-400">
          {option.count} ({Math.round(option.percentage)}%)
        </span>
      </div>
      <div className="h-3 overflow-hidden rounded bg-slate-700">
        <div
          className="h-full rounded bg-indigo-600 transition-all duration-500"
          style={{ width: `${option.percentage}%` }}
        />
      </div>
    </div>
  );
});
