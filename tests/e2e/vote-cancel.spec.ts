import { test, expect } from "./fixtures/app.fixture";
import { resetDatabase, createTopicViaApi } from "./helpers/api.helper";
import {
  reloadAndWaitForWs,
  waitForTopicToAppear,
  waitForScoreUpdate,
} from "./helpers/wait.helper";

test.describe("Vote cancel", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("clicking upvote twice cancels the vote", async ({ pageA }) => {
    const topic = await createTopicViaApi("Cancel Upvote Topic");

    await reloadAndWaitForWs(pageA);
    await waitForTopicToAppear(pageA, "Cancel Upvote Topic");

    // First upvote
    const upvoteBtn = pageA.locator(`#topic-upvote-${topic.id}`);
    await upvoteBtn.click();
    await waitForScoreUpdate(pageA, topic.id, 1);

    // Wait for button to be re-enabled
    await expect(upvoteBtn).toBeEnabled();

    // Click again to cancel
    await upvoteBtn.click();
    await waitForScoreUpdate(pageA, topic.id, 0);
  });

  test("clicking downvote twice cancels the vote", async ({ pageA }) => {
    const topic = await createTopicViaApi("Cancel Downvote Topic");

    await reloadAndWaitForWs(pageA);
    await waitForTopicToAppear(pageA, "Cancel Downvote Topic");

    // First downvote
    const downvoteBtn = pageA.locator(`#topic-downvote-${topic.id}`);
    await downvoteBtn.click();
    await waitForScoreUpdate(pageA, topic.id, -1);

    // Wait for button to be re-enabled
    await expect(downvoteBtn).toBeEnabled();

    // Click again to cancel
    await downvoteBtn.click();
    await waitForScoreUpdate(pageA, topic.id, 0);
  });
});
