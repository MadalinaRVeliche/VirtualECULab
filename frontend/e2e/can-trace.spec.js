import { test, expect } from "@playwright/test";

test("inspects a CAN frame and clears the trace", async ({ page }) => {
  await page.goto("/");

  const trace = page.getByRole("region", {
    name: "CAN Trace — Frame Preview",
  });

  await trace.getByLabel("CAN identifier (hex)").fill("123");
  await trace.getByLabel("Data bytes (hex)").fill("10 27");

  await trace
    .getByRole("button", {
      name: "Inspect frame",
      exact: true,
    })
    .click();

  const row = trace.locator("tbody tr");

  await expect(row).toHaveCount(1);
  await expect(row.getByRole("cell")).toHaveText([
    "1",
    "0x123",
    "Standard data",
    "2",
    "10 27",
  ]);

  await trace
    .getByRole("button", {
      name: "Clear trace",
    })
    .click();

  await expect(row).toHaveCount(0);
});
