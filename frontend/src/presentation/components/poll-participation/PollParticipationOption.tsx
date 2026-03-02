import { memo } from "react";
import type { PollOption } from "@domain/entities/Poll";

interface PollParticipationOptionProps {
  option: PollOption;
  isSelected: boolean;
  isDisabled: boolean;
  onSelect: (id: string) => void;
}

export const PollParticipationOption = memo(
  function PollParticipationOption({
    option,
    isSelected,
    isDisabled,
    onSelect,
  }: PollParticipationOptionProps) {
    const borderClass = isSelected
      ? "border-indigo-500 bg-indigo-900/30"
      : "border-slate-600 bg-slate-700/50";

    return (
      <button
        id={`poll-option-radio-${option.id}`}
        type="button"
        onClick={() => onSelect(option.id)}
        disabled={isDisabled}
        className={`flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${borderClass} ${
          isDisabled
            ? "cursor-not-allowed opacity-50"
            : "cursor-pointer hover:border-indigo-400"
        }`}
      >
        <div
          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
            isSelected
              ? "border-indigo-500 bg-indigo-500"
              : "border-slate-400"
          }`}
        >
          {isSelected && (
            <div className="h-2 w-2 rounded-full bg-white" />
          )}
        </div>
        <span className="text-slate-100">{option.text}</span>
      </button>
    );
  },
);
