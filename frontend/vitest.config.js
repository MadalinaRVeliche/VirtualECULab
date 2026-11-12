import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    // React component tests need DOM APIs. jsdom provides them without
    // launching Chromium; the Playwright suite covers the real browser.
    environment: "jsdom",

    // Keep Vitest focused on component and logic tests under src/.
    include: ["src/**/*.test.jsx"],

    // Register DOM matchers and clean up rendered components after each test.
    setupFiles: ["./src/test/setup.js"],
  },
});
