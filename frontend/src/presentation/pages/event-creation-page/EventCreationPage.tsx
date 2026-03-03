import { useState } from "react";
import { EventApiClient } from "@infrastructure/api/eventApiClient";
import { FingerprintService } from "@infrastructure/fingerprint/fingerprintService";
import { Header } from "@presentation/components/layout";
import { EventCreationViewModel } from "@presentation/view-models/EventCreationViewModel";
import { EventCreationViewModelProvider } from "@presentation/view-models/EventCreationViewModelContext";
import { EventCreationForm } from "@presentation/components/event-creation-form";

export function EventCreationPage() {
  const [vm] = useState(
    () => new EventCreationViewModel(new EventApiClient(), new FingerprintService()),
  );

  return (
    <EventCreationViewModelProvider value={vm}>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <h2 className="mb-6 text-2xl font-bold text-white">
          Create Event
        </h2>
        <EventCreationForm />
      </main>
    </EventCreationViewModelProvider>
  );
}
