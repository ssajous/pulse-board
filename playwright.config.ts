import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  reporter: process.env.CI ? "html" : "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "PULSE_BOARD_TEST_MODE=true uv run uvicorn" +
        " pulse_board.presentation.api.app:create_app" +
        " --host 0.0.0.0 --port 8000 --factory",
      url: "http://localhost:8000/health",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "cd frontend && npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
