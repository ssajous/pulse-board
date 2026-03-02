import { memo } from "react";

interface PollParticipationQuestionProps {
  question: string;
}

export const PollParticipationQuestion = memo(
  function PollParticipationQuestion({
    question,
  }: PollParticipationQuestionProps) {
    return (
      <h3 className="mb-4 text-lg font-semibold text-slate-100">
        {question}
      </h3>
    );
  },
);
