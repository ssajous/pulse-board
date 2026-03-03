import { useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import { EventApiClient } from "@infrastructure/api/eventApiClient";
import { PresentStateApiClient } from "@infrastructure/api/presentStateApiClient";
import { WebSocketClient } from "@infrastructure/websocket/webSocketClient";
import { PresentModeViewModel } from "@presentation/view-models/PresentModeViewModel";
import {
  PresentModeViewModelProvider,
} from "@presentation/view-models/PresentModeViewModelContext";
import { PresentModeView } from "@presentation/components/present-mode";

export function EventPresentPage() {
  const { code } = useParams<{ code: string }>();

  const vm = useMemo(
    () =>
      new PresentModeViewModel(
        new EventApiClient(),
        new PresentStateApiClient(),
        new WebSocketClient(),
      ),
    [],
  );

  useEffect(() => {
    if (code) {
      void vm.initialize(code);
    }
    return () => {
      vm.dispose();
    };
  }, [vm, code]);

  return (
    <PresentModeViewModelProvider value={vm}>
      <PresentModeView />
    </PresentModeViewModelProvider>
  );
}
