import { test as base, expect } from "@playwright/test";
import type { Page, BrowserContext } from "@playwright/test";
import {
  resetDatabase,
  createEventViaApi,
  createEventTopicViaApi,
  updateTopicStatusViaApi,
  closeEventViaApi,
} from "./helpers/api.helper";
import { waitForTopicToAppear } from "./helpers/wait.helper";

interface HostDashboardFixtures {
  event: { id: string; title: string; code: string; creatorToken: string };
  hostContext: BrowserContext;
  hostPage: Page;
  participantContext: BrowserContext;
  participantPage: Page;
}

function wsConnectedPromise(page: Page, code: string) {
  return page.waitForEvent("console", {
    predicate: (msg) =>
      msg.text().includes("WebSocket connected to") &&
      msg.text().includes(`/ws/events/${code}`),
    timeout: 15_000,
  });
}

async function reloadParticipantWithWs(
  page: Page,
  code: string
): Promise<void> {
  const wsPromise = wsConnectedPromise(page, code);
  await page.reload();
  await page.locator("#topic-list").waitFor({ state: "visible" });
  await wsPromise;
}

const test = base.extend<HostDashboardFixtures>({
  event: async ({}, use) => {
    const response = await createEventViaApi("Host Dashboard E2E Event");
    await use({
      id: response.id,
      title: response.title,
      code: response.code,
      creatorToken: response.creator_token!,
    });
  },

  hostContext: async ({ browser }, use) => {
    const context = await browser.newContext();
    await use(context);
    await context.close();
  },

  participantContext: async ({ browser }, use) => {
    const context = await browser.newContext();
    await use(context);
    await context.close();
  },

  hostPage: async ({ hostContext, event }, use) => {
    const page = await hostContext.newPage();
    await page.goto(`/events/${event.code}`);
    await page.evaluate(
      ({ code, token }) => {
        localStorage.setItem(`creator_token:${code}`, token);
      },
      { code: event.code, token: event.creatorToken }
    );
    await page.goto(`/events/${event.code}/admin`);
    await page.locator("#host-dashboard").waitFor({
      state: "visible",
      timeout: 15_000,
    });
    await use(page);
  },

  participantPage: async ({ participantContext, event }, use) => {
    const page = await participantContext.newPage();
    const wsPromise = wsConnectedPromise(page, event.code);
    await page.goto(`/events/${event.code}`);
    await page.locator("#topic-list").waitFor({ state: "visible" });
    await wsPromise;
    await use(page);
  },
});

test.describe("Host Dashboard", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("E2E-7.1: Host marks topic answered, participant sees badge", async ({
    event,
    hostPage,
    participantPage,
  }) => {
    const topic = await createEventTopicViaApi(event.id, "Answer me please");

    // Reload host page to pick up the topic
    await hostPage.reload();
    await hostPage
      .locator("#host-dashboard")
      .waitFor({ state: "visible", timeout: 15_000 });

    // Reload participant page with WS reconnect
    await reloadParticipantWithWs(participantPage, event.code);
    await waitForTopicToAppear(participantPage, "Answer me please");

    // Host marks topic as answered via API (triggers WS broadcast)
    await updateTopicStatusViaApi(
      event.id,
      topic.id,
      "answered",
      event.creatorToken
    );

    // Participant sees the "Answered" badge
    await expect(
      participantPage.locator(".participant-topic-answered-badge")
    ).toBeVisible({ timeout: 10_000 });
  });

  test("E2E-7.2: Host highlights topic, participant sees amber border", async ({
    event,
    participantPage,
  }) => {
    await createEventTopicViaApi(event.id, "Regular Topic");
    const topicB = await createEventTopicViaApi(
      event.id,
      "Highlight Me Topic"
    );

    await reloadParticipantWithWs(participantPage, event.code);
    await waitForTopicToAppear(participantPage, "Regular Topic");
    await waitForTopicToAppear(participantPage, "Highlight Me Topic");

    // Host highlights topicB via API
    await updateTopicStatusViaApi(
      event.id,
      topicB.id,
      "highlighted",
      event.creatorToken
    );

    // Participant sees highlighted topic with amber border
    await expect(
      participantPage.locator(`#topic-card-${topicB.id}`)
    ).toHaveClass(/border-amber/, { timeout: 10_000 });
  });

  test("E2E-7.3: Host archives topic, participant can no longer see it", async ({
    event,
    participantPage,
  }) => {
    const topic = await createEventTopicViaApi(event.id, "Archive This Topic");

    await reloadParticipantWithWs(participantPage, event.code);
    await waitForTopicToAppear(participantPage, "Archive This Topic");

    // Host archives the topic via API
    await updateTopicStatusViaApi(
      event.id,
      topic.id,
      "archived",
      event.creatorToken
    );

    // Topic disappears from the participant view
    await expect(
      participantPage.locator(`#topic-card-${topic.id}`)
    ).not.toBeVisible({ timeout: 10_000 });
  });

  test("E2E-7.4: Host closes event, participant cannot submit topics", async ({
    event,
    participantPage,
  }) => {
    await expect(participantPage.locator("#topic-form")).toBeVisible();

    // Host closes the event via API
    await closeEventViaApi(event.id, event.creatorToken);

    // Participant's topic form shows "event ended" message
    await expect(
      participantPage.locator("#topic-form")
    ).toContainText("This event has ended", { timeout: 10_000 });
  });

  test("E2E-7.5: Non-host user is redirected away from admin page", async ({
    event,
    browser,
  }) => {
    const visitorContext = await browser.newContext();
    const visitorPage = await visitorContext.newPage();

    await visitorPage.goto(`/events/${event.code}/admin`);

    // Should be redirected to the event board
    await expect(visitorPage).toHaveURL(`/events/${event.code}`, {
      timeout: 10_000,
    });
    await expect(
      visitorPage.locator("#host-dashboard")
    ).not.toBeAttached();

    await visitorContext.close();
  });
});
