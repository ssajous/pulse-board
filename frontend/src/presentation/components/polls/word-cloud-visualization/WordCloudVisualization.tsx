import { observer } from "mobx-react-lite";
import type { WordFrequency } from "@domain/entities/Poll";
import { WordCloudWord } from "./WordCloudWord";

const MIN_FONT_SIZE = 14;
const MAX_FONT_SIZE = 72;

interface WordCloudVisualizationProps {
  frequencies: WordFrequency[];
}

function computeFontSize(
  count: number,
  minCount: number,
  maxCount: number,
): number {
  if (maxCount === minCount) return (MIN_FONT_SIZE + MAX_FONT_SIZE) / 2;
  const ratio = (count - minCount) / (maxCount - minCount);
  return MIN_FONT_SIZE + ratio * (MAX_FONT_SIZE - MIN_FONT_SIZE);
}

export const WordCloudVisualization = observer(
  function WordCloudVisualization({
    frequencies,
  }: WordCloudVisualizationProps) {
    if (frequencies.length === 0) {
      return (
        <div
          id="word-cloud-visualization"
          className="flex min-h-[200px] items-center justify-center"
        >
          <p className="text-lg text-slate-400">
            Waiting for responses...
          </p>
        </div>
      );
    }

    const counts = frequencies.map((f) => f.count);
    const minCount = Math.min(...counts);
    const maxCount = Math.max(...counts);

    return (
      <div
        id="word-cloud-visualization"
        className="flex min-h-[200px] flex-wrap items-center justify-center gap-2 p-4"
      >
        {frequencies.map((freq, index) => (
          <WordCloudWord
            key={freq.text}
            text={freq.text}
            fontSize={computeFontSize(freq.count, minCount, maxCount)}
            colorIndex={index}
          />
        ))}
      </div>
    );
  },
);
