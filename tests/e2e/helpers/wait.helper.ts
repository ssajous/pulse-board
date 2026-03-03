import { Page, expect } from "@playwright/test";

const DEFAULT_TIMEOUT = 5_000;
const WS_CONNECT_TIMEOUT = 10_000;

export async function reloadAndWaitForWs(page: Page): Promise<void> {
  const wsReady = page.waitForEvent("console", {
    predicate: (msg) => msg.text().includes("WebSocket connected to"),
    timeout: WS_CONNECT_TIMEOUT,
  });
  await page.reload();
  await wsReady;
}

export async function waitForTopicToAppear(
  page: Page,
  content: string
): Promise<void> {
  await expect(page.locator("#topic-list")).toContainText(content, {
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function waitForScoreUpdate(
  page: Page,
  topicId: string,
  expectedScore: number
): Promise<void> {
  const topicCard = page.locator(`#topic-card-${topicId}`);
  await expect(topicCard).toContainText(String(expectedScore), {
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function waitForTopicToDisappear(
  page: Page,
  topicId: string
): Promise<void> {
  await expect(page.locator(`#topic-card-${topicId}`)).not.toBeVisible({
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function waitForPollToAppear(page: Page): Promise<void> {
  await expect(page.locator("#poll-participation")).toBeVisible({
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function waitForPollResults(page: Page): Promise<void> {
  await expect(page.locator("#poll-results")).toBeVisible({
    timeout: DEFAULT_TIMEOUT,
  });
}

export async function waitForPollToDisappear(page: Page): Promise<void> {
  await expect(page.locator("#poll-participation")).not.toBeVisible({
    timeout: DEFAULT_TIMEOUT,
  });
  await expect(page.locator("#poll-results")).not.toBeVisible({
    timeout: DEFAULT_TIMEOUT,
  });
}
