import { observer } from "mobx-react-lite";
import { Cloud } from "lucide-react";
import type { Poll } from "@domain/entities/Poll";
import type { WordCloudViewModel } from "@presentation/view-models/WordCloudViewModel";
import { WordCloudVisualization } from "@presentation/components/polls/word-cloud-visualization";
import { WordCloudWordCounter } from "./WordCloudWordCounter";

interface WordCloudPollParticipationProps {
  poll: Poll;
  vm: WordCloudViewModel;
}

export const WordCloudPollParticipation = observer(
  function WordCloudPollParticipation({
    poll,
    vm,
  }: WordCloudPollParticipationProps) {
    return (
      <div
        id="word-cloud-participation"
        className="mb-8 rounded-xl border border-l-4 border-slate-700 border-l-violet-500 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
      >
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-violet-400">
          <Cloud size={16} />
          Word Cloud
        </div>
        <h3 className="mb-4 text-lg font-semibold text-slate-100">
          {poll.question}
        </h3>

        {vm.hasSubmitted ? (
          <div>
            <p className="mb-4 text-sm text-emerald-400">
              Response submitted!
            </p>
            <WordCloudVisualization frequencies={vm.frequencies} />
            {vm.totalResponses > 0 && (
              <p
                id="word-cloud-response-count"
                className="mt-2 text-center text-sm text-slate-400"
              >
                {vm.totalResponses}{" "}
                {vm.totalResponses === 1 ? "response" : "responses"}
              </p>
            )}
          </div>
        ) : (
          <div>
            <div className="mb-3 flex items-center gap-2">
              <input
                id="word-cloud-response-input"
                type="text"
                value={vm.inputText}
                onChange={(e) => vm.setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !vm.isSubmitDisabled) {
                    void vm.submitResponse(poll.id);
                  }
                }}
                placeholder="Enter 1-3 words..."
                maxLength={30}
                className="flex-1 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-slate-100 placeholder-slate-400 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
                disabled={vm.isSubmitting}
              />
              <WordCloudWordCounter
                wordCount={vm.wordCount}
                display={vm.wordCountDisplay}
              />
            </div>
            {vm.error && (
              <p className="mb-3 text-sm text-red-400">{vm.error}</p>
            )}
            <button
              id="word-cloud-submit-button"
              type="button"
              onClick={() => void vm.submitResponse(poll.id)}
              disabled={vm.isSubmitDisabled}
              className="w-full rounded-lg bg-violet-600 py-2 text-sm font-semibold text-white transition-colors hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {vm.isSubmitting ? "Submitting..." : "Submit"}
            </button>
          </div>
        )}
      </div>
    );
  },
);
