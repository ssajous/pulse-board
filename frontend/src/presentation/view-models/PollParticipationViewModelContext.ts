import { createContext, useContext } from "react";
import type { PollParticipationViewModel } from "./PollParticipationViewModel";

const PollParticipationViewModelContext =
  createContext<PollParticipationViewModel | null>(null);

export const PollParticipationViewModelProvider =
  PollParticipationViewModelContext.Provider;

export function usePollParticipationViewModel(): PollParticipationViewModel {
  const vm = useContext(PollParticipationViewModelContext);
  if (!vm) {
    throw new Error(
      "usePollParticipationViewModel must be used within PollParticipationViewModelProvider",
    );
  }
  return vm;
}
