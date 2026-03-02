import type { FormEvent } from "react";
import { observer } from "mobx-react-lite";
import { BarChart3 } from "lucide-react";
import { usePollCreationViewModel } from "@presentation/view-models";
import { PollCreationFormQuestion } from "./PollCreationFormQuestion";
import { PollCreationFormOptions } from "./PollCreationFormOptions";
import { PollCreationFormSubmitButton } from "./PollCreationFormSubmitButton";

interface PollCreationFormProps {
  eventId: string;
  onCreated?: () => void;
}

export const PollCreationForm = observer(
  function PollCreationForm({
    eventId,
    onCreated,
  }: PollCreationFormProps) {
    const vm = usePollCreationViewModel();

    const handleSubmit = async (e: FormEvent) => {
      e.preventDefault();
      await vm.submit(eventId);
      if (vm.createdPoll) {
        onCreated?.();
        vm.reset();
      }
    };

    return (
      <div
        id="poll-creation-form"
        className="rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
      >
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
          <BarChart3 className="text-indigo-400" size={20} />
          Create a Poll
        </h3>
        <form onSubmit={handleSubmit}>
          <PollCreationFormQuestion
            value={vm.question}
            onChange={vm.setQuestion}
          />
          <PollCreationFormOptions
            options={[...vm.options]}
            onChange={vm.setOptionText}
            onRemove={vm.removeOption}
            onAdd={vm.addOption}
            canAdd={vm.canAddOption}
            canRemove={vm.canRemoveOption}
          />
          {vm.error && (
            <p className="mb-3 text-sm text-red-400">{vm.error}</p>
          )}
          <PollCreationFormSubmitButton
            disabled={!vm.isValid}
            isSubmitting={vm.isSubmitting}
          />
        </form>
      </div>
    );
  },
);
