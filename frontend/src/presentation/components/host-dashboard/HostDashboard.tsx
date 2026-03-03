import { useEffect, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { observer } from "mobx-react-lite";
import { ArrowLeft } from "lucide-react";
import { EventApiClient } from "@infrastructure/api/eventApiClient";
import { PollApiClient } from "@infrastructure/api/pollApiClient";
import { HostApiClient } from "@infrastructure/api/hostApiClient";
import { WebSocketClient } from "@infrastructure/websocket";
import { HostDashboardViewModel } from "@presentation/view-models/HostDashboardViewModel";
import {
  HostDashboardViewModelProvider,
  useHostDashboardViewModel,
} from "@presentation/view-models/HostDashboardViewModelContext";
import { Header } from "@presentation/components/layout";
import { HostEventStats } from "./HostEventStats";
import { HostTopicList } from "./HostTopicList";
import { HostPollManager } from "./HostPollManager";
import { HostEventControls } from "./HostEventControls";

const HostDashboardContent = observer(
  function HostDashboardContent() {
    const vm = useHostDashboardViewModel();

    if (vm.isLoading) {
      return (
        <div className="py-12 text-center text-slate-400">
          Loading dashboard...
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
      <div id="host-dashboard">
        <div className="mb-8">
          <Link
            to={`/events/${vm.event.code}`}
            className="mb-4 inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300"
          >
            <ArrowLeft size={14} />
            Back to event board
          </Link>
          <h1 className="mb-1 text-2xl font-bold text-white">
            {vm.event.title}
          </h1>
          <div className="flex items-center gap-3">
            <span className="rounded bg-slate-700 px-2 py-0.5 font-mono text-sm text-slate-300">
              {vm.event.code}
            </span>
            <span
              className={`rounded px-2 py-0.5 text-xs font-medium ${
                vm.isClosed
                  ? "bg-slate-700 text-slate-400"
                  : "bg-green-900/30 text-green-400"
              }`}
            >
              {vm.isClosed ? "closed" : "active"}
            </span>
          </div>
          {vm.event.description && (
            <p className="mt-2 text-sm text-slate-400">
              {vm.event.description}
            </p>
          )}
        </div>

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

        {vm.stats && <HostEventStats stats={vm.stats} />}

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="mb-6">
              <h2 className="mb-4 text-lg font-semibold text-slate-100">
                Topics
              </h2>
              <HostTopicList
                highlightedTopics={vm.highlightedTopics}
                activeTopics={vm.activeTopics}
                answeredTopics={vm.answeredTopics}
                archivedTopics={vm.archivedTopics}
                updatingTopicId={vm.updatingTopicId}
                onUpdateStatus={vm.updateTopicStatus}
              />
            </div>

            <div>
              <h2 className="mb-4 text-lg font-semibold text-slate-100">
                Polls
              </h2>
              <HostPollManager
                eventId={vm.event.id}
                polls={vm.polls}
                pollApi={vm.pollApi}
                activatingPollId={vm.activatingPollId}
                pollResults={vm.pollResults}
                onToggleActive={vm.togglePollActive}
                onLoadResults={vm.loadPollResults}
                onPollCreated={vm.onPollCreated}
              />
            </div>
          </div>

          <div className="lg:col-span-1">
            <HostEventControls
              eventCode={vm.event.code}
              isClosed={vm.isClosed}
              isClosingEvent={vm.isClosingEvent}
              codeCopied={vm.codeCopied}
              onCopyCode={vm.copyEventCode}
              onCloseEvent={vm.closeEvent}
            />
          </div>
        </div>
      </div>
    );
  },
);

export function HostDashboard() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const creatorToken = code
    ? localStorage.getItem(`creator_token:${code}`)
    : null;

  const vm = useMemo(() => {
    if (!creatorToken) return null;
    return new HostDashboardViewModel(
      new EventApiClient(),
      new PollApiClient(),
      new HostApiClient(creatorToken),
      new WebSocketClient(),
    );
  }, [creatorToken]);

  useEffect(() => {
    if (!creatorToken) {
      navigate(`/events/${code ?? ""}`);
      return;
    }
    if (vm && code) {
      vm.loadDashboard(code);
    }
    return () => vm?.dispose();
  }, [code, vm, creatorToken, navigate]);

  if (!vm) return null;

  return (
    <>
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <HostDashboardViewModelProvider value={vm}>
          <HostDashboardContent />
        </HostDashboardViewModelProvider>
      </main>
    </>
  );
}
