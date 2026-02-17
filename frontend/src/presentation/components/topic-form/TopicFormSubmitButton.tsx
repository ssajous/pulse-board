import { memo } from "react";

interface TopicFormSubmitButtonProps {
  disabled: boolean;
}

export const TopicFormSubmitButton = memo(function TopicFormSubmitButton({
  disabled,
}: TopicFormSubmitButtonProps) {
  return (
    <button
      id="topic-submit"
      type="submit"
      disabled={disabled}
      className={`flex items-center justify-center rounded-lg px-6 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-slate-900 ${
        disabled
          ? "cursor-not-allowed bg-slate-700 text-slate-500"
          : "bg-indigo-600 text-white hover:bg-indigo-500 active:scale-95 active:transform"
      }`}
    >
      Post Topic
    </button>
  );
});
