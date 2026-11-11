import { test, expect } from "@playwright/test";

test("inspects a CAN frame and clears the trace", async ({ page }) => {
  await page.goto("/");

  const trace = page.getByRole("region", {
    name: "CAN Trace",
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
    "Preview",
    "—",
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

test("CAPL output adds a transmitted frame to the trace", async ({ page }) => {
  await page.goto("/");

  await page
    .getByRole("button", {
      name: /3\. Keyboard events/,
    })
    .click();

  await page.getByLabel("CAPL code").fill(`
    variables
    {
      message 0x123 VehicleSpeed;
    }

    on key 'a'
    {
      VehicleSpeed.dlc = 2;
      VehicleSpeed.byte(0) = 0x10;
      VehicleSpeed.byte(1) = 0x27;
      output(VehicleSpeed);
      write("Speed frame sent");
    }
  `);

  await page
    .getByRole("button", {
      name: "Press A",
      exact: true,
    })
    .click();

  await expect(page.locator("article pre")).toHaveText("Speed frame sent");

  const trace = page.getByRole("region", {
    name: "CAN Trace",
  });

  const row = trace.locator("tbody tr");

  await expect(row).toHaveCount(1);
  await expect(row.getByRole("cell")).toHaveText([
    "1",
    "CAPL Tx",
    "—",
    "0x123",
    "Standard data",
    "2",
    "10 27",
  ]);
});
