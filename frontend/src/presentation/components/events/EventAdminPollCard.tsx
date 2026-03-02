import { memo, useEffect } from "react";
import { BarChart3 } from "lucide-react";
import type { Poll, PollResults } from "@domain/entities/Poll";
import { PollResultsBar } from "@presentation/components/poll-results/PollResultsBar";

interface EventAdminPollCardProps {
  poll: Poll;
  isActivating: boolean;
  results: PollResults | null;
  onToggleActive: (pollId: string) => void;
  onLoadResults: (pollId: string) => void;
}

export const EventAdminPollCard = memo(
  function EventAdminPollCard({
    poll,
    isActivating,
    results,
    onToggleActive,
    onLoadResults,
  }: EventAdminPollCardProps) {
    useEffect(() => {
      onLoadResults(poll.id);
    }, [poll.id, onLoadResults]);

    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800 p-5">
        <div className="mb-3 flex items-start justify-between">
          <div className="flex items-center gap-2">
            <BarChart3
              size={16}
              className="text-indigo-400"
            />
            <h4 className="font-medium text-slate-100">
              {poll.question}
            </h4>
          </div>
          <button
            onClick={() => onToggleActive(poll.id)}
            disabled={isActivating}
            className={`shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              poll.is_active
                ? "bg-red-900/30 text-red-400 hover:bg-red-900/50"
                : "bg-green-900/30 text-green-400 hover:bg-green-900/50"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {isActivating
              ? "..."
              : poll.is_active
                ? "Deactivate"
                : "Activate"}
          </button>
        </div>
        <div className="mb-3 flex items-center gap-2">
          <span
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              poll.is_active
                ? "bg-green-900/30 text-green-400"
                : "bg-slate-700 text-slate-400"
            }`}
          >
            {poll.is_active ? "Active" : "Inactive"}
          </span>
          <span className="text-xs text-slate-500">
            {poll.options.length} options
          </span>
        </div>
        {results && results.total_votes > 0 && (
          <div className="mt-3 border-t border-slate-700 pt-3">
            <p className="mb-2 text-sm text-slate-400">
              {results.total_votes}{" "}
              {results.total_votes === 1 ? "vote" : "votes"}
            </p>
            {[...results.options]
              .sort((a, b) => b.count - a.count)
              .map((option) => (
                <PollResultsBar
                  key={option.option_id}
                  option={option}
                />
              ))}
          </div>
        )}
        {results && results.total_votes === 0 && (
          <p className="mt-2 text-xs text-slate-500">
            No votes yet
          </p>
        )}
      </div>
    );
  },
);
