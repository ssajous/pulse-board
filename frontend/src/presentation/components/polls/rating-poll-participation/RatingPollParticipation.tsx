import { observer } from "mobx-react-lite";
import { BarChart3 } from "lucide-react";
import type { Poll } from "@domain/entities/Poll";
import type { RatingPollViewModel } from "@presentation/view-models/RatingPollViewModel";
import { RatingPollResults } from "../rating-poll-results";
import { RatingStarInput } from "./RatingStarInput";

interface RatingPollParticipationProps {
  poll: Poll;
  vm: RatingPollViewModel;
}

export const RatingPollParticipation = observer(
  function RatingPollParticipation({
    poll,
    vm,
  }: RatingPollParticipationProps) {
    if (vm.hasSubmitted && vm.results) {
      return <RatingPollResults results={vm.results} />;
    }

    return (
      <div
        id="poll-participation"
        className="mb-8 rounded-xl border border-l-4 border-slate-700 border-l-amber-500 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
      >
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-amber-400">
          <BarChart3 size={16} />
          Live Poll — Rating
        </div>
        <p
          id="rating-poll-question"
          className="mb-6 text-lg font-semibold text-slate-100"
        >
          {poll.question}
        </p>
        <div className="mb-6">
          <RatingStarInput vm={vm} />
        </div>
        {vm.error && (
          <p className="mb-3 text-sm text-red-400">{vm.error}</p>
        )}
        <button
          id="rating-poll-submit"
          type="button"
          disabled={!vm.canSubmit}
          onClick={() => vm.submitRating(poll.id)}
          className={[
            "rounded-lg px-6 py-2.5 text-sm font-semibold transition-colors",
            vm.canSubmit
              ? "bg-amber-500 text-white hover:bg-amber-600"
              : "cursor-not-allowed bg-slate-700 text-slate-500",
          ].join(" ")}
        >
          {vm.isSubmitting ? "Submitting…" : "Submit Rating"}
        </button>
      </div>
    );
  },
);
