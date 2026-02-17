import { useState } from "react";
import { TopicsViewModel } from "@presentation/view-models";
import { TopicsViewModelProvider } from "@presentation/view-models";
import { TopicApiClient } from "@infrastructure/api/topicApiClient";
import { Header } from "@presentation/components/layout";
import { TopicForm } from "@presentation/components/topic-form";
import { TopicList, TopicListHeader } from "@presentation/components/topic-list";
import { ToastContainer } from "@presentation/components/toast";

function App() {
  const [vm] = useState(() => new TopicsViewModel(new TopicApiClient()));

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
