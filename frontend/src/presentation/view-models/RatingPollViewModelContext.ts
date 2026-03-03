import { createContext, useContext } from "react";
import type { RatingPollViewModel } from "./RatingPollViewModel";

const RatingPollViewModelContext =
  createContext<RatingPollViewModel | null>(null);

export const RatingPollViewModelProvider =
  RatingPollViewModelContext.Provider;

export function useRatingPollViewModel(): RatingPollViewModel {
  const vm = useContext(RatingPollViewModelContext);
  if (!vm) {
    throw new Error(
      "useRatingPollViewModel must be used within RatingPollViewModelProvider",
    );
  }
  return vm;
}
