import { observer } from "mobx-react-lite";
import { MessageSquare } from "lucide-react";
import type { Poll } from "@domain/entities/Poll";
import type { OpenTextPollViewModel } from "@presentation/view-models/OpenTextPollViewModel";
import { OpenTextResponseCard } from "./OpenTextResponseCard";

interface OpenTextPollResultsProps {
  poll: Poll;
  vm: OpenTextPollViewModel;
}

export const OpenTextPollResults = observer(function OpenTextPollResults({
  poll,
  vm,
}: OpenTextPollResultsProps) {
  return (
    <div id="poll-results" className="space-y-4">
      <div className="flex items-center gap-2">
        <MessageSquare size={16} className="text-emerald-400" />
        <span
          id="open-text-results-count"
          className="text-sm font-medium text-slate-300"
        >
          {vm.totalResponses} response{vm.totalResponses !== 1 ? "s" : ""}
        </span>
      </div>
      <div
        id="open-text-results-list"
        className="max-h-96 space-y-3 overflow-y-auto pr-1"
      >
        {vm.responses.map((response) => (
          <OpenTextResponseCard key={response.id} response={response} />
        ))}
      </div>
      {vm.hasMore && (
        <button
          id="open-text-results-load-more"
          type="button"
          disabled={vm.isLoadingMore}
          onClick={() => vm.loadMoreResponses(poll.id)}
          className={[
            "w-full rounded-lg py-2 text-sm font-medium transition-colors",
            !vm.isLoadingMore
              ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
              : "cursor-not-allowed bg-slate-700 text-slate-500",
          ].join(" ")}
        >
          {vm.isLoadingMore ? "Loading…" : "Load more responses"}
        </button>
      )}
    </div>
  );
});
