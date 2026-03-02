import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import type { Event } from "@domain/entities/Event";

interface EventAdminHeaderProps {
  event: Event;
}

export const EventAdminHeader = memo(
  function EventAdminHeader({ event }: EventAdminHeaderProps) {
    return (
      <div className="mb-8">
        <Link
          to={`/events/${event.code}`}
          className="mb-4 inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300"
        >
          <ArrowLeft size={14} />
          Back to event board
        </Link>
        <h1 className="mb-1 text-2xl font-bold text-white">
          {event.title}
        </h1>
        <div className="flex items-center gap-3">
          <span className="rounded bg-slate-700 px-2 py-0.5 text-sm font-mono text-slate-300">
            {event.code}
          </span>
          <span
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              event.status === "active"
                ? "bg-green-900/30 text-green-400"
                : "bg-slate-700 text-slate-400"
            }`}
          >
            {event.status}
          </span>
        </div>
        {event.description && (
          <p className="mt-2 text-sm text-slate-400">
            {event.description}
          </p>
        )}
      </div>
    );
  },
);
