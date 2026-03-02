import { test, expect } from "./fixtures/event-app.fixture";
import {
  resetDatabase,
  createEventTopicViaApi,
  castVoteViaApi,
} from "./helpers/api.helper";
import {
  waitForTopicToAppear,
  waitForScoreUpdate,
} from "./helpers/wait.helper";

test.describe("Event board", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("event board displays event title", async ({
    event,
    eventPageA,
  }) => {
    const header = eventPageA.locator("#event-board-header");
    await expect(header).toContainText(event.title);
  });

  test("topic created in event appears for the author", async ({
    event,
    eventPageA,
  }) => {
    await eventPageA.fill("#topic-input", "Event Topic Alpha");
    await eventPageA.click("#topic-submit");

    await waitForTopicToAppear(eventPageA, "Event Topic Alpha");
  });

  test("topic created in event broadcasts to other participant", async ({
    event,
    eventPageA,
    eventPageB,
  }) => {
    await eventPageA.fill("#topic-input", "Broadcast Topic");
    await eventPageA.click("#topic-submit");

    // Should appear for both users
    await waitForTopicToAppear(eventPageA, "Broadcast Topic");
    await waitForTopicToAppear(eventPageB, "Broadcast Topic");
  });

  test("multiple topics broadcast in sequence within event", async ({
    event,
    eventPageA,
    eventPageB,
  }) => {
    await eventPageA.fill("#topic-input", "First Event Topic");
    await eventPageA.click("#topic-submit");
    await waitForTopicToAppear(eventPageB, "First Event Topic");

    await eventPageA.fill("#topic-input", "Second Event Topic");
    await eventPageA.click("#topic-submit");
    await waitForTopicToAppear(eventPageB, "Second Event Topic");
  });

  test("event topic starts with score 0", async ({
    event,
    eventPageA,
    eventPageB,
  }) => {
    await eventPageA.fill("#topic-input", "Zero Score Topic");
    await eventPageA.click("#topic-submit");

    await waitForTopicToAppear(eventPageB, "Zero Score Topic");

    const topicCard = eventPageB
      .locator('[id^="topic-card-"]')
      .filter({ hasText: "Zero Score Topic" });
    await expect(topicCard.locator(".tabular-nums")).toContainText("0");
  });

  test("vote on event topic updates score locally", async ({
    event,
    eventPageA,
  }) => {
    // Create topic via API for deterministic ID
    const topic = await createEventTopicViaApi(
      event.id,
      "Voteable Topic"
    );

    // Reload to pick up the API-created topic
    const wsReady = eventPageA.waitForEvent("console", {
      predicate: (msg) =>
        msg.text().includes("WebSocket connected to"),
      timeout: 10_000,
    });
    await eventPageA.reload();
    await wsReady;
    await waitForTopicToAppear(eventPageA, "Voteable Topic");

    // Upvote
    await eventPageA.click(`#topic-upvote-${topic.id}`);
    await waitForScoreUpdate(eventPageA, topic.id, 1);
  });
});
