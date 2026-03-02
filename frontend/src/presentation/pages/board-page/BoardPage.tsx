import { useEffect, useState } from "react";
import { TopicApiClient } from "@infrastructure/api/topicApiClient";
import { VoteApiClient } from "@infrastructure/api/voteApiClient";
import {
  FingerprintService,
} from "@infrastructure/fingerprint/fingerprintService";
import { WebSocketClient } from "@infrastructure/websocket";
import {
  TopicsViewModel,
  TopicsViewModelProvider,
} from "@presentation/view-models";
import { Header } from "@presentation/components/layout";
import { TopicForm } from "@presentation/components/topic-form";
import {
  TopicList,
  TopicListHeader,
} from "@presentation/components/topic-list";
import { ToastContainer } from "@presentation/components/toast";
import { LandingActions } from "@presentation/components/landing-actions";

export function BoardPage() {
  const [vm] = useState(
    () =>
      new TopicsViewModel(
        new TopicApiClient(),
        new VoteApiClient(),
        new FingerprintService(),
        new WebSocketClient(),
      ),
  );

  useEffect(() => {
    vm.connectWebSocket();
    return () => vm.dispose();
  }, [vm]);

  return (
    <TopicsViewModelProvider value={vm}>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <LandingActions />
        <TopicForm />
        <TopicListHeader />
        <TopicList />
      </main>
      <ToastContainer />
    </TopicsViewModelProvider>
  );
}
