import { test, expect } from "./fixtures/app.fixture";
import { resetDatabase } from "./helpers/api.helper";
import { waitForTopicToAppear } from "./helpers/wait.helper";

test.describe("Topic broadcast", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("topic created in Browser A appears in Browser B via WebSocket", async ({
    pageA,
    pageB,
  }) => {
    // Type a topic in pageA
    await pageA.fill("#topic-input", "E2E Test Topic");
    await pageA.click("#topic-submit");

    // Verify it appears in pageA
    await waitForTopicToAppear(pageA, "E2E Test Topic");

    // Verify it appears in pageB via WebSocket (no refresh)
    await waitForTopicToAppear(pageB, "E2E Test Topic");
  });

  test("topic appears with correct initial score of 0", async ({
    pageA,
    pageB,
  }) => {
    await pageA.fill("#topic-input", "Score Zero Topic");
    await pageA.click("#topic-submit");

    await waitForTopicToAppear(pageB, "Score Zero Topic");

    // Check the score is 0
    const topicCard = pageB
      .locator('[id^="topic-card-"]')
      .filter({ hasText: "Score Zero Topic" });
    await expect(topicCard.locator(".tabular-nums")).toContainText("0");
  });

  test("multiple topics broadcast in sequence", async ({ pageA, pageB }) => {
    await pageA.fill("#topic-input", "First Topic");
    await pageA.click("#topic-submit");
    await waitForTopicToAppear(pageB, "First Topic");

    await pageA.fill("#topic-input", "Second Topic");
    await pageA.click("#topic-submit");
    await waitForTopicToAppear(pageB, "Second Topic");
  });
});
