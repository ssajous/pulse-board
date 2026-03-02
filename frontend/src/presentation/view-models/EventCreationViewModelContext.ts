import { createContext, useContext } from "react";
import type { EventCreationViewModel } from "./EventCreationViewModel";

const EventCreationViewModelContext =
  createContext<EventCreationViewModel | null>(null);

export const EventCreationViewModelProvider =
  EventCreationViewModelContext.Provider;

export function useEventCreationViewModel(): EventCreationViewModel {
  const vm = useContext(EventCreationViewModelContext);
  if (!vm) {
    throw new Error(
      "useEventCreationViewModel must be used within EventCreationViewModelProvider",
    );
  }
  return vm;
}
