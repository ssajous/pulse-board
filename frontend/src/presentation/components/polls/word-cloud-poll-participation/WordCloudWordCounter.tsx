import { memo } from "react";

interface WordCloudWordCounterProps {
  wordCount: number;
  display: string;
}

export const WordCloudWordCounter = memo(
  function WordCloudWordCounter({
    wordCount,
    display,
  }: WordCloudWordCounterProps) {
    const colorClass =
      wordCount > 3
        ? "text-red-400"
        : wordCount === 3
          ? "text-amber-400"
          : "text-slate-400";

    return (
      <span className={`text-xs ${colorClass}`}>{display}</span>
    );
  },
);
