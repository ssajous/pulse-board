import { makeAutoObservable, runInAction } from "mobx";
import type { Poll, PollType } from "@domain/entities/Poll";
import type { PollApiPort } from "@domain/ports/PollApiPort";

const MIN_OPTIONS = 2;
const MAX_OPTIONS = 10;
const MAX_QUESTION_LENGTH = 500;

const TYPES_WITHOUT_OPTIONS: PollType[] = ["rating", "open_text", "word_cloud"];

export class PollCreationViewModel {
  question = "";
  pollType: PollType = "multiple_choice";
  options: string[] = ["", ""];
  isSubmitting = false;
  error: string | null = null;
  createdPoll: Poll | null = null;

  private readonly _api: PollApiPort;

  constructor(api: PollApiPort) {
    this._api = api;
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get requiresOptions(): boolean {
    return !TYPES_WITHOUT_OPTIONS.includes(this.pollType);
  }

  get isValid(): boolean {
    const questionTrimmed = this.question.trim();
    if (
      questionTrimmed.length === 0
      || questionTrimmed.length > MAX_QUESTION_LENGTH
    ) {
      return false;
    }
    if (!this.requiresOptions) return true;
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

  setPollType(type: PollType): void {
    this.pollType = type;
    this.options = ["", ""];
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
      const request = this.requiresOptions
        ? {
            question: this.question.trim(),
            options: this.options.map((o) => o.trim()),
            poll_type: this.pollType,
          }
        : {
            question: this.question.trim(),
            poll_type: this.pollType,
          };
      const poll = await this._api.createPoll(eventId, request);
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
    this.pollType = "multiple_choice";
    this.options = ["", ""];
    this.isSubmitting = false;
    this.error = null;
    this.createdPoll = null;
  }

  dispose(): void {
    /* no-op for cleanup */
  }
}
