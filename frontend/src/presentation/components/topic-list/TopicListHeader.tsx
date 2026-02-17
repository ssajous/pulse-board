import { TrendingUp } from "lucide-react";

export function TopicListHeader() {
  return (
    <div
      id="topic-list-header"
      className="mb-4 flex items-center gap-2 px-2 text-sm text-slate-400"
    >
      <TrendingUp size={16} />
      <span className="font-medium">Live Feed</span>
      <span className="mx-1 h-1 w-1 rounded-full bg-slate-700" />
      <span>Sorted by popularity</span>
    </div>
  );
}
