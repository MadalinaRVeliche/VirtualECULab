import { test, expect } from "@playwright/test";

test("opens an applied chapter and remembers the theory language", async ({
  page,
}) => {
  await page.goto("/");

  const tabs = page.getByRole("navigation", { name: "Learning sections" });
  await expect(tabs.getByRole("button")).toHaveText([
    "Theory",
    "Quiz",
    "Workbench",
  ]);

  const contents = page.getByRole("navigation", { name: "Cuprins" });
  await contents
    .getByRole("link", { name: "Din cadrul CAN la viteza din grafic" })
    .click();
  await expect(page).toHaveURL(/#theory-can-dbc$/);

  await page
    .getByRole("combobox", { name: "Limba teoriei" })
    .selectOption("en");
  await expect(
    page.getByRole("heading", { name: "Applied theory" }),
  ).toBeVisible();

  await page.reload();

  await expect(
    page.getByRole("combobox", { name: "Theory language" }),
  ).toHaveValue("en");
  await expect(
    page.getByRole("heading", {
      name: "From a CAN frame to speed on the graph",
    }),
  ).toBeVisible();
});

test("grades a course quiz, saves it and replaces all ten prompts", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  const quiz = page.getByRole("region", { name: "Course quiz" });
  const groups = quiz
    .getByRole("form", { name: "Quiz answers" })
    .getByRole("group");
  await expect(groups).toHaveCount(10);
  const grade = quiz.getByRole("button", { name: "Grade quiz" });
  await expect(grade).toBeDisabled();
  for (const group of await groups.all())
    await group.getByRole("radio").first().check();
  await grade.click();
  const score = quiz.getByText(/^Score: \d+ \/ 10$/);
  await expect(score).toBeVisible();
  const previous = await quiz.locator("legend").allTextContents();
  await quiz.getByRole("button", { name: "New quiz" }).click();
  await expect(score).toHaveCount(0);
  await expect(groups).toHaveCount(10);
  const current = await quiz.locator("legend").allTextContents();
  const prompts = (labels) =>
    labels.map((label) => label.replace(/^\d+\. /, ""));
  expect(new Set(prompts(current)).size).toBe(10);
  expect(
    prompts(current).filter((prompt) => prompts(previous).includes(prompt)),
  ).toEqual([]);
  await page.reload();
  await page.getByRole("button", { name: "Quiz", exact: true }).click();
  await quiz.getByText("Quiz history", { exact: true }).click();
  await expect(quiz.getByText(/^\d+\/10 ·/).first()).toBeVisible();
});
