import { useState } from "react";
import { observer } from "mobx-react-lite";
import type { Poll, PollResults } from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";
import { PollCreationViewModel } from "@presentation/view-models/PollCreationViewModel";
import { PollCreationViewModelProvider } from "@presentation/view-models/PollCreationViewModelContext";
import { PollCreationForm } from "@presentation/components/poll-creation-form";
import { EventAdminPollList } from "@presentation/components/events/EventAdminPollList";

interface HostPollManagerProps {
  eventId: string;
  polls: Poll[];
  pollApi: PollApiPort;
  activatingPollId: string | null;
  pollResults: Map<string, PollResults>;
  onToggleActive: (pollId: string) => void;
  onLoadResults: (pollId: string) => void;
  onPollCreated: (poll: Poll) => void;
}

export const HostPollManager = observer(function HostPollManager({
  eventId,
  polls,
  pollApi,
  activatingPollId,
  pollResults,
  onToggleActive,
  onLoadResults,
  onPollCreated,
}: HostPollManagerProps) {
  const [pollCreationVm] = useState(
    () => new PollCreationViewModel(pollApi),
  );

  const handlePollCreated = () => {
    if (pollCreationVm.createdPoll) {
      onPollCreated(pollCreationVm.createdPoll);
      pollCreationVm.reset();
    }
  };

  return (
    <div id="host-poll-manager">
      <div className="mb-8">
        <PollCreationViewModelProvider value={pollCreationVm}>
          <PollCreationForm
            eventId={eventId}
            onCreated={handlePollCreated}
          />
        </PollCreationViewModelProvider>
      </div>
      <EventAdminPollList
        polls={polls}
        activatingPollId={activatingPollId}
        pollResults={pollResults}
        onToggleActive={onToggleActive}
        onLoadResults={onLoadResults}
      />
    </div>
  );
});
