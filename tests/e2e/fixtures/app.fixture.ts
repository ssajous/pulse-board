import { test as base, expect, BrowserContext, Page } from "@playwright/test";

type AppFixtures = {
  contextA: BrowserContext;
  contextB: BrowserContext;
  pageA: Page;
  pageB: Page;
};

async function waitForPageReady(page: Page): Promise<void> {
  await page.goto("/");
  await page.locator("#topic-list").waitFor({ state: "visible" });
  // Wait for WebSocket connection to establish (logged by our diagnostic code)
  await page.waitForEvent("console", {
    predicate: (msg) => msg.text().includes("WebSocket connected to"),
    timeout: 10_000,
  });
}

export const test = base.extend<AppFixtures>({
  contextA: async ({ browser }, use) => {
    const context = await browser.newContext();
    await use(context);
    await context.close();
  },

  contextB: async ({ browser }, use) => {
    const context = await browser.newContext();
    await use(context);
    await context.close();
  },

  pageA: async ({ contextA }, use) => {
    const page = await contextA.newPage();
    await waitForPageReady(page);
    await use(page);
  },

  pageB: async ({ contextB }, use) => {
    const page = await contextB.newPage();
    await waitForPageReady(page);
    await use(page);
  },
});

export { expect };
