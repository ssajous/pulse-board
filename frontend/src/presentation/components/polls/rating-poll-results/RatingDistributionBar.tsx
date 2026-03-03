import { memo } from "react";
import { Star } from "lucide-react";

interface RatingDistributionBarProps {
  rating: number;
  count: number;
  total: number;
}

export const RatingDistributionBar = memo(function RatingDistributionBar({
  rating,
  count,
  total,
}: RatingDistributionBarProps) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0;

  return (
    <div
      id={`rating-distribution-bar-${rating}`}
      className="flex items-center gap-3"
    >
      <div className="flex w-12 items-center justify-end gap-1 text-sm text-slate-400">
        <span>{rating}</span>
        <Star size={12} className="fill-amber-400 text-amber-400" />
      </div>
      <div className="flex-1 overflow-hidden rounded-full bg-slate-700">
        <div
          className="h-2 rounded-full bg-amber-400 transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="w-14 text-right text-sm text-slate-400">
        {count} ({percentage}%)
      </div>
    </div>
  );
});
