import { test, expect } from "@playwright/test";

const SPEED = `variables { message 0x123 VehicleSpeed; }
on key 'a' {
  VehicleSpeed.dlc = 2;
  VehicleSpeed.byte(0) = 0x10; VehicleSpeed.byte(1) = 0x27;
  output(VehicleSpeed);
  VehicleSpeed.byte(0) = 0x88; VehicleSpeed.byte(1) = 0x13;
  output(VehicleSpeed);
}`;
const TIMER = `variables { msTimer heartbeat; message 0x300 Heartbeat; }
on start { Heartbeat.dlc = 1; Heartbeat.byte(0) = 1; setTimer(heartbeat,100); }
on timer heartbeat { output(Heartbeat); setTimer(heartbeat,100); }
on key 's' { cancelTimer(heartbeat); }
on key 'r' { setTimer(heartbeat,100); }`;
const WATCHDOG = `variables { msTimer watchdog; int timedOut = 0; }
on start { setTimer(watchdog,500); }
on message 0x300 { timedOut = 0; setTimer(watchdog,500); }
on timer watchdog { timedOut = 1; write("Communication timeout"); }`;

async function selectModule(page, title) {
  await page.goto("/");
  await page.getByRole("button", { name: title }).click();
  return page.getByRole("region", { name: "Practice workspace", exact: true });
}

test("transmits 100 then 50 and rejects logging alone", async ({ page }) => {
  const practice = await selectModule(page, /4\. Transmit vehicle speed/);
  await practice.getByLabel("CAPL code", { exact: true }).fill(SPEED);
  await practice
    .getByRole("button", { name: "Start simulation", exact: true })
    .click();
  await practice.getByRole("button", { name: "Send key", exact: true }).click();
  const rows = practice
    .getByRole("region", { name: "CAN Trace" })
    .locator("tbody tr");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(0)).toContainText("10 27");
  await expect(rows.nth(1)).toContainText("88 13");
  await practice
    .getByRole("button", { name: "Check exercise", exact: true })
    .click();
  await expect(
    practice.getByRole("status").filter({ hasText: "Correct!" }),
  ).toBeVisible();
  await practice
    .getByLabel("CAPL code", { exact: true })
    .fill("on key 'a' { write(\"100 then 50 sent\"); }");
  await practice
    .getByRole("button", { name: "Check exercise", exact: true })
    .click();
  await expect(
    practice.getByText("Not yet. Inspect the scenario evidence below.", {
      exact: true,
    }),
  ).toBeVisible();
});

test("persistent state survives actions and section switches", async ({
  page,
}) => {
  const practice = await selectModule(page, /5\. Multiple events and state/);
  await practice
    .getByLabel("CAPL code", { exact: true })
    .fill(
      `variables { int count = 0; message 0x200 Status; } on start { Status.dlc = 1; } on key 'a' { count++; Status.byte(0) = count; output(Status); }`,
    );
  await practice
    .getByRole("button", { name: "Start simulation", exact: true })
    .click();
  await practice.getByRole("button", { name: "Send key", exact: true }).click();
  await page.getByRole("button", { name: "Theory", exact: true }).click();
  await page.getByRole("button", { name: "Practice", exact: true }).click();
  await practice.getByRole("button", { name: "Send key", exact: true }).click();
  const rows = practice
    .getByRole("region", { name: "CAN Trace" })
    .locator("tbody tr");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(1)).toContainText("02");
});

test("advances virtual time and cancels periodic traffic", async ({ page }) => {
  const practice = await selectModule(page, /6\. Timers and periodic traffic/);
  await practice.getByLabel("CAPL code", { exact: true }).fill(TIMER);
  await practice
    .getByRole("button", { name: "Start simulation", exact: true })
    .click();
  await practice.getByLabel("Advance time (ms)").fill("300");
  await practice
    .getByRole("button", { name: "Advance clock", exact: true })
    .click();
  await expect(practice.getByTestId("virtual-clock")).toHaveText("300 ms");
  const rows = practice
    .getByRole("region", { name: "CAN Trace" })
    .locator("tbody tr");
  await expect(rows).toHaveCount(3);
  await practice.getByLabel("Key character").fill("s");
  await practice.getByRole("button", { name: "Send key", exact: true }).click();
  await practice
    .getByRole("button", { name: "Advance clock", exact: true })
    .click();
  await expect(practice.getByTestId("virtual-clock")).toHaveText("600 ms");
  await expect(rows).toHaveCount(3);
});

test("receives a frame and detects subsequent silence", async ({ page }) => {
  const practice = await selectModule(page, /7\. Reception and watchdogs/);
  await practice.getByLabel("CAPL code", { exact: true }).fill(WATCHDOG);
  await practice
    .getByRole("button", { name: "Start simulation", exact: true })
    .click();
  await practice
    .getByRole("button", { name: "Advance clock", exact: true })
    .click();
  await expect(practice.getByTestId("virtual-clock")).toHaveText("100 ms");
  await practice
    .getByRole("button", { name: "Inject Rx frame", exact: true })
    .click();
  await practice.getByLabel("Advance time (ms)").fill("499");
  await practice
    .getByRole("button", { name: "Advance clock", exact: true })
    .click();
  await expect(practice.locator(".console")).toHaveText("No console output.");
  await practice.getByLabel("Advance time (ms)").fill("1");
  await practice
    .getByRole("button", { name: "Advance clock", exact: true })
    .click();
  await expect(practice.locator(".console")).toContainText(
    "[600 ms] Communication timeout",
  );
});

test("signal decoder reacts to byte order and checks configuration", async ({
  page,
}) => {
  const practice = await selectModule(page, /8\. Signals and DBC/);
  await practice
    .getByRole("button", { name: "Decode payload", exact: true })
    .click();
  await expect(
    practice.getByText("Raw 10000 → 100 km/h", { exact: true }),
  ).toBeVisible();
  await practice.getByLabel("Byte order").selectOption("big");
  await practice
    .getByRole("button", { name: "Check exercise", exact: true })
    .click();
  await expect(
    practice.getByText("Not yet. Inspect the scenario evidence below.", {
      exact: true,
    }),
  ).toBeVisible();
  await practice.getByLabel("Byte order").selectOption("little");
  await practice
    .getByRole("button", { name: "Check exercise", exact: true })
    .click();
  await expect(
    practice.getByText("Correct! You completed the exercise.", { exact: true }),
  ).toBeVisible();
});

test("E2E explorer separates CRC faults and repeated counters", async ({
  page,
}) => {
  const practice = await selectModule(page, /9\. E2E integrity and sequence/);
  await practice
    .getByRole("button", { name: "Run explorer", exact: true })
    .click();
  await expect(
    practice.locator("tbody tr").filter({ hasText: "REPEATED" }),
  ).toHaveCount(1);
  await practice
    .getByLabel("Corrupt CRC at index (-1 = none)", { exact: true })
    .fill("4");
  await practice
    .getByRole("button", { name: "Run explorer", exact: true })
    .click();
  await expect(
    practice.locator("tbody tr").filter({ hasText: "WRONG_CRC" }),
  ).toHaveCount(1);
  const predictions = ["INITIAL", "OK", "OK", "REPEATED", "WRONG_CRC", "OK"];
  for (let index = 0; index < predictions.length; index++)
    await practice
      .locator(".prediction select")
      .nth(index)
      .selectOption(predictions[index]);
  await practice
    .getByRole("button", { name: "Check exercise", exact: true })
    .click();
  await expect(
    practice.getByText("Correct! You completed the exercise.", { exact: true }),
  ).toBeVisible();
});

test("test bench checks timing and setup predictions", async ({ page }) => {
  const practice = await selectModule(page, /10\. Test verdicts and deadlines/);
  await practice.getByLabel("Checking strategy").selectOption("event");
  for (const [index, verdict] of [
    "PASS",
    "PASS",
    "FAIL",
    "FAIL",
    "NOT_EXECUTED",
  ].entries())
    await practice
      .locator(".prediction select")
      .nth(index)
      .selectOption(verdict);
  await practice
    .getByRole("button", { name: "Check exercise", exact: true })
    .click();
  await expect(
    practice.getByText("Correct! You completed the exercise.", { exact: true }),
  ).toBeVisible();
});

test("ADAS explorer changes state for sensor failure", async ({ page }) => {
  const practice = await selectModule(page, /11\. ADAS scenario reasoning/);
  await practice
    .getByRole("button", { name: "Run explorer", exact: true })
    .click();
  await expect(practice.locator(".tool-result")).toContainText("BRAKE_REQUEST");
  await practice.getByLabel("Sensors valid", { exact: true }).uncheck();
  await practice
    .getByRole("button", { name: "Run explorer", exact: true })
    .click();
  await expect(practice.locator(".tool-result")).toContainText("DEGRADED");
});

test("independent speed challenge has different targets", async ({ page }) => {
  await selectModule(page, /4\. Transmit vehicle speed/);
  await page.getByRole("button", { name: "Challenges", exact: true }).click();
  const challenge = page.getByRole("region", {
    name: "Challenge workspace",
    exact: true,
  });
  await challenge.getByLabel("Challenge program", { exact: true }).fill(SPEED);
  await challenge
    .getByRole("button", { name: "Check challenge", exact: true })
    .click();
  await expect(
    challenge.getByText("Not yet. Inspect the scenario evidence below.", {
      exact: true,
    }),
  ).toBeVisible();
  await challenge
    .getByLabel("Challenge program", { exact: true })
    .fill(
      SPEED.replace("0x10", "0xC4")
        .replace("0x27", "0x09")
        .replace("0x88", "0x4C")
        .replace("0x13;", "0x1D;"),
    );
  await challenge
    .getByRole("button", { name: "Check challenge", exact: true })
    .click();
  await expect(
    challenge.getByText("Correct! You completed the challenge.", {
      exact: true,
    }),
  ).toBeVisible();
  await page.reload();
  await page
    .getByRole("button", { name: /4\. Transmit vehicle speed/ })
    .click();
  await page.getByRole("button", { name: "Progress", exact: true }).click();
  await expect(
    page.getByText("Challenge", { exact: true }).locator(".."),
  ).toContainText("Completed");
});

test("theory review is separate from completion and survives reload", async ({
  page,
}) => {
  await selectModule(page, /11\. ADAS scenario reasoning/);
  await page.getByRole("button", { name: "Theory", exact: true }).click();
  const reviewed = page.getByRole("button", {
    name: "Mark theory reviewed",
    exact: true,
  });
  if (await reviewed.count()) await reviewed.click();
  await expect(
    page.getByRole("button", { name: "Theory reviewed", exact: true }),
  ).toBeDisabled();
  await page.reload();
  await page
    .getByRole("button", { name: /11\. ADAS scenario reasoning/ })
    .click();
  await page.getByRole("button", { name: "Progress", exact: true }).click();
  await expect(
    page
      .locator(".milestone-grid")
      .getByText("Theory", { exact: true })
      .locator(".."),
  ).toContainText("Reviewed");
});

test("quiz attempt history is persisted", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  const answers = [
    "output(VehicleSpeed);",
    "50 km/h",
    "Trace window",
    "No, because counter 7 is repeated",
    "Wait for the required active state with a 100 ms deadline",
  ];
  for (const answer of answers)
    await page.getByRole("radio", { name: answer, exact: true }).check();
  await page.getByRole("button", { name: "Grade quiz", exact: true }).click();
  await expect(page.getByText("Score: 5 / 5", { exact: true })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Progress", exact: true }).click();
  await expect(page.getByText("100%", { exact: true })).toBeVisible();
  await expect(page.getByText(/5\/5 ·/).first()).toBeVisible();
});

test("mobile navigation stays within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page
    .getByRole("button", { name: /9\. E2E integrity and sequence/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "E2E integrity and sequence",
      exact: true,
    }),
  ).toBeVisible();
  const width = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(width).toBeLessThanOrEqual(390);
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Knowledge check" }),
  ).toBeVisible();
});

test("workspace loads without browser errors or duplicate control IDs", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page
    .getByRole("button", { name: /4\. Transmit vehicle speed/ })
    .click();
  await page.getByRole("button", { name: "Challenges", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Challenge workspace", exact: true }),
  ).toBeVisible();
  const duplicates = await page.evaluate(() => {
    const ids = [...document.querySelectorAll("[id]")].map((node) => node.id);
    return ids.filter((id, index) => ids.indexOf(id) !== index);
  });
  expect(duplicates).toEqual([]);
  expect(errors).toEqual([]);
});
