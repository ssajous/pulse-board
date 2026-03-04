import { observer } from "mobx-react-lite";
import type { WordFrequency } from "@domain/entities/Poll";
import { WordCloudVisualization } from "@presentation/components/polls/word-cloud-visualization";

interface WordCloudPollResultsProps {
  frequencies: WordFrequency[];
  totalResponses: number;
}

export const WordCloudPollResults = observer(
  function WordCloudPollResults({
    frequencies,
    totalResponses,
  }: WordCloudPollResultsProps) {
    return (
      <div>
        <WordCloudVisualization frequencies={frequencies} />
        {totalResponses > 0 && (
          <p
            id="word-cloud-response-count"
            className="mt-2 text-center text-sm text-slate-400"
          >
            {totalResponses}{" "}
            {totalResponses === 1 ? "response" : "responses"}
          </p>
        )}
      </div>
    );
  },
);
