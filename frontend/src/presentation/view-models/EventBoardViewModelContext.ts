import { createContext, useContext } from "react";
import type { EventBoardViewModel } from "./EventBoardViewModel";

const EventBoardViewModelContext =
  createContext<EventBoardViewModel | null>(null);

export const EventBoardViewModelProvider =
  EventBoardViewModelContext.Provider;

export function useEventBoardViewModel(): EventBoardViewModel {
  const vm = useContext(EventBoardViewModelContext);
  if (!vm) {
    throw new Error(
      "useEventBoardViewModel must be used within EventBoardViewModelProvider",
    );
  }
  return vm;
}
