import { createContext, useContext } from "react";
import type { TopicsViewModel } from "./TopicsViewModel";

const TopicsViewModelContext = createContext<TopicsViewModel | null>(null);

export const TopicsViewModelProvider = TopicsViewModelContext.Provider;

export function useTopicsViewModel(): TopicsViewModel {
  const vm = useContext(TopicsViewModelContext);
  if (!vm) {
    throw new Error(
      "useTopicsViewModel must be used within TopicsViewModelProvider",
    );
  }
  return vm;
}
