import { Activity } from "lucide-react";

export function Header() {
  return (
    <header
      id="header"
      className="sticky top-0 z-30 border-b border-slate-800 bg-slate-900"
    >
      <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-4 sm:px-6">
        <div className="rounded-lg bg-indigo-600 p-2 text-white">
          <Activity size={24} />
        </div>
        <div>
          <h1 className="text-xl font-bold leading-tight text-white">
            Community Pulse
          </h1>
          <p className="text-xs font-medium text-slate-400">
            Anonymous Feedback Board
          </p>
        </div>
      </div>
    </header>
  );
}
