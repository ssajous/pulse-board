import { observer } from "mobx-react-lite";
import type { RatingPollViewModel } from "@presentation/view-models/RatingPollViewModel";
import { RatingStar } from "./RatingStar";

interface RatingStarInputProps {
  vm: RatingPollViewModel;
}

export const RatingStarInput = observer(function RatingStarInput({
  vm,
}: RatingStarInputProps) {
  return (
    <div
      id="rating-star-input"
      className="flex items-center gap-2"
      role="group"
      aria-label="Star rating selector"
    >
      {[1, 2, 3, 4, 5].map((n) => (
        <RatingStar
          key={n}
          index={n}
          filled={vm.starStates[n - 1] ?? false}
          onHover={vm.setHoveredRating}
          onClick={vm.selectRating}
          disabled={vm.hasSubmitted}
        />
      ))}
    </div>
  );
});
