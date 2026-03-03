import { useEffect } from "react";
import { observer } from "mobx-react-lite";
import { usePresentModeViewModel } from "@presentation/view-models/PresentModeViewModelContext";
import { PresentHeader } from "./PresentHeader";
import { PresentPollResults } from "./PresentPollResults";
import { PresentTopicFeed } from "./PresentTopicFeed";

const JOIN_BASE_URL = window.location.origin;

export const PresentModeView = observer(() => {
  const vm = usePresentModeViewModel();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === "t" || e.key === "T") {
        vm.toggleTheme();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [vm]);

  const themeClasses = vm.isDarkTheme
    ? "bg-slate-900 text-slate-100"
    : "bg-white text-slate-900";

  if (vm.isLoading) {
    return (
      <div
        id="present-mode-view"
        className={`flex h-screen items-center justify-center ${themeClasses}`}
      >
        <p className="text-xl opacity-60">Loading presentation...</p>
      </div>
    );
  }

  if (vm.error) {
    return (
      <div
        id="present-mode-view"
        className={`flex h-screen items-center justify-center ${themeClasses}`}
      >
        <p className="text-xl text-red-400">{vm.error}</p>
      </div>
    );
  }

  if (!vm.event) {
    return (
      <div
        id="present-mode-view"
        className={`flex h-screen items-center justify-center ${themeClasses}`}
      >
        <p className="text-xl opacity-60">Event not found.</p>
      </div>
    );
  }

  const joinUrl = `${JOIN_BASE_URL}/events/${vm.event.code}`;

  return (
    <div
      id="present-mode-view"
      className={`flex h-screen flex-col ${themeClasses}`}
    >
      <PresentHeader
        eventTitle={vm.event.title}
        eventCode={vm.event.code}
        participantCount={vm.participantCount}
        isDarkTheme={vm.isDarkTheme}
        joinUrl={joinUrl}
        onToggleTheme={vm.toggleTheme}
      />
      <div className="flex flex-1 overflow-hidden">
        <section className="flex w-1/2 flex-col overflow-y-auto border-r border-current/10 p-8">
          {vm.activePoll ? (
            <PresentPollResults poll={vm.activePoll} />
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="text-xl opacity-50">No active poll</p>
            </div>
          )}
        </section>
        <section className="flex w-1/2 flex-col overflow-y-auto p-8">
          <PresentTopicFeed topics={vm.topTopics} />
        </section>
      </div>
    </div>
  );
});
