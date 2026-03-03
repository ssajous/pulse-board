import { useState } from "react";
import { Link } from "react-router-dom";
import { observer } from "mobx-react-lite";
import { Copy, Check, Monitor, XCircle } from "lucide-react";

interface HostEventControlsProps {
  eventCode: string;
  isClosed: boolean;
  isClosingEvent: boolean;
  codeCopied: boolean;
  onCopyCode: () => void;
  onCloseEvent: () => void;
}

export const HostEventControls = observer(
  function HostEventControls({
    eventCode,
    isClosed,
    isClosingEvent,
    codeCopied,
    onCopyCode,
    onCloseEvent,
  }: HostEventControlsProps) {
    const [showConfirm, setShowConfirm] = useState(false);

    const handleCloseRequest = () => setShowConfirm(true);
    const handleCancelClose = () => setShowConfirm(false);
    const handleConfirmClose = () => {
      setShowConfirm(false);
      onCloseEvent();
    };

    return (
      <div
        id="host-event-controls"
        className="rounded-xl border border-slate-700 bg-slate-800 p-6"
      >
        <h3 className="mb-4 text-base font-semibold text-slate-100">
          Event Controls
        </h3>
        <div className="flex flex-col gap-3">
          <button
            id="host-copy-code-btn"
            onClick={onCopyCode}
            className="flex items-center justify-center gap-2 rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-2.5 text-sm font-medium text-indigo-300 transition-colors hover:bg-indigo-500/20"
          >
            {codeCopied ? (
              <>
                <Check size={16} />
                Copied!
              </>
            ) : (
              <>
                <Copy size={16} />
                Copy Join Code: {eventCode}
              </>
            )}
          </button>

          <Link
            id="host-open-present-link"
            to={`/events/${eventCode}/present`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 rounded-lg border border-slate-600 bg-slate-700/50 px-4 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700"
          >
            <Monitor size={16} />
            Open Present Mode
          </Link>

          {!isClosed && (
            <button
              id="host-close-event-btn"
              onClick={handleCloseRequest}
              disabled={isClosingEvent}
              className="flex items-center justify-center gap-2 rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2.5 text-sm font-medium text-rose-400 transition-colors hover:bg-rose-500/20 disabled:opacity-50"
            >
              <XCircle size={16} />
              {isClosingEvent ? "Closing..." : "Close Event"}
            </button>
          )}

          {isClosed && (
            <div className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-slate-500">
              <XCircle size={16} />
              Event Closed
            </div>
          )}
        </div>

        {showConfirm && (
          <div
            id="host-close-event-dialog"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          >
            <div className="w-full max-w-sm rounded-2xl border border-slate-700 bg-slate-800 p-6 shadow-2xl">
              <h4 className="mb-2 text-lg font-semibold text-slate-100">
                Close this event?
              </h4>
              <p className="mb-6 text-sm text-slate-400">
                This will end the event for all participants. Topics
                and polls will be read-only. This cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  id="host-close-event-cancel-btn"
                  onClick={handleCancelClose}
                  className="flex-1 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-600"
                >
                  Cancel
                </button>
                <button
                  id="host-close-event-confirm-btn"
                  onClick={handleConfirmClose}
                  className="flex-1 rounded-lg border border-rose-500/40 bg-rose-500/20 px-4 py-2 text-sm font-medium text-rose-400 hover:bg-rose-500/30"
                >
                  Close Event
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  },
);
