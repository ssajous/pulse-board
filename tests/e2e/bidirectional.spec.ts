import { test } from "./fixtures/app.fixture";
import { resetDatabase } from "./helpers/api.helper";
import { waitForTopicToAppear } from "./helpers/wait.helper";

test.describe("Bidirectional updates", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("both browsers can create topics and see each other updates", async ({
    pageA,
    pageB,
  }) => {
    // Browser A creates a topic
    await pageA.fill("#topic-input", "From Browser A");
    await pageA.click("#topic-submit");
    await waitForTopicToAppear(pageB, "From Browser A");

    // Browser B creates a topic
    await pageB.fill("#topic-input", "From Browser B");
    await pageB.click("#topic-submit");
    await waitForTopicToAppear(pageA, "From Browser B");
  });
});
