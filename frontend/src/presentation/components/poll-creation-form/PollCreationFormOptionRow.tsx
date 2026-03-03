import { memo } from "react";
import { X } from "lucide-react";

interface PollCreationFormOptionRowProps {
  index: number;
  value: string;
  onChange: (index: number, text: string) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}

export const PollCreationFormOptionRow = memo(
  function PollCreationFormOptionRow({
    index,
    value,
    onChange,
    onRemove,
    canRemove,
  }: PollCreationFormOptionRowProps) {
    return (
      <div className="flex items-center gap-2">
        <input
          id={`poll-option-input-${index}`}
          type="text"
          value={value}
          onChange={(e) => onChange(index, e.target.value)}
          placeholder={`Option ${index + 1}`}
          className="flex-1 rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none"
        />
        {canRemove && (
          <button
            type="button"
            onClick={() => onRemove(index)}
            className="rounded p-1 text-red-400 hover:text-red-300"
            aria-label={`Remove option ${index + 1}`}
          >
            <X size={16} />
          </button>
        )}
      </div>
    );
  },
);
