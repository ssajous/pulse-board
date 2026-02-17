import { memo } from "react";

interface TopicCardRemovalBarProps {
  score: number;
}

export const TopicCardRemovalBar = memo(function TopicCardRemovalBar({
  score,
}: TopicCardRemovalBarProps) {
  if (score >= 0) return null;

  const width = Math.min(Math.abs(score) * 20, 100);

  return (
    <div className="mx-5 mb-4 h-1 overflow-hidden rounded-full bg-slate-700">
      <div
        className="h-full bg-rose-500 transition-all duration-500"
        style={{ width: `${width}%` }}
      />
    </div>
  );
});
