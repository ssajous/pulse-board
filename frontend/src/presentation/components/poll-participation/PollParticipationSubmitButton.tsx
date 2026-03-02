import { memo } from "react";

interface PollParticipationSubmitButtonProps {
  disabled: boolean;
  isSubmitting: boolean;
}

export const PollParticipationSubmitButton = memo(
  function PollParticipationSubmitButton({
    disabled,
    isSubmitting,
  }: PollParticipationSubmitButtonProps) {
    return (
      <button
        id="poll-submit-response-btn"
        type="button"
        disabled={disabled}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Submitting..." : "Submit Vote"}
      </button>
    );
  },
);
