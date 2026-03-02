import { test as base, expect, BrowserContext, Page } from "@playwright/test";
import { createEventViaApi } from "../helpers/api.helper";

interface EventInfo {
  id: string;
  title: string;
  code: string;
}

type EventAppFixtures = {
  event: EventInfo;
  contextA: BrowserContext;
  contextB: BrowserContext;
  eventPageA: Page;
  eventPageB: Page;
};

async function waitForEventPageReady(
  page: Page,
  code: string
): Promise<void> {
  // Start listening for the WebSocket console message BEFORE navigating,
  // to avoid a race where the WS connects before the listener is set up.
  const wsConnected = page.waitForEvent("console", {
    predicate: (msg) =>
      msg.text().includes("WebSocket connected to") &&
      msg.text().includes(`/ws/events/${code}`),
    timeout: 15_000,
  });
  await page.goto(`/events/${code}`);
  await page.locator("#topic-list").waitFor({ state: "visible" });
  await wsConnected;
}

export const test = base.extend<EventAppFixtures>({
  event: async ({}, use) => {
    const response = await createEventViaApi("E2E Test Event");
    await use({
      id: response.id,
      title: response.title,
      code: response.code,
    });
  },

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

  eventPageA: async ({ contextA, event }, use) => {
    const page = await contextA.newPage();
    await waitForEventPageReady(page, event.code);
    await use(page);
  },

  eventPageB: async ({ contextB, event }, use) => {
    const page = await contextB.newPage();
    await waitForEventPageReady(page, event.code);
    await use(page);
  },
});

export { expect };
