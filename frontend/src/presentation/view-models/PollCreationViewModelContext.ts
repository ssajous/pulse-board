import { createContext, useContext } from "react";
import type { PollCreationViewModel } from "./PollCreationViewModel";

const PollCreationViewModelContext =
  createContext<PollCreationViewModel | null>(null);

export const PollCreationViewModelProvider =
  PollCreationViewModelContext.Provider;

export function usePollCreationViewModel(): PollCreationViewModel {
  const vm = useContext(PollCreationViewModelContext);
  if (!vm) {
    throw new Error(
      "usePollCreationViewModel must be used within PollCreationViewModelProvider",
    );
  }
  return vm;
}
