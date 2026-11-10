import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "Virtual ECU Lab",
      exact: true,
    }),
  ).toBeVisible();
});

test("runs CAPL code and displays its output", async ({ page }) => {
  await page.getByLabel("CAPL code").fill(`
    on start
    {
      write("Browser test");
    }
  `);

  await page
    .getByRole("button", {
      name: "Run",
      exact: true,
    })
    .click();

  await expect(page.locator("article pre")).toHaveText("Browser test");
});

test("rejects messages in the wrong order", async ({ page }) => {
  await page
    .getByRole("button", {
      name: /2\. Multiple messages/,
    })
    .click();

  await page.getByLabel("CAPL code").fill(`
    on start
    {
      write("System ready");
      write("Starting ECU");
    }
  `);

  await page
    .getByRole("button", {
      name: "Check exercise",
      exact: true,
    })
    .click();

  await expect(page.getByRole("status")).toHaveText(
    "Expected messages in this exact order: Starting ECU → System ready",
  );
});

test("keeps completion visible after refreshing", async ({ page }) => {
  await page.getByLabel("CAPL code").fill(`
    on start
    {
      write("ECU ready");
    }
  `);

  await page
    .getByRole("button", {
      name: "Check exercise",
      exact: true,
    })
    .click();

  await expect(page.getByRole("status")).toHaveText(
    "Correct! You completed the exercise.",
  );

  const lessonButton = page.getByRole("button", {
    name: /1\. Your first CAPL event/,
  });

  await expect(lessonButton.locator(".completion-badge")).toHaveText(
    "Completed",
  );

  await page.reload();

  await expect(lessonButton.locator(".completion-badge")).toHaveText(
    "Completed",
  );
});

test("triggers a keyboard event only when its key is pressed", async ({
  page,
}) => {
  await page
    .getByRole("button", {
      name: /3\. Keyboard events/,
    })
    .click();

  await page.getByLabel("CAPL code").fill(`
    on key 'a'
    {
      write("Key A pressed");
    }
  `);

  await page
    .getByRole("button", {
      name: "Run",
      exact: true,
    })
    .click();

  await expect(
    page.getByRole("button", { name: "Run", exact: true }),
  ).toBeEnabled();

  await expect(
    page.getByText("No output to display.", { exact: true }),
  ).toBeVisible();

  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.locator("article pre")).toHaveCount(0);

  await page
    .getByRole("button", {
      name: "Press A",
      exact: true,
    })
    .click();

  await expect(page.locator("article pre")).toHaveText("Key A pressed");

  await page
    .getByRole("button", {
      name: "Check exercise",
      exact: true,
    })
    .click();

  await expect(page.getByRole("status")).toHaveText(
    "Correct! You completed the exercise.",
  );

  await expect(
    page
      .getByRole("button", {
        name: /3\. Keyboard events/,
      })
      .locator(".completion-badge"),
  ).toHaveText("Completed");
});
