import { test, expect } from "@playwright/test";

async function openWorkbench(page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Workbench", exact: true }).click();
  return page.getByRole("region", { name: "CAN workbench" });
}

test("runs an edited relay program, records Rx and Tx, and plots decoded speed", async ({ page }) => {
  const workbench = await openWorkbench(page);
  await expect(workbench.getByRole("button", { name: "Inject Rx" })).toBeDisabled();
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  await expect(workbench.getByText(/Last: 100 km\/h/)).toBeVisible();
  await workbench.getByRole("button", { name: "Advance clock" }).click();
  await workbench.getByLabel("Rx bytes (hex)").fill("88 13");
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  await expect(workbench.getByText(/Last: 50 km\/h/)).toBeVisible();
  const rows = workbench.locator("tbody tr");
  await expect(rows).toHaveCount(4);
  await expect(rows.nth(2)).toContainText("Rx");
  await expect(rows.nth(2)).toContainText("120");
  await expect(rows.nth(3)).toContainText("Tx");
  await expect(rows.nth(3)).toContainText("123");
  await workbench.getByLabel("Graph signal").selectOption("");
  await expect(workbench.getByRole("img", { name: "CAN frame timeline over virtual time" })).toBeVisible();
  await workbench.getByLabel("CAPL node program").fill('on start { write("New program"); }');
  await expect(rows).toHaveCount(0);
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  await expect(workbench.getByText("[0 ms] New program")).toBeVisible();
});

test("applies an editable DBC and preserves the previous graph when validation fails", async ({ page }) => {
  const workbench = await openWorkbench(page);
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  await expect(workbench.getByText(/Last: 100 km\/h/)).toBeVisible();
  await workbench.getByText("DBC editor", { exact: true }).click();
  const dbc = workbench.getByLabel("DBC source");
  const original = await dbc.inputValue();
  await dbc.fill(original.replace("(0.01,0)", "(0.02,0)"));
  await workbench.getByRole("button", { name: "Apply DBC" }).click();
  await expect(workbench.getByText(/Last: 200 km\/h/)).toBeVisible();
  await dbc.fill("BO_ 3000 Invalid: 2 SpeedECU");
  await workbench.getByRole("button", { name: "Apply DBC" }).click();
  await expect(workbench.getByRole("alert")).toContainText("standard 11-bit CAN ID");
  await expect(workbench.getByText(/Last: 200 km\/h/)).toBeVisible();
});

test("checks a timer frame at the deadline and distinguishes pending, pass and fail", async ({ page }) => {
  const workbench = await openWorkbench(page);
  await workbench.getByLabel("CAPL example").selectOption("timer");
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  const module = workbench.getByRole("article", { name: "Test Module" });
  await module.getByLabel("Start waiting at").selectOption("start");
  const run = module.getByRole("button", { name: "Run trace check" });
  await run.click();
  await expect(module.getByRole("status")).toContainText("PENDING");
  await workbench.getByRole("button", { name: "Advance clock" }).click();
  await run.click();
  await expect(module.getByRole("status")).toContainText("PASS · Matching frame after 100 ms");
  await module.getByLabel("Deadline (ms)").fill("99");
  await run.click();
  await expect(module.getByRole("status")).toContainText("FAIL · First matching frame arrived after 100 ms");
});

test("does not use a stale response from a previous same-time input", async ({ page }) => {
  const workbench = await openWorkbench(page);
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  const module = workbench.getByRole("article", { name: "Test Module" });
  const run = module.getByRole("button", { name: "Run trace check" });
  await run.click();
  await expect(module.getByRole("status")).toContainText("PASS");
  await workbench.getByLabel("Rx ID (hex)").fill("121");
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  await run.click();
  await expect(module.getByRole("status")).toContainText("PENDING");
});

test("keeps the editor draft and fits a phone viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const workbench = await openWorkbench(page);
  await workbench.getByLabel("CAPL node program").fill("on start {}");
  await page.getByRole("button", { name: "Theory", exact: true }).click();
  await page.getByRole("button", { name: "Workbench", exact: true }).click();
  await expect(workbench.getByLabel("CAPL node program")).toHaveValue("on start {}");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test("transmits only after sending the matching key", async ({ page }) => {
  const workbench = await openWorkbench(page);
  await workbench.getByLabel("CAPL example").selectOption("transmit");
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  const send = workbench.getByRole("button", { name: "Send key" });
  await expect(send).toBeEnabled();
  const rows = workbench.locator("tbody tr");
  await expect(rows).toHaveCount(0);
  await workbench.getByLabel("Key", { exact: true }).fill("b");
  await send.click();
  await expect(send).toBeEnabled();
  await expect(rows).toHaveCount(0);
  await workbench.getByLabel("Key", { exact: true }).fill("a");
  await send.click();
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText("10 27");
});

test("rejects a short injected frame and can continue the measurement", async ({ page }) => {
  const workbench = await openWorkbench(page);
  await workbench.getByRole("button", { name: "Start measurement" }).click();
  await workbench.getByLabel("Rx bytes (hex)").fill("10");
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  await expect(workbench.getByRole("alert")).toBeVisible();
  await expect(workbench.locator("tbody tr")).toHaveCount(0);
  await workbench.getByLabel("Rx bytes (hex)").fill("10 27");
  await workbench.getByRole("button", { name: "Inject Rx" }).click();
  await expect(workbench.getByRole("alert")).toHaveCount(0);
  await expect(workbench.locator("tbody tr")).toHaveCount(2);
});
