import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",

  // Quiz scenarios use the same test database. Run browser tests serially
  // so requests from different workers do not interleave.
  fullyParallel: false,
  workers: 1,

  // Fail CI if a focused test is accidentally committed with test.only().
  forbidOnly: Boolean(process.env.CI),
  reporter: "list",

  // CI starts both servers and waits for their URLs to respond.
  // For local runs, start FastAPI and Vite before running Playwright.
  webServer: process.env.CI
    ? [
        {
          command:
            "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000",

          // Run from the repository root so Python can import backend.main.
          cwd: "..",
          url: "http://127.0.0.1:8000/health",
          reuseExistingServer: false,
          timeout: 60_000,
        },
        {
          // Keep Vite on the port expected by baseURL and the backend's
          // CORS settings. Fail if that port is already occupied.
          command: "npm run dev -- --host localhost --port 5173 --strictPort",
          url: "http://localhost:5173",
          reuseExistingServer: false,
          timeout: 60_000,
        },
      ]
    : undefined,

  use: {
    // Tests can use page.goto("/") and resolve it against the frontend.
    baseURL: "http://localhost:5173",
    browserName: "chromium",

    // Allow a runner to supply its own Chromium executable. Otherwise,
    // use the browser installed by Playwright with its default options.
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? {
          executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
          args: ["--no-sandbox"],
        }
      : undefined,

    // Keep debugging artifacts for failed tests: a screenshot of the page
    // and a trace for inspecting the sequence of browser actions.
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
