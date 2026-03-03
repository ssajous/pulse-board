import { memo } from "react";

interface OpenTextCharCounterProps {
  count: number;
  max: number;
  colorClass: string;
}

export const OpenTextCharCounter = memo(function OpenTextCharCounter({
  count,
  max,
  colorClass,
}: OpenTextCharCounterProps) {
  return (
    <span
      id="open-text-poll-char-counter"
      className={`text-xs ${colorClass}`}
    >
      {count}/{max}
    </span>
  );
});
