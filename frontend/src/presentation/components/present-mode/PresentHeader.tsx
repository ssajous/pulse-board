import { QRCodeDisplay } from "./QRCodeDisplay";

interface PresentHeaderProps {
  eventTitle: string;
  eventCode: string;
  participantCount: number;
  isDarkTheme: boolean;
  joinUrl: string;
  onToggleTheme: () => void;
}

export const PresentHeader = ({
  eventTitle,
  eventCode,
  participantCount,
  isDarkTheme,
  joinUrl,
  onToggleTheme,
}: PresentHeaderProps) => {
  const borderColor = isDarkTheme
    ? "border-slate-700"
    : "border-slate-200";
  const subTextColor = isDarkTheme
    ? "text-slate-400"
    : "text-slate-500";

  return (
    <header
      id="present-header"
      className={`flex items-center justify-between border-b px-8 py-4 ${borderColor}`}
    >
      <div className="flex flex-col gap-1">
        <h1
          id="present-event-title"
          className="text-4xl font-bold leading-tight"
        >
          {eventTitle}
        </h1>
        <div className={`flex items-center gap-4 ${subTextColor}`}>
          <span className="text-sm">Code: {eventCode}</span>
          <span id="present-participant-count" className="text-sm">
            {participantCount}{" "}
            {participantCount === 1 ? "participant" : "participants"}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <QRCodeDisplay url={joinUrl} size={120} />
        <button
          id="present-theme-toggle"
          type="button"
          onClick={onToggleTheme}
          className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
            isDarkTheme
              ? "border-slate-600 text-slate-300 hover:border-slate-400 hover:text-white"
              : "border-slate-300 text-slate-600 hover:border-slate-500 hover:text-slate-900"
          }`}
          title="Toggle theme (T)"
        >
          {isDarkTheme ? "Light mode" : "Dark mode"}
        </button>
      </div>
    </header>
  );
};
