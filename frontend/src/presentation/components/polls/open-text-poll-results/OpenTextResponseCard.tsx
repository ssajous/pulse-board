import { memo } from "react";
import type { OpenTextResponse } from "@domain/entities/Poll";

interface OpenTextResponseCardProps {
  response: OpenTextResponse;
}

export const OpenTextResponseCard = memo(function OpenTextResponseCard({
  response,
}: OpenTextResponseCardProps) {
  const formattedDate = new Date(response.created_at).toLocaleTimeString(
    [],
    { hour: "2-digit", minute: "2-digit" },
  );

  return (
    <div
      id={`open-text-response-${response.id}`}
      className="rounded-lg border border-slate-700 bg-slate-900 p-4"
    >
      <p className="text-sm leading-relaxed text-slate-200">
        {response.text}
      </p>
      <time className="mt-2 block text-xs text-slate-500">
        {formattedDate}
      </time>
    </div>
  );
});
