import { memo } from "react";
import type { Poll, PollResults } from "@domain/entities/Poll";
import { EventAdminPollCard } from "./EventAdminPollCard";

interface EventAdminPollListProps {
  polls: Poll[];
  activatingPollId: string | null;
  pollResults: Map<string, PollResults>;
  onToggleActive: (pollId: string) => void;
  onLoadResults: (pollId: string) => void;
}

export const EventAdminPollList = memo(
  function EventAdminPollList({
    polls,
    activatingPollId,
    pollResults,
    onToggleActive,
    onLoadResults,
  }: EventAdminPollListProps) {
    if (polls.length === 0) {
      return (
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6 text-center">
          <p className="text-slate-400">
            No polls created yet. Create your first poll above.
          </p>
        </div>
      );
    }

    return (
      <div>
        <h3 className="mb-4 text-lg font-semibold text-slate-100">
          Polls ({polls.length})
        </h3>
        <div className="space-y-4">
          {polls.map((poll) => (
            <EventAdminPollCard
              key={poll.id}
              poll={poll}
              isActivating={activatingPollId === poll.id}
              results={pollResults.get(poll.id) ?? null}
              onToggleActive={onToggleActive}
              onLoadResults={onLoadResults}
            />
          ))}
        </div>
      </div>
    );
  },
);
