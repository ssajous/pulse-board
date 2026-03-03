import { observer } from "mobx-react-lite";
import { MessageSquare, CheckCircle } from "lucide-react";
import type { Poll } from "@domain/entities/Poll";
import type { OpenTextPollViewModel } from "@presentation/view-models/OpenTextPollViewModel";
import { OpenTextPollResults } from "../open-text-poll-results";
import { OpenTextCharCounter } from "./OpenTextCharCounter";

const MAX_TEXT_LENGTH = 500;

interface OpenTextPollParticipationProps {
  poll: Poll;
  vm: OpenTextPollViewModel;
}

export const OpenTextPollParticipation = observer(
  function OpenTextPollParticipation({
    poll,
    vm,
  }: OpenTextPollParticipationProps) {
    return (
      <div
        id="poll-participation"
        className="mb-8 rounded-xl border border-l-4 border-slate-700 border-l-emerald-500 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
      >
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-400">
          <MessageSquare size={16} />
          Live Poll — Open Response
        </div>
        <p
          id="open-text-poll-question"
          className="mb-4 text-lg font-semibold text-slate-100"
        >
          {poll.question}
        </p>
        {vm.hasSubmitted ? (
          <div className="mb-6 flex items-center gap-2 rounded-lg bg-emerald-900/30 px-4 py-3 text-emerald-400">
            <CheckCircle size={18} />
            <span className="text-sm font-medium">
              Response submitted! Thank you.
            </span>
          </div>
        ) : (
          <div className="mb-4">
            <div className="mb-1 flex items-end justify-between">
              <label
                htmlFor="open-text-poll-textarea"
                className="sr-only"
              >
                Your response
              </label>
              <OpenTextCharCounter
                count={vm.charCount}
                max={MAX_TEXT_LENGTH}
                colorClass={vm.counterColorClass}
              />
            </div>
            <textarea
              id="open-text-poll-textarea"
              value={vm.inputText}
              onChange={(e) => vm.setInputText(e.target.value)}
              rows={4}
              placeholder="Type your response…"
              className="w-full resize-none rounded-lg border border-slate-600 bg-slate-900 p-3 text-sm text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        )}
        {vm.error && (
          <p className="mb-3 text-sm text-red-400">{vm.error}</p>
        )}
        {!vm.hasSubmitted && (
          <button
            id="open-text-poll-submit"
            type="button"
            disabled={vm.isSubmitDisabled}
            onClick={() => vm.submitResponse(poll.id)}
            className={[
              "rounded-lg px-6 py-2.5 text-sm font-semibold transition-colors",
              !vm.isSubmitDisabled
                ? "bg-emerald-600 text-white hover:bg-emerald-700"
                : "cursor-not-allowed bg-slate-700 text-slate-500",
            ].join(" ")}
          >
            {vm.isSubmitting ? "Submitting…" : "Submit Response"}
          </button>
        )}
        {vm.hasSubmitted && vm.totalResponses > 0 && (
          <div className="mt-6">
            <OpenTextPollResults poll={poll} vm={vm} />
          </div>
        )}
      </div>
    );
  },
);
