import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { observer } from "mobx-react-lite";
import { EventApiClient } from "@infrastructure/api/eventApiClient";
import { PollApiClient } from "@infrastructure/api/pollApiClient";
import { EventAdminViewModel } from "@presentation/view-models/EventAdminViewModel";
import { PollCreationViewModel } from "@presentation/view-models/PollCreationViewModel";
import { PollCreationViewModelProvider } from "@presentation/view-models/PollCreationViewModelContext";
import { Header } from "@presentation/components/layout";
import { PollCreationForm } from "@presentation/components/poll-creation-form";
import { EventAdminPollList } from "./EventAdminPollList";
import { EventAdminHeader } from "./EventAdminHeader";

const EventAdminContent = observer(function EventAdminContent({
  vm,
}: {
  vm: EventAdminViewModel;
}) {
  const [pollCreationVm] = useState(
    () => new PollCreationViewModel(vm.pollApi),
  );

  const handlePollCreated = () => {
    if (pollCreationVm.createdPoll) {
      vm.onPollCreated(pollCreationVm.createdPoll);
    }
    vm.loadPolls();
  };

  if (vm.isLoading) {
    return (
      <div className="py-12 text-center text-slate-400">
        Loading event...
      </div>
    );
  }

  if (vm.error && !vm.event) {
    return (
      <div className="py-12 text-center">
        <p className="mb-4 text-red-400">{vm.error}</p>
        <Link
          to="/"
          className="text-indigo-400 hover:text-indigo-300"
        >
          Back to home
        </Link>
      </div>
    );
  }

  if (!vm.event) return null;

  return (
    <>
      <EventAdminHeader event={vm.event} />
      {vm.error && (
        <div className="mb-4 rounded-lg border border-red-700 bg-red-900/20 px-4 py-3">
          <p className="text-sm text-red-400">{vm.error}</p>
          <button
            onClick={vm.dismissError}
            className="mt-1 text-xs text-red-300 underline hover:text-red-200"
          >
            Dismiss
          </button>
        </div>
      )}
      <div className="mb-8">
        <PollCreationViewModelProvider value={pollCreationVm}>
          <PollCreationForm
            eventId={vm.event.id}
            onCreated={handlePollCreated}
          />
        </PollCreationViewModelProvider>
      </div>
      <EventAdminPollList
        polls={vm.polls}
        activatingPollId={vm.activatingPollId}
        pollResults={vm.pollResults}
        onToggleActive={vm.togglePollActive}
        onLoadResults={vm.loadPollResults}
      />
    </>
  );
});

export function EventAdminPage() {
  const { code } = useParams<{ code: string }>();
  const [vm] = useState(
    () =>
      new EventAdminViewModel(
        new EventApiClient(),
        new PollApiClient(),
      ),
  );

  useEffect(() => {
    if (code) {
      vm.loadEvent(code);
    }
    return () => vm.dispose();
  }, [code, vm]);

  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <EventAdminContent vm={vm} />
      </main>
    </>
  );
}
