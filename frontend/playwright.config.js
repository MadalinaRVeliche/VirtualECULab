import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  reporter: "list",
  webServer: process.env.CI
    ? [
        {
          command:
            "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000",
          cwd: "..",
          url: "http://127.0.0.1:8000/health",
          reuseExistingServer: false,
          timeout: 60_000,
        },
        {
          command: "npm run dev -- --host localhost --port 5173 --strictPort",
          url: "http://localhost:5173",
          reuseExistingServer: false,
          timeout: 60_000,
        },
      ]
    : undefined,
  use: {
    baseURL: "http://localhost:5173",
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
