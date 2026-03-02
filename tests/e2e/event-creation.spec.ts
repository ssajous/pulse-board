import { test, expect } from "@playwright/test";
import { resetDatabase } from "./helpers/api.helper";

test.describe("Event creation", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("user can create an event and see the join code", async ({
    page,
  }) => {
    await page.goto("/events/new");

    await page.fill("#event-title", "My Test Event");
    await page.click("#event-creation-submit");

    // Confirmation should appear with a 6-digit code
    await expect(page.locator("#event-creation-confirmation")).toBeVisible(
      { timeout: 5_000 }
    );
    const codeEl = page.locator(
      "#event-creation-confirmation #event-join-code"
    );
    await expect(codeEl).toBeVisible();
    const code = await codeEl.textContent();
    expect(code).toMatch(/^\d{6}$/);
  });

  test("user can navigate to event board from confirmation", async ({
    page,
  }) => {
    await page.goto("/events/new");

    await page.fill("#event-title", "Board Nav Event");
    await page.click("#event-creation-submit");

    await expect(page.locator("#event-creation-confirmation")).toBeVisible(
      { timeout: 5_000 }
    );

    // Click "Go to Event Board" link
    await page.click("text=Go to Event Board");

    // Should navigate to the event board page
    await expect(page).toHaveURL(/\/events\/\d{6}$/);
    await expect(page.locator("#event-board-header")).toBeVisible({
      timeout: 10_000,
    });
  });

  test("submit button is disabled when title is empty", async ({
    page,
  }) => {
    await page.goto("/events/new");

    const submitBtn = page.locator("#event-creation-submit");
    await expect(submitBtn).toBeDisabled();
  });

  test("event can be created with a description", async ({ page }) => {
    await page.goto("/events/new");

    await page.fill("#event-title", "Described Event");
    await page.fill("#event-description", "A detailed description");
    await page.click("#event-creation-submit");

    await expect(page.locator("#event-creation-confirmation")).toBeVisible(
      { timeout: 5_000 }
    );
    const codeEl = page.locator(
      "#event-creation-confirmation #event-join-code"
    );
    const code = await codeEl.textContent();
    expect(code).toMatch(/^\d{6}$/);
  });
});
