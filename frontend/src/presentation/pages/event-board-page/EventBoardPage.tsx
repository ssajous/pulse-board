import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { observer } from "mobx-react-lite";
import { EventApiClient } from "@infrastructure/api/eventApiClient";
import { EventBoardViewModel } from "@presentation/view-models/EventBoardViewModel";
import { TopicsViewModelProvider } from "@presentation/view-models/TopicsViewModelContext";
import { PollParticipationViewModelProvider } from "@presentation/view-models/PollParticipationViewModelContext";
import { Header } from "@presentation/components/layout";
import { TopicForm } from "@presentation/components/topic-form";
import {
  TopicList,
  TopicListHeader,
} from "@presentation/components/topic-list";
import { ToastContainer } from "@presentation/components/toast";
import { EventBoardHeader } from "@presentation/components/event-board-header";
import { PollParticipation } from "@presentation/components/poll-participation";

const EventBoardContent = observer(function EventBoardContent({
  vm,
}: {
  vm: EventBoardViewModel;
}) {
  if (vm.isLoading) {
    return (
      <div className="py-12 text-center text-slate-400">
        Loading event...
      </div>
    );
  }

  if (vm.error) {
    return (
      <div className="py-12 text-center">
        <p className="text-red-400">{vm.error}</p>
      </div>
    );
  }

  if (!vm.topicsViewModel || !vm.event) {
    return null;
  }

  return (
    <TopicsViewModelProvider value={vm.topicsViewModel}>
      <EventBoardHeader event={vm.event} />
      {vm.pollParticipationViewModel && (
        <PollParticipationViewModelProvider
          value={vm.pollParticipationViewModel}
        >
          <PollParticipation />
        </PollParticipationViewModelProvider>
      )}
      <TopicForm />
      <TopicListHeader />
      <TopicList />
      <ToastContainer />
    </TopicsViewModelProvider>
  );
});

export function EventBoardPage() {
  const { code } = useParams<{ code: string }>();
  const [vm] = useState(
    () => new EventBoardViewModel(new EventApiClient()),
  );

  useEffect(() => {
    if (code) {
      vm.resolveEvent(code);
    }
    return () => vm.dispose();
  }, [code, vm]);

  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <EventBoardContent vm={vm} />
      </main>
    </>
  );
}
