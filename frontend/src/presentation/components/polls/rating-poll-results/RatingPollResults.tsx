import { memo } from "react";
import { Star } from "lucide-react";
import type { RatingPollResults as RatingPollResultsType } from "@domain/entities/Poll";
import { RatingDistributionBar } from "./RatingDistributionBar";

interface RatingPollResultsProps {
  results: RatingPollResultsType;
}

const RATING_LABELS: Record<number, string> = {
  5: "Excellent",
  4: "Good",
  3: "Average",
  2: "Poor",
  1: "Terrible",
};

export const RatingPollResults = memo(function RatingPollResults({
  results,
}: RatingPollResultsProps) {
  const averageDisplay =
    results.average_rating !== null
      ? results.average_rating.toFixed(1)
      : "—";

  return (
    <div
      id="poll-results"
      className="mb-8 rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
    >
      <h3 className="mb-1 text-lg font-semibold text-slate-100">
        {results.question}
      </h3>
      <div className="mb-6 flex items-center gap-4">
        <div className="flex items-baseline gap-1">
          <span
            id="rating-results-average"
            className="text-4xl font-bold text-amber-400"
          >
            {averageDisplay}
          </span>
          <span className="text-slate-400">/ 5</span>
        </div>
        <Star
          size={28}
          className="fill-amber-400 text-amber-400"
        />
        <span
          id="rating-results-total"
          className="text-sm text-slate-400"
        >
          {results.total_votes} vote{results.total_votes !== 1 ? "s" : ""}
        </span>
      </div>
      <div className="space-y-3">
        {[5, 4, 3, 2, 1].map((rating) => (
          <RatingDistributionBar
            key={rating}
            rating={rating}
            count={results.distribution[String(rating)] ?? 0}
            total={results.total_votes}
          />
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-500">
        {results.average_rating !== null && RATING_LABELS[Math.round(results.average_rating)]
          ? `Average: ${RATING_LABELS[Math.round(results.average_rating)]}`
          : "No ratings yet"}
      </p>
    </div>
  );
});
