import { useParams, Link } from "react-router-dom";
import { Header } from "@presentation/components/layout";

export function EventAdminPage() {
  const { code } = useParams<{ code: string }>();

  return (
    <>
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <div className="rounded-lg border border-slate-700 bg-slate-800 p-8 text-center">
          <h2 className="mb-2 text-xl font-semibold text-white">
            Event Administration
          </h2>
          <p className="mb-4 text-slate-400">
            Admin panel for event {code} coming soon.
          </p>
          <Link
            to={`/events/${code}`}
            className="text-indigo-400 hover:text-indigo-300"
          >
            Back to event board
          </Link>
        </div>
      </main>
    </>
  );
}
