import { createContext, useContext } from "react";
import type { HostDashboardViewModel } from "./HostDashboardViewModel";

const HostDashboardViewModelContext =
  createContext<HostDashboardViewModel | null>(null);

export const HostDashboardViewModelProvider =
  HostDashboardViewModelContext.Provider;

export function useHostDashboardViewModel(): HostDashboardViewModel {
  const vm = useContext(HostDashboardViewModelContext);
  if (!vm) {
    throw new Error(
      "useHostDashboardViewModel must be used within HostDashboardViewModelProvider",
    );
  }
  return vm;
}
