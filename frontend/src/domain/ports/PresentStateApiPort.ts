import type { PresentState } from "@domain/entities/PresentState";

export interface PresentStateApiPort {
  getPresentState(eventId: string): Promise<PresentState>;
}
