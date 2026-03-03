import { createContext, useContext } from "react";
import type { OpenTextPollViewModel } from "./OpenTextPollViewModel";

const OpenTextPollViewModelContext =
  createContext<OpenTextPollViewModel | null>(null);

export const OpenTextPollViewModelProvider =
  OpenTextPollViewModelContext.Provider;

export function useOpenTextPollViewModel(): OpenTextPollViewModel {
  const vm = useContext(OpenTextPollViewModelContext);
  if (!vm) {
    throw new Error(
      "useOpenTextPollViewModel must be used within OpenTextPollViewModelProvider",
    );
  }
  return vm;
}
