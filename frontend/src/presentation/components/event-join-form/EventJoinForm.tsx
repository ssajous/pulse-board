import { observer } from "mobx-react-lite";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useEventJoinViewModel } from "@presentation/view-models/EventJoinViewModelContext";

export const EventJoinForm = observer(function EventJoinForm() {
  const vm = useEventJoinViewModel();
  const navigate = useNavigate();

  useEffect(() => {
    if (vm.joinedEvent) {
      navigate(`/events/${vm.joinedEvent.code}`);
    }
  }, [vm.joinedEvent, navigate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    vm.join();
  };

  return (
    <form
      id="event-join-form"
      onSubmit={handleSubmit}
      className="rounded-lg border border-slate-700 bg-slate-800 p-6"
    >
      <label
        htmlFor="event-join-code"
        className="mb-2 block text-sm font-medium text-slate-300"
      >
        Enter 6-digit event code
      </label>
      <input
        id="event-join-code"
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        value={vm.code}
        onChange={(e) => vm.setCode(e.target.value)}
        placeholder="000000"
        className="mb-4 w-full rounded-md border border-slate-600 bg-slate-700 px-3 py-3 text-center font-mono text-2xl tracking-widest text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        autoFocus
      />
      {vm.error && (
        <p className="mb-4 text-sm text-red-400">{vm.error}</p>
      )}
      <button
        id="event-join-submit"
        type="submit"
        disabled={!vm.isValid || vm.isJoining}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {vm.isJoining ? "Joining..." : "Join Event"}
      </button>
    </form>
  );
});
