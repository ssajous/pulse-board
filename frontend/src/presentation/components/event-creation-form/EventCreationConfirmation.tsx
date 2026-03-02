import { observer } from "mobx-react-lite";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Copy, Check } from "lucide-react";
import { useEventCreationViewModel } from "@presentation/view-models/EventCreationViewModelContext";

export const EventCreationConfirmation = observer(
  function EventCreationConfirmation() {
    const vm = useEventCreationViewModel();
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
      if (!vm.createdCode) return;
      await navigator.clipboard.writeText(vm.createdCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    return (
      <div
        id="event-creation-confirmation"
        className="rounded-lg border border-slate-700 bg-slate-800 p-8 text-center"
      >
        <h3 className="mb-2 text-xl font-semibold text-white">
          Event Created!
        </h3>
        <p className="mb-6 text-slate-400">
          Share this code with participants:
        </p>
        <div className="mb-6 flex items-center justify-center gap-3">
          <span
            id="event-join-code"
            className="font-mono text-4xl font-bold tracking-widest text-indigo-400"
          >
            {vm.createdCode}
          </span>
          <button
            id="event-code-copy"
            onClick={handleCopy}
            className="rounded-md p-2 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white"
            aria-label="Copy code"
            type="button"
          >
            {copied ? <Check size={20} /> : <Copy size={20} />}
          </button>
        </div>
        <div className="flex items-center justify-center gap-4">
          <Link
            to={`/events/${vm.createdCode}`}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
          >
            Go to Event Board
          </Link>
          <button
            onClick={vm.reset}
            type="button"
            className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
          >
            Create Another
          </button>
        </div>
      </div>
    );
  },
);
