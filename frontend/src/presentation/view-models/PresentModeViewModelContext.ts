import { createContext, useContext } from "react";
import type { PresentModeViewModel } from "./PresentModeViewModel";

const PresentModeViewModelContext =
  createContext<PresentModeViewModel | null>(null);

export const PresentModeViewModelProvider =
  PresentModeViewModelContext.Provider;

export function usePresentModeViewModel(): PresentModeViewModel {
  const vm = useContext(PresentModeViewModelContext);
  if (!vm) {
    throw new Error(
      "usePresentModeViewModel must be used within PresentModeViewModelProvider",
    );
  }
  return vm;
}
