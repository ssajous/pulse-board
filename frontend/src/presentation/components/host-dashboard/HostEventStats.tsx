import { memo } from "react";
import { Users, MessageSquare, BarChart3, CheckSquare } from "lucide-react";
import type { EventStats } from "@domain/entities/EventStats";

interface HostEventStatsProps {
  stats: EventStats;
}

interface StatCardProps {
  id: string;
  label: string;
  value: number | string;
  icon: React.ReactNode;
  highlight?: boolean;
}

const StatCard = memo(function StatCard({
  id,
  label,
  value,
  icon,
  highlight,
}: StatCardProps) {
  return (
    <div
      id={id}
      className={`rounded-xl border p-4 ${
        highlight
          ? "border-indigo-500/40 bg-indigo-900/20"
          : "border-slate-700 bg-slate-800"
      }`}
    >
      <div className="mb-2 flex items-center gap-2 text-slate-400">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="text-3xl font-bold text-slate-100">{value}</p>
    </div>
  );
});

export const HostEventStats = memo(function HostEventStats({
  stats,
}: HostEventStatsProps) {
  return (
    <div
      id="host-event-stats"
      className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4"
    >
      <StatCard
        id="host-stats-participant-count"
        label="Participants"
        value={stats.participant_count}
        icon={<Users size={16} />}
      />
      <StatCard
        id="host-stats-topic-count"
        label="Topics"
        value={stats.topic_count}
        icon={<MessageSquare size={16} />}
      />
      <StatCard
        id="host-stats-poll-count"
        label="Polls"
        value={stats.poll_count}
        icon={<BarChart3 size={16} />}
        highlight={stats.has_active_poll}
      />
      <StatCard
        id="host-stats-response-count"
        label="Responses"
        value={stats.total_poll_responses}
        icon={<CheckSquare size={16} />}
      />
    </div>
  );
});
