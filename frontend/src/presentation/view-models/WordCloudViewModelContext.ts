import { createContext, useContext } from "react";
import type { WordCloudViewModel } from "./WordCloudViewModel";

const WordCloudViewModelContext =
  createContext<WordCloudViewModel | null>(null);

export const WordCloudViewModelProvider =
  WordCloudViewModelContext.Provider;

export function useWordCloudViewModel(): WordCloudViewModel {
  const vm = useContext(WordCloudViewModelContext);
  if (!vm) {
    throw new Error(
      "useWordCloudViewModel must be used within WordCloudViewModelProvider",
    );
  }
  return vm;
}
