import { observer } from "mobx-react-lite";
import { useEventCreationViewModel } from "@presentation/view-models/EventCreationViewModelContext";

export const EventCreationFormFields = observer(
  function EventCreationFormFields() {
    const vm = useEventCreationViewModel();

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      vm.submit();
    };

    return (
      <form
        id="event-creation-form"
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-slate-700 bg-slate-800 p-6"
      >
        <div>
          <label
            htmlFor="event-title"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Event Title *
          </label>
          <input
            id="event-title"
            type="text"
            value={vm.title}
            onChange={(e) => vm.setTitle(e.target.value)}
            placeholder="e.g., Team Retrospective"
            maxLength={200}
            className="w-full rounded-md border border-slate-600 bg-slate-700 px-3 py-2 text-white placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label
            htmlFor="event-description"
            className="mb-1 block text-sm font-medium text-slate-300"
          >
            Description
          </label>
          <textarea
            id="event-description"
            value={vm.description}
            onChange={(e) => vm.setDescription(e.target.value)}
            placeholder="Optional description..."
            rows={3}
            className="w-full rounded-md border border-slate-600 bg-slate-700 px-3 py-2 text-white placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        {vm.error && (
          <p className="text-sm text-red-400">{vm.error}</p>
        )}
        <button
          id="event-creation-submit"
          type="submit"
          disabled={!vm.isValid || vm.isSubmitting}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {vm.isSubmitting ? "Creating..." : "Create Event"}
        </button>
      </form>
    );
  },
);
