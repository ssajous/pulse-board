import { observer } from "mobx-react-lite";
import { BarChart3 } from "lucide-react";
import { usePollParticipationViewModel } from "@presentation/view-models";
import { PollResults } from "@presentation/components/poll-results";
import { PollParticipationQuestion } from "./PollParticipationQuestion";
import { PollParticipationOptionList } from "./PollParticipationOptionList";
import { PollParticipationSubmitButton } from "./PollParticipationSubmitButton";

export const PollParticipation = observer(
  function PollParticipation() {
    const vm = usePollParticipationViewModel();

    if (!vm.activePoll) return null;

    if (vm.showResults && vm.results) {
      return <PollResults results={vm.results} />;
    }

    return (
      <div
        id="poll-participation"
        className="mb-8 rounded-xl border border-l-4 border-slate-700 border-l-indigo-500 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
      >
        <div className="mb-2 flex items-center gap-2 text-sm font-medium text-indigo-400">
          <BarChart3 size={16} />
          Live Poll
        </div>
        <PollParticipationQuestion
          question={vm.activePoll.question}
        />
        <PollParticipationOptionList
          options={vm.activePoll.options}
          selectedOptionId={vm.selectedOptionId}
          isDisabled={vm.hasSubmitted}
          onSelect={vm.selectOption}
        />
        {vm.error && (
          <p className="mb-3 text-sm text-red-400">{vm.error}</p>
        )}
        <PollParticipationSubmitButton
          disabled={!vm.canSubmit}
          isSubmitting={vm.isSubmitting}
          onSubmit={vm.submit}
        />
      </div>
    );
  },
);
