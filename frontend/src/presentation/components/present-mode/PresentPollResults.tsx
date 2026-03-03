import type { PresentActivePoll } from "@domain/entities/PresentState";

interface PresentPollResultsProps {
  poll: PresentActivePoll;
}

export const PresentPollResults = ({
  poll,
}: PresentPollResultsProps) => {
  return (
    <div id="present-poll-results" className="flex flex-col gap-6">
      <h2 className="text-4xl font-bold leading-tight">
        {poll.question}
      </h2>
      <p className="text-sm opacity-60">
        {poll.total_votes}{" "}
        {poll.total_votes === 1 ? "vote" : "votes"} total
      </p>
      <div className="flex flex-col gap-4">
        {poll.options.map((option) => (
          <div
            key={option.option_id}
            id={`present-poll-bar-${option.option_id}`}
            className="flex flex-col gap-1"
          >
            <div className="flex items-center justify-between">
              <span className="text-2xl font-medium">
                {option.text}
              </span>
              <span className="text-base opacity-70">
                {option.count} votes &middot; {option.percentage}%
              </span>
            </div>
            <div className="h-8 w-full overflow-hidden rounded-lg bg-current/10">
              <div
                className="h-full min-w-1 rounded-lg bg-indigo-500 transition-all duration-500 ease-out"
                style={{ width: `${Math.max(option.percentage, 0)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
