import { MessageSquarePlus } from "lucide-react";

export function TopicListEmpty() {
  return (
    <div className="py-20 text-center opacity-50">
      <MessageSquarePlus className="mx-auto mb-3 h-12 w-12 text-slate-700" />
      <p className="text-lg font-medium text-slate-500">No topics yet</p>
      <p className="text-sm text-slate-600">
        Be the first to start the conversation
      </p>
    </div>
  );
}
