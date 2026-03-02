import { Link } from "react-router-dom";
import { Plus, LogIn } from "lucide-react";

export function LandingActions() {
  return (
    <div
      id="landing-actions"
      className="mb-8 flex items-center justify-center gap-4"
    >
      <Link
        to="/events/new"
        id="landing-create-event"
        className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
      >
        <Plus size={16} />
        Create Event
      </Link>
      <Link
        to="/events/join"
        id="landing-join-event"
        className="flex items-center gap-2 rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
      >
        <LogIn size={16} />
        Join Event
      </Link>
    </div>
  );
}
