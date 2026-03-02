import { test, expect } from "./fixtures/event-app.fixture";
import {
  resetDatabase,
  createPollViaApi,
  activatePollViaApi,
  submitPollResponseViaApi,
} from "./helpers/api.helper";
import {
  waitForPollToAppear,
  waitForPollResults,
} from "./helpers/wait.helper";

test.describe("Poll voting", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("participant can see active poll question and options", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a poll via API
    const poll = await createPollViaApi(
      event.id,
      "Which framework do you prefer?",
      ["React", "Vue", "Angular"],
    );
    await activatePollViaApi(poll.id);

    // Wait for the poll to appear on the participant's page
    await waitForPollToAppear(eventPageA);

    // Verify question is visible
    await expect(
      eventPageA.getByText("Which framework do you prefer?")
    ).toBeVisible();

    // Verify all options are visible
    await expect(eventPageA.getByText("React")).toBeVisible();
    await expect(eventPageA.getByText("Vue")).toBeVisible();
    await expect(eventPageA.getByText("Angular")).toBeVisible();

    // Verify submit button is present but disabled (no option selected)
    await expect(
      eventPageA.locator("#poll-submit-response-btn")
    ).toBeVisible();
    await expect(
      eventPageA.locator("#poll-submit-response-btn")
    ).toBeDisabled();
  });

  test("participant can select an option and submit their vote", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a poll
    const poll = await createPollViaApi(
      event.id,
      "Favorite season?",
      ["Spring", "Summer", "Autumn", "Winter"],
    );
    await activatePollViaApi(poll.id);

    await waitForPollToAppear(eventPageA);

    // Select an option by clicking the radio button
    const firstOptionId = poll.options[0].id;
    await eventPageA.click(`#poll-option-radio-${firstOptionId}`);

    // Submit button should now be enabled
    await expect(
      eventPageA.locator("#poll-submit-response-btn")
    ).toBeEnabled();

    // Submit the vote
    await eventPageA.click("#poll-submit-response-btn");

    // After voting, results should be displayed
    await waitForPollResults(eventPageA);

    // Verify results container is visible with the poll question context
    await expect(eventPageA.getByText("Poll Results")).toBeVisible();
  });

  test("after voting, results display vote counts and percentages", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a poll
    const poll = await createPollViaApi(
      event.id,
      "Best meal of the day?",
      ["Breakfast", "Lunch", "Dinner"],
    );
    await activatePollViaApi(poll.id);

    await waitForPollToAppear(eventPageA);

    // Select the first option and submit
    const firstOptionId = poll.options[0].id;
    await eventPageA.click(`#poll-option-radio-${firstOptionId}`);
    await eventPageA.click("#poll-submit-response-btn");

    // Wait for results to appear
    await waitForPollResults(eventPageA);

    // Verify the results bar for the voted option exists
    await expect(
      eventPageA.locator(`#poll-results-bar-${firstOptionId}`)
    ).toBeVisible();

    // Verify vote count and percentage text is present
    // The voted option should show 1 vote at 100%
    await expect(
      eventPageA.locator(`#poll-results-bar-${firstOptionId}`)
    ).toContainText("1 (100%)");
  });

  test("multiple participants voting updates results in real-time", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a poll
    const poll = await createPollViaApi(
      event.id,
      "Team building activity?",
      ["Bowling", "Escape Room", "Trivia Night"],
    );
    await activatePollViaApi(poll.id);

    // Wait for participant A to see the poll
    await waitForPollToAppear(eventPageA);

    // Participant A votes for the first option via UI
    const option1Id = poll.options[0].id;
    await eventPageA.click(`#poll-option-radio-${option1Id}`);
    await eventPageA.click("#poll-submit-response-btn");

    // Wait for results to appear for participant A
    await waitForPollResults(eventPageA);

    // Participant A should see 1 vote (100%) for their option
    await expect(
      eventPageA.locator(`#poll-results-bar-${option1Id}`)
    ).toContainText("1 (100%)");

    // Simulate another participant voting via API with a different fingerprint.
    // This triggers a WebSocket broadcast of updated results.
    const option2Id = poll.options[1].id;
    await submitPollResponseViaApi(
      poll.id,
      "e2e-other-participant",
      option2Id,
    );

    // Participant A's results should be updated via WebSocket broadcast
    // Both options should now show 1 vote each (50%)
    await expect(
      eventPageA.locator(`#poll-results-bar-${option1Id}`)
    ).toContainText("1 (50%)", { timeout: 10_000 });
    await expect(
      eventPageA.locator(`#poll-results-bar-${option2Id}`)
    ).toContainText("1 (50%)", { timeout: 5_000 });
  });

  test("participant cannot vote twice on the same poll", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a poll
    const poll = await createPollViaApi(
      event.id,
      "One-time vote test",
      ["Choice A", "Choice B"],
    );
    await activatePollViaApi(poll.id);

    await waitForPollToAppear(eventPageA);

    // Vote for the first option
    const firstOptionId = poll.options[0].id;
    await eventPageA.click(`#poll-option-radio-${firstOptionId}`);
    await eventPageA.click("#poll-submit-response-btn");

    // After voting, results are shown instead of the participation form
    await waitForPollResults(eventPageA);

    // The participation form should no longer be visible
    await expect(
      eventPageA.locator("#poll-participation")
    ).not.toBeVisible();

    // The submit button should not be visible (replaced by results)
    await expect(
      eventPageA.locator("#poll-submit-response-btn")
    ).not.toBeVisible();
  });
});
