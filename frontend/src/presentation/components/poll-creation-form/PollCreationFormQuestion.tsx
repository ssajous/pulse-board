import { memo } from "react";

interface PollCreationFormQuestionProps {
  value: string;
  onChange: (value: string) => void;
}

export const PollCreationFormQuestion = memo(
  function PollCreationFormQuestion({
    value,
    onChange,
  }: PollCreationFormQuestionProps) {
    return (
      <div className="mb-4">
        <label
          htmlFor="poll-question-input"
          className="mb-1 block text-sm font-medium text-slate-300"
        >
          Question
        </label>
        <input
          id="poll-question-input"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="What would you like to ask?"
          maxLength={500}
          className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none"
        />
      </div>
    );
  },
);
