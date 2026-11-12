// Register DOM assertions such as toBeVisible() and toBeDisabled().
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Unmount React trees between tests so later queries cannot match
// elements left by an earlier render.
afterEach(cleanup);
