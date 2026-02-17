import { Page, expect } from "@playwright/test";

const DEFAULT_TIMEOUT = 5_000;

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
