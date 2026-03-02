import { test, expect } from "./fixtures/event-app.fixture";
import {
  resetDatabase,
  createPollViaApi,
  activatePollViaApi,
} from "./helpers/api.helper";
import {
  waitForPollToAppear,
  waitForPollToDisappear,
} from "./helpers/wait.helper";

test.describe("Poll activation", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("admin can activate a poll from the admin page", async ({
    event,
    contextA,
  }) => {
    // Create a poll via API
    await createPollViaApi(event.id, "Should we activate?", [
      "Yes",
      "No",
    ]);

    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Wait for poll list to load with the created poll
    await expect(
      adminPage.getByText("Should we activate?")
    ).toBeVisible({ timeout: 5_000 });

    // Click Activate button
    await adminPage.getByRole("button", { name: "Activate" }).click();

    // Verify the poll now shows Active badge
    await expect(
      adminPage.getByText("Active", { exact: true })
    ).toBeVisible({ timeout: 5_000 });

    // Verify the Deactivate button is present
    await expect(
      adminPage.getByRole("button", { name: "Deactivate" })
    ).toBeVisible();
  });

  test("activated poll appears as Live Poll on participant event board", async ({
    event,
    eventPageB,
  }) => {
    // Create and activate a poll via API
    const poll = await createPollViaApi(
      event.id,
      "What topic should we discuss?",
      ["Architecture", "Testing", "Performance"],
    );
    await activatePollViaApi(poll.id);

    // The participant's event board page (eventPageB) should show the poll
    // via WebSocket broadcast
    await waitForPollToAppear(eventPageB);

    // Verify the poll question and "Live Poll" label are visible
    await expect(eventPageB.getByText("Live Poll")).toBeVisible();
    await expect(
      eventPageB.getByText("What topic should we discuss?")
    ).toBeVisible();

    // Verify all options are visible
    await expect(eventPageB.getByText("Architecture")).toBeVisible();
    await expect(eventPageB.getByText("Testing")).toBeVisible();
    await expect(eventPageB.getByText("Performance")).toBeVisible();
  });

  test("admin can deactivate a poll", async ({ event, contextA }) => {
    // Create and activate a poll via API
    const poll = await createPollViaApi(
      event.id,
      "Deactivation test",
      ["A", "B"],
    );
    await activatePollViaApi(poll.id);

    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Wait for poll to show as active
    await expect(adminPage.getByText("Deactivation test")).toBeVisible({
      timeout: 5_000,
    });
    await expect(
      adminPage.getByRole("button", { name: "Deactivate" })
    ).toBeVisible({ timeout: 5_000 });

    // Deactivate the poll
    await adminPage.getByRole("button", { name: "Deactivate" }).click();

    // Verify the poll now shows Inactive badge and Activate button
    await expect(
      adminPage.getByText("Inactive", { exact: true })
    ).toBeVisible({ timeout: 5_000 });
    await expect(
      adminPage.getByRole("button", { name: "Activate" })
    ).toBeVisible();
  });

  test("deactivated poll disappears from participant event board", async ({
    event,
    contextA,
    eventPageB,
  }) => {
    // Create and activate a poll via API
    const poll = await createPollViaApi(
      event.id,
      "Disappearing poll",
      ["Alpha", "Beta"],
    );
    await activatePollViaApi(poll.id);

    // Wait for participant to see the poll
    await waitForPollToAppear(eventPageB);
    await expect(
      eventPageB.getByText("Disappearing poll")
    ).toBeVisible();

    // Open admin page and deactivate
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });
    await expect(
      adminPage.getByRole("button", { name: "Deactivate" })
    ).toBeVisible({ timeout: 5_000 });
    await adminPage.getByRole("button", { name: "Deactivate" }).click();

    // Poll should disappear from participant's board via WebSocket
    await waitForPollToDisappear(eventPageB);
  });

  test("only one poll can be active at a time", async ({
    event,
    eventPageB,
  }) => {
    // Create two polls via API
    const poll1 = await createPollViaApi(
      event.id,
      "First poll question",
      ["Option 1A", "Option 1B"],
    );
    const poll2 = await createPollViaApi(
      event.id,
      "Second poll question",
      ["Option 2A", "Option 2B"],
    );

    // Activate the first poll
    await activatePollViaApi(poll1.id);

    // Verify participant sees the first poll
    await waitForPollToAppear(eventPageB);
    await expect(
      eventPageB.getByText("First poll question")
    ).toBeVisible();

    // Now activate the second poll (this should deactivate the first)
    await activatePollViaApi(poll2.id);

    // The participant should see the second poll, not the first
    await expect(
      eventPageB.getByText("Second poll question")
    ).toBeVisible({ timeout: 5_000 });
    await expect(
      eventPageB.getByText("First poll question")
    ).not.toBeVisible();
  });
});
