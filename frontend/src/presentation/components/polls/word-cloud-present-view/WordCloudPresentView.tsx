import type { PresentActivePoll } from "@domain/entities/PresentState";
import { WordCloudVisualization } from "@presentation/components/polls/word-cloud-visualization";

interface WordCloudPresentViewProps {
  poll: PresentActivePoll;
}

export function WordCloudPresentView({
  poll,
}: WordCloudPresentViewProps) {
  return (
    <div id="word-cloud-present-view" className="flex h-full flex-col">
      <h2 className="mb-6 text-center text-3xl font-bold">
        {poll.question}
      </h2>
      <div className="flex flex-1 items-center justify-center">
        <WordCloudVisualization frequencies={poll.frequencies ?? []} />
      </div>
      {(poll.total_responses ?? 0) > 0 && (
        <p className="mt-4 text-center text-lg opacity-60">
          {poll.total_responses}{" "}
          {poll.total_responses === 1 ? "response" : "responses"}
        </p>
      )}
    </div>
  );
}
