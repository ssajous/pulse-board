import { makeAutoObservable, runInAction } from "mobx";
import type { Poll } from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";

const MIN_OPTIONS = 2;
const MAX_OPTIONS = 10;
const MAX_QUESTION_LENGTH = 500;

export class PollCreationViewModel {
  question = "";
  options: string[] = ["", ""];
  isSubmitting = false;
  error: string | null = null;
  createdPoll: Poll | null = null;

  private readonly _api: PollApiPort;

  constructor(api: PollApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get isValid(): boolean {
    const questionTrimmed = this.question.trim();
    if (
      questionTrimmed.length === 0
      || questionTrimmed.length > MAX_QUESTION_LENGTH
    ) {
      return false;
    }
    if (
      this.options.length < MIN_OPTIONS
      || this.options.length > MAX_OPTIONS
    ) {
      return false;
    }
    return this.options.every((opt) => opt.trim().length > 0);
  }

  get canAddOption(): boolean {
    return this.options.length < MAX_OPTIONS;
  }

  get canRemoveOption(): boolean {
    return this.options.length > MIN_OPTIONS;
  }

  setQuestion(value: string): void {
    this.question = value;
  }

  addOption(): void {
    if (!this.canAddOption) return;
    this.options.push("");
  }

  removeOption(index: number): void {
    if (!this.canRemoveOption) return;
    this.options.splice(index, 1);
  }

  setOptionText(index: number, text: string): void {
    if (index >= 0 && index < this.options.length) {
      this.options[index] = text;
    }
  }

  async submit(eventId: string): Promise<void> {
    if (!this.isValid || this.isSubmitting) return;
    this.isSubmitting = true;
    this.error = null;
    try {
      const poll = await this._api.createPoll(eventId, {
        question: this.question.trim(),
        options: this.options.map((o) => o.trim()),
      });
      runInAction(() => {
        this.createdPoll = poll;
        this.isSubmitting = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error =
          e instanceof Error ? e.message : "Failed to create poll";
        this.isSubmitting = false;
      });
    }
  }

  reset(): void {
    this.question = "";
    this.options = ["", ""];
    this.isSubmitting = false;
    this.error = null;
    this.createdPoll = null;
  }

  dispose(): void {
    /* no-op for cleanup */
  }
}
