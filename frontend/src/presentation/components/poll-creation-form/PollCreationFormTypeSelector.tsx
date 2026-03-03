import { memo } from "react";
import { BarChart3, Star, MessageSquare } from "lucide-react";
import type { PollType } from "@domain/entities/Poll";

interface PollTypeOption {
  readonly type: PollType;
  readonly label: string;
  readonly icon: React.ReactNode;
  readonly id: string;
}

const POLL_TYPE_OPTIONS: PollTypeOption[] = [
  {
    type: "multiple_choice",
    label: "Multiple Choice",
    icon: <BarChart3 size={16} />,
    id: "poll-type-option-multiple-choice",
  },
  {
    type: "rating",
    label: "Star Rating",
    icon: <Star size={16} />,
    id: "poll-type-option-rating",
  },
  {
    type: "open_text",
    label: "Open Response",
    icon: <MessageSquare size={16} />,
    id: "poll-type-option-open-text",
  },
];

interface PollCreationFormTypeSelectorProps {
  selectedType: PollType;
  onChange: (type: PollType) => void;
}

export const PollCreationFormTypeSelector = memo(
  function PollCreationFormTypeSelector({
    selectedType,
    onChange,
  }: PollCreationFormTypeSelectorProps) {
    return (
      <div id="poll-type-selector" className="mb-4">
        <p className="mb-2 text-sm font-medium text-slate-300">
          Poll Type
        </p>
        <div className="flex gap-2">
          {POLL_TYPE_OPTIONS.map(({ type, label, icon, id }) => {
            const isSelected = type === selectedType;
            return (
              <button
                key={type}
                id={id}
                type="button"
                onClick={() => onChange(type)}
                className={[
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isSelected
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-700 text-slate-300 hover:bg-slate-600",
                ].join(" ")}
              >
                {icon}
                {label}
              </button>
            );
          })}
        </div>
      </div>
    );
  },
);
