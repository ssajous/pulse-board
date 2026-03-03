import { test, expect, type Page } from "@playwright/test";
import { resetDatabase } from "./helpers/api.helper";

/**
 * Helper: create an event via the UI and return the 6-digit join code.
 *
 * The page object must belong to the browser context that will later navigate
 * to the event board so that the creator_fingerprint written by FingerprintJS
 * during creation is the same fingerprint used when the board is visited.
 */
async function createEventViaUi(
  page: Page,
  title: string,
): Promise<string> {
  await page.goto("/events/new");
  await page.fill("#event-title", title);
  await page.click("#event-creation-submit");

  await expect(page.locator("#event-creation-confirmation")).toBeVisible({
    timeout: 5_000,
  });

  const codeEl = page.locator(
    "#event-creation-confirmation #event-join-code",
  );
  await expect(codeEl).toBeVisible();
  const code = await codeEl.textContent();
  expect(code).toMatch(/^\d{6}$/);
  return code!;
}

/**
 * Helper: navigate to an event board and wait until the board header is
 * visible (the page is fully loaded and the async creator-check has had
 * time to resolve).
 */
async function navigateToEventBoard(
  page: Page,
  code: string,
): Promise<void> {
  await page.goto(`/events/${code}`);
  await page.locator("#topic-list").waitFor({ state: "visible" });
  await expect(page.locator("#event-board-header")).toBeVisible({
    timeout: 10_000,
  });
}

test.describe("Admin navigation", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("creator sees admin link on event board", async ({ page }) => {
    // Arrange: create the event through the UI so the browser fingerprint is
    // stored as creator_fingerprint on the backend.
    const code = await createEventViaUi(page, "Creator Admin Test Event");

    // Act: navigate to the event board in the same page/context so the same
    // fingerprint is sent to the check-creator endpoint.
    await navigateToEventBoard(page, code);

    // Assert: the admin link should appear after the async fingerprint check
    // resolves.  Give it a generous timeout because FingerprintJS initialises
    // and the API call happens after the initial render.
    await expect(page.locator("#event-admin-link")).toBeVisible({
      timeout: 10_000,
    });
  });

  test("non-creator does not see admin link on event board", async ({
    browser,
  }) => {
    // Arrange: creator creates the event in context A.
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    const code = await createEventViaUi(
      creatorPage,
      "Non-Creator Admin Test Event",
    );
    await creatorContext.close();

    // Act: a different browser context (fresh fingerprint) visits the board.
    const visitorContext = await browser.newContext();
    const visitorPage = await visitorContext.newPage();
    await navigateToEventBoard(visitorPage, code);

    // Wait long enough for the check-creator call to have completed before
    // asserting absence, matching the generous timeout used in the positive
    // test above.
    await visitorPage.waitForTimeout(10_000);
    await expect(visitorPage.locator("#event-admin-link")).not.toBeAttached();

    await visitorContext.close();
  });

  test("admin link navigates to admin URL", async ({ page }) => {
    // Arrange: creator creates the event via UI.
    const code = await createEventViaUi(page, "Admin Link Navigation Event");

    // Navigate to the event board in the same context so creator status is
    // detected.
    await navigateToEventBoard(page, code);

    // Wait for the admin link to appear before interacting with it.
    const adminLink = page.locator("#event-admin-link");
    await expect(adminLink).toBeVisible({ timeout: 10_000 });

    // Act: click the admin link.
    await adminLink.click();

    // Assert: the URL should change to the admin page for this event.
    await expect(page).toHaveURL(`/events/${code}/admin`, {
      timeout: 5_000,
    });
  });
});
