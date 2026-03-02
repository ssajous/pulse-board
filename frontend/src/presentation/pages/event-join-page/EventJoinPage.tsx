import { useState } from "react";
import { EventApiClient } from "@infrastructure/api/eventApiClient";
import { Header } from "@presentation/components/layout";
import { EventJoinViewModel } from "@presentation/view-models/EventJoinViewModel";
import { EventJoinViewModelProvider } from "@presentation/view-models/EventJoinViewModelContext";
import { EventJoinForm } from "@presentation/components/event-join-form";

export function EventJoinPage() {
  const [vm] = useState(
    () => new EventJoinViewModel(new EventApiClient()),
  );

  return (
    <EventJoinViewModelProvider value={vm}>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <h2 className="mb-6 text-2xl font-bold text-white">
          Join Event
        </h2>
        <EventJoinForm />
      </main>
    </EventJoinViewModelProvider>
  );
}
