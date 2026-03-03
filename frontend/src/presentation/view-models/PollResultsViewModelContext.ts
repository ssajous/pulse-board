import { createContext, useContext } from "react";
import type { PollResultsViewModel } from "./PollResultsViewModel";

const PollResultsViewModelContext =
  createContext<PollResultsViewModel | null>(null);

export const PollResultsViewModelProvider =
  PollResultsViewModelContext.Provider;

export function usePollResultsViewModel(): PollResultsViewModel {
  const vm = useContext(PollResultsViewModelContext);
  if (!vm) {
    throw new Error(
      "usePollResultsViewModel must be used within PollResultsViewModelProvider",
    );
  }
  return vm;
}
