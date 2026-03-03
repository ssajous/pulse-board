import { useState, type FormEvent } from "react";
import { observer } from "mobx-react-lite";
import { MessageSquarePlus, XCircle } from "lucide-react";
import { useTopicsViewModel } from "@presentation/view-models";
import { TopicFormInput } from "./TopicFormInput";
import { TopicFormSubmitButton } from "./TopicFormSubmitButton";

const MAX_CHARS = 255;

export const TopicForm = observer(function TopicForm() {
  const vm = useTopicsViewModel();
  const [content, setContent] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  const charCount = content.length;
  const isOverLimit = charCount > MAX_CHARS;
  const isEmpty = content.trim().length === 0;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (isEmpty || isOverLimit) return;

    const success = await vm.submitTopic(content.trim());
    if (success) {
      setContent("");
    }
  };

  if (vm.isEventClosed) {
    return (
      <div
        id="topic-form"
        className="mb-8 rounded-xl border border-slate-700 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
      >
        <div className="flex items-center gap-3 text-slate-400">
          <XCircle size={20} className="text-slate-500" />
          <p className="text-base font-medium">
            This event has ended.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      id="topic-form"
      className="mb-8 rounded-xl border border-l-4 border-slate-700 border-l-indigo-500 bg-slate-800 p-6 shadow-lg shadow-slate-900/20"
    >
      <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
        <MessageSquarePlus className="text-indigo-400" size={20} />
        Submit a Topic
      </h2>
      <form onSubmit={handleSubmit}>
        <TopicFormInput
          value={content}
          onChange={setContent}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          isFocused={isFocused}
          isOverLimit={isOverLimit}
          charCount={charCount}
        />
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Topics starting at score 0. Removed if score reaches -5.
          </p>
          <TopicFormSubmitButton disabled={isEmpty || isOverLimit} />
        </div>
      </form>
    </div>
  );
});
