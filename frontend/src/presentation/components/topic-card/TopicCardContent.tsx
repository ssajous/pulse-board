import { memo } from "react";
import { Clock, AlertCircle } from "lucide-react";

interface TopicCardContentProps {
  content: string;
  createdAt: string;
  score: number;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  const time = date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const day = date.toLocaleDateString();
  return `${time} \u2022 ${day}`;
}

export const TopicCardContent = memo(function TopicCardContent({
  content,
  createdAt,
  score,
}: TopicCardContentProps) {
  const isDanger = score <= -3;

  return (
    <div className="relative flex-1 p-5">
      <div className="mb-2 flex items-start justify-between">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Clock size={12} />
          {formatTimestamp(createdAt)}
        </div>
        {isDanger && (
          <div className="flex items-center gap-1 rounded-full border border-rose-500/20 bg-rose-500/20 px-2 py-1 text-xs font-bold text-rose-300">
            <AlertCircle size={12} />
            Risk of Removal
          </div>
        )}
      </div>
      <p className="break-words text-lg leading-relaxed text-slate-200">
        {content}
      </p>
    </div>
  );
});
