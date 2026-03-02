import { test, expect } from "@playwright/test";
import { resetDatabase, createEventViaApi } from "./helpers/api.helper";

test.describe("Event join", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("user can join an event with a valid code", async ({ page }) => {
    const event = await createEventViaApi("Joinable Event");

    await page.goto("/events/join");
    await page.fill("#event-join-code", event.code);
    await page.click("#event-join-submit");

    // Should navigate to the event board
    await expect(page).toHaveURL(`/events/${event.code}`, {
      timeout: 10_000,
    });
    await expect(page.locator("#event-board-header")).toBeVisible({
      timeout: 10_000,
    });
  });

  test("join button is disabled for incomplete codes", async ({
    page,
  }) => {
    await page.goto("/events/join");
    await page.fill("#event-join-code", "123");

    const submitBtn = page.locator("#event-join-submit");
    await expect(submitBtn).toBeDisabled();
  });

  test("error shown for nonexistent event code", async ({ page }) => {
    await page.goto("/events/join");
    await page.fill("#event-join-code", "999999");
    await page.click("#event-join-submit");

    // Should show an error message
    await expect(page.locator("text=Event not found")).toBeVisible({
      timeout: 5_000,
    });
  });

  test("full flow: create event then join from another tab", async ({
    browser,
  }) => {
    // Creator creates event
    const contextA = await browser.newContext();
    const creatorPage = await contextA.newPage();
    await creatorPage.goto("/events/new");
    await creatorPage.fill("#event-title", "Cross-Tab Event");
    await creatorPage.click("#event-creation-submit");

    await expect(
      creatorPage.locator("#event-creation-confirmation")
    ).toBeVisible({ timeout: 5_000 });
    const code = await creatorPage
      .locator("#event-creation-confirmation #event-join-code")
      .textContent();
    expect(code).toBeTruthy();

    // Joiner joins with the code
    const contextB = await browser.newContext();
    const joinerPage = await contextB.newPage();
    await joinerPage.goto("/events/join");
    await joinerPage.fill("#event-join-code", code!);
    await joinerPage.click("#event-join-submit");

    await expect(joinerPage).toHaveURL(`/events/${code}`, {
      timeout: 10_000,
    });
    await expect(joinerPage.locator("#event-board-header")).toBeVisible({
      timeout: 10_000,
    });

    await contextA.close();
    await contextB.close();
  });
});
