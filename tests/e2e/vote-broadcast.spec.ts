import { test } from "./fixtures/app.fixture";
import { resetDatabase, createTopicViaApi } from "./helpers/api.helper";
import {
  reloadAndWaitForWs,
  waitForTopicToAppear,
  waitForScoreUpdate,
} from "./helpers/wait.helper";

test.describe("Vote broadcast", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("upvote in Browser A updates score in Browser B", async ({
    pageA,
    pageB,
  }) => {
    // Create topic via API so both browsers see it
    const topic = await createTopicViaApi("Vote Test Topic");

    // Reload both pages to pick up the new topic and re-establish WebSocket
    await reloadAndWaitForWs(pageA);
    await reloadAndWaitForWs(pageB);
    await waitForTopicToAppear(pageA, "Vote Test Topic");
    await waitForTopicToAppear(pageB, "Vote Test Topic");

    // Upvote in pageA
    await pageA.click(`#topic-upvote-${topic.id}`);

    // Score should update in pageB via WebSocket
    await waitForScoreUpdate(pageB, topic.id, 1);
  });

  test("downvote in Browser A updates score in Browser B", async ({
    pageA,
    pageB,
  }) => {
    const topic = await createTopicViaApi("Downvote Test Topic");

    await reloadAndWaitForWs(pageA);
    await reloadAndWaitForWs(pageB);
    await waitForTopicToAppear(pageA, "Downvote Test Topic");
    await waitForTopicToAppear(pageB, "Downvote Test Topic");

    // Downvote in pageA
    await pageA.click(`#topic-downvote-${topic.id}`);

    // Score should update in pageB
    await waitForScoreUpdate(pageB, topic.id, -1);
  });
});
