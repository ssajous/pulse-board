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

function App() {
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
      <div className="min-h-screen bg-slate-900 pb-20 font-sans text-slate-100">
        <Header />
        <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
          <TopicForm />
          <TopicListHeader />
          <TopicList />
        </main>
        <ToastContainer />
      </div>
    </TopicsViewModelProvider>
  );
}

export default App;
