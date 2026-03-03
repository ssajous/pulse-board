import { memo } from "react";
import { Star } from "lucide-react";

interface RatingStarProps {
  index: number;
  filled: boolean;
  onHover: (rating: number | null) => void;
  onClick: (rating: number) => void;
  disabled: boolean;
}

export const RatingStar = memo(function RatingStar({
  index,
  filled,
  onHover,
  onClick,
  disabled,
}: RatingStarProps) {
  return (
    <button
      id={`rating-star-${index}`}
      type="button"
      disabled={disabled}
      aria-label={`Rate ${index} star${index !== 1 ? "s" : ""}`}
      onClick={() => onClick(index)}
      onMouseEnter={() => onHover(index)}
      onMouseLeave={() => onHover(null)}
      className={[
        "transition-transform duration-100",
        disabled ? "cursor-default" : "cursor-pointer hover:scale-110",
      ].join(" ")}
    >
      <Star
        size={32}
        className={
          filled
            ? "fill-amber-400 text-amber-400"
            : "fill-transparent text-slate-500"
        }
      />
    </button>
  );
});
