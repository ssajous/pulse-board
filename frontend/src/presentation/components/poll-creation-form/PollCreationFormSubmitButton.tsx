import { memo } from "react";

interface PollCreationFormSubmitButtonProps {
  disabled: boolean;
  isSubmitting: boolean;
}

export const PollCreationFormSubmitButton = memo(
  function PollCreationFormSubmitButton({
    disabled,
    isSubmitting,
  }: PollCreationFormSubmitButtonProps) {
    return (
      <button
        id="poll-submit-btn"
        type="submit"
        disabled={disabled || isSubmitting}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Creating..." : "Create Poll"}
      </button>
    );
  },
);
