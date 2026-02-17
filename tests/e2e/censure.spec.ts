import { test, expect } from "./fixtures/app.fixture";
import {
  resetDatabase,
  createTopicViaApi,
  castVoteViaApi,
} from "./helpers/api.helper";
import {
  reloadAndWaitForWs,
  waitForTopicToAppear,
  waitForTopicToDisappear,
} from "./helpers/wait.helper";

test.describe("Censure", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("topic disappears when downvoted to censure threshold", async ({
    pageA,
  }) => {
    const topic = await createTopicViaApi("Censure Test Topic");

    // Cast 4 downvotes via API from different fingerprints to bring score to -4
    for (let i = 0; i < 4; i++) {
      await castVoteViaApi(topic.id, `api-voter-${i}`, "down");
    }

    // Reload to pick up the topic with score -4
    await reloadAndWaitForWs(pageA);
    await waitForTopicToAppear(pageA, "Censure Test Topic");

    // Cast the 5th downvote via UI (this pushes score to -5, triggering censure)
    const downvoteBtn = pageA.locator(`#topic-downvote-${topic.id}`);
    await downvoteBtn.click();

    // Topic should disappear from the board
    await waitForTopicToDisappear(pageA, topic.id);

    // Verify toast notification appears
    await expect(pageA.locator("text=censured")).toBeVisible({
      timeout: 5_000,
    });
  });
});
