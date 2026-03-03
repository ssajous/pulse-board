import { Link } from "react-router-dom";
import type { Event } from "@domain/entities/Event";

interface EventBoardHeaderProps {
  event: Event;
  isCreator?: boolean;
}

export function EventBoardHeader({
  event,
  isCreator,
}: EventBoardHeaderProps) {
  return (
    <div
      id="event-board-header"
      className="mb-6 rounded-lg border border-slate-700 bg-slate-800 p-4"
    >
      <h2 className="text-xl font-bold text-white">{event.title}</h2>
      {event.description && (
        <p className="mt-1 text-sm text-slate-400">
          {event.description}
        </p>
      )}
      <div className="mt-2 flex items-center gap-2">
        <span className="rounded bg-indigo-600/20 px-2 py-0.5 text-xs font-medium text-indigo-400">
          Code: {event.code}
        </span>
        <span className="rounded bg-green-600/20 px-2 py-0.5 text-xs font-medium text-green-400">
          {event.status}
        </span>
        {isCreator && (
          <>
            <Link
              to={`/events/${event.code}/admin`}
              id="event-admin-link"
              className="rounded bg-amber-600/20 px-2 py-0.5 text-xs font-medium text-amber-400 hover:bg-amber-600/30 transition-colors"
            >
              Admin
            </Link>
            <button
              id="open-present-mode-btn"
              type="button"
              onClick={() =>
                window.open(
                  `/events/${event.code}/present`,
                  "_blank",
                  "noopener,noreferrer",
                )
              }
              className="rounded bg-purple-600/20 px-2 py-0.5 text-xs font-medium text-purple-400 hover:bg-purple-600/30 transition-colors"
            >
              Present Mode
            </button>
          </>
        )}
      </div>
    </div>
  );
}
