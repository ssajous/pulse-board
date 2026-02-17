import { useEffect, useState } from "react";
import { Activity } from "lucide-react";

interface HealthStatus {
  status: string;
  database: string;
}

const HEALTH_POLL_INTERVAL_MS = 30000;

function LoadingIndicator() {
  return (
    <div className="flex items-center gap-3 text-slate-400">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
      Checking system health...
    </div>
  );
}

function ErrorDisplay({ message }: { message: string }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-red-400" />
        <span className="font-medium text-red-300">System Unavailable</span>
      </div>
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}

function StatusCard({ label, value, connected }: { label: string; value: string; connected: boolean }) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
        {label}
      </p>
      <p className={`mt-1 text-sm font-medium ${connected ? "text-emerald-400" : "text-amber-400"}`}>
        {value}
      </p>
    </div>
  );
}

function HealthDisplay({ health }: { health: HealthStatus }) {
  const isDbConnected = health.database === "connected";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div
          className={`h-3 w-3 rounded-full ${
            health.status === "healthy" ? "bg-emerald-400" : "bg-amber-400"
          }`}
        />
        <span className="font-medium capitalize">{health.status}</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <StatusCard label="API Server" value="Connected" connected />
        <StatusCard
          label="Database"
          value={isDbConnected ? "Connected" : "Disconnected"}
          connected={isDbConnected}
        />
      </div>
    </div>
  );
}

function StatusContent({ loading, error, health }: {
  loading: boolean;
  error: string | null;
  health: HealthStatus | null;
}) {
  if (loading) return <LoadingIndicator />;
  if (error) return <ErrorDisplay message={error} />;
  if (health) return <HealthDisplay health={health} />;
  return null;
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch("/health");
        if (!response.ok && response.status !== 503) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Connection failed");
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, HEALTH_POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-6 py-4">
          <Activity className="h-8 w-8 text-indigo-400" />
          <h1 className="text-xl font-bold tracking-tight">
            Community Pulse
          </h1>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="animate-fade-in">
          <h2 className="mb-8 text-2xl font-semibold text-slate-200">
            System Status
          </h2>

          <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-6 shadow-lg backdrop-blur-sm">
            <StatusContent loading={loading} error={error} health={health} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
