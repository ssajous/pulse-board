import { memo } from "react";

interface TopicFormInputProps {
  value: string;
  onChange: (value: string) => void;
  onFocus: () => void;
  onBlur: () => void;
  isFocused: boolean;
  isOverLimit: boolean;
  charCount: number;
}

export const TopicFormInput = memo(function TopicFormInput({
  value,
  onChange,
  onFocus,
  onBlur,
  isFocused,
  isOverLimit,
  charCount,
}: TopicFormInputProps) {
  let borderClass = "border-slate-600";
  if (isOverLimit) borderClass = "border-rose-500 ring-rose-500/20";
  else if (isFocused) borderClass = "border-indigo-500 ring-2 ring-indigo-500/20";

  return (
    <div className={`relative rounded-lg border transition-all duration-200 ${borderClass}`}>
      <textarea
        id="topic-input"
        className="min-h-[100px] w-full resize-none rounded-lg bg-transparent p-4 text-slate-200 outline-none placeholder:text-slate-500"
        placeholder="What's on your mind? Share an idea with the community..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        onBlur={onBlur}
        maxLength={300}
      />
      <div className="absolute bottom-3 right-3">
        <span
          className={`text-xs font-medium transition-colors ${
            isOverLimit ? "text-rose-400" : "text-slate-500"
          }`}
        >
          {charCount}/255
        </span>
      </div>
    </div>
  );
});
