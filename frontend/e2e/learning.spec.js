import { test, expect } from "@playwright/test";

test("switches between theory and practice", async ({ page }) => {
  await page.goto("/");

  await page
    .getByRole("button", {
      name: "Theory",
      exact: true,
    })
    .click();

  await expect(
    page.getByRole("heading", {
      name: "CAN frames and CAPL transmission",
      exact: true,
    }),
  ).toBeVisible();

  await expect(page.getByLabel("CAPL code")).toBeHidden();

  await page
    .getByRole("button", {
      name: "Practice",
      exact: true,
    })
    .click();

  await expect(page.getByLabel("CAPL code")).toBeVisible();
});

test("grades the quiz and clears the result when an answer changes", async ({
  page,
}) => {
  await page.goto("/");

  await page
    .getByRole("button", {
      name: "Quiz",
      exact: true,
    })
    .click();

  const grade = page.getByRole("button", {
    name: "Grade quiz",
    exact: true,
  });

  await expect(grade).toBeDisabled();

  const correctAnswers = [
    "output(VehicleSpeed);",
    "50 km/h",
    "Trace window",
    "No, because counter 7 is repeated",
    "Wait for the required active state with a 100 ms deadline",
  ];

  for (const answer of correctAnswers) {
    await page
      .getByRole("radio", {
        name: answer,
        exact: true,
      })
      .check();
  }

  await grade.click();

  await expect(
    page.getByText("Score: 5 / 5", {
      exact: true,
    }),
  ).toBeVisible();

  await page
    .getByRole("radio", {
      name: "100 km/h",
      exact: true,
    })
    .check();

  await expect(page.getByText("Score: 5 / 5", { exact: true })).toHaveCount(0);

  await grade.click();

  await expect(
    page.getByText("Score: 4 / 5", {
      exact: true,
    }),
  ).toBeVisible();
});
