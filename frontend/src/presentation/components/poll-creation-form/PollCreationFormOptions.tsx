import { memo } from "react";
import { Plus } from "lucide-react";
import { PollCreationFormOptionRow } from "./PollCreationFormOptionRow";

interface PollCreationFormOptionsProps {
  options: string[];
  onChange: (index: number, text: string) => void;
  onRemove: (index: number) => void;
  onAdd: () => void;
  canAdd: boolean;
  canRemove: boolean;
}

export const PollCreationFormOptions = memo(
  function PollCreationFormOptions({
    options,
    onChange,
    onRemove,
    onAdd,
    canAdd,
    canRemove,
  }: PollCreationFormOptionsProps) {
    return (
      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-slate-300">
          Options
        </label>
        <div className="space-y-2">
          {options.map((option, index) => (
            <PollCreationFormOptionRow
              key={index}
              index={index}
              value={option}
              onChange={onChange}
              onRemove={onRemove}
              canRemove={canRemove}
            />
          ))}
        </div>
        {canAdd && (
          <button
            type="button"
            onClick={onAdd}
            className="mt-2 flex items-center gap-1 rounded-lg bg-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-600"
          >
            <Plus size={14} />
            Add option
          </button>
        )}
      </div>
    );
  },
);
