import { memo } from "react";
import { motion } from "motion/react";

const COLORS = [
  "text-violet-400",
  "text-indigo-400",
  "text-blue-400",
  "text-cyan-400",
  "text-teal-400",
  "text-emerald-400",
  "text-fuchsia-400",
  "text-rose-400",
];

interface WordCloudWordProps {
  text: string;
  fontSize: number;
  colorIndex: number;
}

export const WordCloudWord = memo(function WordCloudWord({
  text,
  fontSize,
  colorIndex,
}: WordCloudWordProps) {
  return (
    <motion.span
      layout
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`inline-block px-2 py-1 font-bold ${COLORS[colorIndex % COLORS.length]}`}
      style={{ fontSize: `${fontSize}px` }}
    >
      {text}
    </motion.span>
  );
});
