import { test, expect } from "./fixtures/event-app.fixture";
import { resetDatabase } from "./helpers/api.helper";

test.describe("Poll creation", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("admin can create a poll with question and options", async ({
    event,
    contextA,
  }) => {
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Fill in question
    await adminPage.fill("#poll-question-input", "What is your favorite color?");

    // Fill in options (2 options are pre-populated as empty inputs)
    await adminPage.fill("#poll-option-input-0", "Red");
    await adminPage.fill("#poll-option-input-1", "Blue");

    // Submit the form
    await adminPage.click("#poll-submit-btn");

    // Verify the created poll appears in the poll list
    await expect(
      adminPage.getByText("What is your favorite color?")
    ).toBeVisible({ timeout: 5_000 });
  });

  test("created poll appears in the poll list on admin page", async ({
    event,
    contextA,
  }) => {
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Create a poll
    await adminPage.fill("#poll-question-input", "Best programming language?");
    await adminPage.fill("#poll-option-input-0", "Python");
    await adminPage.fill("#poll-option-input-1", "TypeScript");

    // Add a third option
    await adminPage.getByText("Add option").click();
    await adminPage.fill("#poll-option-input-2", "Rust");

    await adminPage.click("#poll-submit-btn");

    // Verify poll question and the Polls heading (with count) appear
    await expect(
      adminPage.getByText("Best programming language?")
    ).toBeVisible({ timeout: 5_000 });
    await expect(adminPage.getByText("Polls (1)")).toBeVisible();
  });

  test("poll starts as inactive", async ({ event, contextA }) => {
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Create a poll
    await adminPage.fill("#poll-question-input", "Inactive poll test");
    await adminPage.fill("#poll-option-input-0", "Option A");
    await adminPage.fill("#poll-option-input-1", "Option B");
    await adminPage.click("#poll-submit-btn");

    // Verify the poll shows Inactive badge
    await expect(
      adminPage.getByText("Inactive poll test")
    ).toBeVisible({ timeout: 5_000 });
    await expect(
      adminPage.getByText("Inactive", { exact: true })
    ).toBeVisible();

    // Verify Activate button is present (not Deactivate)
    await expect(
      adminPage.getByRole("button", { name: "Activate" })
    ).toBeVisible();
  });

  test("cannot create a poll with empty question", async ({
    event,
    contextA,
  }) => {
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Leave question empty, fill in options
    await adminPage.fill("#poll-option-input-0", "Option A");
    await adminPage.fill("#poll-option-input-1", "Option B");

    // Submit button should be disabled
    await expect(adminPage.locator("#poll-submit-btn")).toBeDisabled();
  });

  test("cannot create a poll with fewer than 2 filled options", async ({
    event,
    contextA,
  }) => {
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Fill question but only one option
    await adminPage.fill("#poll-question-input", "Incomplete poll?");
    await adminPage.fill("#poll-option-input-0", "Only option");
    // Leave option 1 empty

    // Submit button should be disabled because one option is empty
    await expect(adminPage.locator("#poll-submit-btn")).toBeDisabled();
  });
});
