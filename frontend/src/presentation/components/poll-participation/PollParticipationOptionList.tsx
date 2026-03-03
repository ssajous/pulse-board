import { memo } from "react";
import type { PollOption } from "@domain/entities/Poll";
import { PollParticipationOption } from "./PollParticipationOption";

interface PollParticipationOptionListProps {
  options: readonly PollOption[];
  selectedOptionId: string | null;
  isDisabled: boolean;
  onSelect: (id: string) => void;
}

export const PollParticipationOptionList = memo(
  function PollParticipationOptionList({
    options,
    selectedOptionId,
    isDisabled,
    onSelect,
  }: PollParticipationOptionListProps) {
    return (
      <div className="mb-4 space-y-2">
        {options.map((option) => (
          <PollParticipationOption
            key={option.id}
            option={option}
            isSelected={option.id === selectedOptionId}
            isDisabled={isDisabled}
            onSelect={onSelect}
          />
        ))}
      </div>
    );
  },
);
