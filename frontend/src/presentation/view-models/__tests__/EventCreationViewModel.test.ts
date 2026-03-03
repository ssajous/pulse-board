import { describe, it, expect, vi, beforeEach } from "vitest";
import { EventCreationViewModel } from "../EventCreationViewModel";
import type { Event } from "@domain/entities/Event";
import type { EventApiPort } from "@domain/ports/EventApiPort";
import type { FingerprintPort } from "@domain/ports/FingerprintPort";

// --- Factories ---

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    id: "evt-1",
    title: "Test Event",
    code: "123456",
    description: null,
    start_date: null,
    end_date: null,
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function createMockEventApi(): EventApiPort {
  return {
    createEvent: vi.fn().mockResolvedValue(makeEvent()),
    getEventByCode: vi.fn().mockResolvedValue(makeEvent()),
    getEventById: vi.fn().mockResolvedValue(makeEvent()),
    checkCreator: vi
      .fn()
      .mockResolvedValue({ is_creator: false }),
  };
}

function createMockFingerprint(
  id: string = "test-fingerprint-id",
): FingerprintPort {
  return {
    getFingerprint: vi.fn().mockResolvedValue(id),
  };
}

// --- Tests ---

describe("EventCreationViewModel", () => {
  let api: EventApiPort;
  let fingerprint: FingerprintPort;
  let vm: EventCreationViewModel;

  beforeEach(() => {
    api = createMockEventApi();
    fingerprint = createMockFingerprint();
    vm = new EventCreationViewModel(api, fingerprint);
  });

  describe("initial state", () => {
    it("has empty title", () => {
      expect(vm.title).toBe("");
    });

    it("has empty description", () => {
      expect(vm.description).toBe("");
    });

    it("has empty startDate", () => {
      expect(vm.startDate).toBe("");
    });

    it("has empty endDate", () => {
      expect(vm.endDate).toBe("");
    });

    it("is not submitting", () => {
      expect(vm.isSubmitting).toBe(false);
    });

    it("has no error", () => {
      expect(vm.error).toBeNull();
    });

    it("has no createdCode", () => {
      expect(vm.createdCode).toBeNull();
    });
  });

  describe("isValid computed", () => {
    it("returns false when title is empty", () => {
      expect(vm.isValid).toBe(false);
    });

    it("returns false when title is only whitespace", () => {
      vm.setTitle("   ");
      expect(vm.isValid).toBe(false);
    });

    it("returns false when title exceeds 200 characters", () => {
      vm.setTitle("A".repeat(201));
      expect(vm.isValid).toBe(false);
    });

    it("returns true when title is exactly 200 characters", () => {
      vm.setTitle("A".repeat(200));
      expect(vm.isValid).toBe(true);
    });

    it("returns true when title has content", () => {
      vm.setTitle("Valid Title");
      expect(vm.isValid).toBe(true);
    });
  });

  describe("isComplete computed", () => {
    it("returns false when createdCode is null", () => {
      expect(vm.isComplete).toBe(false);
    });

    it("returns true after successful submit", async () => {
      vm.setTitle("My Event");
      await vm.submit();
      expect(vm.isComplete).toBe(true);
    });
  });

  describe("setters", () => {
    it("setTitle updates the title", () => {
      vm.setTitle("New Title");
      expect(vm.title).toBe("New Title");
    });

    it("setDescription updates the description", () => {
      vm.setDescription("Some description");
      expect(vm.description).toBe("Some description");
    });

    it("setStartDate updates the startDate", () => {
      vm.setStartDate("2026-03-01");
      expect(vm.startDate).toBe("2026-03-01");
    });

    it("setEndDate updates the endDate", () => {
      vm.setEndDate("2026-03-31");
      expect(vm.endDate).toBe("2026-03-31");
    });
  });

  describe("submit", () => {
    it("includes creator_fingerprint from fingerprint service", async () => {
      vm.setTitle("My Event");

      await vm.submit();

      expect(api.createEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          creator_fingerprint: "test-fingerprint-id",
        }),
      );
    });

    it("passes fingerprint to create request with all fields", async () => {
      vm.setTitle("My Event");
      vm.setDescription("desc");

      await vm.submit();

      expect(api.createEvent).toHaveBeenCalledWith({
        title: "My Event",
        description: "desc",
        start_date: undefined,
        end_date: undefined,
        creator_fingerprint: "test-fingerprint-id",
      });
    });

    it("trims title and description before sending", async () => {
      vm.setTitle("  My Event  ");
      vm.setDescription("  desc  ");

      await vm.submit();

      expect(api.createEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "My Event",
          description: "desc",
        }),
      );
    });

    it("sends start_date and end_date when provided", async () => {
      vm.setTitle("My Event");
      vm.setStartDate("2026-03-01");
      vm.setEndDate("2026-03-31");

      await vm.submit();

      expect(api.createEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: "2026-03-01",
          end_date: "2026-03-31",
        }),
      );
    });

    it("sets createdCode on success", async () => {
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockResolvedValue(makeEvent({ code: "999999" }));

      vm.setTitle("My Event");
      await vm.submit();

      expect(vm.createdCode).toBe("999999");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.error).toBeNull();
    });

    it("sets isSubmitting during the API call", async () => {
      let resolvePromise: (value: Event) => void;
      const pendingPromise = new Promise<Event>((resolve) => {
        resolvePromise = resolve;
      });
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockReturnValue(pendingPromise);

      vm.setTitle("My Event");

      const submitPromise = vm.submit();
      expect(vm.isSubmitting).toBe(true);

      resolvePromise!(makeEvent());
      await submitPromise;

      expect(vm.isSubmitting).toBe(false);
    });

    it("handles fingerprint service failure gracefully", async () => {
      const failingFingerprint: FingerprintPort = {
        getFingerprint: vi
          .fn()
          .mockRejectedValue(new Error("Fingerprint failed")),
      };
      const failVm = new EventCreationViewModel(
        api,
        failingFingerprint,
      );

      failVm.setTitle("My Event");
      await failVm.submit();

      expect(failVm.error).toBe("Fingerprint failed");
      expect(failVm.isSubmitting).toBe(false);
      expect(failVm.createdCode).toBeNull();
    });

    it("sets error on API failure", async () => {
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Network error"));

      vm.setTitle("My Event");
      await vm.submit();

      expect(vm.error).toBe("Network error");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.createdCode).toBeNull();
    });

    it("sets generic error when non-Error is thrown", async () => {
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockRejectedValue("string error");

      vm.setTitle("My Event");
      await vm.submit();

      expect(vm.error).toBe("Failed to create event");
    });

    it("does nothing when form is invalid", async () => {
      // Title is empty, so isValid is false
      await vm.submit();

      expect(fingerprint.getFingerprint).not.toHaveBeenCalled();
      expect(api.createEvent).not.toHaveBeenCalled();
      expect(vm.isSubmitting).toBe(false);
    });

    it("does nothing when already submitting", async () => {
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockReturnValue(new Promise(() => {}));

      vm.setTitle("My Event");

      // Start first submit (will hang)
      vm.submit();
      expect(vm.isSubmitting).toBe(true);

      // Second submit should be a no-op
      await vm.submit();

      expect(api.createEvent).toHaveBeenCalledTimes(1);
    });

    it("clears previous error on new submission", async () => {
      // First call fails
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockRejectedValueOnce(new Error("First fail"));
      // Second call succeeds
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockResolvedValueOnce(makeEvent());

      vm.setTitle("My Event");

      await vm.submit();
      expect(vm.error).toBe("First fail");

      await vm.submit();
      expect(vm.error).toBeNull();
    });
  });

  describe("reset", () => {
    it("clears all state back to initial values", async () => {
      vm.setTitle("My Event");
      vm.setDescription("Some description");
      vm.setStartDate("2026-03-01");
      vm.setEndDate("2026-03-31");

      await vm.submit();

      // Verify state was modified
      expect(vm.createdCode).not.toBeNull();

      vm.reset();

      expect(vm.title).toBe("");
      expect(vm.description).toBe("");
      expect(vm.startDate).toBe("");
      expect(vm.endDate).toBe("");
      expect(vm.isSubmitting).toBe(false);
      expect(vm.error).toBeNull();
      expect(vm.createdCode).toBeNull();
    });

    it("clears error state", async () => {
      (
        api.createEvent as ReturnType<typeof vi.fn>
      ).mockRejectedValue(new Error("Fail"));

      vm.setTitle("My Event");
      await vm.submit();

      expect(vm.error).toBe("Fail");

      vm.reset();

      expect(vm.error).toBeNull();
    });
  });
});
