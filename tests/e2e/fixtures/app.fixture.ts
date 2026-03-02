import { test as base, expect, BrowserContext, Page } from "@playwright/test";

type AppFixtures = {
  contextA: BrowserContext;
  contextB: BrowserContext;
  pageA: Page;
  pageB: Page;
};

async function waitForPageReady(page: Page): Promise<void> {
  // Start listening for the WebSocket console message BEFORE navigating,
  // to avoid a race where the WS connects before the listener is set up.
  const wsConnected = page.waitForEvent("console", {
    predicate: (msg) => msg.text().includes("WebSocket connected to"),
    timeout: 15_000,
  });
  await page.goto("/");
  await page.locator("#topic-list").waitFor({ state: "visible" });
  await wsConnected;
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
