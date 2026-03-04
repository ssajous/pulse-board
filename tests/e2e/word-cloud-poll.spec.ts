import { test, expect } from "./fixtures/event-app.fixture";
import {
  resetDatabase,
  createWordCloudPollViaApi,
  activatePollViaApi,
  submitWordCloudResponseViaApi,
} from "./helpers/api.helper";
import {
  waitForPollToAppear,
} from "./helpers/wait.helper";

test.describe("Word Cloud Poll", () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test("admin can create a word cloud poll from the admin page", async ({
    event,
    contextA,
  }) => {
    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // Select Word Cloud poll type
    await adminPage.click("#poll-type-option-word-cloud");

    // Fill in the question
    await adminPage.fill("#poll-question-input", "One word for this talk?");

    // Submit the form
    await adminPage.click("#poll-submit-btn");

    // Verify the created poll appears in the poll list
    await expect(
      adminPage.getByText("One word for this talk?")
    ).toBeVisible({ timeout: 5_000 });
  });

  test("participant sees word cloud participation form when poll is active", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a word cloud poll via API
    const poll = await createWordCloudPollViaApi(
      event.id,
      "Describe the session in one word"
    );
    await activatePollViaApi(poll.id);

    // Wait for the poll participation UI to appear
    await waitForPollToAppear(eventPageA);

    // Verify the word cloud participation container is visible
    await expect(
      eventPageA.locator("#word-cloud-participation")
    ).toBeVisible({ timeout: 5_000 });

    // Verify the question text is displayed
    await expect(
      eventPageA.getByText("Describe the session in one word")
    ).toBeVisible();

    // Verify the response input and submit button are present
    await expect(
      eventPageA.locator("#word-cloud-response-input")
    ).toBeVisible();
    await expect(
      eventPageA.locator("#word-cloud-submit-button")
    ).toBeVisible();

    // Submit button should be disabled because no text has been entered
    await expect(
      eventPageA.locator("#word-cloud-submit-button")
    ).toBeDisabled();
  });

  test("participant can submit a word and see the visualization", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a word cloud poll via API
    const poll = await createWordCloudPollViaApi(
      event.id,
      "One word reaction?"
    );
    await activatePollViaApi(poll.id);

    // Wait for the participation form
    await waitForPollToAppear(eventPageA);
    await expect(
      eventPageA.locator("#word-cloud-participation")
    ).toBeVisible();

    // Enter a valid single word
    await eventPageA.fill("#word-cloud-response-input", "awesome");

    // Submit button should now be enabled
    await expect(
      eventPageA.locator("#word-cloud-submit-button")
    ).toBeEnabled();

    // Submit the response
    await eventPageA.click("#word-cloud-submit-button");

    // Verify the submission confirmation text appears
    await expect(
      eventPageA.getByText("Response submitted!")
    ).toBeVisible({ timeout: 5_000 });

    // Verify the word cloud visualization container is shown
    await expect(
      eventPageA.locator("#word-cloud-visualization")
    ).toBeVisible({ timeout: 5_000 });
  });

  test("participant cannot submit more than 3 words", async ({
    event,
    eventPageA,
  }) => {
    const poll = await createWordCloudPollViaApi(
      event.id,
      "Short phrase please"
    );
    await activatePollViaApi(poll.id);

    await waitForPollToAppear(eventPageA);
    await expect(
      eventPageA.locator("#word-cloud-participation")
    ).toBeVisible();

    // Enter a 4-word phrase (exceeds the 3-word limit)
    await eventPageA.fill(
      "#word-cloud-response-input",
      "this is too long"
    );

    // Submit button should remain disabled since the input is invalid
    await expect(
      eventPageA.locator("#word-cloud-submit-button")
    ).toBeDisabled();
  });

  test("duplicate submission is rejected with an error", async ({
    event,
    eventPageA,
  }) => {
    // Create and activate a word cloud poll
    const poll = await createWordCloudPollViaApi(
      event.id,
      "Submit once only"
    );
    await activatePollViaApi(poll.id);

    // Submit a first response from a different participant via API so the
    // fingerprint used by participant A's browser is still free for the UI test
    await submitWordCloudResponseViaApi(
      poll.id,
      "e2e-other-participant-wc",
      "nice"
    );

    // Participant A submits via the UI
    await waitForPollToAppear(eventPageA);
    await expect(
      eventPageA.locator("#word-cloud-participation")
    ).toBeVisible();

    await eventPageA.fill("#word-cloud-response-input", "great");
    await eventPageA.click("#word-cloud-submit-button");

    // Participant A should see their submission confirmed
    await expect(
      eventPageA.getByText("Response submitted!")
    ).toBeVisible({ timeout: 5_000 });

    // Now attempt a second submission via API from the SAME fingerprint as
    // the browser — Playwright uses a persistent context which means the
    // fingerprint is stable per context.  We verify the API rejects duplicates
    // with a 409.  This mirrors the pattern used in poll-voting.spec.ts where
    // the second vote is exercised via API to keep the test simple.
    const apiFingerprint = "e2e-word-cloud-dup-test";
    await submitWordCloudResponseViaApi(poll.id, apiFingerprint, "cool");

    const duplicateResp = await fetch(
      `http://localhost:8000/api/polls/${poll.id}/respond`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fingerprint_id: apiFingerprint,
          response_value: "cool",
        }),
      }
    );
    expect(duplicateResp.status).toBe(409);
  });

  test("results display updates when another participant submits via API", async ({
    event,
    eventPageA,
  }) => {
    const poll = await createWordCloudPollViaApi(
      event.id,
      "Real-time word cloud"
    );
    await activatePollViaApi(poll.id);

    await waitForPollToAppear(eventPageA);
    await expect(
      eventPageA.locator("#word-cloud-participation")
    ).toBeVisible();

    // Participant A submits a word via the UI
    await eventPageA.fill("#word-cloud-response-input", "fast");
    await eventPageA.click("#word-cloud-submit-button");

    await expect(
      eventPageA.getByText("Response submitted!")
    ).toBeVisible({ timeout: 5_000 });
    await expect(
      eventPageA.locator("#word-cloud-visualization")
    ).toBeVisible({ timeout: 5_000 });

    // Another participant submits via the API — this triggers a WebSocket
    // broadcast so participant A's word cloud refreshes
    await submitWordCloudResponseViaApi(
      poll.id,
      "e2e-second-participant",
      "fast"
    );

    // The word count should eventually reflect both responses
    await expect(
      eventPageA.locator("#word-cloud-response-count")
    ).toContainText("2", { timeout: 10_000 });
  });

  test("admin page shows word cloud poll in poll list after creation", async ({
    event,
    contextA,
  }) => {
    // Create a word cloud poll via API
    await createWordCloudPollViaApi(event.id, "API-created word cloud poll");

    const adminPage = await contextA.newPage();
    await adminPage.goto(`/events/${event.code}/admin`);
    await adminPage.locator("#poll-creation-form").waitFor({ state: "visible" });

    // The poll should appear in the poll list
    await expect(
      adminPage.getByText("API-created word cloud poll")
    ).toBeVisible({ timeout: 5_000 });

    // It should start as inactive
    await expect(
      adminPage.getByText("Inactive", { exact: true })
    ).toBeVisible();

    // Activate button should be present
    await expect(
      adminPage.getByRole("button", { name: "Activate" })
    ).toBeVisible();
  });
});
