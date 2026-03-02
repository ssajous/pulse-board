import { createContext, useContext } from "react";
import type { EventJoinViewModel } from "./EventJoinViewModel";

const EventJoinViewModelContext =
  createContext<EventJoinViewModel | null>(null);

export const EventJoinViewModelProvider =
  EventJoinViewModelContext.Provider;

export function useEventJoinViewModel(): EventJoinViewModel {
  const vm = useContext(EventJoinViewModelContext);
  if (!vm) {
    throw new Error(
      "useEventJoinViewModel must be used within EventJoinViewModelProvider",
    );
  }
  return vm;
}
